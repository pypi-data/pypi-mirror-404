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

import datetime
import numpy as np
import vtk

from ._vtk_utils import (
    create_aspheric_surface_actor,
    create_cylindric_surface_actor,
    quit
)

from ..optics._surface_misc import SurfaceType, SurfaceShape
from ..optics._surface import SurfaceVisualProperties

from ..optics._cpu_transforms import local_to_telescope_rotation, local_to_pointing_rotation

from .._iact import IACT

from ..optics._optical_system import OpticalSystem


class VTKOpticalSystem():
    """Class to viasualize the geometry of an optical system.
    Each surface actor can be accessed from :py:attr:`actors` attribute after a :py:meth:`update` call.

    Parameters
    ----------
    optical_system : OpticalSystem or IACT
        Optical sistem for which visualize surfaces.
    resolution : float, optional
            Objects mesh resolution (in mm). By default 10 mm.

    Notes
    -----
    If you perform some operation on an actor, make sure to call :py:meth:`start_render` with ``update=False``, otherwise the actors will be replaced.
    
    """
    def __init__(self, optical_system, resolution=None):
        self.actors = {}
        """Dictionary of surface name: surface actor."""

        if issubclass(type(optical_system), OpticalSystem):
            self.os = optical_system
            self._tel_to_local_rot =  np.eye(3)
            self._translation_vector = np.zeros(3)
        elif issubclass(type(optical_system), IACT):
            self.os = optical_system.optical_system
            self._tel_to_local_rot =  local_to_telescope_rotation(*optical_system.pointing).T
            self._translation_vector = optical_system.position
        else:
            raise(ValueError("optical system must be an instance of OpticalSystem or IACT."))

        """Optical system to be visualized."""
        
        self._mirror_props = SurfaceVisualProperties(
            color=(0.6, 0.6, 0.6),
            opacity=1.0,
            specular=0.4,
            wireframe=False,
            resolution=None,
            visible=True
        )

        self._opaque_props = SurfaceVisualProperties(
            color=(0.4, 0.4, 0.4),
            opacity=1.0,
            specular=0.1,
            wireframe=False,
            resolution=None,
            visible=True
        )

        self._sensitive_props = SurfaceVisualProperties(
            color=(0.55, 0.55, 0.55),
            opacity=1.0,
            specular=0.2,
            wireframe=False,
            resolution=None,
            visible=True
        )

        self._refractive_props = SurfaceVisualProperties(
            color=(0.5, 0.5, 1.0),
            opacity=0.2,
            specular=0.3,
            wireframe=False,
            resolution=None,
            visible=True
        )
                
        """Dictionary to custumize surface colors based on surface type."""

        # Wireframe
        self.wireframe = False
        """Whether to use wireframe representation by default."""

        # Window size
        self.window_size = (1024,1024)
        """Window size in pixel."""

        self._resolution = resolution # mm
        """Objects mesh resolution (in mm)."""

        self._ray_opacity = None
        """Ray opacity."""

        self._update()

        self._apply_global_transform()
    
    def _update(self):
        """Generate all surface actors.
        """
        self.actors = {}
        for i,s in enumerate(self.os):
            vp = s.visual_properties

            res = self._resolution
            if vp.resolution is not None:
                res = vp.resolution
            
            if s._shape == SurfaceShape.CYLINDRICAL:
                actor = create_cylindric_surface_actor(s, res)
            else:
                actor = create_aspheric_surface_actor(s, res)

            transform = vtk.vtkTransform()
            transform.Translate(*s.position)
            R = s.get_rotation_matrix()
            vtk_rotation_matrix = vtk.vtkMatrix4x4()
            for i in range(3):
                for j in range(3):
                    vtk_rotation_matrix.SetElement(i, j, R[j, i])
            transform.PreMultiply()
            transform.Concatenate(vtk_rotation_matrix)
            transform.Update()
            actor.SetUserTransform(transform)

            prop = actor.GetProperty()

            is_sensitive = s.type in [
                SurfaceType.SENSITIVE,
                SurfaceType.SENSITIVE_BACK,
                SurfaceType.SENSITIVE_FRONT,
                SurfaceType.REFLECTIVE_SENSITIVE,
                SurfaceType.REFLECTIVE_SENSITIVE_BACK,
                SurfaceType.REFLECTIVE_SENSITIVE_FRONT
            ]
            dvp = None
            if s.type in [SurfaceType.REFLECTIVE, SurfaceType.REFLECTIVE_BACK, SurfaceType.REFLECTIVE_FRONT]:
                dvp = self._mirror_props
            elif s.type == SurfaceType.OPAQUE:
                dvp = self._opaque_props
            elif is_sensitive:
                dvp = self._sensitive_props
            elif s.type == SurfaceType.REFRACTIVE:
                dvp = self._refractive_props
            
            if self.wireframe or vp.wireframe:
                prop.SetRepresentationToWireframe()

            if vp.visible is not None:
                actor.SetVisibility(vp.visible)

            if vp.color is not None:
                prop.SetColor(*vp.color)
            else:
                prop.SetColor(*dvp.color)
            
            if vp.opacity is not None:
                prop.SetOpacity(vp.opacity)
            else:
                prop.SetOpacity(dvp.opacity)

            if vp.specular is not None:
                prop.SetSpecular(vp.specular)
            else:
                prop.SetSpecular(dvp.specular)

            prop.SetAmbient(0.3)
            prop.SetDiffuse(0.5)
            prop.SetSpecularPower(10)

            self.actors[s.name] = actor

    @staticmethod
    def _get_sigmoid_opacity(n_rays, n_50=1000, k=1.5, min_opacity=0.005):
        """
        Calculates ray opacity using a descending sigmoid curve.
        
        Parameters
        ----------
        n_rays : int
            Number of rays being plotted.
        n_50 : int
            The 'knee' of the curve: number of rays where opacity is ~0.5.
        k : float
            Steepness of the curve (the greater the steeper the curve). 
        min_opacity : float
            Minimum visibility floor.
        """
        if n_rays <= 0: return 0.0
        
        # Calculate sigmoid
        opacity = min_opacity + (1.0 - min_opacity) / (1 + (n_rays / n_50)**k)
        
        return opacity

    def start_render(self, camera_position=None, focal_point=None, view_up=(0, 0, 1), orthographic=False):
        """Render the optical system geometry on a VTK window.

        Parameters
        ----------
        camera_position : tuple or list, optional
            (x, y, z) coordinates for the camera position.
        focal_point : tuple, list, or str, optional
            If tuple/list: (x, y, z) coordinates to look at.
            If str: The name of the surface in self.os to look at.
            If None: Defaults to center of system.
        view_up : tuple or list, optional
            (x, y, z) vector defining the "up" direction. Default is (0, 0, 1).
        orthographic : bool, optional
            If True, start with a parallel projection. 
            If False, start with a perspective projection. Default is False.
        """

        # Set opacity based on number of ray actors
        # N.B.: this overestimates the number of photons.
        # N.B.: _set_ray_opacity will not update _ray_opacity
        #       at each start render the opacity will be set automatically
        #       unless an opacity is specified with set_ray_opacity
        if self._ray_opacity is None:
            n_rays = 0
            for actor in self.actors:
                if actor.startswith('rays'):
                    n_rays += self.actors[actor].GetMapper().GetDataSetInput().GetLines().GetNumberOfCells()
            opacity = self._get_sigmoid_opacity(n_rays)
            self._set_ray_opacity(opacity)

        # Rendering
        renderer = vtk.vtkRenderer()
        renderer.SetBackground(0.1, 0.15, 0.25)

        inf = float('inf')
        sys_bounds = [inf, -inf, inf, -inf, inf, -inf]
        has_system_actors = False

        for name, actor in self.actors.items():
            renderer.AddActor(actor)
            
            # Include this actor in the bounds calculation
            if not name.startswith("rays"):
                has_system_actors = True
                b = actor.GetBounds() # (xmin, xmax, ymin, ymax, zmin, zmax)
                sys_bounds[0] = min(sys_bounds[0], b[0])
                sys_bounds[1] = max(sys_bounds[1], b[1])
                sys_bounds[2] = min(sys_bounds[2], b[2])
                sys_bounds[3] = max(sys_bounds[3], b[3])
                sys_bounds[4] = min(sys_bounds[4], b[4])
                sys_bounds[5] = max(sys_bounds[5], b[5])

        # Display instructions
        desc = [
            "Press: 'e/q' to exit/quit",
            "Press: 'w' or 's' to switch to wireframe or surface representation",
            "Press: 'r' to reset the camera zoom",
            "Press: 'o' to toggle orthographic/perspective view",
            "Press: 'p' to pick/unpick actor under cursor",
            "Press: 'f' fly to the picked actor",
            "Press: 'h' to hide the picked actors",
            "Press: 'P' to print the current view",
            "Press: 'i' to isolate picked actors (and hide others)",
            "Press: 'Esc' to clear selection and actions",
            "Press: 'x', 'y' or 'z' to align the up-vector to the desired axis",
        ]
        desc_has_gpu_info = False
        textActor = vtk.vtkTextActor()
        textActor.SetInput('\n'.join(desc))
        position_coordinate = textActor.GetPositionCoordinate()
        position_coordinate.SetCoordinateSystemToNormalizedViewport()
        position_coordinate.SetValue(0.01, 0.99)
        textActor.GetTextProperty().SetJustificationToLeft()
        textActor.GetTextProperty().SetVerticalJustificationToTop()
        textActor.GetTextProperty().SetFontSize(18)
        textActor.GetTextProperty().SetColor(vtk.vtkNamedColors().GetColor3d("Gold"))
        textActor.GetTextProperty().SetFontFamily(vtk.VTK_COURIER)
        textActor.SetVisibility(False)
        renderer.AddActor2D(textActor)

        hintActor = vtk.vtkTextActor()
        hintActor.SetInput("Press '?' for instructions")
        hprop = hintActor.GetTextProperty()
        hprop.SetFontSize(16)
        hprop.SetColor(vtk.vtkNamedColors().GetColor3d("Gold"))
        hprop.SetFontFamily(vtk.VTK_COURIER)
        hprop.SetJustificationToLeft()
        hprop.SetVerticalJustificationToTop()
        hcoord = hintActor.GetPositionCoordinate()
        hcoord.SetCoordinateSystemToNormalizedViewport()
        hcoord.SetValue(0.01, 0.99)
        hintActor.SetVisibility(True)
        renderer.AddActor2D(hintActor)

        render_window = vtk.vtkRenderWindow()
        render_window.SetWindowName(self.os.name)
        render_window.AddRenderer(renderer)
        render_window.SetSize(*self.window_size)
        render_window_interactor = vtk.vtkRenderWindowInteractor()
        render_window_interactor.SetRenderWindow(render_window)

        # Camera
        cam_style = vtk.vtkInteractorStyleTrackballCamera()
        render_window_interactor.SetInteractorStyle(cam_style)

        # Axes
        axes = vtk.vtkAxesActor()
        widget = vtk.vtkOrientationMarkerWidget()
        rgba = [0] * 4
        vtk.vtkNamedColors().GetColor('Carrot', rgba)
        widget.SetOutlineColor(rgba[0], rgba[1], rgba[2])
        widget.SetOrientationMarker(axes)
        widget.SetInteractor(render_window_interactor)
        widget.SetEnabled(1)
        widget.InteractiveOn()

        selected_actors = {} # Store picked actors and their original color
        is_isolated = False
        picker = vtk.vtkCellPicker()
        picker.SetTolerance(0.005)

        def perform_view_reset(up_vector):
            active_camera = renderer.GetActiveCamera()
            
            if not active_camera:
                return

            # Get current view plane normal
            vpn = active_camera.GetViewPlaneNormal()
            
            # Compute dot product
            dot = sum(vpn[i] * up_vector[i] for i in range(3))
            
            # Parallel vectors
            if abs(dot) > 0.95:
                fp = active_camera.GetFocalPoint()
                dist = active_camera.GetDistance()
                
                # Move camera to a perpendicular axis based on target UP
                if abs(up_vector[2]) > 0.9: 
                    active_camera.SetPosition(fp[0], fp[1] - dist, fp[2])
                elif abs(up_vector[1]) > 0.9:
                    active_camera.SetPosition(fp[0] - dist, fp[1], fp[2])
                else:
                    active_camera.SetPosition(fp[0], fp[1], fp[2] + dist)

                if has_system_actors:
                    renderer.ResetCamera(sys_bounds)
                else:
                    renderer.ResetCamera()

            active_camera.SetViewUp(*up_vector)
            active_camera.OrthogonalizeViewUp() 
            render_window.Render()

        def key_press_callback(caller, event):
            nonlocal desc_has_gpu_info
            nonlocal is_isolated

            interactor = caller
            key_sym = interactor.GetKeySym()
            
            if key_sym is None:
                return
            
            # Reset view ('r')
            # Override deafult action to not include rays
            if key_sym.lower() == 'r':
                if has_system_actors:
                    renderer.ResetCamera(sys_bounds)
                else:
                    renderer.ResetCamera()
                render_window.Render()
                interactor.SetKeySym("") 
                interactor.SetKeyCode("\0")
            
            # Instructions ('?')
            elif key_sym == 'question':
                if not desc_has_gpu_info:
                    # Fetch GPU Info
                    info = render_window.ReportCapabilities()
                    gpu_lines = []
                    for line in info.splitlines():
                        if "OpenGL vendor" in line or "OpenGL renderer" in line:
                            gpu_lines.append(line)
                    # Update the TextActor
                    full_text = desc + gpu_lines
                    textActor.SetInput('\n'.join(full_text))
                desc_has_gpu_info = True

                current_vis = textActor.GetVisibility()
                # If currently visible, make invisible.
                textActor.SetVisibility(not current_vis)
                # Hint is always the opposite of Instructions
                hintActor.SetVisibility(current_vis)
                render_window.Render()

            # Orthographic/perspective ('o')
            elif key_sym.lower() == 'o':
                cam = renderer.GetActiveCamera()
                if cam.GetParallelProjection():
                    # Switching from parallel to perspective
                    scale = cam.GetParallelScale()
                    fov = cam.GetViewAngle()
                    if fov > 0:
                        target_dist = scale / np.tan(np.deg2rad(fov) / 2.0)
                        fp = np.array(cam.GetFocalPoint())
                        pos = np.array(cam.GetPosition())
                        direction = fp - pos
                        dist_mag = np.linalg.norm(direction)
                        if dist_mag > 0:
                            direction_norm = direction / dist_mag
                            cam.SetPosition(fp - direction_norm * target_dist)
                    cam.SetParallelProjection(False)
                else:
                    # Switching from perspective to Parallel
                    dist = cam.GetDistance()
                    fov = cam.GetViewAngle()
                    new_scale = dist * np.tan(np.deg2rad(fov) / 2.0)
                    cam.SetParallelScale(new_scale)
                    cam.SetParallelProjection(True)
                
                renderer.ResetCameraClippingRange()
                render_window.Render()
            
            # Selection ('p')
            # Override default action to pick more than one actor 
            elif key_sym == 'p':
                click_pos = interactor.GetEventPosition()
                picker.Pick(click_pos[0], click_pos[1], 0, renderer)
                picked_actor = picker.GetActor()
                if picked_actor:
                    if picked_actor in selected_actors:
                        # Deselect
                        original_color = selected_actors.pop(picked_actor)
                        picked_actor.GetProperty().SetColor(*original_color)
                    else:
                        # Select
                        current_color = picked_actor.GetProperty().GetColor()
                        selected_actors[picked_actor] = current_color
                        picked_actor.GetProperty().SetColor(0.0, 1.0, 0.0) # Green
                render_window.Render()
                interactor.SetKeySym("") 
                interactor.SetKeyCode("\0")
            
            # Fly-to ('f')
            # Override default action to take into account more than one picked actor
            elif key_sym.lower() == 'f':
                if selected_actors:
                    # Calculate center of all selected actors
                    sel_bounds = [inf, -inf, inf, -inf, inf, -inf]
                    for actor in selected_actors:
                        b = actor.GetBounds()
                        sel_bounds[0] = min(sel_bounds[0], b[0])
                        sel_bounds[1] = max(sel_bounds[1], b[1])
                        sel_bounds[2] = min(sel_bounds[2], b[2])
                        sel_bounds[3] = max(sel_bounds[3], b[3])
                        sel_bounds[4] = min(sel_bounds[4], b[4])
                        sel_bounds[5] = max(sel_bounds[5], b[5])
                    center_x = 0.5 * (sel_bounds[0] + sel_bounds[1])
                    center_y = 0.5 * (sel_bounds[2] + sel_bounds[3])
                    center_z = 0.5 * (sel_bounds[4] + sel_bounds[5])
                    
                    interactor.FlyTo(
                        renderer,
                        center_x, center_y, center_z
                    )

                    render_window.Render()
                    interactor.SetKeySym("") 
                    interactor.SetKeyCode("\0")

            # Hide picked actors ('h')
            elif key_sym.lower() == 'h':
                # Create a reverse lookup to find surface names from actor objects
                actor_to_name = {v: k for k, v in self.actors.items()}

                for actor in list(selected_actors.keys()):
                    # Hide the surface (reset the original color before removing from picked list)
                    original_color = selected_actors.pop(actor)
                    actor.GetProperty().SetColor(*original_color)
                    actor.SetVisibility(False)
                    
                    # Find and hide associated hits
                    if actor in actor_to_name:
                        surface_name = actor_to_name[actor]
                        # Look for keys starting with "hits_" + surface_name
                        target_prefix = f"hits_{surface_name}"
                        for key, hit_actor in self.actors.items():
                            if key == target_prefix or key.startswith(target_prefix + "_"):
                                hit_actor.SetVisibility(False)

                render_window.Render()

            # Isolate selected ('i')
            elif key_sym.lower() == 'i':
                # Create a reverse lookup to find surface names from actor objects
                actor_to_name = {v: k for k, v in self.actors.items()}

                # If we have a selection, isolate it and then deselect
                if selected_actors:
                    is_isolated = True
                    # Hide everything not in selection
                    for actor_name, actor in self.actors.items():
                        # Always keep rays visible
                        if actor_name.startswith('rays'):
                            actor.SetVisibility(True)
                            continue

                        for sel_actor in selected_actors:
                            hit_prefix = f"hits_{actor_to_name[sel_actor]}"
                            # Keep the surface
                            if sel_actor == actor:
                                actor.SetVisibility(True)
                                # Restore color
                                orig_col = selected_actors[actor]
                                actor.GetProperty().SetColor(*orig_col)
                            # Keep surface hits
                            elif actor_name == hit_prefix or actor_name.startswith(hit_prefix+'_'):
                                actor.SetVisibility(True)
                            # Hide others
                            else:
                                actor.SetVisibility(False)
                    
                    # Clear selection since we have now no active targets
                    selected_actors.clear()
                    
                # If nothing selected, 'i' acts as "Show All" if currently isolated
                elif is_isolated:
                    is_isolated = False
                    for actor in self.actors.values():
                        actor.SetVisibility(True)
                
                render_window.Render()

                # Consume the key, otherwise the axes will disappear (IDKW)
                interactor.SetKeySym("") 
                interactor.SetKeyCode("\0")

            # Clear selections ('Escape')
            elif key_sym == 'Escape':
                is_isolated = False
                # Restore colors of selected
                for actor, color in selected_actors.items():
                    actor.GetProperty().SetColor(*color)
                selected_actors.clear()
                # Ensure everything is visible
                for actor in self.actors.values():
                    actor.SetVisibility(True)
                render_window.Render()

            # Axes and modes
            elif key_sym.lower() == 'y':
                perform_view_reset((0,1,0))
            elif key_sym.lower() == 'x':
                perform_view_reset((1,0,0))
            elif key_sym.lower() == 'z':
                perform_view_reset((0,0,1))
            
            elif key_sym == 'P':
                # Make invisible
                current_vis_text = textActor.GetVisibility()
                current_vis_hint = hintActor.GetVisibility()
                textActor.SetVisibility(False)
                hintActor.SetVisibility(False)

                w2if = vtk.vtkWindowToImageFilter()
                w2if.SetInput(render_window)
                w2if.SetInputBufferTypeToRGB()
                w2if.ReadFrontBufferOff()
                w2if.Update()

                now = datetime.datetime.now()
                timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

                writer = vtk.vtkPNGWriter()
                writer.SetFileName(f'vtk_{timestamp}.png')
                writer.SetInputConnection(w2if.GetOutputPort())
                writer.Write()
                interactor.SetKeySym("") 
                interactor.SetKeyCode("\0")

                # Restore visibility
                textActor.SetVisibility(current_vis_text)
                hintActor.SetVisibility(current_vis_hint)

        priority = 1.0
        render_window_interactor.AddObserver(vtk.vtkCommand.CharEvent, key_press_callback, priority)

        # Start
        render_window.Render()
        
        # Camera configuration
        cam = renderer.GetActiveCamera()
        
        # Apply initial projection type
        cam.SetParallelProjection(orthographic)

        # Set default camera position
        if has_system_actors:
            renderer.ResetCamera(sys_bounds)
        else:
            renderer.ResetCamera()

        # Set custom camera position
        if camera_position is not None:
            cam.SetPosition(*camera_position)
            cam.SetViewUp(*view_up)

        # Set custom focal point
        if focal_point is not None:
            if isinstance(focal_point, str):
                if focal_point in self.os:
                    fp = self.os[focal_point].position
                    if self._tel_to_local_rot is not None:
                        fp = self._tel_to_local_rot @ fp + self._translation_vector
                    cam.SetFocalPoint(*fp)
                else:
                    quit(render_window_interactor)
                    raise(RuntimeError(f'Surface {focal_point} not found in optical system.'))
            else:
                cam.SetFocalPoint(*focal_point)
            
            # Recalculate clipping to ensure the new view doesn't cut off objects
            renderer.ResetCameraClippingRange()
        
        # Increase far clip plane
        clip_rng = cam.GetClippingRange()
        cam.SetClippingRange(clip_rng[0], clip_rng[1] * 1000)

        render_window.Render()
        render_window_interactor.Initialize()
        render_window_interactor.Start()

        # Stop
        quit(render_window_interactor)

    def _create_wavelength_lut(self):
        """Creates a color transfer function for wavelength in the range 200nm - 1000nm."""
        ctf = vtk.vtkColorTransferFunction()
        ctf.SetColorSpaceToRGB()
        
        # Bright white/blue
        ctf.AddRGBPoint(200.0, 0.9, 0.9, 1.0) 
        # Electric purple
        ctf.AddRGBPoint(300.0, 0.7, 0.5, 1.0)   
        
        # Standard Rainbow, fully saturated
        ctf.AddRGBPoint(380.0, 0.5, 0.0, 1.0)   # Violet
        ctf.AddRGBPoint(440.0, 0.0, 0.2, 1.0)   # Blue
        ctf.AddRGBPoint(490.0, 0.0, 1.0, 1.0)   # Cyan
        ctf.AddRGBPoint(510.0, 0.2, 1.0, 0.2)   # Green
        ctf.AddRGBPoint(580.0, 1.0, 1.0, 0.0)   # Yellow
        ctf.AddRGBPoint(600.0, 1.0, 0.5, 0.0)   # Orange
        ctf.AddRGBPoint(700.0, 1.0, 0.0, 0.0)   # Red
        
        # Bright cherry red
        ctf.AddRGBPoint(850.0, 0.9, 0.2, 0.2)   
        # Pale pink
        ctf.AddRGBPoint(1000.0, 0.7, 0.5, 0.5)
        
        return ctf

    def add_rays(self, start, stop, surface_id=None, wavelengths=None, directions=None, length=None, point_size=1.0, show_rays=True, show_hits=True):
        """
        Draw rays from start to stop positions and highlight stop points.
        
        If a stop position is NaN (indicating a miss), the ray is skipped by default.
        If 'length' and 'directions' are provided, rays with NaN stops are drawn 
        starting from 'start' along 'direction' for 'length' units (without a hit dot).
        
        Parameters
        ----------
        start : ndarray
            (n, 3) array of starting coordinates (x, y, z).
        stop : ndarray
            (n, 3) array of stopping coordinates (x, y, z).
        surface_id: ndarray
            (n,) array of surface indices reached by each ray.
        directions : ndarray, optional
            (n, 3) array of direction vectors. Required if plotting NaN rays with fixed length.
        length : float, optional
            If provided, rays with NaN stop will be drawn with this length using the direction vector.
        opacity : float, optional
            Transparency of the rays from 0.0 (invisible) to 1.0 (opaque). Default is 0.5.
        point_size : float, optional
            Size of the hit points. Default is 1.0
        show_rays : bool, optional
            Whether to show rays or not. Default is True.
        show_hits : bool, optional
            Whether to show hits or not. Default is True.
        """

        if not show_hits and not show_rays:
            return

        has_directions = directions is not None

        has_wavelengths = wavelengths is not None

        if start.shape != stop.shape:
            raise ValueError("Start and stop points must have the same shape.")

        if has_directions and start.shape != directions.shape:
            raise ValueError("Start/stop poinnts and directions must have the same shape.")
        
        if has_wavelengths and start.shape[0] != wavelengths.shape[0]:
            print(start.shape[0], wavelengths.shape[0])
            raise ValueError("Start/stop points and wavelengths shape mismatch.")
        
        wavelength_scalars = vtk.vtkFloatArray()
        wavelength_scalars.SetName("Wavelengths")
        
        n_photons = start.shape[0]
        
        # Rays
        points_rays = vtk.vtkPoints()
        lines_rays = vtk.vtkCellArray()
        
        # Hits
        hits_collections = {}
        if surface_id is None:
            surface_id = np.zeros((n_photons,), dtype=np.int32)

        # Check which rays have intersected a surface
        valid_stops = ~np.any(np.isnan(stop), axis=1)
        
        for i in range(n_photons):
            current_start = start[i]
            current_stop = stop[i]
            label = self.os[surface_id[i]].name
            
            is_valid_stop = valid_stops[i]
            
            final_stop = None
            draw_hit = False
            if is_valid_stop:
                # Draw from start to stop and add a hit
                final_stop = current_stop
                draw_hit = True
            elif length is not None and has_directions:
                # Draw fixed length ray if directions are available
                final_stop = current_start + directions[i] * length
                draw_hit = False
            else:
                # Ignore not intersected ray
                continue
            
            if show_rays:
                ## Ray logic
                id_start = points_rays.InsertNextPoint(current_start)
                id_stop_line = points_rays.InsertNextPoint(final_stop)
                
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, id_start)
                line.GetPointIds().SetId(1, id_stop_line)
                lines_rays.InsertNextCell(line)

                # Store wavelength
                if has_wavelengths:
                    wavelength_scalars.InsertNextValue(wavelengths[i])
            
            ## Hit logic
            if draw_hit:
                if label not in hits_collections:
                    hits_collections[label] = {
                        'points': vtk.vtkPoints(),
                        'verts': vtk.vtkCellArray()
                    }
                # Add point to specific surface collection
                pt_id = hits_collections[label]['points'].InsertNextPoint(final_stop)
                hits_collections[label]['verts'].InsertNextCell(1)
                hits_collections[label]['verts'].InsertCellPoint(pt_id)
            
        ## Rays actor
        if show_rays:
            raysPolyData = vtk.vtkPolyData()
            raysPolyData.SetPoints(points_rays)
            raysPolyData.SetLines(lines_rays)
            
            mapper_rays = vtk.vtkPolyDataMapper()
            mapper_rays.SetInputData(raysPolyData)

            if has_wavelengths:
                raysPolyData.GetCellData().SetScalars(wavelength_scalars)                
                # Use the lookup table
                lut = self._create_wavelength_lut()
                mapper_rays.SetLookupTable(lut)
                mapper_rays.SetScalarRange(200, 1000) # nm
                mapper_rays.SetScalarModeToUseCellData()
            else:
                mapper_rays.ScalarVisibilityOff()
            
            actor_rays = vtk.vtkActor()
            actor_rays.SetMapper(mapper_rays)

            if not has_wavelengths:
                actor_rays.GetProperty().SetColor(0.0, 0.7, 1.0) # Electric blue
            
            actor_rays.GetProperty().SetLineWidth(1.0)
            if self._ray_opacity is not None:
                actor_rays.GetProperty().SetOpacity(float(self._ray_opacity))
            
            # Make rays unpickable
            actor_rays.PickableOff()

            base_key = 'rays'
            key = base_key
            count = 0
            while key in self.actors:
                key = f"{base_key}_{count}"
                count += 1
            
            self.actors[key] = actor_rays

        ## Hits actor
        if show_hits:
            for label, data in hits_collections.items():
                if data['points'].GetNumberOfPoints() == 0:
                    continue
            
                dotsPolyData = vtk.vtkPolyData()
                dotsPolyData.SetPoints(data['points'])
                dotsPolyData.SetVerts(data['verts'])
                
                mapper_dots = vtk.vtkPolyDataMapper()
                mapper_dots.SetInputData(dotsPolyData)
                
                actor_dots = vtk.vtkActor()
                actor_dots.SetMapper(mapper_dots)
                actor_dots.GetProperty().SetColor(1.0, 1.0, 0.0)
                actor_dots.GetProperty().SetPointSize(point_size)
                actor_dots.GetProperty().SetOpacity(1.0)
                actor_dots.PickableOff()

                # Naming convention: hits_SurfaceID
                # If multiple batches are added, append an index
                base_key = f"hits_{label}"
                key = base_key
                count = 0
                while key in self.actors:
                    key = f"{base_key}_{count}"
                    count += 1
                
                self.actors[key] = actor_dots

    def _set_ray_opacity(self, value):
        """Set the opacity of rays.
        
        Parameters
        ----------
        value: float
            Ray opacity.
        
        """
        if value is None:
            return
        
        for actor_name in self.actors:
            if actor_name.startswith("rays"):
                self.actors[actor_name].GetProperty().SetOpacity(float(value))

    def set_ray_opacity(self, value):
        """Set the opacity of rays.
        
        Parameters
        ----------
        value: float
            Ray opacity.
        
        """
        self._ray_opacity = value
        self._set_ray_opacity(value)

    def _apply_global_transform(self):
        """
        Apply a global rotation and translation to all current actors.
        
        Parameters
        ----------
        R : ndarray
            (3, 3) Rotation matrix. 
        t : ndarray or list
            (3,) Translation vector (x, y, z).
        """
        # Convert numpy array to vtkMatrix4x4
        vtk_R = vtk.vtkMatrix4x4()
        for i in range(3):
            for j in range(3):
                vtk_R.SetElement(i, j, self._tel_to_local_rot[i, j])

        # Iterate over all actors
        for actor in self.actors.values():
            
            # Get the existing transform
            transform = actor.GetUserTransform()
            if transform is None:
                transform = vtk.vtkTransform()
                transform.SetMatrix(actor.GetMatrix())
                actor.SetUserTransform(transform)
            
            # Apply transformations
            # PostMultiply ensures we are applying this to the "Global" world coordinates
            transform.PostMultiply()
            
            # Apply rotation
            transform.Concatenate(vtk_R)
            
            # Apply translation
            transform.Translate(*self._translation_vector)

            transform.Update()

    def get_screenshot(self,
        camera_position,
        filename=None,
        focal_point=None,
        view_up=(0, 0, 1),
        size=None,
        image_scale=1,
        orthographic=False,
        representation='surface',
        hide_surfaces=None,
        zoom=1.0,
        show=False,
        position_reference='telescope',
        position_shift=(0,0,0)
    ) -> np.ndarray:
        """
        Render the scene off-screen and save it to a PNG file.

        Coordinates for camera position, focal point, and view up should be provided 
        in the telescope coordinate system. The method handles the transformation 
        to the local coordinate system automatically.

        Parameters
        ----------
        camera_position : sequence of float
            The (x, y, z) coordinates of the camera position. The reference frame can be specified with the position_reference parameter.
        filename : str, optional
            Path to save the resulting PNG file. If None, the screenshot is not saved.
        focal_point : str or sequence of float, optional
            The point the camera is looking at. 
            - If None (default): The camera looks at the center of the bounding box of all system actors.
            - If str: Looks for an optical surface with this name and targets its position.
            - If sequence: Uses the provided (x, y, z) coordinates (assumend to be local coordinates).
        view_up : sequence of float
            The vector defining the "up" direction for the camera, default=(0, 0, 1).
        size : tuple of int, optional
            The (width, height) of the rendered image in pixels. 
            If None, uses the current window size.
        image_scale : int
            Resolution multiplier (e.g., 2 doubles the pixel density), default=1.
        orthographic : bool
            If True, uses parallel projection.
            If False, uses standard perspective projection.
            By default False.
        representation : {'surface', 'wireframe', 'points'}
            The rendering style of the actors in the scene, default='surface'.
        hide_surfaces : list of str, optional
            A list of names of surfaces/actors to exclude from the render.
        zoom : float
            Zoom factor applied when ``orthographic`` is True.
            - 1.0: Fits the object diagonal to the screen height.
            - > 1.0: Zooms in.
            - < 1.0: Zooms out.
            By default 1.0.
            Note: This parameter currently implies no effect if orthographic is False.
        show : bool
            If True, displays the image using Matplotlib. Default is False.
        position_reference:
            Reference system of the specified camera position, by default 'telescope'.
            If does not starts with 't', the camera position is assumed to be relative to the local reference system.
        
        Returns
        -------
        numpy.ndarray
            RGB image array with shape (height, width, 3).
        """
        # Setup Renderer
        renderer = vtk.vtkRenderer()
        renderer.SetBackground(0.1, 0.15, 0.25)
        render_window = vtk.vtkRenderWindow()
        render_window.SetOffScreenRendering(1)
        render_window.AddRenderer(renderer)
        
        if size: render_window.SetSize(*size)
        else: render_window.SetSize(*self.window_size)

        # Ray Opacity
        if self._ray_opacity is None:
            n_rays = 0
            for actor_name, actor in self.actors.items():
                if actor_name.startswith('rays'):
                    n_rays += actor.GetMapper().GetDataSetInput().GetLines().GetNumberOfCells()
            self._set_ray_opacity(self._get_sigmoid_opacity(n_rays))

        # Add actors and calculate bounds
        inf = float('inf')
        sys_bounds = [inf, -inf, inf, -inf, inf, -inf]
        has_system_actors = False
        hidden_set = set(hide_surfaces) if hide_surfaces else set()

        for name, actor in self.actors.items():
            # Check if the surface must be hidden
            should_skip = name in hidden_set
            if not should_skip and name.startswith("hits_"):
                for hidden_name in hidden_set:
                    if name.startswith(f"hits_{hidden_name}"):
                        should_skip = True
                        break
            if should_skip:
                continue

            # Set representation
            prop = actor.GetProperty()
            if representation == 'wireframe':
                prop.SetRepresentationToWireframe()
            elif representation == 'points':
                prop.SetRepresentationToPoints()
            else: prop.SetRepresentationToSurface()

            renderer.AddActor(actor)
            
            # Update bounds (using world coordinates of the actor)
            if not name.startswith("rays"):
                has_system_actors = True
                b = actor.GetBounds()
                sys_bounds[0] = min(sys_bounds[0], b[0])
                sys_bounds[1] = max(sys_bounds[1], b[1])
                sys_bounds[2] = min(sys_bounds[2], b[2])
                sys_bounds[3] = max(sys_bounds[3], b[3])
                sys_bounds[4] = min(sys_bounds[4], b[4])
                sys_bounds[5] = max(sys_bounds[5], b[5])

        # Configure camera coordinates
        cam = renderer.GetActiveCamera()
        cam.SetParallelProjection(orthographic)

        # Handle focal point
        final_fp = np.zeros(3)
        if focal_point is not None:
            if isinstance(focal_point, str):
                # Look for surface by name
                if focal_point not in self.os:
                    raise(RuntimeError(f"Surface {focal_point} not found."))
                s = self.os[focal_point]
                fp_local = np.array(s.position, dtype=float)
                if self._tel_to_local_rot is not None:
                    final_fp = self._tel_to_local_rot @ fp_local + self._translation_vector
                else:
                    final_fp = fp_local
            else:
                fp_input = np.array(focal_point, dtype=float)
                final_fp = fp_input
        elif has_system_actors:
            # Center of bounding box
            final_fp[0] = (sys_bounds[0] + sys_bounds[1]) / 2.0
            final_fp[1] = (sys_bounds[2] + sys_bounds[3]) / 2.0
            final_fp[2] = (sys_bounds[4] + sys_bounds[5]) / 2.0

        # Camera position
        final_pos = np.array(camera_position, dtype=float)
        if self._tel_to_local_rot is not None and position_reference.startswith('t'):
            final_pos = self._tel_to_local_rot @ final_pos + self._translation_vector

        # Camera shift
        view_vec = final_fp - final_pos
        shift_vec = np.array(position_shift, dtype=float)
        if self._tel_to_local_rot is not None and position_reference.startswith('t'):
            shift_vec = self._tel_to_local_rot @ shift_vec
        final_pos += shift_vec
        final_fp = final_pos + view_vec

        # Set camera parameters
        cam.SetPosition(*final_pos)
        cam.SetViewUp(*view_up)
        cam.SetFocalPoint(*final_fp)

        # Handle orthographic scaling
        if orthographic and has_system_actors:
            # Calculate diagonal length of the bounding box
            dx = sys_bounds[1] - sys_bounds[0]
            dy = sys_bounds[3] - sys_bounds[2]
            dz = sys_bounds[5] - sys_bounds[4]
            diagonal = np.sqrt(dx*dx + dy*dy + dz*dz)
            
            # Set scale so the whole object fits, adjusted by zoom
            # ParallelScale is half the height of the viewport
            if zoom == 0:
                zoom = 1.0
            cam.SetParallelScale((diagonal / 2.0) / zoom)

        renderer.ResetCameraClippingRange()
        render_window.Render()

        # Capture
        w2if = vtk.vtkWindowToImageFilter()
        w2if.SetInput(render_window)
        w2if.SetScale(image_scale)
        w2if.SetInputBufferTypeToRGB()
        w2if.ReadFrontBufferOff()
        w2if.Update()
        
        # Save
        if filename:
            writer = vtk.vtkPNGWriter()
            writer.SetFileName(filename)
            writer.SetInputConnection(w2if.GetOutputPort())
            writer.Write()

        from vtkmodules.util.numpy_support import vtk_to_numpy
        img_data = w2if.GetOutput()
        width, height, _ = img_data.GetDimensions()
        sc = img_data.GetPointData().GetScalars()
        arr = vtk_to_numpy(sc)
        arr = arr.reshape(height, width, -1)
        arr = np.flipud(arr)
        
        # Show
        if show:
            import matplotlib.pyplot as plt
            plt.imshow(arr)
            plt.axis('off')
            plt.show()

        return arr