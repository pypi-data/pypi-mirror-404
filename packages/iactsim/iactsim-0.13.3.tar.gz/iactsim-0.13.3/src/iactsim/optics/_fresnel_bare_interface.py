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

import numpy as np

from ._surface import SurfaceShape
from ._surface_misc import SurfaceProperties

from ..visualization._iactsim_style import iactsim_style

class FresnelSurfacePropertiesGenerator:
    """
    Handles the calculation and population of SurfaceProperties objects 
    based on Fresnel equations for a given Surface instance.
    """

    @staticmethod
    def _calculate_fresnel(n1, n2, theta_deg, polarization='unpolarized'):
        """
        Perform a vectorized Fresnel calculation for a specific polarization.

        Parameters
        ----------
        n1 : np.ndarray
            Refractive index of the incident medium. Shape must be broadcastable 
            to (N_angles, N_wl).
        n2 : np.ndarray
            Refractive index of the transmission medium. Shape must be broadcastable 
            to (N_angles, N_wl).
        theta_deg : np.ndarray
            Incident angles in degrees. Shape must be broadcastable 
            to (N_angles, N_wl).
        polarization : str, optional
            The polarization mode to compute. Options are:
            - 'unpolarized': Average of s- and p-polarization.
            - 's', 'rs': s-polarization only.
            - 'p', 'rp': p-polarization only.
            Default is 'unpolarized'.

        Returns
        -------
        np.ndarray
            Reflectance matrix R with shape (N_angles, N_wl).

        Raises
        ------
        ValueError
            If an invalid polarization string is provided.
        """
        theta_i = np.radians(theta_deg)
        
        # Snell's law
        sin_theta_t = (n1 / n2) * np.sin(theta_i)

        # Total internal reflection
        tir_mask = np.abs(sin_theta_t) > 1.0

        sin_theta_t_safe = np.where(tir_mask, 0.0, sin_theta_t)
        theta_t = np.arcsin(sin_theta_t_safe)

        # Amplitude coefficients
        cos_theta_i = np.cos(theta_i)
        cos_theta_t = np.cos(theta_t)

        # Initialize result
        R_out = None

        # Calculate s-pol if needed
        if polarization in ['s', 'rs', 'unpolarized']:
            rs_num = n1 * cos_theta_i - n2 * cos_theta_t
            rs_den = n1 * cos_theta_i + n2 * cos_theta_t
            rs = np.divide(rs_num, rs_den, out=np.zeros_like(rs_num), where=rs_den!=0)
            Rs = np.abs(rs)**2
            Rs = np.where(tir_mask, 1.0, Rs)
            
            if polarization in ['s', 'rs']:
                R_out = Rs

        # Calculate p-pol if needed
        if polarization in ['p', 'rp', 'unpolarized']:
            rp_num = n2 * cos_theta_i - n1 * cos_theta_t
            rp_den = n2 * cos_theta_i + n1 * cos_theta_t
            rp = np.divide(rp_num, rp_den, out=np.zeros_like(rp_num), where=rp_den!=0)
            Rp = np.abs(rp)**2
            Rp = np.where(tir_mask, 1.0, Rp)

            if polarization in ['p', 'rp']:
                R_out = Rp

        # Unpolarized
        if polarization == 'unpolarized':
            R_out = 0.5 * (Rs + Rp)

        if R_out is None:
            raise ValueError(f"Invalid polarization mode: '{polarization}'. "
                             "Use 's', 'p', or 'unpolarized'.")

        return R_out

    def generate(self, surface, wavelengths=None, angles=None, polarization='unpolarized', inplace=False):
        """
        Generate a populated SurfaceProperties object.

        Parameters
        ----------
        surface : iactsim.optics.Surface
            The surface object containing `material_in` and `material_out` attributes,
            which must have `get_refractive_index(wavelengths)` methods.
        wavelengths : np.ndarray, optional
            1D array of wavelengths in nm. If None, defaults to `np.arange(200, 901, 1)`.
        angles : np.ndarray, optional
            1D array of incidence angles in degrees. If None, defaults to `np.arange(0, 91, 1)`.
        polarization : {'unpolarized', 's', 'p', 'rs', 'rp'}, optional
            The specific polarization to compute for reflectance and transmittance.
            Default is 'unpolarized'.
        inplace : bool, optional
            If True, modifies the provided surface properties in place.
            Default is False.

        Returns
        -------
        iactsim.optics.SurfaceProperties
            If `inplace` is False, a populated properties object containing the calculated matrices:
            - `reflectance`, `transmittance` (Front interface)
            - `reflectance_back`, `transmittance_back` (Back interface)
            - `wavelength`, `incidence_angle` vectors.
        """
        pol_clean = polarization.lower().strip()

        # Apply defaults
        if wavelengths is None:
            wavelengths = np.arange(200, 901, 1)
        
        if angles is None:
            angles = np.arange(0, 91, 1)

        # Ensure inputs are numpy arrays
        wl = np.asarray(wavelengths)
        ang = np.asarray(angles)

        # Retrieve materials and reshape for broadcasting
        # n: (1, N_wl) | ang: (N_ang, 1)
        n_in = surface.material_in.get_refractive_index(wl).reshape(1, -1)
        n_out = surface.material_out.get_refractive_index(wl).reshape(1, -1)
        ang_reshaped = ang.reshape(-1, 1)

        # For a cylindrical solid: n_in is the material inside; n_out is the material outside.
        if surface._shape == SurfaceShape.CYLINDRICAL:
            n_in, n_out = n_out, n_in

        # Front interface (n_in -> n_out)
        R_front = self._calculate_fresnel(n_in, n_out, ang_reshaped, pol_clean)
        
        # Cleanup
        nan_mask_f = np.isnan(R_front)
        T_front = 1.0 - R_front

        # NaNs will be treated as absorption
        R_front[nan_mask_f] = 0.0
        T_front[nan_mask_f] = 0.0

        # Back interface (n_out -> n_in)
        R_back = self._calculate_fresnel(n_out, n_in, ang_reshaped, pol_clean)
        
        # Cleanup
        nan_mask_b = np.isnan(R_back)
        T_back = 1.0 - R_back

        # NaNs will be treated as absorption
        R_back[nan_mask_b] = 0.0
        T_back[nan_mask_b] = 0.0

        # Populate Object
        surface_prop = SurfaceProperties()
        surface_prop.wavelength = wl
        surface_prop.incidence_angle = ang
        
        surface_prop.reflectance = R_front
        surface_prop.transmittance = T_front
        surface_prop.reflectance_back = R_back
        surface_prop.transmittance_back = T_back

        if inplace:
            surface.properties = surface_prop
        else:
            return surface_prop