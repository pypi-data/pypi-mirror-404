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

from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import cupy as cp

from ..visualization._iactsim_style import iactsim_style


class SurfaceType(Enum):
    """
    Enumeration representing the different types of optical surfaces.

    The directionality of reflection and sensitivity (e.g., "from above" or 
    "from below") is defined within the *local reference frame* of the surface at the point 
    of photon incidence. As a reference:

        - the front side of a surface with negative curvature is the convex side.
        - the front side of a surface with posistive curvature is the concave side.

    Attributes
    ----------
    REFLECTIVE : int
        Represents a reflective surface (both sides).
    REFLECTIVE_FRONT : int
        Represents a surface that is reflective on the front side. 
        In the surface reference frame, only photons arriving with a negative 
        z-component of their direction vector are reflected. 
        The curvature of the surface does not affect this behavior.
    REFLECTIVE_BACK : int
        Represents a surface that is reflective on the back side. In the surface 
        reference frame, only photons arriving with a positive z-component of 
        their direction vector are reflected. The curvature of the surface 
        does not affect this behavior.
    REFRACTIVE : int
        Represents a refractive surface. The refraction is the same on both sides.
    SENSITIVE : int
        Represents the focal plane surface where photons are detected. The sensitivity
        is the same on both sides.
    SENSITIVE_BACK : int
        Represents a surface that is sensitive on the front side. In the surface reference 
        frame, only photons arriving with a negative z-component of their direction 
        vector are detected. The curvature of the surface does not affect 
        this behavior.
    SENSITIVE_FRONT : int
        Represents a surface that is sensitive on the back side. In the surface
        reference frame, only photons arriving with a positive z-component of 
        their direction vector are detected. The curvature of the surface 
        does not affect this behavior.
    OPAQUE : int
        Represents a surface that blocks light.
    DUMMY : int
        Represents a surface that neither reflects nor refracts light. 
        It can be used to introduce artificial absorption or scattering effects, 
        serving as a means to model specific behaviors within the optical system.
    
    """
    REFLECTIVE = 0
    REFLECTIVE_FRONT = 1
    REFLECTIVE_BACK = 2
    REFRACTIVE = 3
    SENSITIVE = 4
    SENSITIVE_BACK = 5
    SENSITIVE_FRONT = 6
    OPAQUE = 7
    DUMMY = 8
    REFLECTIVE_SENSITIVE = 9
    REFLECTIVE_SENSITIVE_FRONT = 10
    REFLECTIVE_SENSITIVE_BACK = 11

class SensorSurfaceType(Enum):
    """Enumeration representing different types of sensor surfaces.

    Attributes
    ----------
    NONE : int
        Represents no specific sensor surface type.
    SIPM_TILE : int
        Represents a SiPM tile sensor surface.
    
    """
    NONE = 0
    SIPM_TILE = 1

class SurfaceShape(Enum):
    """
    Enumeration representing different types of surface shapes.

    This enum defines common surface shapes encountered in optical systems or
    other fields requiring precise geometrical definitions.

    """
    ASPHERICAL = 0
    """Represents an aspherical surface."""
    CYLINDRICAL = 1
    """Represents a cylindrical surface."""
    FLAT = 2
    """Represents a flat surface."""
    SPHERICAL = 3
    """Represents a spherical surface."""

class ApertureShape(Enum):
    """
    Enumeration representing the possible shapes of an aperture.

    Attributes
    ----------
    CIRCULAR : int
        Represents a circular aperture.
    HEXAGONAL : int
        Represents a flat-top hexagonal aperture.
    SQUARE : int
        Represents a square aperture.
    HEXAGONAL_PT : int
        Represents a pointy-top hexagonal aperture.
    """
    CIRCULAR = 0
    HEXAGONAL = 1
    SQUARE = 2
    HEXAGONAL_PT = 3

@dataclass
class SurfaceTextures:
    """
    Container for GPU texture objects (optical + efficiency) 
    and the metadata required to map physical values (wavelength, angle) 
    to texture coordinates. It can retains a reference to the underlying 
    CUDA arrays to prevent premature garbage collection.
    Because efficiency can be defined on a different grid than transmittance/reflectance,
    this class stores two separate sets of coordinate mappings.
    """
    # Front-side optical textures
    transmittance: cp.cuda.texture.TextureObject
    reflectance: cp.cuda.texture.TextureObject
    
    # Back-side optical textures
    transmittance_back: cp.cuda.texture.TextureObject
    reflectance_back: cp.cuda.texture.TextureObject
    
    # Optical grid
    optical_wavelength_start: float
    optical_wavelength_inv_step: float
    optical_angle_start: float
    optical_angle_inv_step: float

    # Detection efficiency texture
    efficiency: cp.cuda.texture.TextureObject
    
    # Efficiency grid
    efficiency_wavelength_start: float
    efficiency_wavelength_inv_step: float
    efficiency_angle_start: float
    efficiency_angle_inv_step: float

    # References to prevent garbage collection
    _t_array: cp.cuda.texture.CUDAarray = field(default=None, repr=False)
    _r_array: cp.cuda.texture.CUDAarray = field(default=None, repr=False)
    _t_back_array: cp.cuda.texture.CUDAarray = field(default=None, repr=False)
    _r_back_array: cp.cuda.texture.CUDAarray = field(default=None, repr=False)
    _eff_array: cp.cuda.texture.CUDAarray = field(default=None, repr=False)


@dataclass
class SurfaceProperties:
    """
    Represents surface transmittance, reflectance, absorption and detection efficiency
    as a function of photon wavelength and incidence angle.
    """
    # Front-side optical properties
    transmittance: np.ndarray = field(default=None, metadata={'units': 'None'})
    reflectance: np.ndarray = field(default=None, metadata={'units': 'None'})
    absorption: np.ndarray = field(default=None, metadata={'units': 'None'})

    # Back-side optical properties
    transmittance_back: np.ndarray = field(default=None, metadata={'units': 'None'})
    reflectance_back: np.ndarray = field(default=None, metadata={'units': 'None'})
    absorption_back: np.ndarray = field(default=None, metadata={'units': 'None'})

    # Optical grid
    wavelength: np.ndarray = field(default=None, metadata={'units': 'nanometers'})
    incidence_angle: np.ndarray = field(default=None, metadata={'units': 'degrees'})

    # Detection efficiency
    efficiency: np.ndarray = field(default=None, metadata={'units': 'None'})
    efficiency_kind: str = field(default='incident')
    """ 'incident' (relative to incoming photons) or 'absorbed' (relative to absorbed photons). """

    # Efficiency grid
    efficiency_wavelength: np.ndarray = field(default=None, metadata={'units': 'nanometers'})
    efficiency_incidence_angle: np.ndarray = field(default=None, metadata={'units': 'degrees'})

    def __setattr__(self, key, value):
        if value is not None:
            # Convert lists/tuples to arrays automatically
            if key in {'transmittance', 'reflectance', 'absorption', 
                       'transmittance_back', 'reflectance_back', 'absorption_back',
                       'wavelength', 'incidence_angle', 
                       'efficiency', 'efficiency_wavelength', 'efficiency_incidence_angle'}:
                value = np.asarray(value)
        
        super().__setattr__(key, value)
    
    @property
    def is_defined(self):
        try:
            self._validate()
            return True
        except:
            return False

    def _validate_side(self, t_arr, r_arr, a_arr, side_name="Front"):
        """Helper to validate and fill missing optical properties for one side."""
        if sum([x is None for x in [t_arr, r_arr, a_arr]]) > 1:
            raise(ValueError("At least two properties among transmittance, reflectance and absorption must be defined."))

        t = np.zeros_like(r_arr) if t_arr is None else np.asarray(t_arr, dtype=float)
        r = np.zeros_like(t_arr) if r_arr is None else np.asarray(r_arr, dtype=float)
        a = np.zeros_like(r_arr) if a_arr is None else np.asarray(a_arr, dtype=float)

        # Check out of range values
        for name, arr in [('Transmittance', t), ('Reflectance', r), ('Absorption', a)]:
            if arr is not None:
                if np.any(arr < -1e-6) or np.any(arr > 1.0 + 1e-6):
                    raise ValueError(f"{side_name} {name} contains non negligible values outside [0, 1] range.")
                np.clip(arr, 0.0, 1.0, out=arr)

        # Compute missing property
        if t_arr is None: 
            t = 1.0 - np.clip(r + a, 0.0, 1.0)
        elif r_arr is None: 
            r = 1.0 - np.clip(t + a, 0.0, 1.0)
        elif a_arr is None: 
            a = 1.0 - np.clip(t + r, 0.0, 1.0)

        ## Check energy conservation
        # Remove negative rounding values
        t = np.maximum(t, 0.0)
        r = np.maximum(r, 0.0)
        a = np.maximum(a, 0.0)
        # Get total energy
        total_energy = t + r + a
        # Check conservation
        tolerance = 1e-5
        mask_significant = total_energy > (1.0 + tolerance)
        mask_noise = (total_energy > 1.0) & (total_energy <= 1.0 + tolerance)

        # Non negligible conservation violation
        if np.any(mask_significant):
            max_val = np.max(total_energy[mask_significant])
            raise ValueError(f"{side_name} conservation violation: r + t + a > 1 + {tolerance} "
                            f"(max found: {max_val:.9f}). Check input data.")

        # Normalize negligibleout of range values
        if np.any(mask_noise):
            t[mask_noise] /= total_energy[mask_noise]
            r[mask_noise] /= total_energy[mask_noise]
            a[mask_noise] /= total_energy[mask_noise]
        
        return t, r, a

    def _validate(self):
        """
        Validation of properties. 
        """

        # Validate efficiency
        has_efficiency_grid = (self.efficiency_wavelength is not None or self.efficiency_incidence_angle is not None)
        
        if self.efficiency is not None:
            if not has_efficiency_grid:
                 raise ValueError("Efficiency defined but wavelength/incidence angle are missing.")
            
            # Range check
            if np.any(self.efficiency < -1e-9) or np.any(self.efficiency > 1.0 + 1e-9):
                raise ValueError("Efficiency must be between 0 and 1.")
            self.efficiency = np.clip(self.efficiency, 0.0, 1.0)

        # Validate optical properties
        has_optical_grid = (self.wavelength is not None or self.incidence_angle is not None)

        front_optical_props_present = any(x is not None for x in [self.transmittance, self.reflectance, self.absorption])

        back_optical_props_present = any(x is not None for x in [self.transmittance_back, self.reflectance_back, self.absorption_back])

        if back_optical_props_present or front_optical_props_present:
            if not has_optical_grid:
                 raise ValueError("Optical properties defined but wavelength/incidence angle are missing.")
        
        if front_optical_props_present:
            self.transmittance, self.reflectance, self.absorption = self._validate_side(
                self.transmittance, self.reflectance, self.absorption, side_name="Front"
            )

        if front_optical_props_present and back_optical_props_present:
            self.transmittance_back, self.reflectance_back, self.absorption_back = self._validate_side(
                self.transmittance_back, self.reflectance_back, self.absorption_back, side_name="Back"
            )

    def _prepare_texture_data_for_grid(self, data, wl_arr, ang_arr):
        """Pads and formats data for a specific wavelength/angle grid."""
        n_wl = len(wl_arr) if wl_arr is not None else 1
        n_th = len(ang_arr) if ang_arr is not None else 1

        if data is None:
            arr = np.zeros((n_th, n_wl), dtype=np.float32)
        else:
            arr = np.asarray(data, dtype=np.float32)
            # Check compatibility
            if arr.shape != (n_th, n_wl):
                # Allow reshaping only if the total number of elements matches
                if arr.size == n_th * n_wl:
                    arr = arr.reshape((n_th, n_wl))
                else:
                    raise ValueError(f"Data shape {arr.shape} does not match grid dimensions ({n_th}, {n_wl}).")

        # Wavelength padding
        wl_start = 0.0
        wl_inv_step = 0.0
        if wl_arr is not None and n_wl > 1:
            step = float(wl_arr[1] - wl_arr[0])
            if step != 0:
                wl_inv_step = 1.0 / step
                wl_start = float(wl_arr[0]) - step
                arr = np.pad(arr, ((0, 0), (1, 1)), mode='constant', constant_values=0)
        elif wl_arr is not None and n_wl == 1:
            wl_start = float(wl_arr[0])

        # Angle padding
        th_start = 0.0
        th_inv_step = 0.0
        if ang_arr is not None and n_th > 1:
            step = float(ang_arr[1] - ang_arr[0])
            if step != 0:
                th_inv_step = 1.0 / step
                
                pad_top = 1 
                pad_bottom = 1 
                if float(ang_arr[0]) - step < -1e-5: pad_top = 0
                if float(ang_arr[-1]) + step > 90.0 + 1e-5: pad_bottom = 0

                if pad_top == 1: th_start = float(ang_arr[0]) - step
                else: th_start = float(ang_arr[0])
                
                if pad_top > 0 or pad_bottom > 0:
                    arr = np.pad(arr, ((pad_top, pad_bottom), (0, 0)), mode='constant', constant_values=0)
                    
        elif ang_arr is not None and n_th == 1:
            th_start = float(ang_arr[0])

        return arr, wl_start, wl_inv_step, th_start, th_inv_step

    def get_textures(self) -> SurfaceTextures:
        """
        Creates a SurfaceTextures object.
        """
        self._validate()

        no_front_props = self.transmittance is None and self.reflectance is None
        no_back_props = self.transmittance_back is None and self.reflectance_back is None

        # Optical properties
        # If front(back) properties are missing use the back(front) ones

        if no_back_props and no_front_props:
            # Default dummy grid if no optical props
            # The ray-tracing kernel will check if the grid spacing is > 0 
            wl_grid = self.wavelength if self.wavelength is not None else np.array([0.0])
            ang_grid = self.incidence_angle if self.incidence_angle is not None else np.array([0.0])
            t_data, _, _, _, _ = self._prepare_texture_data_for_grid(None, wl_grid, ang_grid)
            r_data, _, _, _, _ = self._prepare_texture_data_for_grid(None, wl_grid, ang_grid)
            opt_wl_s, opt_wl_inv = 0.0, 0.0 
            opt_th_s, opt_th_inv = 0.0, 0.0
            no_back_props = True
            no_front_props = False

        elif no_back_props or no_front_props:
            input_tran = self.transmittance if not no_front_props else self.transmittance_back
            input_refl = self.reflectance if not no_front_props else self.reflectance_back
            t_data, opt_wl_s, opt_wl_inv, opt_th_s, opt_th_inv = self._prepare_texture_data_for_grid(
                input_tran, self.wavelength, self.incidence_angle
            )
            r_data, _, _, _, _ = self._prepare_texture_data_for_grid(
                input_refl, self.wavelength, self.incidence_angle
            )
        else:
            t_data, opt_wl_s, opt_wl_inv, opt_th_s, opt_th_inv = self._prepare_texture_data_for_grid(
                self.transmittance, self.wavelength, self.incidence_angle
            )
            r_data, _, _, _, _ = self._prepare_texture_data_for_grid(
                self.reflectance, self.wavelength, self.incidence_angle
            )
            t_back_data, _, _, _, _ = self._prepare_texture_data_for_grid(
                self.transmittance_back, self.wavelength, self.incidence_angle
            )
            r_back_data, _, _, _, _ = self._prepare_texture_data_for_grid(
                self.reflectance_back, self.wavelength, self.incidence_angle
            )

        if not no_front_props:
            tex_t, arr_t = self._create_texture_2d(t_data)
            tex_r, arr_r = self._create_texture_2d(r_data)
        
        if not no_back_props:
            tex_t_back, arr_t_back = self._create_texture_2d(t_back_data)
            tex_r_back, arr_r_back = self._create_texture_2d(r_back_data)
        
        if no_back_props and not no_front_props:
            tex_t_back, tex_r_back = tex_t, tex_r
            arr_t_back, arr_r_back = None, None
        
        if no_front_props and not no_back_props:
            tex_t, tex_r = tex_t_back, tex_r_back
            arr_t, arr_r = None, None

        # Efficiency
        if self.efficiency is None:
            # Void texture data (is going to be ignored by the ray-traacing kernel)
            eff_data, _, _, _, _ = self._prepare_texture_data_for_grid(None, [0.], [0.])
            eff_wl_s, eff_wl_inv = 0.0, 0.0
            eff_th_s, eff_th_inv = 0.0, 0.0
        else:
            eff_data, eff_wl_s, eff_wl_inv, eff_th_s, eff_th_inv = self._prepare_texture_data_for_grid(
                self.efficiency, self.efficiency_wavelength, self.efficiency_incidence_angle
            )

        tex_eff, arr_eff = self._create_texture_2d(eff_data)

        return SurfaceTextures(
            transmittance=tex_t, reflectance=tex_r,
            transmittance_back=tex_t_back, reflectance_back=tex_r_back,
            optical_wavelength_start=opt_wl_s, optical_wavelength_inv_step=opt_wl_inv,
            optical_angle_start=opt_th_s, optical_angle_inv_step=opt_th_inv,
            efficiency=tex_eff,
            efficiency_wavelength_start=eff_wl_s, efficiency_wavelength_inv_step=eff_wl_inv,
            efficiency_angle_start=eff_th_s, efficiency_angle_inv_step=eff_th_inv,
            _t_array=arr_t, _r_array=arr_r,
            _t_back_array=arr_t_back, _r_back_array=arr_r_back, _eff_array=arr_eff
        )

    def _create_texture_2d(self, texture_data_np):
        """Internal helper to create a TextureObject from a numpy array."""
        texture_data = texture_data_np.astype(np.float32)
        height, width = texture_data.shape
        
        desc = cp.cuda.texture.ChannelFormatDescriptor(
            32, 0, 0, 0,
            cp.cuda.runtime.cudaChannelFormatKindFloat
        )
        
        cu_array = cp.cuda.texture.CUDAarray(
            desc,
            width,
            height
        )
        cu_array.copy_from(texture_data)
        
        res_desc = cp.cuda.texture.ResourceDescriptor(
            cp.cuda.runtime.cudaResourceTypeArray,
            cuArr=cu_array
        )
        
        tex_desc = cp.cuda.texture.TextureDescriptor(
            addressModes=(cp.cuda.runtime.cudaAddressModeClamp, cp.cuda.runtime.cudaAddressModeClamp),
            filterMode=cp.cuda.runtime.cudaFilterModeLinear,
            readMode=cp.cuda.runtime.cudaReadModeElementType,
            normalizedCoords=False
        )

        return cp.cuda.texture.TextureObject(res_desc, tex_desc), cu_array

    @iactsim_style
    def plot(self, kind: str = 'transmittance', heatmap: bool | None = None, cmap: str = "Spectral"):
        """Plot properties including transmittance, reflectance, absorption, and efficiency."""
        self._validate()

        import matplotlib.pyplot as plt

        kind_lower = kind.lower()
        is_back = 'back' in kind_lower

        if kind_lower.startswith('e'):
            data = self.efficiency
            if data is None: 
                raise ValueError("No efficiency defined.")

            # Determine grid
            pl_wl = self.efficiency_wavelength
            pl_ang = self.efficiency_incidence_angle
            
            label_suffix = " (incident)" if self.efficiency_kind == 'incident' else " (absorbed)"
            title_label = "Efficiency" + label_suffix

        else:
            if kind_lower.startswith('t'): 
                base_attr = 'transmittance'
            elif kind_lower.startswith('r'): 
                base_attr = 'reflectance'
            elif kind_lower.startswith('a'): 
                base_attr = 'absorption'
            else: 
                raise ValueError(f"Unknown plot kind: '{kind}'")
            
            target_attr = f"{base_attr}_back" if is_back else base_attr
            data = getattr(self, target_attr)
            if data is None: 
                raise ValueError(f"{target_attr} is not initialized.")

            pl_wl = self.wavelength
            pl_ang = self.incidence_angle
            title_label = f"{base_attr.title()}" + (" (back)" if is_back else " (front)")

        fig, ax = plt.subplots()
        n_wl = len(pl_wl) if pl_wl is not None else 1
        n_th = len(pl_ang) if pl_ang is not None else 1
        
        if data.ndim == 1:
            if n_th == 1: curves = data.reshape(1, n_wl)
            elif n_wl == 1: curves = data.reshape(n_th, 1)
            else: curves = data.reshape(n_th, n_wl)
        else:
            curves = data.reshape(n_th, n_wl)

        if heatmap is None: heatmap = (n_th > 11 and n_wl > 11)
        if not (pl_wl is not None and pl_ang is not None): heatmap = False

        if heatmap:
            contour = ax.contourf(pl_wl, pl_ang, curves, levels=np.linspace(0, 1, 100), cmap=cmap)
            ax.set_xlabel("Wavelength (nm)")
            ax.set_ylabel("Incidence angle ($\\degree$)")
            cbar = fig.colorbar(contour, ax=ax, boundaries=np.linspace(0, 1, 100))
            cbar.set_label(title_label)
        else:
            show_legend = False
            if n_th <= n_wl:
                x_axis = pl_wl if pl_wl is not None else np.arange(n_wl)
                for i in range(n_th):
                    lbl = f'{pl_ang[i]:.1f} $\\degree$' if pl_ang is not None else None
                    ax.plot(x_axis, curves[i], label=lbl)
                ax.set_xlabel('Wavelength (nm)')
                if n_th > 0:
                    show_legend = True
            else:
                x_axis = pl_ang if pl_ang is not None else np.arange(n_th)
                for i in range(n_wl):
                    lbl = f'{pl_wl[i]:.1f} nm' if pl_wl is not None else None
                    ax.plot(x_axis, curves[:, i], label=lbl)
                ax.set_xlabel('Incidence angle ($\\degree$)')
                if n_wl > 0:
                    show_legend = True

            if show_legend:
                ax.legend()
            
            ax.set_ylabel(title_label)
            ax.grid(which='both')

        return fig, ax

    def save_json(self, filename: str):
        """
        Saves the raw surface attributes to a JSON file.
        """
        import json
        
        # Helper to convert data for JSON
        def to_json_friendly(val):
            if val is None:
                return None
            if isinstance(val, np.ndarray):
                return val.tolist() # Convert numpy -> list
            return val

        # Dictionary of all attributes to save
        data = {
            # Optical
            'transmittance': to_json_friendly(self.transmittance),
            'reflectance':   to_json_friendly(self.reflectance),
            'absorption':    to_json_friendly(self.absorption),
            'transmittance_back': to_json_friendly(self.transmittance_back),
            'reflectance_back':   to_json_friendly(self.reflectance_back),
            'absorption_back':    to_json_friendly(self.absorption_back),
            'wavelength':      to_json_friendly(self.wavelength),
            'incidence_angle': to_json_friendly(self.incidence_angle),
            
            # Efficiency
            'efficiency':                 to_json_friendly(self.efficiency),
            'efficiency_kind':            self.efficiency_kind,
            'efficiency_wavelength':      to_json_friendly(self.efficiency_wavelength),
            'efficiency_incidence_angle': to_json_friendly(self.efficiency_incidence_angle),
        }

        # Filter out None values to keep the file clean
        data = {k: v for k, v in data.items() if v is not None}

        with open(filename, 'w') as f:
            # indent=2 ensures pretty printing
            json.dump(data, f, indent=2)

    @classmethod
    def load_json(cls, filename: str):
        """
        Loads surface attributes from a JSON file.
        """
        import json
        
        with open(filename, 'r') as f:
            data = json.load(f)
            
        obj = cls()
        
        # Helper to restore numpy arrays
        def from_json(key):
            val = data.get(key)
            if val is None:
                return None
            # Strings (efficiency_kind) stay strings, lists become arrays
            if isinstance(val, list):
                return np.array(val, dtype=np.float32)
            return val

        # Optical
        obj.transmittance = from_json('transmittance')
        obj.reflectance   = from_json('reflectance')
        obj.absorption    = from_json('absorption')
        
        obj.transmittance_back = from_json('transmittance_back')
        obj.reflectance_back   = from_json('reflectance_back')
        obj.absorption_back    = from_json('absorption_back')
        
        # Grids
        obj.wavelength      = from_json('wavelength')
        obj.incidence_angle = from_json('incidence_angle')
        
        # Efficiency
        obj.efficiency = from_json('efficiency')
        if 'efficiency_kind' in data:
            obj.efficiency_kind = data['efficiency_kind']
            
        obj.efficiency_wavelength      = from_json('efficiency_wavelength')
        obj.efficiency_incidence_angle = from_json('efficiency_incidence_angle')

        return obj