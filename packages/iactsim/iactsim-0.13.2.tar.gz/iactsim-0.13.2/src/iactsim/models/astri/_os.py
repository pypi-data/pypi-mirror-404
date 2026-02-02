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

from pathlib import Path
from typing import Tuple, Union, Dict, Any, Optional

import numpy as np
import yaml

from ...optics._surface_misc import SurfaceType
from ...optics._surface import (
    AsphericalSurface,
    FlatSurface,
    SphericalSurface,
    CylindricalSurface,
    ApertureShape,
    SurfaceProperties,
    SipmTileSurface,
    SurfaceVisualProperties
)
from ...optics._optical_system import OpticalSystem
from ...optics._materials import Materials
from ...optics._cpu_transforms import photon_to_local_rotation

from ._camera import AstriCameraGeometry

from ...io._path_loader import PathLoader

class AstriOpticalSystem(OpticalSystem):
    """
    ASTRI optical system definition (dual-mirror Schwarzschild-Couder).

    This class defines the optical geometry and the main shadowing elements of the mechanical structure of the ASTRI telescope.

    Coordinate System
    -----------------
    - Origin (0,0,0): vertex of the primary mirror (M1).
    - z-axis: optical axis, concave surfaces must have c>0.

    Parametrization
    ---------------
    The system is divided into independent clusters that can be moved along the optical axis (Z)
    without affecting other components:

    1. M1:
       - Static at Z=0.
       - Can be segmented (hexagonal segments) or monolithic.

    2. Secondary mirror (M2):
       - Controlled by `m2_axial_position`.
       - Includes the M2 mirror and its mechanical baffles.

    3. Camera:
       - Controlled by `fp_axial_position` (focal plane vertex);
       - Includes the focal plane, the camera window, the camera body, and the central tube;
       - Moving the FP automatically moves the window and sensors;

    Direct Surface Access
    ---------------------
    Apart from the main parameters that control the M1, M2, and Camera clusters, the properties 
    of each specific surface can be modified via direct access (e.g., ``self['M2'].position = ``).
    
    .. warning::
        When modifying surfaces directly, no overlap or collision checks are performed. 
       
        When to call `rebuild_structure()` manually:
        If you modify a parameter that affects dependent geometry (e.g., changing M2 position 
        should change the M2 Baffle position), you can call `self.rebuild_structure()` 
        manually after your changes to apply them to the rest of the system.

        The auto-reorganization of the surfaces is not completely supported, please check your geometry with `visualization.VTKOpticalSystem`.
        A lot of surfaces are destroyed and recreated from scratch whenever 
        `rebuild_structure()` is called. Any custom properties applied directly will be lost.
        So, it would be better to assign non-geometry properties after calling `rebuild_structure()`.

    See Also
    --------
    :py:class:`iactsim.optics.OpticalSystem`
    """

    # Design values for M1
    default_m1_r = 2153.
    default_m1_c = 1/8223.
    default_m1_a = -np.array([
        0.0, 9.610594335657154e-13, -5.655007251743067e-20, 6.779846300812014e-27,
        3.895878871219899e-33, 5.280381799628059e-40, -2.991060741547783e-47,
        -4.391530590471279e-53, -6.174332023811481e-60, 2.7358654573036966e-66
    ])

    # Design values for M2
    default_m2_r = 900.
    default_m2_c = -1/2180.
    default_m2_a = -np.array([
        0.0, 1.620759030635574e-11, -2.895843564948884e-17, 8.633712193781264e-24,
        3.348558057289531e-30, -1.033610024069273e-36, -6.735253655133213e-43,
        -3.0654711881577763e-49, 3.1716123568176433e-55, -3.711831037954923e-62
    ])

    # Default positions
    default_m2_z = 3108.4
    default_fp_z = 3108.4 - 519.6 # ~2588.8
    
    _min_fp_cb_distance = 200.0 

    def __init__(self):
        # Initialize visual properties
        self._init_visual_props()

        # Initialize m2 and fp position
        self._m2_global_z = self.default_m2_z
        self._fp_global_z = self.default_fp_z
        
        # Initialize camera parameters
        self._camera_window_radius = 250.
        self._camera_body_size = [250, 400] # [Radius, Height]

        # No masts by default
        self._include_masts = False

        # Camera window parameters (None = dummy window)
        self._camera_window_parameters: Optional[Dict[str, float]] = None 

        # Camera body position (by deafult with a dummy window)
        # Window position (FP + 2) + 10mm offset - half_Height
        initial_window_top = self._fp_global_z + 2
        self._camera_body_global_z = initial_window_top - 0.5 * self._camera_body_size[1] + 10

        # Create basic optical system surface objects
        self._create_base_surfaces()
        
        # Camera geometry (bot used at the moment)
        self.camera_geometry = AstriCameraGeometry()

        # Initialize base class
        super().__init__(surfaces=[self.m1, self.m2, self.fp], name='ASTRI-OS')

        # Cache for module properties, since they are rebuild from scratch at each rebuild_structure() call
        self._module_properties_cache: Dict[str, SurfaceProperties] = {}
        self._module_type_cache: Dict[str, SurfaceType] = {}

        # Apply parameterization
        self.rebuild_structure()

    def _init_visual_props(self):
        self._mirror_vis_props = SurfaceVisualProperties(
            color=(0.6, 0.6, 0.6), opacity=1.0, specular=0.4, visible=True)
        self._opaque_vis_props = SurfaceVisualProperties(
            color=(1, 0.3, 0.3), opacity=1.0, specular=0.1, visible=True)
        self._refractive_vis_props = SurfaceVisualProperties(
            color=(0.4, 0.7, 1.0), opacity=0.2, specular=0.3, visible=True)

    def _create_base_surfaces(self):
        """Instantiate surface objects. Positions are computed in rebuild_structure."""
        
        # M1
        self.m1 = AsphericalSurface(
            half_aperture=self.default_m1_r,
            curvature=self.default_m1_c,
            conic_constant=0.,
            aspheric_coefficients=self.default_m1_a,
            surface_type=SurfaceType.REFLECTIVE_FRONT,
            aperture_shape=ApertureShape.CIRCULAR,
            central_hole_shape=ApertureShape.HEXAGONAL,
            central_hole_half_aperture=423.,
            name='M1',
        )
        self.m1.visual_properties = self._mirror_vis_props

        # M2
        self.m2 = AsphericalSurface(
            half_aperture=self.default_m2_r,
            curvature=self.default_m2_c,
            conic_constant=0.,
            aspheric_coefficients=self.default_m2_a,
            surface_type=SurfaceType.REFLECTIVE_BACK,
            name='M2',
        )
        self.m2.visual_properties = self._mirror_vis_props

        # Focal plane (FP)
        c_fp = -1./1060.
        r_fp = 250.
        self.fp = SphericalSurface(
            half_aperture=r_fp,
            curvature=c_fp,
            surface_type=SurfaceType.SENSITIVE_FRONT,
            name='FP'
        )

        # Dummy window
        self._dummy_window = FlatSurface(
            self._camera_window_radius,
            position=(0,0,0),
            surface_type=SurfaceType.DUMMY,
            name='Window',
        )
        self._dummy_window.visual_properties = self._refractive_vis_props

        # Camera body
        self.camera_body = CylindricalSurface(
            radius=self._camera_body_size[0],
            height=self._camera_body_size[1],
            surface_type=SurfaceType.OPAQUE,
            name='CameraBody',
            has_top=False,
            has_bottom=True
        )
        self.camera_body.visual_properties = self._opaque_vis_props

        # Central tube
        self.central_tube = CylindricalSurface(
            radius=203.2,
            height=100,
            position=(0,0,0),
            has_bottom=True,
            has_top=True,
            surface_type=SurfaceType.OPAQUE,
            name='CentralTube',
        )
        self.central_tube.visual_properties = self._opaque_vis_props

        # M2 Baffles
        self.m2_baffle_1 = FlatSurface(
            position=(0,0,0),
            half_aperture=1070.,
            central_hole_half_aperture=self.m2.half_aperture-50, 
            surface_type=SurfaceType.OPAQUE,
            name='M2-baffle-1'
        )
        self.m2_baffle_1.visual_properties = self._opaque_vis_props
        
        self.m2_baffle_2 = CylindricalSurface(
            position=(0,0,0), radius=1070., height=100.,
            surface_type=SurfaceType.OPAQUE, has_bottom=False, has_top=False,
            name='M2-baffle-2'
        )
        self.m2_baffle_2.visual_properties = self._opaque_vis_props

    @property
    def m2_axial_position(self):
        """Axial position of the M2 mirror vertex.
        Changing this moves M2 and its baffles.
        """
        return self._m2_global_z

    @m2_axial_position.setter
    def m2_axial_position(self, value):
        self._m2_global_z = float(value)
        self._update_m2_cluster()

    @property
    def fp_axial_position(self):
        """Axial position of the focal plane vertex.
        Changing this moves the camera sensitive surface, window, and central tube.
        """
        return self._fp_global_z

    @fp_axial_position.setter
    def fp_axial_position(self, value):
        self._fp_global_z = float(value)
        self._update_camera_cluster()

    @property
    def camera_body_axial_position(self):
        """Axial position of the camera body center."""
        return self._camera_body_global_z
    
    @camera_body_axial_position.setter
    def camera_body_axial_position(self, value):
        self._camera_body_global_z = float(value)
        self._update_camera_cluster()

    @property
    def camera_body_size(self):
        """Cylindrical camera body dimensions [radius, height]."""
        return self._camera_body_size

    @camera_body_size.setter
    def camera_body_size(self, value):
        if len(value) != 2:
             raise ValueError("Camera body size must be [radius, height]")
        self._camera_body_size = value
        self._update_camera_cluster()

    @property
    def camera_window_parameters(self) -> Optional[Dict[str, float]]:
        """Dictionary of camera window parameters. Read-only property.
        Use `set_camera_window_parameters` to modify.
        """
        return self._camera_window_parameters

    def set_camera_window_parameters(
        self, 
        radius: float, 
        sipm_distance: float, 
        thickness: float, 
        separation: float, 
        top_camera_body_distance: float,
        layer_1_as_cylinder: bool = True,
        layer_2_as_cylinder: bool = True,
        layer_3_as_cylinder: bool = True
    ) -> None:
        """
        Set the camera window parameters and build the window layers.

        Parameters
        ----------
        radius : float
            Radius of the window layers.
        sipm_distance : float
            Distance from the SiPM surface to the window.
        thickness : float
            Thickness of each window layer.
        separation : float
            Separation between window layers.
        top_camera_body_distance : float
            Distance between the top window layer and the top of the camera body.
        """
        self._camera_window_parameters = {
            'radius': radius,
            'sipm_distance': sipm_distance,
            'thickness': thickness,
            'separation': separation,
            'top_camera_body_distance': top_camera_body_distance,
            'layer_1_as_cylinder': layer_1_as_cylinder,
            'layer_2_as_cylinder': layer_2_as_cylinder,
            'layer_3_as_cylinder': layer_3_as_cylinder
        }
        self._update_camera_cluster()

    def remove_window_layers(self) -> None:
        """Removes the window layers and restores the dummy window."""
        self._camera_window_parameters = None
        self._update_camera_cluster()

    def rebuild_structure(self):
        """
        Full rebuild of all component positions based on current independent parameters.
        """
        # M1 is at origin (unless segmented logic removed it)
        self.m1.position = (0, 0, 0)

        # Rebuild M1 if missing (e.g., after removing segments)
        if 'M1' not in self and not any([s.name.startswith('M1-segment') for s in self]):
            self.add_surface(self.m1, replace=True)

        # Update M2 surfaces
        self._update_m2_cluster()

        # Update camera surfaces
        self._update_camera_cluster()

        # Masts
        if self._include_masts:
            self.build_masts()

    def _update_m2_cluster(self):
        """Updates M2 and its attached baffles based on _m2_global_z."""
        
        # M2 Position
        self.m2.position = (0, 0, self._m2_global_z)
        self._ensure_surface_in_list('M2', self.m2)

        # M2 baffles
        sag_at_900 = self.m2.sagitta(self.m2.half_aperture)
        m2_baffle_z = self.m2.position[2] + sag_at_900
        
        self.m2_baffle_1.position = (0, 0, m2_baffle_z+50)
        
        baffle_dz = 150.4 + 50
        self.m2_baffle_2.height = baffle_dz
        self.m2_baffle_2.position = (0, 0, m2_baffle_z + 50 - 0.5 * baffle_dz)

        self._ensure_surface_in_list('M2-baffle-1', self.m2_baffle_1)
        self._ensure_surface_in_list('M2-baffle-2', self.m2_baffle_2)

    def _update_camera_cluster(self):
        """Updates focal plane, window, camera body, and central tube positions."""
        top_body_dist = 10.
        if self._camera_window_parameters:
            top_body_dist = self._camera_window_parameters.get('top_camera_body_distance')

        final_fp_z = self._fp_global_z
        self.fp.position = (0, 0, final_fp_z)
        
        # Build window and determine top reference
        active_window_surface = None
        window_top_z = -1e9

        # Dummy window
        if self._camera_window_parameters is None:
            self._dummy_window.radius = self._camera_window_radius

            # Position dummy window at 2 mm from focal plane
            self._dummy_window.position = (0, 0, final_fp_z + 2)
            
            active_window_surface = self._dummy_window
            window_top_z = self._dummy_window.position[2]
            
            self._ensure_surface_in_list('Window', self._dummy_window)
            self._remove_window_layers_internal()
        # Real multi-layer window
        else:
            params = self._camera_window_parameters
            w_rad = params['radius']
            sipm_dist = params['sipm_distance']
            l_thick = params['thickness']
            l_sep = params['separation']
            
            start_z = final_fp_z + sipm_dist
            self.remove_surface('Window') # Remove dummy if present
            
            as_cylinder = [
                params['layer_1_as_cylinder'],
                params['layer_2_as_cylinder'],
                params['layer_3_as_cylinder']
            ]

            # Build the three layers
            for i in range(3):
                if as_cylinder[i]:
                    layer_name = f'WindowLayer{i+1}'
                    z_pos = start_z + 0.5 * l_thick + i * (l_sep + l_thick)
                    
                    if layer_name in self:
                        layer = self[layer_name]
                        layer.radius = w_rad
                        layer.height = l_thick
                        layer.position = (0, 0, z_pos)
                    else:
                        layer = CylindricalSurface(
                            radius=w_rad, height=l_thick, name=layer_name,
                            surface_type=SurfaceType.REFRACTIVE, position=(0,0,z_pos),
                            has_bottom=True, has_top=True
                        )
                        layer.visual_properties = self._refractive_vis_props
                        layer.material_in = Materials.FUSED_SILICA
                        layer.material_out = Materials.AIR
                        self.add_surface(layer, replace=True)
                    
                    # Keep this as reference for the camera body positioning
                    if i == 2: 
                        active_window_surface = layer 
                        window_top_z = layer.position[2] + 0.5 * layer.height
                else:
                    self.remove_surface(f'WindowLayer{i+1}')
                    layer_bottom = FlatSurface(
                        half_aperture=w_rad,
                        position=(0, 0, start_z + i * (l_sep + l_thick)),
                        surface_type=SurfaceType.REFRACTIVE,
                        material_in=Materials.FUSED_SILICA,
                        material_out=Materials.AIR,
                        name=f'WindowLayer{i+1}Bottom'
                    )
                    layer_top = FlatSurface(
                        half_aperture=w_rad,
                        position=(0, 0, start_z + l_thick + i * (l_sep + l_thick)),
                        surface_type=SurfaceType.REFRACTIVE,
                        material_out=Materials.FUSED_SILICA,
                        material_in=Materials.AIR,
                        name=f'WindowLayer{i+1}'
                    )
                    self.add_surface(layer_bottom, replace=True)
                    self.add_surface(layer_top, replace=True)
                    
                    # Keep this as reference for the camera body positioning
                    if i == 2: 
                        active_window_surface = layer_top 
                        window_top_z = layer_top.position[2]
        
        # Position camera body based on window top + distance
        cam_rad, cam_h = self._camera_body_size
        
        # Align top of body with top of window + specified distance
        # body_center_z = window_top + distance - body_height/2
        body_z_center = window_top_z + top_body_dist - 0.5 * cam_h
        
        self.camera_body.radius = cam_rad
        self.camera_body.height = cam_h
        self.camera_body.position = (0, 0, body_z_center)
        self.camera_body.tilt_angles = (0., 0., 0.)
        
        # Update internal state variable
        self._camera_body_global_z = body_z_center
        self._ensure_surface_in_list('CameraBody', self.camera_body)

        # Update SiPM modules or focal plane (that is, remove and rebuild)
        if not 'FP' in self and 'PDM1' in self:
             self.remove_camera_modules()
             self.build_camera_modules()
        else:
             self._ensure_surface_in_list('FP', self.fp)

        ######
        ###### Check positioning        
        body_z_top = body_z_center + 0.5 * cam_h
        body_z_bottom = body_z_center - 0.5 * cam_h

        if window_top_z > body_z_top + 1e-4:
            raise ValueError(
                f"Invalid Configuration: The window top (Z={window_top_z:.2f}) "
                f"extends outside the Camera Body (Top Z={body_z_top:.2f})."
            )

        if final_fp_z < body_z_bottom + self._min_fp_cb_distance:
            raise ValueError(
                f"Invalid Configuration: The Focal Plane (Z={final_fp_z:.2f}) "
                f"is too close to the Camera Body bottom (Z={body_z_bottom:.2f}). "
                f"Minimum clearance required: {self._min_fp_cb_distance}mm."
            )

        ######
        ###### Rest of the camera structure

        # Camera body cap
        window_r = active_window_surface.radius if hasattr(active_window_surface, 'radius') else active_window_surface.half_aperture
        
        cap_z = body_z_top 
        
        if cam_rad - window_r > 0.1:
            if 'CameraBodyTop' in self:
                cap = self['CameraBodyTop']
                cap.half_aperture = cam_rad
                cap.central_hole_half_aperture = window_r
                cap.position = (0, 0, cap_z)
            else:
                cap = FlatSurface(
                    half_aperture=cam_rad,
                    central_hole_half_aperture=window_r,
                    surface_type=SurfaceType.OPAQUE,
                    position=(0,0,cap_z),
                    name='CameraBodyTop'
                )
                cap.visual_properties = self._opaque_vis_props
                self.add_surface(cap, replace=True)
        else:
            if 'CameraBodyTop' in self: self.remove_surface('CameraBodyTop')

        # Central tube
        camera_bottom_z = body_z_bottom
        tube_h = max(0.1, camera_bottom_z)
        
        self.central_tube.height = tube_h
        self.central_tube.position = (0, 0, 0.5 * tube_h)
        self._ensure_surface_in_list('CentralTube', self.central_tube)

    def _ensure_surface_in_list(self, name, surface_obj):
        """Helper to ensure a surface object is in the system dict."""
        if name not in self:
            self.add_surface(surface_obj, replace=True)

    def _remove_window_layers_internal(self):
        """Helper to clean up window layers."""
        for i in range(3):
            name = f'WindowLayer{i+1}'
            if name in self: self.remove_surface(name)
    
    def build_m1_segments(self):
        """
        Builds the 18 hexagonal segments of M1 using nominal coordinates.
        Each segment inherits optical properties from the monolithic M1, 
        which is then removed.
        """
        positions = {
            1:  np.array([     0.   ,   856.5   ,   44.2300]),
            2:  np.array([  -741.4  ,   428.2   ,   44.1964]),
            3:  np.array([  -741.4  ,  -428.2   ,   44.1964]),
            4:  np.array([     0.   ,  -856.5   ,   44.2300]),
            5:  np.array([   741.4  ,  -428.2   ,   44.1964]),
            6:  np.array([   741.4  ,   428.2   ,   44.1964]),
            7:  np.array([  -739.3  ,  1280.5   ,  129.6475]),
            8:  np.array([ -1478.6  ,     0.    ,  129.6483]),
            9:  np.array([  -739.3  , -1280.5   ,  129.6475]),
            10: np.array([   739.3  , -1280.5   ,  129.6475]),
            11: np.array([  1478.6  ,     0.    ,  129.6483]),
            12: np.array([   739.3  ,  1280.5   ,  129.6475]),
            13: np.array([     0.   ,  1704.8   ,  170.5714]),
            14: np.array([ -1476.4  ,   852.4   ,  170.5714]),
            15: np.array([ -1476.4  ,  -852.4   ,  170.5714]),
            16: np.array([     0.   , -1704.8   ,  170.5714]),
            17: np.array([  1476.4  ,  -852.4   ,  170.5714]),
            18: np.array([  1476.4  ,   852.4   ,  170.5714]),
        }

        if 'M1' in self:
            ref_surf = self['M1']
        else:
            ref_surf = AsphericalSurface(
                self.default_m1_r, self.default_m1_c, 0., self.default_m1_a,
                surface_type=SurfaceType.REFLECTIVE_FRONT
            )
            ref_surf.visual_properties = self._mirror_vis_props

        # Half aperture ~423mm (hexagonal)
        seg_half_aperture = 423.0 

        for seg_id, pos in positions.items():
            segment = AsphericalSurface(
                conic_constant=ref_surf.conic_constant,
                aspheric_coefficients=ref_surf.aspheric_coefficients,
                curvature=ref_surf.curvature,
                half_aperture=seg_half_aperture,
                aperture_shape=ApertureShape.HEXAGONAL,
                surface_type=ref_surf.type,
                position=pos,
                name=f'M1-segment-{seg_id}',
                scattering_dispersion=ref_surf.scattering_dispersion
            )
            segment.offset = pos[:2]
            segment.properties = ref_surf.properties
            segment.visual_properties = ref_surf.visual_properties
            self.add_surface(segment, replace=True)

        if 'M1' in self:
            self.remove_surface('M1')

    def remove_m1_segments(self):
        """Removes M1 segments and restores the monolithic M1 mirror."""
        # Find all segments
        segments = [s.name for s in self if s.name.startswith('M1-segment')]
        for name in segments:
            self.remove_surface(name)
        
        # Restore monolithic M1
        self.add_surface(self.m1, replace=True)

    # Configuration helper
    def configure(self, config: Union[str, Path, Dict[str, Any]]) -> None:
        """Configure the optical system."""
        # Load Config
        if isinstance(config, (str, Path)):
            with open(config, 'r') as file:
                os_conf = yaml.load(file, Loader=PathLoader)
        elif isinstance(config, dict):
            os_conf = config
        else:
            raise TypeError("Config must be path or dict")

        if 'include_masts' in os_conf:
            self._include_masts = os_conf['include_masts']

        if 'camera_window' in os_conf:
            if 'parameters' in os_conf['camera_window']:
                values = os_conf['camera_window']['parameters']
                if isinstance(values, (list, tuple)):
                    if len(values) < 5:
                        raise ValueError('Not enough values for camera window list configuration')
                    
                    layer3_defined = 'layer3_properties' in os_conf['camera_window']
                    layer2_defined = 'layer2_properties' in os_conf['camera_window']
                    layer1_defined = 'layer1_properties' in os_conf['camera_window']
                    
                    if not all([layer1_defined, layer2_defined, layer3_defined]):
                        raise(RuntimeError("Properties not defined for all layers of the camera window"))
                    
                    layer3_properties = os_conf['camera_window']['layer3_properties']
                    layer2_properties = os_conf['camera_window']['layer2_properties']
                    layer1_properties = os_conf['camera_window']['layer1_properties']

                    layer_1_as_cylinder = sum(1 for x in layer1_properties if x is not None) == 1
                    layer_2_as_cylinder = sum(1 for x in layer2_properties if x is not None) == 1
                    layer_3_as_cylinder = sum(1 for x in layer3_properties if x is not None) == 1

                    self.set_camera_window_parameters(
                        radius=values[0],
                        sipm_distance=values[1],
                        thickness=values[2],
                        separation=values[3],
                        top_camera_body_distance=values[4],
                        layer_1_as_cylinder=layer_1_as_cylinder,
                        layer_2_as_cylinder=layer_2_as_cylinder,
                        layer_3_as_cylinder=layer_3_as_cylinder
                    )
                elif values is None:
                    self.remove_window_layers()

        if 'camera_body_size' in os_conf:
            values = os_conf['camera_body_size']
            if len(values) < 2:
                raise ValueError('Not enough values for camera body')
            self.camera_body_size = values

        # m2_pos = self.m2_axial_position
        # if 'M2' in os_conf and 'position' in os_conf['M2']:
        #     m2_pos = os_conf['M2']['position'][2]
        # self.m2_axial_position = m2_pos
        
        # if 'FP' in os_conf and 'position' in os_conf['FP']:
        #     self.fp_axial_position = os_conf['FP']['position'][2]
        # else:
        #     self.fp_axial_position = m2_pos - 519.6
        
        if 'CameraBody' in os_conf and 'position' in os_conf['CameraBody']:
            self.camera_body_axial_position = os_conf['CameraBody']['position'][2]

        # Update mirror properties
        for surface_name in ['M1', 'M2']:
            if surface_name not in os_conf:
                continue
            
            if surface_name not in self:
                continue
            
            surface_dict = os_conf[surface_name]
            if 'properties' in surface_dict:
                prop_file = surface_dict['properties']
                self[surface_name].properties = SurfaceProperties.load_json(prop_file)
            
            if 'scattering_dispersion' in surface_dict:
                self[surface_name].scattering_dispersion = surface_dict['scattering_dispersion']

        # M1 Segments
        if "M1-segments" in os_conf:
            self._configure_m1_segments(os_conf["M1-segments"])
        
        # SiPM modules
        self.build_camera_modules()

        # Final rebuild to apply everything
        self.rebuild_structure()

        if 'M2' in os_conf and 'axial_shift' in os_conf['M2']:
            shift = os_conf['M2']['axial_shift']
            if shift is not None:
                self['M2'].position[2] += shift
        
        # For now a single SurfaceProperties for all modules
        if 'sipm' in os_conf:
            sipm_conf = os_conf['sipm']

            s_type = SurfaceType.SENSITIVE_FRONT
            if sipm_conf.get('is_reflective', False):
                s_type = SurfaceType.REFLECTIVE_SENSITIVE_FRONT
            
            surf_props = sipm_conf.get('surface_properties', None)
            if surf_props is not None:
                surf_props = SurfaceProperties.load_json(surf_props)
                if s_type == SurfaceType.REFLECTIVE_SENSITIVE_FRONT:
                    surf_props.efficiency_kind = 'absorbed'
                else:
                    surf_props.efficiency_kind = 'incident'

            self.fp.properties = surf_props
            self.fp.type = s_type

            for k in range(37):
                s_name = f'PDM{k+1}'
                if s_name in self:
                    self[s_name].properties = surf_props
                    self[s_name].type = s_type
        
        if 'camera_window' in os_conf:
            window_conf = os_conf['camera_window']
            if 'Window' in self:
                if 'layer3_properties' in window_conf:
                    prop_file = window_conf['layer3_properties']
                    if prop_file[0] is not None:
                        self['Window'].properties = SurfaceProperties.load_json(prop_file)
            else:
                for i in range(1,4):
                    layer_name = f'WindowLayer{i}'
                    layer_prop_name = f'layer{i}_properties'
                    if layer_prop_name in window_conf:
                        layer_properties = window_conf[layer_prop_name]
                        if layer_properties is not None:
                            if len(layer_properties) < 1:
                                raise(RuntimeError(f'No properties specified for {layer_name}'))
                            if len(layer_properties) == 1:
                                if layer_properties[0] is None:
                                    raise(RuntimeError(f'No properties specified for {layer_name}'))
                                else:
                                    self[layer_name].properties = SurfaceProperties.load_json(layer_properties[0])
                            else:
                                if f'{layer_name}Bottom' in self:
                                    if layer_properties[1] is None:
                                        raise(RuntimeError(f'No properties specified for WindowLayer{i}Bottom'))
                                    else:
                                        self[f'{layer_name}Bottom'].properties = SurfaceProperties.load_json(layer_properties[1])

    def _configure_m1_segments(self, segments_conf):
        """Helper to configure segments from a dict."""
        
        # Check if usage is explicitly disabled
        if not segments_conf.get('use', True):
            return
        else:
            self.build_m1_segments()

        for key in segments_conf:
            
            if key == 'use': 
                continue

            segment_conf = segments_conf[key] 
            
            segment_name = f'M1-segment-{key}'

            segment = self[segment_name]

            offset = segment_conf.get('offset', None)

            half_aperture = segment_conf.get('half_aperture', None)

            shift = segment_conf.get('position_shift', None)
            
            tilt_angles = segment_conf.get('tilt_angles', None)
            
            scattering_dispersion = segment_conf.get('scattering_dispersion', None)
            
            curvature = segment_conf.get('curvature', None)
            
            surf_offset = segment_conf.get('surf_offset', None)

            asph_coeffs = segment_conf.get('aspherical_coefficients', None)
            if asph_coeffs is not None:
                asph_coeffs = np.asarray(asph_coeffs)
            
            if offset is not None:
                r_loc = np.sqrt(offset[0]**2 + offset[1]**2)
                z_loc = self.m1.sagitta(r_loc)
                segment.position = [
                    offset[0],
                    offset[1],
                    z_loc,
                ]

            if shift is not None:
                segment.position[0] += shift[0]
                segment.position[1] += shift[1]
                segment.position[2] += shift[2]
            
            if half_aperture is not None:
                segment.half_aperture = half_aperture
            
            if asph_coeffs is not None:
                segment.aspheric_coefficients = asph_coeffs
            
            if curvature is not None:
                segment.curvature = curvature
            
            if tilt_angles is not None:
                segment.tilt_angles = tilt_angles
            
            if scattering_dispersion is not None:
                segment.scattering_dispersion = scattering_dispersion
            
            if surf_offset is not None:
                segment.offset = surf_offset

            # Handle surface properties
            if 'properties' in segment_conf and segment_conf['properties'] is not None:
                prop_file = segment_conf['properties']
                segment.properties = SurfaceProperties.load_json(prop_file)
            else:
                # Inherit from parent M1 if not specified
                segment.properties = self.m1.properties

    def build_masts(self):        
        mast1_radius = 50.8
        mast1_height = 3135.28 + 100
        mast1_position = [0,-1729.66,1407.78]
        mast2_radius = mast3_radius = 38.05
        mast2_height = 2290.78-50
        mast2_position = [0,-1214.62,1162.12]
        mast3_height = 1156.94
        mast3_position = [0,-705.21,2311.20]
        hollow = True

        mast1_1 = CylindricalSurface(
            radius=mast1_radius, height=mast1_height, has_bottom=not hollow, has_top=not hollow,
            position=mast1_position, tilt_angles=((63.9-90),0,0), name="Mast1-1",
        )
        mast1_2 = CylindricalSurface(
            radius=mast2_radius, height=mast2_height, has_bottom=not hollow, has_top=not hollow,
            position=mast2_position, tilt_angles=((32.6-90),0,0), name="Mast1-2",
        )
        mast1_3 = CylindricalSurface(
            radius=mast3_radius, height=mast3_height, has_bottom=not hollow, has_top=not hollow,
            position=mast3_position, tilt_angles=((90-43.9),0,0), name="Mast1-3",
        )
        mast1_1.visual_properties = self._opaque_vis_props
        mast1_2.visual_properties = self._opaque_vis_props
        mast1_3.visual_properties = self._opaque_vis_props

        self.add_surface(mast1_1, replace=True)
        self.add_surface(mast1_2, replace=True)
        self.add_surface(mast1_3, replace=True)

        theta = 2*np.pi/3
        for i in range(1,3):
            cos_z = np.cos(i*theta)
            sin_z = np.sin(i*theta)
            z_rot = np.array([[ cos_z, -sin_z, 0.], [ sin_z,  cos_z, 0.], [ 0., 0., 1.]])
            
            mast_i_1 = CylindricalSurface(
                radius=mast1_radius, height=mast1_height, has_bottom=not hollow, has_top=not hollow,
                position=z_rot@mast1_1.position, name=f"Mast{i+1}-1",
            )
            mast_i_2 = CylindricalSurface(
                radius=mast2_radius, height=mast2_height, has_bottom=not hollow, has_top=not hollow,
                position=z_rot@mast1_2.position, name=f"Mast{i+1}-2",
            )
            mast_i_3 = CylindricalSurface(
                radius=mast3_radius, height=mast3_height, has_bottom=not hollow, has_top=not hollow,
                position=z_rot@mast1_3.position, name=f"Mast{i+1}-3",
            )
            mast_i_1.visual_properties = self._opaque_vis_props
            mast_i_2.visual_properties = self._opaque_vis_props
            mast_i_3.visual_properties = self._opaque_vis_props

            for mast_i_x, mast1_x in zip([mast_i_1,mast_i_2,mast_i_3],[mast1_1,mast1_2,mast1_3]):
                surface_to_telescope = mast1_x.get_rotation_matrix().T
                updated_surface_to_telescope = z_rot @ surface_to_telescope
                updated_telescope_to_surface = updated_surface_to_telescope.T
                mast_i_x.set_rotation_matrix(updated_telescope_to_surface)
            
            self.add_surface(mast_i_1, replace=True)
            self.add_surface(mast_i_2, replace=True)
            self.add_surface(mast_i_3, replace=True)
    
    def remove_masts(self):
        for s in self:
            if s.name.startswith('Mast'):
                self.remove_surface(s)

    def build_camera_modules(self):
        fp = self.fp
        cam_geom = self.camera_geometry
        pdm_p = cam_geom.modules_p
        pdm_n = cam_geom.modules_n
        
        for k in range(37):
            pdm = SipmTileSurface(
                pixels_per_side=8,
                pixel_active_side=cam_geom.pixel_active_side,
                pixels_separation=cam_geom.pixels_separation,
                border_to_active_area=0.2,
                microcell_size=0.075,
                surface_type=SurfaceType.REFLECTIVE_SENSITIVE_FRONT,
                position = pdm_p[k] + fp.position,
                tilt_angles=(0.,0.,0.),
                name = f'PDM{k+1}'
            )
            pdm.sensor_id = k
            R = photon_to_local_rotation(pdm_n[k]).T
            pdm.set_rotation_matrix(R)
            self.add_surface(pdm, replace=True)

        if 'FP' in self:
            self.remove_surface('FP')

    def remove_camera_modules(self):
        for k in range(37):
            s_name = f'PDM{k+1}'
            if s_name in self:
                self.remove_surface(s_name)

        self.add_surface(self.fp, replace=True)

    @staticmethod
    def load_efficiency_data(filepath: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Loads surface efficiency data from a specially formatted text file."""
        lines = []
        empties = 0
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line.startswith('#'):
                    if line == "":
                        empties += 1
                        if empties > 1:
                            raise(RuntimeError(f"{filepath}: at most one empty line is allowed in an efficiency file."))
                    lines.append(line)
        
        wavelengths = np.fromstring(lines[0], sep=' ')
        if wavelengths.shape[0] == 1 and wavelengths[0] == -1:
            wavelengths = None
        
        incidence_angles = np.fromstring(lines[1], sep=' ')
        if incidence_angles.shape[0] == 1 and incidence_angles[0] == -1:
            incidence_angles = None
        
        if incidence_angles is None and wavelengths is None:
            raise(RuntimeError(f"{filepath}: no wavelength or incidence angle found."))

        efficiencies = np.array([np.fromstring(line, sep=' ') for line in lines[2:]])

        return wavelengths, incidence_angles, efficiencies