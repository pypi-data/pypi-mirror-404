# Copyright (C) 2024- Davide Mollica <davide.mollica@inaf.it>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of iactsim.
#
# iactsim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iactsim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with iactsim.  If not, see <https://www.gnu.org/licenses/>.

import time
from typing import (
    Tuple, List, 
    Union, Optional
)

import cupy as cp
import numpy as np
from tqdm.auto import tqdm
import random

from .optics._optical_system import OpticalSystem
from .optics.utils._aspheric_coeffs import normalize_aspheric_coefficients
from .optics._cpu_transforms import local_to_telescope_rotation
from .optics._surface_misc import SurfaceShape, SensorSurfaceType
from .optics._atmosphere import AtmosphericTransmission
from .optics._materials import Materials
from .optics import ray_tracing

from .electronics import CherenkovCamera, CherenkovSiPMCamera

from .utils._timer import BenchmarkTimer


class IACT:
    """A class to represent an Imaging Atmospheric Cherenkov Telescope (IACT).

    This class serves as a wrapper for a CUDA-accelerated backend. It handles the conversion 
    of optical system and camera information into CuPy ndarrays (transferring data to the GPU), 
    and arranges this data in a format suitable for input to the CUDA kernels that perform the 
    actual simulation.

    Parameters
    ----------
    optical_system : OpticalSystem
        An instance of a class derived from :py:class:`OpticalSystem` representing the 
        telescope optical system.
    camera : CherenkovCamera
        An instance of a class derived from :py:class:`CherenkovCamera` representing the 
        telescope Cherenkov camera.
    position : Tuple[float, float, float] | List[float] | numpy.ndarray
        The Cartesian coordinates (x, y, z) representing the telescope 
        position in millimeters. Can be a tuple, list, or NumPy array.
    pointing : Tuple[float, float] | List[float] | numpy.ndarray
        The horizontal coordinates (altitude, azimuth) representing the 
        telescope pointing direction in degrees. Can be a tuple, list, 
        or NumPy array.    
    
    Raises
    ------
    TypeError
        
        - If optical_system is not an instance of :py:class:`OpticalSystem` or a derived class.
        - If camera is not an instance of :py:class:`CherenkovCamera` or a derived class.

    ValueError
        
        - If position does not have 3 elements.
        - If pointing does not have 2 elements.

    """

    def __init__(
        self,
        optical_system: OpticalSystem,
        camera: CherenkovCamera = None,
        position: Tuple[float, float, float] | List[float] | np.ndarray = (0.,0.,0.),
        pointing: Tuple[float, float] | List[float] | np.ndarray = (0,0),
    ):
        if not isinstance(optical_system, OpticalSystem):
            raise TypeError("optical_system must be an instance of OpticalSystem or a derived class")

        # Validate and convert position to NumPy array
        if not isinstance(position, (tuple, list, np.ndarray)) or len(position) != 3:
            raise ValueError("position must be a tuple, list, or NumPy array of length 3")

        self._cuda_tracing_args = [None] * 5 # ray-tracing kernel related arguments
        self._cuda_atmosphere_args = [None] * 5 # atmosphere transmission related arguments
        self._cuda_materials_args = [None] * 5 # materials refractive index args
        
        self._position = np.asarray(position)

        self.pointing = pointing

        self._optical_system = optical_system
        self._camera = camera

        self.atmospheric_transmission = AtmosphericTransmission()

        # Benchmark
        self.timer = BenchmarkTimer()
        self.timer.add_section('simulate_response')

        self.show_progress = False

        self._blocksize = 128 # Threads per block

    @property
    def position(self) -> np.ndarray:
        """
        numpy.ndarray: The telescope position in Cartesian coordinates (x, y, z) 
                    in millimeters.
        """
        return self._position

    @position.setter
    def position(self, value: Tuple[float, float, float] | List[float] | np.ndarray):
        if not isinstance(value, (tuple, list, np.ndarray)) or len(value) != 3:
            raise ValueError("position must be a tuple, list, or NumPy array of length 3")
        self._position = np.asarray(value)
        self._cuda_telescope_init()

    @property
    def pointing(self) -> np.ndarray:
        """
        numpy.ndarray: The telescope pointing direction in horizontal 
                    coordinates (altitude, azimuth) in degrees.
        """
        return self._pointing

    @pointing.setter
    def pointing(self, value: Tuple[float, float] | List[float] | np.ndarray):
        if not isinstance(value, (tuple, list, np.ndarray)) or len(value) != 2:
            raise ValueError("pointing must be a tuple, list, or NumPy array of length 2")
        self._pointing = np.asarray(value)
        self._altitude = value[0]
        self._azimuth = value[1]
        self._cuda_telescope_init()
    
    @property
    def altitude(self) -> float:
        """
        float: Telescope pointing altitude (0-90).
        """
        return self._altitude
    
    @altitude.setter
    def altitude(self, value: float):
        if value < 0 or value > 90:
            raise(ValueError('Telescope pointing altitude must be between 0 (horizon) and 90 (zenith) degrees.'))
        self._altitude = value
        self._pointing[0] = value
        self._cuda_telescope_init()

    @property
    def azimuth(self) -> float:
        """
        float: Telescope pointing azimuth (0-360).
        """
        return self._azimuth
    
    @azimuth.setter
    def azimuth(self, value: float):
        if value < 0 or value > 360:
            raise(ValueError('Telescope pointing azimuth must be between 0 and 360 degrees (increasing from north to east).'))
        self._azimuth = value
        self._pointing[1] = value
        self._cuda_telescope_init()
    
    @property
    def optical_system(self) -> OpticalSystem:
        """
        OpticalSystem: The telescope optical system
        """
        return self._optical_system
    
    @property
    def camera(self) -> CherenkovCamera:
        """
        CherenkovCamera: The telescope Cherenkov camera.
        """
        return self._camera

    @camera.setter
    def camera(self, a_camera):
        if a_camera is not None and not isinstance(a_camera, CherenkovCamera):
            raise TypeError("camera must be an instance of CherenkovCamera or a derived class")
        self._camera = a_camera

    def _cuda_telescope_init(self):
        # Position and rotation to transform into the telescope reference frame
        telescope_rot = cp.asarray(local_to_telescope_rotation(*self.pointing), dtype=cp.float32)
        telescope_pos = cp.asarray(self.position, dtype=cp.float32)
        
        self._cuda_tracing_args[0] = telescope_pos
        self._cuda_tracing_args[1] = telescope_rot
    
    def _cuda_surfaces_init(self):
        """Prepares optical surface data for CUDA-based ray tracing.

        This function extracts relevant properties from the optical surfaces
        defined in :py:attr:`optical_system` and converts them into CuPy arrays.
        """

        NUM_ASPHERIC_COEFFS = 10
        ROT_MATRIX_SIZE = 9

        surface_data_dtype = np.dtype([
            ('position',              np.float32, 3),                   # 12 bytes
            ('_pad1',                 np.uint8,   4),                   # ! Padding to align 'offset' (float2) to 8 bytes (12+4=16)
            ('offset',                np.float32, 2),                   # 8 bytes (starts at 16)
            ('rotation_matrix',       np.float32, ROT_MATRIX_SIZE),     # 36 bytes (starts at 24)
            ('curvature',             np.float32),                      # 4 bytes (starts at 60)
            ('conic_constant',        np.float32),                      # 4 bytes (starts at 64)
            ('aspheric_coefficients', np.float32, NUM_ASPHERIC_COEFFS), # 40 bytes (starts at 68, ends at 108)
            ('_pad2',                 np.uint8,   4),                   # ! Padding to align 'aperture_size' to 112
            ('aperture_size',         np.float32, 2),                   # 8 bytes (starts at 112)
            ('aperture_shape',        np.int32,   2),                   # 8 bytes
            ('flags',                 np.bool_,   2),                   # 2 bytes
            # align=True will automatically handle the 2-byte padding needed here for 'type' (int)
            ('type',                  np.int32),                        # 4 bytes
            ('shape',                 np.int32),                        # 4 bytes
            ('material1',             np.int32),                        # 4 bytes
            ('material2',             np.int32),                        # 4 bytes
            ('scattering_dispersion', np.float32),                      # 4 bytes
            ('sensor_info',           np.float32, 8),                   # 24 bytes
        ], align=True)

        n_surfaces = len(self.optical_system)

        h_surfaces = np.zeros(n_surfaces, dtype=surface_data_dtype)

        self._sub_pixels_per_side = []
        sensor_counter = 0
        for i, surface in enumerate(self.optical_system):
            if surface._shape not in SurfaceShape:
                raise(ValueError(f"Surface shape '{surface._shape}' ray-tracing not yet implemented."))

            h_surfaces[i]['position'] = np.asarray(surface.position, dtype=np.float32)
            h_surfaces[i]['rotation_matrix'] = np.asarray(surface.get_rotation_matrix().flatten(), dtype=np.float32)
            h_surfaces[i]['type'] = np.int32(surface.type.value)
            h_surfaces[i]['shape'] = np.int32(surface._shape.value)
            
            h_surfaces[i]['scattering_dispersion'] = np.float32(surface.scattering_dispersion/180.)

            if surface._shape == SurfaceShape.CYLINDRICAL:
                h_surfaces[i]['material1'] = np.int32(surface.material_out.value)
                h_surfaces[i]['material2'] = np.int32(surface.material_in.value)
                h_surfaces[i]['aperture_size'][0] = np.float32(surface.radius)
                h_surfaces[i]['aperture_size'][1] = np.float32(surface.height)
                h_surfaces[i]['flags'][0] = np.bool_(surface.top)
                h_surfaces[i]['flags'][1] = np.bool_(surface.bottom)
                continue
            
            h_surfaces[i]['material1'] = np.int32(surface.material_in.value)
            h_surfaces[i]['material2'] = np.int32(surface.material_out.value)
            h_surfaces[i]['aperture_size'][0] = np.float32(surface.half_aperture)
            h_surfaces[i]['aperture_size'][1] = np.float32(surface.central_hole_half_aperture)
            h_surfaces[i]['aperture_shape'][0] = np.int32(surface.aperture_shape.value)
            h_surfaces[i]['aperture_shape'][1] = np.int32(surface.central_hole_shape.value)

            # Register pixels (in the order they have been inserted in the optical system)
            sensor_type = surface.sensor_type
            h_surfaces[i]['sensor_info'][0] = np.float32(sensor_type.value)
            if surface.sensor_type is not SensorSurfaceType.NONE:
                if sensor_type == SensorSurfaceType.SIPM_TILE:
                    h_surfaces[i]['sensor_info'][0] = np.float32(surface.sensor_type.value)
                    h_surfaces[i]['sensor_info'][1] = np.float32(sensor_counter)
                    h_surfaces[i]['sensor_info'][2] = np.float32(surface.pixels_per_side)
                    h_surfaces[i]['sensor_info'][3] = np.float32(surface.pixel_active_side)
                    h_surfaces[i]['sensor_info'][4] = np.float32(surface.pixels_separation)
                    h_surfaces[i]['sensor_info'][5] = np.float32(surface.border_to_active_area)
                    h_surfaces[i]['sensor_info'][6] = np.float32(surface._inv_ucell_size)
                    h_surfaces[i]['sensor_info'][7] = np.float32(surface._n_ucells_per_side)
                    self._sub_pixels_per_side.append(surface._n_ucells_per_side)
                    surface._first_pixel_id = sensor_counter
                sensor_counter += surface._n_pixels

            if surface._shape == SurfaceShape.FLAT:
                continue
            
            h_surfaces[i]['offset'] = np.asarray(surface.offset, dtype=np.float32)
            h_surfaces[i]['curvature'] = np.float32(surface.curvature)
            h_surfaces[i]['flags'][0] = np.bool_(surface.is_fresnel)

            if surface._shape == SurfaceShape.ASPHERICAL:
                h_surfaces[i]['conic_constant'] = np.float32(surface.conic_constant)
                surface_asph_coeffs = normalize_aspheric_coefficients(surface.aspheric_coefficients, surface.half_aperture)
                for j in range(len(surface_asph_coeffs)):
                    h_surfaces[i]['aspheric_coefficients'][j] = np.float32(surface_asph_coeffs[j])

        self._sub_pixels_per_side = cp.asarray(self._sub_pixels_per_side, dtype=cp.int32)
        self._cuda_tracing_args[2] = cp.asarray(h_surfaces.view(np.uint8), dtype=cp.uint8)

    def _cuda_surfaces_efficiency_init(self):
        optical_tables_dtype = np.dtype([
            ('transmittance_front', np.uint64),
            ('reflectance_front',   np.uint64),
            ('transmittance_back',  np.uint64),
            ('reflectance_back',    np.uint64),
            ('efficiency',          np.uint64),
            ('opt_inv_dwl',         np.float32),
            ('opt_start_wl',        np.float32),
            ('opt_inv_dang',        np.float32),
            ('opt_start_ang',       np.float32),
            ('eff_inv_dwl',         np.float32),
            ('eff_start_wl',        np.float32),
            ('eff_inv_dang',        np.float32),
            ('eff_start_ang',       np.float32)
        ], align=True)
        
        n_surfaces = len(self.optical_system)
        h_optical_tables = np.zeros(n_surfaces, dtype=optical_tables_dtype)
        self._surface_textures = [] # keep a reference to the textures to avoid garbage collection
        for k,s in enumerate(self.optical_system):
            surface_prop = s.properties
            if surface_prop is None or not surface_prop.is_defined:
                continue
            opt_textures = surface_prop.get_textures()
            self._surface_textures.append(opt_textures)
            h_optical_tables[k]['transmittance_front'] = opt_textures.transmittance.ptr
            h_optical_tables[k]['reflectance_front'] = opt_textures.reflectance.ptr
            h_optical_tables[k]['transmittance_back'] = opt_textures.transmittance_back.ptr
            h_optical_tables[k]['reflectance_back'] = opt_textures.reflectance_back.ptr
            h_optical_tables[k]['opt_inv_dwl'] = opt_textures.optical_wavelength_inv_step
            h_optical_tables[k]['opt_start_wl'] = opt_textures.optical_wavelength_start
            h_optical_tables[k]['opt_inv_dang'] = opt_textures.optical_angle_inv_step
            h_optical_tables[k]['opt_start_ang'] = opt_textures.optical_angle_start

            h_optical_tables[k]['efficiency'] = opt_textures.efficiency.ptr
            h_optical_tables[k]['eff_inv_dwl'] = opt_textures.efficiency_wavelength_inv_step
            h_optical_tables[k]['eff_start_wl'] = opt_textures.efficiency_wavelength_start
            h_optical_tables[k]['eff_inv_dang'] = opt_textures.efficiency_angle_inv_step
            h_optical_tables[k]['eff_start_ang'] = opt_textures.efficiency_angle_start
        
        self._cuda_tracing_args[3] = cp.asarray(h_optical_tables.view(np.uint8), dtype=cp.uint8)
    
    def _cuda_materials_init(self):
        """Prepares materials data for CUDA-based ray tracing.
        This function extracts relevant properties from all defined materials.
        """
        # Refractive indices
        refractive_tables_dtype = np.dtype([
            ('texture',  np.uint64),
            ('inv_dwl',  np.float32),
            ('start_wl', np.float32)
        ], align=True)

        n_materials = sum(1 for _ in Materials._members())

        h_refractive_tables = np.zeros(n_materials, dtype=refractive_tables_dtype)

        self._ri_textures = [] # keep a reference to the textures to avoid garbage collection
        for material in Materials._members():
            material_texture = material.get_refractive_index_texture()
            self._ri_textures.append(material_texture)
            h_refractive_tables[material.value]['texture'] = material_texture.texture.ptr
            h_refractive_tables[material.value]['inv_dwl'] = material_texture.wavelength_inv_step
            h_refractive_tables[material.value]['start_wl'] = material_texture.wavelength_start

        self._cuda_tracing_args[4] = cp.asarray(h_refractive_tables.view(np.uint8), dtype=cp.uint8)

    def _cuda_atmosphere_init(self):
        if self.atmospheric_transmission.value is not None:
            wl = self.atmospheric_transmission.wavelength
            zem = self.atmospheric_transmission.altitude
            self._cuda_atmosphere_args[:] = [
                cp.asarray(self.atmospheric_transmission.value, dtype=cp.float32),
                cp.asarray(wl, dtype=cp.float32),
                cp.asarray(zem, dtype=cp.float32),
                cp.asarray([len(wl), len(zem)], dtype=cp.int32),
            ]
                
    def cuda_init(self):
        """Build and copy to device all the CUDA kernels input related to the optical configuration."""

        self._cuda_surfaces_init()

        self._cuda_materials_init()

        self._cuda_telescope_init()

        self._cuda_surfaces_efficiency_init()

        if isinstance(self.camera, CherenkovSiPMCamera):
            pass

        self._cuda_atmosphere_init()

        self._d_num_surfaces = cp.int32(len(self.optical_system))

    def trace_photons(self,
            positions: Union[np.ndarray, cp.ndarray],
            directions: Union[np.ndarray, cp.ndarray],
            wavelengths: Union[np.ndarray, cp.ndarray],
            arrival_times: Union[np.ndarray, cp.ndarray],
            emission_altitudes: Optional[Union[np.ndarray, cp.ndarray]] = None,
            events_mapping: Union[np.ndarray, list] = None,
            *,
            photons_per_bunch: int = 1,
            transform_to_tel = True,
            simulate_camera = False,
            min_n_pes = 1,
            get_camera_input: bool = False,
            max_bounces=100,
            save_last_bounce=False,
            reset_state=True,
            seed: Optional[int] = None,
        ):
        """Traces photons through the telescope optical system and optionally simulates the Cherenkov camera response.

        This function simulates the propagation of photons through an optical system,
        taking into account their initial positions, directions, wavelengths, and arrival times.
        It can optionally:
        
          - model the effects of atmospheric transmission based on emission altitudes;
          - simulate the Cherenkov camera response.

        Each element in the input arrays can represent either a single photon or a "bunch" of photons.
        The ``photons_per_bunch`` parameter determines how many photons are represented by each element.
        If ``photons_per_bunch`` > 1, it is assumed that all photons within a bunch share the same
        initial position, direction, wavelength, and arrival time.

        Parameters
        ----------
        positions : Union[numpy.ndarray, cp.ndarray] of shape (N, 3)
            Initial Cartesian coordinates (x, y, z) of the photon bunches in millimeters (mm).
            Must be either a NumPy (CPU) or CuPy (GPU) array.
        directions : Union[numpy.ndarray, cp.ndarray] of shape (N, 3)
            Initial direction vectors (vx, vy, vz) of the photon bunches.
            These should be normalized. Must be either a NumPy (CPU) or CuPy (GPU) array.
        wavelengths : Union[numpy.ndarray, cp.ndarray] of shape (N,)
            Wavelengths of the photon bunches in nanometers (nm).
            Must be either a NumPy (CPU) or CuPy (GPU) array.
        arrival_times : Union[numpy.ndarray, cp.ndarray] of shape (N,)
            Arrival times of the photon bunches at their respective positions in nanoseconds (ns).
            Must be either a NumPy (CPU) or CuPy (GPU) array.
        emission_altitudes : Optional[Union[numpy.ndarray, cp.ndarray]], optional
            Emission altitudes of the photon bunches in millimeters (mm).
            This is used to calculate atmospheric transmission effects if enabled.
            Must be either a NumPy (CPU) or CuPy (GPU) array.
        events_mapping : numpy.ndarray or list
            A NumPy array of shape (N+1,) to split the photons in to groups corresponding to N different events when 
            generating the camera input arrays.
            ``events_mapping[i]`` indicates the starting index in ``positions`` for the i-th event.
            ``events_mapping[i+1]`` indicates the ending index (exclusive) in ``positions`` for the i-th event.
            Therefore, photons belonging to event i are located in ``positions[events_mapping[i]:events_mapping[i+1], :]``.
            The last element of events_mapping must be equal to the number of photons.
        photons_per_bunch : int, optional
            Number of photons represented by each element in the input arrays. If 1, each element represents a single photon.
            If > 1, each element represents a bunch of photons that share the same properties, by default 1. Maximum value is 65535.
        transform_to_tel: bool, optional
            Whether to move detected photons into the telescope refrence frame or in the detector(s) reference frame. By default True.
        simulate_camera : bool, optional
            Whether to simulate the response of the telescope Cherenkov camera.
        min_n_pes : int, optional
            Minimum number of photo-electrons needed to trigger a camera simulation (if ``simulate_camera`` is True). By default 1.
        get_camera_input : bool, optional
            Wheter to return the input for camera simulation (i.e. photon arrival times for each pixel) as CuPy ndarrays.
            By default False.
        max_bounces : int, optional
            Maxium number of bounces before the photon is killed. By default 100.
        save_last_bounce : float, optional
            Keep the position at the last bounce. Only for ray tracing visualization. By default False.
        reset_state : bool, optional
            Keep the ID of the last surface reached without re-initialize the _d_weights array. Only for ray tracing visualization. By default True.
        seed : int, optional
            Base seed of the simulation. If None a random seed will be used. By default None.

        Returns
        -------
        ndarray
            List of triggered events index. If ``simulate_camera`` is True and ``get_camera_input`` is False.
        tuple(cp.ndarray, cp.ndaray)
            Input CuPy arrays for :py:meth:`CherenkovCamera.simulate_response()`` method. If ``simulate_camera`` is False and ``get_camera_input`` is True.
        tuple(cp.ndarray, cp.ndaray, np.ndarray)
            Input CuPy arrays for :py:meth:`CherenkovCamera.simulate_response()`` method and the list of triggered events index. If ``simulate_camera`` is True and ``get_camera_input`` is True.

        Warning
        -------
            The input arrays can be either CuPy or NumPy ndarray. In the former case arrays are modified in place.
            In the latter case the arrays are copied to the device and can be accessed through the following attributes:

              - self._d_directions
              - self._d_positions
              - self._d_wavelengths
              - self._d_arrival_times
              - self._d_emission_altitudes
              - self._d_weights
        
        Warning
        -------
            Telescope configuration must be copied into the device before calling this method. Use the :py:meth:`cuda_init()` method.

        Notes
        -----

          - The ray-tracing operates with positions in mm, wavelengths in nm, and times in ns. It also handles photon bunches,
            where each thread may process multiple photons if ``photons_per_bunch`` > 1. In this case is assumed 
            that each element of the input arrays represents a bunch of photons that share the same 
            initial position, direction, wavelength, and arrival time. The arrays will maintain this
            structure, with each element representing the updated properties of a photon bunch, but the bunch size may
            be reduced throught the ray-tracing due to the interacrtion with optical elements, atmosphere and pixels.

        """
        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t0 = time.time()

        # Copy photon bunches into GPU
        self._d_directions = cp.asarray(directions, dtype=cp.float32)
        self._d_positions = cp.asarray(positions, dtype=cp.float32)
        self._d_wavelengths = cp.asarray(wavelengths, dtype=cp.float32)
        self._d_arrival_times = cp.asarray(arrival_times, dtype=cp.float32)
        if emission_altitudes is not None:
            self._d_emission_altitudes = cp.asarray(emission_altitudes, dtype=cp.float32)

        # Calculate number of photons and kernel call parameters
        n_photons = self._d_positions.shape[0]
        num_blocks = int(np.ceil(n_photons / self._blocksize))
        d_num_photons = cp.int32(n_photons)

        # Initialize photon bunches size on device
        #   - This step can be skipped for visualization purposes. 
        #     Since when save_last_bounce is True the last 
        #     surface ID is stored in the last 16 bit of 
        #     each element in _d_weights.
        if reset_state:
            self._d_weights = cp.full((n_photons,), photons_per_bunch, dtype=cp.int32)
        
        # ID of the pixel reached by each bunch
        self._d_pixid = cp.empty((n_photons,), dtype=cp.int32)
        self._d_subpixid = cp.empty((n_photons,), dtype=cp.int32)

        if seed is None:
            seed = random.getrandbits(62)

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t1 = time.time()
            self.timer.add_entry('simulate_response', 'copy to device', t1-t0)
        
        # Optional atmospheric transmission calculation
        if self.atmospheric_transmission.value is not None and emission_altitudes is not None:
            ray_tracing.atmospheric_transmission(
                (num_blocks,), 
                (self._blocksize,),
                (
                    self._d_positions,
                    self._d_directions,
                    self._d_wavelengths,
                    self._d_arrival_times,
                    self._d_emission_altitudes,
                    *self._cuda_atmosphere_args,
                    d_num_photons,
                    cp.uint64(seed)
                )
            )

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t2 = time.time()
            self.timer.add_entry('simulate_response', 'atmospheric transmission', t2-t1)

        # Perform ray tracing
        ray_tracing.ray_tracing(
            (num_blocks,),
            (self._blocksize,),
            (
                self._d_positions,
                self._d_directions,
                self._d_wavelengths,
                self._d_arrival_times,
                self._d_weights,
                self._d_pixid,
                self._d_subpixid,
                *self._cuda_tracing_args,
                self._d_num_surfaces,
                d_num_photons,
                cp.int32(max_bounces),
                cp.bool_(save_last_bounce),
                cp.bool_(transform_to_tel),
                cp.uint64(seed+1)
            ),
            shared_mem = len(self.optical_system) * 5 * 4 # Surface positions, bounding radii and shape ID
        )

        if self.timer.active:
            cp.cuda.stream.get_current_stream().synchronize()
            t3 = time.time()
            self.timer.add_entry('simulate_response', 'trace onto focal plane', t3-t2)

        # Build the input for `CherenkovCamera.simulate_response()` method
        if get_camera_input or simulate_camera:

            # Split photons into events
            if events_mapping is None:
                events_mapping = cp.asarray([0, n_photons], dtype=cp.int32)
            else:
                events_mapping = cp.asarray(events_mapping, dtype=cp.int32)

            n_pixels = self.camera.n_pixels
            n_events = len(events_mapping) - 1

            # Filter for detected photons to reduce workload
            hit_mask = cp.isfinite(self._d_arrival_times) & (self._d_pixid > -1)
            
            if not hit_mask.any():
                # No photons detected
                phs = cp.array([], dtype=cp.float32)
                phs_mapping = cp.zeros((n_events, n_pixels + 1), dtype=cp.int32)
                pe_mapping = cp.zeros((n_events + 1,), dtype=cp.int32)
                active_indices = np.array([], dtype=np.int32)
                pe_mapping_host = np.zeros((n_events + 1,), dtype=np.int32)
            else:
                hit_indices_global = cp.where(hit_mask)[0]
                hit_pix = self._d_pixid[hit_mask]
                hit_subpix = self._d_subpixid[hit_mask]
                hit_time = self._d_arrival_times[hit_mask]
                hit_weight = self._d_weights[hit_mask]

                # Get event IDs of each detected photon
                hit_event = cp.searchsorted(events_mapping, hit_indices_global, side='right').astype(cp.int32) - 1
                
                # Check if we need to expand bunches (weight > 1)
                # Use cumulative sum + searchsorted to expand indices.
                if cp.any(hit_weight > 1):
                    # Create the cumulative offsets for expansion
                    offsets = cp.cumsum(hit_weight)
                    total_pes = int(offsets[-1])
                    
                    dest_idx = cp.arange(total_pes, dtype=cp.int32)
                    source_idx = cp.searchsorted(offsets, dest_idx, side='right')
                    
                    # Basic properties are simply replicated
                    final_pix = hit_pix[source_idx]
                    final_event = hit_event[source_idx]
                    final_time = hit_time[source_idx]

                    if getattr(self.camera, 'simulate_ucells', False):
                        if photons_per_bunch > 9:
                            raise ValueError("Microcell simulation not supported for bunch-size > 9.")
                        # Calculate position within the bunch (0, 1, 2...)
                        shift_offsets = cp.zeros(len(offsets), dtype=cp.int32)
                        shift_offsets[1:] = offsets[:-1]
                        bunch_local_idx = dest_idx - shift_offsets[source_idx]

                        # Map the specific pixel n_ucells_per_side to every expanded photon based on its pixel ID
                        n_side = self._sub_pixels_per_side[final_pix] 
                        
                        ###########################################################################
                        ###########################################################################
                        # Use this to get rid of the weight<9 limit
                        #
                        # def get_spiral_offsets(max_weight):
                        #     dr = np.zeros(max_weight, dtype=np.int32)
                        #     dc = np.zeros(max_weight, dtype=np.int32)
                        #     x = y = 0
                        #     dx = 0
                        #     dy = -1
                        #     for i in range(max_weight):
                        #         dr[i] = dy
                        #         dc[i] = dx
                        #         if x == y or (x < 0 and x == -y) or (x > 0 and x == 1-y):
                        #             dx, dy = -dy, dx
                        #         x, y = x + dx, y + dy
                        #     return cp.asarray(dr), cp.asarray(dc)
                        #
                        # dr, dc = get_spiral_offsets(max_weight_possible)
                        # pattern_idx = bunch_local_idx # No modulo needed if dr/dc is long enough
                        ###########################################################################
                        ###########################################################################


                        # Define pattern offsets (9x9 window):
                        #   0: Center
                        #   1-4: cardinal (up, down, left, right)
                        #   5-8: diagonals (up-left, up-right, down-left, down-right)
                        dr = cp.array([0, -1,  1,  0,  0, -1, -1,  1,  1], dtype=cp.int32)
                        dc = cp.array([0,  0,  0, -1,  1, -1,  1, -1,  1], dtype=cp.int32)
                        pattern_idx = bunch_local_idx % 9
                        
                        # Coordinate decomposition using the per-photon n_side
                        orig_subpix = hit_subpix[source_idx]
                        r0 = orig_subpix // n_side
                        c0 = orig_subpix % n_side
                        
                        # Apply shifts (clip using the per-photon n_side as limit)
                        # N.B.: this will accumulate at the border, but shouldn't be a big deal
                        final_r = cp.clip(r0 + dr[pattern_idx], 0, n_side - 1)
                        final_c = cp.clip(c0 + dc[pattern_idx], 0, n_side - 1)
                        
                        final_subpix = (final_r * n_side + final_c).astype(cp.int32)
                    else:
                        final_subpix = hit_subpix[source_idx]
                else:
                    final_pix = hit_pix
                    final_subpix = hit_subpix
                    final_event = hit_event
                    final_time = hit_time

                # Create composite key to sort by event, then by pixel
                composite_key = final_event.astype(cp.int64) * n_pixels + final_pix
                
                # CUDA kernel that simulate ucells needs sorted arrivial times per each pixel
                if getattr(self.camera, 'simulate_ucells', False) > 0:
                    # First sort key: event -> inside composite_key
                    # Second sort key: pixel -> inside composite_key
                    # Third sort key: time
                    keys = cp.stack((final_time, composite_key))
                    sort_order = cp.lexsort(keys)
                else:
                    # First sort key: event -> inside composite_key
                    # Second sort key: pixel -> inside composite_key
                    sort_order = cp.argsort(composite_key)
                
                phs = final_time[sort_order]
                subids = final_subpix[sort_order]

                # Generate mappings
                # bincount calculates how many PEs are in each (event, pixel) bin
                flat_counts = cp.bincount(composite_key, minlength=n_events*n_pixels).astype(cp.int32)
                counts_2d = flat_counts.reshape((n_events, n_pixels))

                # phs_mapping: cumulative sum along pixels for each event
                zeros_col = cp.zeros((n_events, 1), dtype=cp.int32)
                counts_padded = cp.hstack([zeros_col, counts_2d])
                phs_mapping = cp.cumsum(counts_padded, axis=1, dtype=cp.int32)

                # pe_mapping: global offsets for slicing 'phs' by event
                event_pes = counts_2d.sum(axis=1)
                # TODO: rename this for clarity
                pe_mapping = cp.concatenate([cp.array([0], dtype=cp.int32), cp.cumsum(event_pes, dtype=cp.int32)])

            if self.timer.active:
                cp.cuda.stream.get_current_stream().synchronize()
                t4 = time.time()
                self.timer.add_entry('simulate_response', 'generate camera input', t4-t3)

            # Simulate camera response
            if simulate_camera:
                self.camera.base_seed = seed + 2

                if phs.size > 0:
                    n_pes_per_event = pe_mapping[1:] - pe_mapping[:-1]
                    active_mask = n_pes_per_event >= min_n_pes
                    active_indices_gpu = cp.where(active_mask)[0]

                    # Transfer minimal loop control data to CPU
                    active_indices = active_indices_gpu.get()
                    pe_mapping_host = pe_mapping.get()
                else:
                    active_indices = []
                
                if self.timer.active:
                    cp.cuda.stream.get_current_stream().synchronize()
                    t5 = time.time()
                    self.timer.add_entry('simulate_response', 'filter events to be simulated', t5-t4)

                event_number = []

                for i in tqdm(active_indices, disable=not self.show_progress):
                    start_phs = pe_mapping_host[i]
                    end_phs = pe_mapping_host[i+1]
                    if getattr(self.camera, 'simulate_ucells', False):
                        source = (phs[start_phs:end_phs], phs_mapping[i], subids[start_phs:end_phs])
                    else:
                        source = (phs[start_phs:end_phs], phs_mapping[i])
                    self.camera.simulate_response(source)
                    if self.camera.triggered:
                        event_number.append(i)
                
                event_number = np.array(event_number)

                if self.timer.active:
                    cp.cuda.stream.get_current_stream().synchronize()
                    t6 = time.time()
                    self.timer.add_entry('simulate_response', 'simulate camera response', t6-t5)

                if get_camera_input:
                    if getattr(self.camera, 'simulate_ucells', False):
                        return phs, phs_mapping, subids, event_number
                    else:
                        return phs, phs_mapping, event_number
                else:
                    return event_number
            
            if get_camera_input:
                if getattr(self.camera, 'simulate_ucells', False):
                    return phs, phs_mapping, subids
                else:
                    return phs, phs_mapping
    
    def visualize_ray_tracing(self,
            positions: Union[np.ndarray, cp.ndarray],
            directions: Union[np.ndarray, cp.ndarray],
            wavelengths: Union[np.ndarray, cp.ndarray],
            arrival_times: Union[np.ndarray, cp.ndarray],
            emission_altitudes: Optional[Union[np.ndarray, cp.ndarray]] = None,
            photons_per_bunch: int = 1,
            *,
            show_not_detected: bool = True,
            map_wavelength_color=True,
            get_renderer = False,
            opacity=None,
            show_hits=True,
            show_rays=True, 
            point_size=1,
            orthographic=False,
            focal_point=None,
            resolution=None
        ):
        """
        Visualizes the ray tracing process by performing step-by-step propagation of photons.

        This method initializes a VTK renderer and iteratively calls `trace_photons` with 
        `max_bounces=1` to capture and visualize the path of photons between surfaces.

        Parameters
        ----------
        positions : Union[numpy.ndarray, cp.ndarray] of shape (N, 3)
            Initial Cartesian coordinates (x, y, z) of the photon bunches in millimeters (mm).
            Must be either a NumPy (CPU) or CuPy (GPU) array.
        directions : Union[numpy.ndarray, cp.ndarray] of shape (N, 3)
            Initial direction vectors (vx, vy, vz) of the photon bunches.
            These should be normalized. Must be either a NumPy (CPU) or CuPy (GPU) array.
        wavelengths : Union[numpy.ndarray, cp.ndarray] of shape (N,)
            Wavelengths of the photon bunches in nanometers (nm).
            Must be either a NumPy (CPU) or CuPy (GPU) array.
        arrival_times : Union[numpy.ndarray, cp.ndarray] of shape (N,)
            Arrival times of the photon bunches at their respective positions in nanoseconds (ns).
            Must be either a NumPy (CPU) or CuPy (GPU) array.
        emission_altitudes : Optional[Union[numpy.ndarray, cp.ndarray]], optional
            Emission altitudes of the photon bunches in millimeters (mm).
            This is used to calculate atmospheric transmission effects if enabled.
            Must be either a NumPy (CPU) or CuPy (GPU) array.
        photons_per_bunch : int, optional
            Number of physical photons represented by one simulated photon. Defaults to 1.
        show_not_detected : bool, optional
            Whether to show also photons that are not detected by the camera. Defaults to True.
        map_wavelength_color : bool, optional
            Whether to color rays based on their wavelength. Defaults to True.
        get_renderer : bool, optional
            If True, returns the `VTKOpticalSystem` instance instead of starting the render loop immediately. 
            Defaults to False.
        opacity : float, optional
            Opacity of the ray lines (0.0 to 1.0). If None, it is calculated based on the number 
            of photons. Defaults to None.
        show_hits : bool, optional
            Whether to render points at the location where rays intersect surfaces. Defaults to True.
        show_rays : bool, optional
            Whether to render lines representing the photon paths. Defaults to True.
        point_size : int, optional
            Size of the points rendered at intersection hits. Defaults to 1.
        orthographic : bool, optional
            If True, start with a parallel projection. 
            If False, start with a Perspective projection. Default is False.
        focal_point : tuple, list, or str, optional
            If tuple/list: (x, y, z) coordinates to look at.
            If str: The name of the surface in self.os to look at.
            If None: Defaults to center of system.
        resolution : float, optional
            Objects mesh resolution (in mm). By default None (depends on object extent).
        
        Returns
        -------
        VTKOpticalSystem or None
            Returns the renderer instance if `get_renderer` is True, otherwise returns None 
            after the render window is closed.
        """
        from .visualization._vtk_optical_system import VTKOpticalSystem
        
        # Ensure input arrays are on GPU, so any modifications is inplace
        positions = cp.asarray(positions, dtype=cp.float32)
        directions = cp.asarray(directions, dtype=cp.float32)
        wavelengths = cp.asarray(wavelengths, dtype=cp.float32)
        arrival_times = cp.asarray(arrival_times, dtype=cp.float32)
        emission_altitudes = cp.asarray(emission_altitudes, dtype=cp.float32) if emission_altitudes is not None else None

        # Initialize VTK renderer
        renderer = VTKOpticalSystem(self, resolution=resolution)
        
        # Where to put rays if showing only detected ones at the end
        ps_start_list = []
        ps_stop_list = []
        surface_hits_list = []
        vis_wavelengths = None

        bounces = 0
        while True:
            # Store start positions
            ps_start = positions.get()
            
            # Perform ray tracing for one bounce
            self.trace_photons(
                positions,
                directions,
                wavelengths,
                arrival_times,
                emission_altitudes,
                photons_per_bunch=photons_per_bunch, 
                simulate_camera=False,
                max_bounces=1, 
                save_last_bounce=True,
                reset_state=bounces==0,
                transform_to_tel=False,
            )

            # Filter photons based on photon status
            # If show_not_detected is False, this will be called only at the first bounce
            # to remove photons not hitting any surface
            if show_not_detected or (not show_not_detected and bounces==0):
                survivors = cp.isfinite(wavelengths)
                positions = positions[survivors]
                directions = directions[survivors]
                wavelengths = wavelengths[survivors]
                arrival_times = arrival_times[survivors]
                self._d_weights = self._d_weights[survivors]
                if emission_altitudes is not None:
                    emission_altitudes = emission_altitudes[survivors]
                if map_wavelength_color:
                    vis_wavelengths = wavelengths.get()
                ps_start = ps_start[survivors.get()]
            
            # Surface hit IDs and stop positions (already filtered as needed)
            surface_hits = (self._d_weights >> 16) & 0xFFFF
            surface_hits = surface_hits.astype(cp.int32).get() - 1
            ps_stop = positions.get()
            
            # Stop if no more changes
            if np.array_equal(ps_start, ps_stop, equal_nan=True):
                break
            
            # Add rays to renderer
            if show_not_detected:
                renderer.add_rays(
                    ps_start, ps_stop,
                    wavelengths=vis_wavelengths,
                    surface_id=surface_hits,
                    show_hits=show_hits,
                    show_rays=show_rays,
                    point_size=point_size
                )
            # Store for later rendering
            else:
                ps_start_list.append(ps_start)
                ps_stop_list.append(ps_stop)
                surface_hits_list.append(surface_hits)
            
            # Break if max bounces reached
            if bounces > 100:
                break

            # Update bounce counter
            bounces += 1
        
        # If showing only detected photons, add them now
        if not show_not_detected:
            for ps_start, ps_stop, surface_hits in zip(ps_start_list, ps_stop_list, surface_hits_list):
                mask = cp.isfinite(wavelengths).get(),
                if map_wavelength_color:
                    vis_wavelengths = wavelengths.get()[mask]
                renderer.add_rays(
                    ps_start[mask], ps_stop[mask],
                    wavelengths=vis_wavelengths,
                    surface_id=surface_hits[mask],
                    show_hits=show_hits,
                    show_rays=show_rays,
                    point_size=point_size
                )

        # Set ray opacity (by deafault based on number of photons)
        renderer.set_ray_opacity(opacity)

        # Return the renderer if requested
        if get_renderer:
            return renderer
        # otherwise start the render loop
        else:
            renderer.start_render(focal_point=focal_point, orthographic=orthographic)