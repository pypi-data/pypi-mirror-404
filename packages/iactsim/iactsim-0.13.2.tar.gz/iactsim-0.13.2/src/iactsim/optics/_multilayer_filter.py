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
from typing import List, Dict, Tuple, Optional, Callable, Union

from tqdm.auto import tqdm

try:
    import tmm_fast
    _HAS_TMM_FAST = True
except ImportError:
    _HAS_TMM_FAST = False

try:
    import tmm
    _HAS_TMM = True
except ImportError:
    _HAS_TMM = False

from ._air_refractive_index import calculate_ciddor_rindex
from ._surface_misc import SurfaceProperties
from ..visualization._iactsim_style import iactsim_style

class OpticalStackSimulator:
    """
    A class to handle dispersive Transfer Matrix Method (TMM) simulations 
    using the tmm_fast backend, with a dynamic material database.

    Parameters
    ----------
    core_materials : List[str]
        List of material names for the core layers (from top to bottom).
    core_thicknesses : List[float]
        List of thicknesses for the core layers in nanometers.
    ambient : str, optional
        Name of the ambient medium (default is "Air").
    substrate : str, optional
        Name of the substrate material (default is "SiO2").
    coh_mask : list, optional
        List of coherence tags ('c' for coherent, 'i' for incoherent) for each layer 
        (including ambient and substrate). If empty, coherent simulation is assumed.

    Raises
    ------
    ImportError
        If neither 'tmm_fast' nor 'tmm' package is installed.
    
    """

    def __init__(
        self, 
        core_materials: List[str], 
        core_thicknesses: List[float],
        ambient: str = "Air", 
        substrate: str = "SiO2",
        coh_list: list = []
    ):
        if not _HAS_TMM_FAST and not _HAS_TMM:
            raise ImportError(
                "Neither 'tmm_fast' nor 'tmm' package are installed.\n"
            )

        # Internal database: Maps name -> callable function(wavelength)
        self._material_db: Dict[str, Callable[[np.ndarray], np.ndarray]] = {}
        self._load_default_materials()

        # Set up stack materials thicknesses
        core_materials = list(core_materials)
        self.materials = [ambient] + core_materials + [substrate]

        # Validate materials
        self._validate_materials(self.materials)

        # Set up thicknesses (in meters)
        core_thicknesses_list = list(core_thicknesses)
        core_thicknesses_list = [float(d)*1e-9 for d in core_thicknesses_list]
        self.thicknesses = np.array([0.0] + core_thicknesses_list + [0.0])

        self._wavelengths: Optional[np.ndarray] = None
        self._angles_rad: Optional[np.ndarray] = None

        if len(coh_list) and not _HAS_TMM:
            raise(RuntimeError('tmm package is needed for incoherent simulation.'))
        
        self._coh_list = coh_list

        self.show_progress = True
    
    @property
    def wavelengths(self):
        return self._wavelengths*1e9  # Convert to nm
    
    @property
    def incidence_angles(self):
        return self._angles_rad*180/np.pi  # Convert to degrees

    def get_available_materials(self) -> List[str]:
        """Returns a sorted list of all currently registered material names."""
        return sorted(list(self._material_db.keys()))

    def register_material(self, name: str, n_func: Callable[[np.ndarray], np.ndarray]) -> None:
        """
        Register a custom material using a refractive index function.

        Parameters
        ----------
        name : str
            The name to refer to the material.
        n_func : Callable
            Function accepting 1D wavelengths (m) and returning 1D complex indices.
        """
        self._material_db[name] = n_func

    def register_sellmeier_material(self, name: str, B_coeffs: List[float], C_coeffs: List[float]) -> None:
        """Register a material defined by the Sellmeier equation."""
        def sellmeier_wrapper(lam_meters):
            return self._sellmeier_n(lam_meters, B_coeffs, C_coeffs)
        self.register_material(name, sellmeier_wrapper)

    def register_ciddor_air(
        self, 
        name: str = "Air", 
        p: float = 101325.0, 
        t: float = 288.15, 
        xCO2: float = 450.0, 
        rh: Optional[float] = 0.0
    ) -> None:
        """
        Register the air refractive index using the Ciddor equation.

        Parameters
        ----------
        name : str
            The material name to register (defaults to "Air", overwriting the default vacuum).
        p : float
            Pressure in Pascals (default 101325 Pa).
        t : float
            Temperature in Kelvin (default 288.15 K).
        xCO2 : float
            CO2 concentration in ppm (default 450 ppm).
        rh : float, optional
            Relative humidity (0.0 to 1.0).
        """
        def ciddor_wrapper(lam_meters: np.ndarray) -> np.ndarray:
            # Calculate real index (returns float64)
            n_real = calculate_ciddor_rindex(lam_meters*1e9, p, t, xCO2, rh)
            # Convert to complex128 for TMM compatibility
            return n_real.astype(np.complex128)
        
        self.register_material(name, ciddor_wrapper)

    def set_simulation_params(
        self, 
        wl_range: Union[Tuple[float, float, int], np.ndarray, List[float]] = (200, 1000, 801),
        angle_range: Union[Tuple[float, float, int], np.ndarray, List[float]] = (0, 90, 91)
    ) -> None:
        """
        Set the wavelength (in nanometers) and angle ranges (in degrees).

        Parameters
        ----------
        wl_range : Tuple, List, or np.ndarray
            If tuple: (start_nm, stop_nm, points).
            If array/list: exact wavelengths in Nanometers.
            Default is (200, 1000, 801).
        angle_range : Tuple, List, or np.ndarray
            If tuple: (start_deg, stop_deg, points).
            If array/list: exact angles in Degrees.
            Default is (0, 90, 91).
        """
        if isinstance(wl_range, (list, np.ndarray)):
            wl_nm = np.array(wl_range, dtype=np.float64)
        elif isinstance(wl_range, tuple):
             wl_nm = np.linspace(*wl_range)
        else:
            raise TypeError("wl_range must be a tuple, list, or numpy array.")
        
        # Store internally as meters
        self._wavelengths = wl_nm * 1e-9

        if isinstance(angle_range, (list, np.ndarray)):
            ang_deg = np.array(angle_range, dtype=np.float64)
        elif isinstance(angle_range, tuple):
            ang_deg = np.linspace(*angle_range)
        else:
            raise TypeError("angle_range must be a tuple, list, or numpy array.")

        # Store internally as radians
        self._angles_rad = np.deg2rad(ang_deg)

    def _run(self, polarization: str = 's') -> np.ndarray:
        if self._wavelengths is None or self._angles_rad is None:
            raise ValueError("Simulation parameters not set. Call set_simulation_params() first.")

        # Matrix of refractive indices for all materials and wavelengths
        n_matrix = np.zeros((len(self._wavelengths), len(self.materials)), dtype=np.complex128)
        for i, name in enumerate(self.materials):
            if name not in self._material_db:
                 raise ValueError(f"Material '{name}' not found. Available: {self.get_available_materials()}")
            n_matrix[:, i] = self._material_db[name](self._wavelengths)
        
        # Reshape for tmm_fast broadcasting
        T = self.thicknesses[np.newaxis, :]
        N = n_matrix.T[np.newaxis, :, :]

        if _HAS_TMM_FAST:
            from tmm_fast import coh_tmm
            args = {
                'pol': polarization, 
                'N': N, 
                'T': T,
                'Theta': self._angles_rad,
                'lambda_vacuum': self._wavelengths,
                'device': 'cpu'
            }
        else:
            from tmm import coh_tmm
            args = {
                'pol': polarization, 
                'n_list': N, 
                'd_list': T,
                'th_0': self._angles_rad,
                'lam_vac': self._wavelengths,
            }    
        
        if len(self._coh_list) > 0:
            if not _HAS_TMM:
                raise ImportError("For transfer-matrix-method calculation in the incoherent case tmm package is needed.")
            else:
                from tmm import inc_tmm
                args = {
                    'pol': polarization, 
                    'n_list': N, 
                    'd_list': T,
                    'c_list': self._coh_list,
                    'th_0': self._angles_rad,
                    'lam_vac': self._wavelengths,
                }   
            tmm_func = inc_tmm
        else:
            tmm_func = coh_tmm

        # Run Simulation
        if _HAS_TMM_FAST and len(self._coh_list) == 0:
            if polarization not in ['s', 'p']:
                args['pol'] = 's'
                res_s = tmm_func(**args)
                args['pol'] = 'p'
                res_p = tmm_func(**args)
                # Average results for unpolarized light
                results = {}
                for key in res_s:
                    results[key] = 0.5*(res_s[key] + res_p[key])
            else:
                results = tmm_func(**args)

            # Squeeze results to remove singleton dimensions
            for key in results:
                results[key] = np.squeeze(results[key])
            
            for key in ['R', 'T']:
                results[key] = np.clip(results[key], 0.0, 1.0)
            
            for i,ang in enumerate(self._angles_rad):
                if abs(ang-np.pi/2) < 1e-6:
                    results['R'][i,:] = 1.0
                    results['T'][i,:] = 0.
            
        else:
            d_list = T[0]
            d_list[0] = np.inf
            d_list[-1] = np.inf
            from tmm import inc_tmm

            args = {
                'pol': polarization, 
                'n_list': None, 
                'd_list': T[0],
                'th_0': None,
                'lam_vac': None,
            }
            if len(self._coh_list) > 0:
                args['c_list'] = ['i'] + self._coh_list + ['i']
            
            results = {
                'R': np.empty((len(self._angles_rad), len(self._wavelengths))),
                'T': np.empty((len(self._angles_rad), len(self._wavelengths)))
            }

            with tqdm(total=results['T'].size, disable=not self.show_progress) as pbar:
                for i,ang in enumerate(self._angles_rad):
                    for j,lam in enumerate(self._wavelengths):
                        args['n_list'] = N[0,:,j]
                        args['th_0'] = ang
                        args['lam_vac'] = lam
                        if abs(ang-np.pi/2) < 1e-6:
                            res = {'R':1.0, 'T':0.}
                        else:
                            res = inc_tmm(**args)
                        results['R'][i,j] = res['R']
                        results['T'][i,j] = res['T']
                        pbar.update()
        
        return results
    
    def get_refractive_index(self, material: str, wavelengths_nm: Union[np.ndarray, List[float], float]) -> np.ndarray:
        """
        Get the refractive index of a registered material at specified wavelengths.

        Parameters
        ----------
        material : str
            The name of the material.
        wavelengths_nm : np.ndarray or List[float] or float
            Wavelengths in nanometers.

        Returns
        -------
        np.ndarray
            Complex refractive indices at the specified wavelengths.
        """
        if material not in self._material_db:
            raise ValueError(f"Material '{material}' not found. Available: {self.get_available_materials()}")
        
        wavelengths_m = np.asarray(wavelengths_nm, dtype=np.float64) * 1e-9
        ri = self._material_db[material](wavelengths_m)

        if isinstance(wavelengths_nm, float):
            return ri[0]
        else:
            return ri
    
    def run(self, polarization: str = 's') -> np.ndarray:
        """Run the TMM simulation for a specific polarization."""
        if polarization in ['s', 'p']:
            results = self._run(polarization)
            if polarization == 'p':
                self._tran_p = results['T']
                self._refl_p = results['R']
                self._tran_s = None
                self._refl_s = None
            else:
                self._tran_s = results['T']
                self._refl_s = results['R']
                self._tran_p = None
                self._refl_p = None
        else:
            self._results_s = self._run('s')
            self._results_p = self._run('p')
            results = {}
            results['T'] = 0.5*(self._results_s['T'] + self._results_p['T'])
            results['R'] = 0.5*(self._results_s['R'] + self._results_p['R'])

            self._tran_s = self._results_s['T']
            self._refl_s = self._results_s['R']
            self._tran_p = self._results_p['T']
            self._refl_p = self._results_p['R']
        
        self.transmittance = results['T']
        self.reflectance = results['R']

        return results


    def _validate_materials(self, materials_list: List[str]) -> None:
        """Check if requested materials exist in the DB."""
        missing = [m for m in materials_list if m not in self._material_db]
        if missing:
            print(f"Warning: Materials {set(missing)} are not yet registered. Please register them.")

    def _load_default_materials(self) -> None:
        """Populates the database with the standard set of materials."""
        defaults = {
            "SiO2":  ([0.6961663, 0.4079426, 0.8974794], [0.0684043**2, 0.1162414**2, 9.896161**2]),
            "MgF2":  ([0.48755108, 0.39875031, 2.3120353], [0.04338408**2, 0.09461442**2, 23.793604**2]),
            "ZrO2":  ([1.347091, 2.117788, 9.452943], [0.062543**2, 0.166739**2, 24.320570**2]),
            "Al2O3": ([1.4313493, 0.65054713, 5.3414021], [0.0726631**2, 0.1193242**2, 18.028251**2]),
            "TiO2":  ([5.913, 0.2441], [0.187**2, 10.0**2]),
            "Y2O3":  ([1.32854, 1.20309, 0.31251], [0.05320**2, 0.11653**2, 12.2425**2]),
            "Si3N4":  ([2.8939], [0.13967**2]), # Philipp 1973
        }
        for name, (B, C) in defaults.items():
            self.register_sellmeier_material(name, B, C)

        self.register_ciddor_air("Air")
        self.register_material("Al", self._get_al_n_interp)
        self.register_material("Si", self._get_silicon_n_interp)
        self.register_material("TiO2", self._get_titanium_dioxide_n_interp)
        self.register_material("Ta2O5", self._get_tantalum_pentoxide_n_interp) # Cheikh et al. 2025
        self.register_material("HfO2", lambda lam: 1.875 + 6.28e-3 * (lam*1e6)**(-2) + 5.80e-4 * (lam*1e6)**(-4)+0.j) # Al-Kuhaili 2004

    @staticmethod
    def _sellmeier_n(lam_meters: np.ndarray, B_coeffs: List[float], C_coeffs: List[float]) -> np.ndarray:
        """Static helper for Sellmeier equation."""
        lam_um = lam_meters * 1e6
        lam_sq = lam_um ** 2
        n_sq = 1.0
        for B, C in zip(B_coeffs, C_coeffs):
            n_sq += (B * lam_sq) / (lam_sq - C)
        return np.sqrt(n_sq + 0j)

    @iactsim_style
    def plot_simulation_results(
        self,
        mode: str = 'R',
        cmap: str = "Spectral",
        show_all_pol: bool = True,
    ) -> None:
        """
        Plots simulation results for s-polarization, p-polarization, and unpolarized light.
        Automatically calculates axis extent from the stored simulation parameters.
    
        Parameters
        ----------
        mode : str
            'R' for Reflectance or 'T' for Transmittance. Determines which data key to use.
        cmap : str, optional
            The colormap to use for the plots.
        """
        if self._wavelengths is None or self._angles_rad is None:
            raise ValueError("Simulation parameters are missing. Cannot calculate plot extent.")

        from mpl_toolkits.axes_grid1 import ImageGrid
        import matplotlib.pyplot as plt

        has_p = False
        has_s = False
        if self._tran_p is not None:
            has_p = True
        if self._tran_s is not None:
            has_s = True
        
        if not has_s and not has_p:
            return
        
        data_s = None
        data_p = None
        data = None
        
        if not any([mode.lower().startswith(key) for key in ['t', 'r']]):
            raise ValueError("Invalid mode. Must be 'R' or 'T'.")
        
        if has_s:
            if mode.lower().startswith('t'):
                data_s = self._tran_s
            else:
                data_s = self._refl_s
        
        if has_p:
            if mode.lower().startswith('t'):
                data_p = self._tran_p
            else:
                data_p = self._refl_p
        
        if has_s and has_p:
            data = 0.5 * (data_s + data_p)
        elif has_s:
            data = data_s
        elif has_p:
            data = data_p
        
        if data is None:
            return
        
        if has_p and has_s and show_all_pol:
            plot_data = [
                ("S-polarization", data_s),
                ("P-polarization", data_p),
                ("Unpolarized", data)
            ]
        else:
            title = "S-polarization" if has_s else "P-polarization"
            plot_data = [(title, data)]
        
        xlabel = "Wavelength (nm)"
        ylabel = "Incident angle (°)"
        cbar_label = "Reflectance (%)" if mode.lower().startswith('r') else "Transmittance (%)"

        # Calculate extent
        wl_min_nm = self._wavelengths[0] * 1e9
        wl_max_nm = self._wavelengths[-1] * 1e9
        ang_min_deg = np.rad2deg(self._angles_rad[0])
        ang_max_deg = np.rad2deg(self._angles_rad[-1])
        extent = [wl_min_nm, wl_max_nm, ang_min_deg, ang_max_deg]
        
        # Calculate aspect ratio for figure sizing
        aspect_ratio = (wl_max_nm - wl_min_nm) / (ang_max_deg - ang_min_deg) / 3

        fig = plt.figure(figsize=(len(plot_data)*4*aspect_ratio, 4))  
        
        grid = ImageGrid(
            fig, 111,
            nrows_ncols=(1, len(plot_data)),
            axes_pad=0.5,
            share_all=True,
            cbar_location="right",
            cbar_mode="single",
            cbar_size="5%",
            cbar_pad=0.15,
        )
        
        for ax, (title, data) in zip(grid, plot_data):
            im = ax.imshow(
                data * 100,
                cmap=cmap, 
                aspect=aspect_ratio,
                extent=extent,
                origin='lower',
                vmin=0, vmax=100 
            )
            ax.set_title(title)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
        
        # Add colorbar
        grid.cbar_axes[0].colorbar(im, label=cbar_label)
        plt.show()

    @staticmethod
    def _get_al_n_interp(lam_array: np.ndarray) -> np.ndarray:
        """Static helper for Aluminum interpolation."""
        # Wavelengths in um
        wl = np.array([
            0.15, 0.155, 0.16, 0.165, 0.17, 0.175, 0.18, 0.185, 0.19, 0.195, 0.2, 0.205, 0.21, 0.215, 0.22, 0.225, 0.23, 0.235, 0.24, 0.245, 
            0.25, 0.255, 0.26, 0.265, 0.27, 0.275, 0.28, 0.285, 0.29, 0.295, 0.3, 0.305, 0.31, 0.315, 0.32, 0.325, 0.33, 0.335, 0.34, 0.345, 
            0.35, 0.355, 0.36, 0.365, 0.37, 0.375, 0.38, 0.385, 0.39, 0.395, 0.4, 0.405, 0.41, 0.415, 0.42, 0.425, 0.43, 0.435, 0.44, 0.445, 
            0.45, 0.455, 0.46, 0.465, 0.47, 0.475, 0.48, 0.485, 0.49, 0.495, 0.5, 0.505, 0.51, 0.515, 0.52, 0.525, 0.53, 0.535, 0.54, 0.545, 
            0.55, 0.555, 0.56, 0.565, 0.57, 0.575, 0.58, 0.585, 0.59, 0.595, 0.6, 0.605, 0.61, 0.615, 0.62, 0.625, 0.63, 0.635, 0.64, 0.645, 
            0.65, 0.655, 0.66, 0.665, 0.67, 0.675, 0.68, 0.685, 0.69, 0.695, 0.7, 0.705, 0.71, 0.715, 0.72, 0.725, 0.73, 0.735, 0.74, 0.745, 
            0.75, 0.755, 0.76, 0.765, 0.77, 0.775, 0.78, 0.785, 0.79, 0.795, 0.8, 0.805, 0.81, 0.815, 0.82, 0.825, 0.83, 0.835, 0.84, 0.845, 
            0.85, 0.855, 0.86, 0.865, 0.87, 0.875, 0.88, 0.885, 0.89, 0.895, 0.9, 0.905, 0.91, 0.915, 0.92, 0.925, 0.93, 0.935, 0.94, 0.945, 
            0.95, 0.955, 0.96, 0.965, 0.97, 0.975, 0.98, 0.985, 0.99, 0.995, 1.0, 1.005, 1.01, 1.015, 1.02, 1.025, 1.03, 1.035, 1.04, 1.045, 
            1.05, 1.055, 1.06, 1.065, 1.07, 1.075, 1.08, 1.085, 1.09, 1.095, 1.1, 1.105, 1.11, 1.115, 1.12, 1.125, 1.13, 1.135, 1.14, 1.145, 
            1.15, 1.155, 1.16, 1.165, 1.17, 1.175, 1.18, 1.185, 1.19, 1.195, 1.2, 1.205, 1.21, 1.215, 1.22, 1.225, 1.23, 1.235, 1.24, 1.245, 
            1.25, 1.255, 1.26, 1.265, 1.27, 1.275, 1.28, 1.285, 1.29, 1.295, 1.3, 1.305, 1.31, 1.315, 1.32, 1.325, 1.33, 1.335, 1.34, 1.345, 
            1.35, 1.355, 1.43, 1.435, 1.44, 1.445, 1.45, 1.455, 1.46, 1.465, 1.47, 1.475, 1.48, 1.485, 1.49, 1.495, 1.5, 1.505, 1.51, 1.515, 
            1.52, 1.525, 1.53, 1.535, 1.54, 1.545, 1.55, 1.555, 1.56, 1.565, 1.57, 1.575, 1.58, 1.585, 1.59, 1.595, 1.6, 1.605, 1.61, 1.615, 
            1.62, 1.625, 1.63, 1.635, 1.64, 1.645, 1.65, 1.655, 1.66, 1.665, 1.67, 1.675, 1.68, 1.685, 1.69, 1.695, 1.7
        ])

        # Refractive index
        n = np.array([
            0.095390828, 0.095510386, 0.09903925, 0.098692838, 0.100850207, 0.1069563, 0.099715746, 0.108316112, 0.106567769, 0.111513266, 0.110803374, 0.111587326, 0.11365555, 0.115928445, 0.116173424, 0.119771906, 0.124315543, 0.129276519, 0.133002743, 0.139688588, 
            0.141162655, 0.148765766, 0.150722638, 0.161465056, 0.164610587, 0.172365826, 0.178635303, 0.18587018, 0.188953314, 0.197315218, 0.204991638, 0.210097266, 0.218816718, 0.224454799, 0.237666454, 0.24464928, 0.251892832, 0.259391824, 0.267481852, 0.275201252, 
            0.28349792, 0.291774119, 0.300125667, 0.308578012, 0.317597538, 0.32692637, 0.335956002, 0.345714203, 0.354901676, 0.364968364, 0.375150842, 0.385211589, 0.396086448, 0.40706511, 0.417647849, 0.429543735, 0.440996226, 0.452837879, 0.464232752, 0.477070026, 
            0.489220122, 0.501228231, 0.514817248, 0.528042125, 0.53987657, 0.554932886, 0.568005038, 0.582771419, 0.596705366, 0.610784373, 0.625686295, 0.640306464, 0.655709839, 0.672565753, 0.688336416, 0.704045108, 0.720793584, 0.737603948, 0.75446839, 0.772330366, 
            0.789405353, 0.808351698, 0.829205097, 0.848630853, 0.867376853, 0.887661988, 0.908569739, 0.928308533, 0.948955518, 0.9714896, 0.992465612, 1.016073317, 1.038145667, 1.062059906, 1.088160063, 1.112663572, 1.136328574, 1.165731637, 1.190265203, 1.218505245, 
            1.246364405, 1.275302761, 1.304382818, 1.333854457, 1.365410391, 1.395892303, 1.426024482, 1.457391234, 1.493230683, 1.5274935, 1.559751729, 1.596346402, 1.631621525, 1.669698976, 1.706780893, 1.745260386, 1.786398844, 1.827772224, 1.872189153, 1.916802427, 
            1.958355454, 2.005349601, 2.054224115, 2.09984451, 2.144528834, 2.189915668, 2.231500036, 2.275479945, 2.314643646, 2.350258044, 2.373653298, 2.399438967, 2.409296598, 2.414395973, 2.410049326, 2.399462094, 2.375277499, 2.342102357, 2.301774531, 2.257656113, 
            2.204898553, 2.148111401, 2.092718783, 2.03127715, 1.973568962, 1.915492386, 1.854996083, 1.802564727, 1.750120449, 1.694671727, 1.64715608, 1.602399525, 1.557188172, 1.516837858, 1.483545494, 1.447230511, 1.415213787, 1.385433286, 1.355589911, 1.325884954, 
            1.302164463, 1.280288795, 1.25976713, 1.23821822, 1.218188621, 1.201067407, 1.182294465, 1.167631515, 1.153696234, 1.140905235, 1.126639087, 1.114680776, 1.102964941, 1.09358083, 1.08727974, 1.081445553, 1.071397488, 1.061537336, 1.055494597, 1.051806876, 
            1.043454926, 1.036482441, 1.033133204, 1.02747793, 1.025591906, 1.024418445, 1.020244607, 1.015304156, 1.014378517, 1.011890304, 1.009905005, 1.008451539, 1.005344855, 1.00382405, 1.004294808, 1.003882164, 1.003972742, 1.00500573, 1.002828586, 1.003941179, 
            1.005317282, 1.003754384, 1.008818757, 1.007932489, 1.008357257, 1.012688334, 1.015213183, 1.014759181, 1.017683803, 1.01813905, 1.021736807, 1.022859293, 1.024257787, 1.026450838, 1.029738722, 1.035047848, 1.038667581, 1.039978895, 1.043389606, 1.046657092, 
            1.049913391, 1.051297547, 1.056495057, 1.057188404, 1.061492702, 1.066383574, 1.070500901, 1.073080696, 1.078091053, 1.081263285, 1.08667656, 1.090905752, 1.094227716, 1.097106966, 1.104427092, 1.108138114, 1.109282178, 1.112492808, 1.123987022, 1.129233973, 
            1.132981867, 1.135566133, 1.20897633, 1.215774284, 1.222359347, 1.225637477, 1.232348412, 1.235053048, 1.23989324, 1.245674136, 1.25590184, 1.252421713, 1.265153644, 1.264792932, 1.275023692, 1.277693673, 1.285699173, 1.290149697, 1.296809948, 1.304059962, 
            1.313924676, 1.31627889, 1.325289614, 1.332565366, 1.338103685, 1.342317392, 1.347399401, 1.354287918, 1.36162657, 1.367953829, 1.374881699, 1.374949427, 1.385662006, 1.390425967, 1.400170689, 1.39786136, 1.400984694, 1.402928097, 1.421414675, 1.424742484, 
            1.436002763, 1.439358574, 1.44609075, 1.447904247, 1.45643876, 1.458873135, 1.469917493, 1.478177828, 1.474977808, 1.477843053, 1.462292742, 1.425778483, 1.427335087, 1.454908413, 1.514176047, 1.555668449, 1.584018511
        ])

        # Extinction coefficient
        k = np.array([
            1.283666394, 1.337393822, 1.402928641, 1.46616516, 1.532569987, 1.596539899, 1.657661977, 1.734368006, 1.79116071, 1.853411775, 1.908606137, 1.969936987, 2.028057589, 2.091850713, 2.151998203, 2.213039835, 2.274896559, 2.336773934, 2.395514502, 2.457358928, 
            2.515219055, 2.573777623, 2.633214255, 2.693431077, 2.750035753, 2.81099804, 2.868973784, 2.923276881, 2.98248275, 3.042340102, 3.100858199, 3.157347124, 3.214790935, 3.267473023, 3.323775766, 3.37932734, 3.436779015, 3.493749292, 3.550147397, 3.607178361, 
            3.663518946, 3.719829584, 3.776251503, 3.831608068, 3.889198914, 3.945995546, 4.002607455, 4.058265431, 4.114238107, 4.169676475, 4.226433266, 4.281283449, 4.336805792, 4.391435073, 4.447407079, 4.503499508, 4.559109307, 4.613682059, 4.669101846, 4.724044433, 
            4.778319404, 4.832828338, 4.887948117, 4.943260916, 4.997345967, 5.051331558, 5.105940631, 5.159226931, 5.212874187, 5.265933683, 5.320477736, 5.374848125, 5.428163169, 5.481545831, 5.535955836, 5.58799423, 5.641767754, 5.693773756, 5.746496546, 5.799008035, 
            5.851936501, 5.905288517, 5.958236408, 6.009090973, 6.060226283, 6.112687118, 6.165184423, 6.215605902, 6.267417058, 6.317103137, 6.368986418, 6.417351867, 6.46681888, 6.517052343, 6.566589093, 6.61475776, 6.66312559, 6.710806975, 6.759417967, 6.807110623, 
            6.852329839, 6.898361917, 6.942363757, 6.987643931, 7.031951759, 7.071104251, 7.116287362, 7.157652493, 7.197481356, 7.23603734, 7.27391404, 7.311383032, 7.34575992, 7.380372258, 7.414249862, 7.446739811, 7.475374294, 7.502849546, 7.528352557, 7.55216072, 
            7.571403838, 7.585211073, 7.599462923, 7.605086914, 7.61216158, 7.610567038, 7.603853787, 7.589387919, 7.572223927, 7.547894599, 7.522581337, 7.486541749, 7.449477169, 7.410756231, 7.369351244, 7.325600203, 7.288411569, 7.253098886, 7.225729444, 7.204374444, 
            7.188085811, 7.177700369, 7.181328004, 7.184642431, 7.198887028, 7.218248477, 7.243411521, 7.274079983, 7.309782595, 7.350096072, 7.393045594, 7.439468008, 7.48978204, 7.542665118, 7.592621895, 7.647710517, 7.70342976, 7.756057335, 7.812465936, 7.872100794, 
            7.928721983, 7.985307721, 8.04593147, 8.1051949, 8.163760378, 8.22268587, 8.279240316, 8.338247019, 8.399524689, 8.457757667, 8.511598888, 8.571960874, 8.629920722, 8.687515124, 8.74843856, 8.809967337, 8.867857271, 8.920081923, 8.978255334, 9.036830069, 
            9.083765639, 9.148731926, 9.204040646, 9.264432573, 9.318521275, 9.373122913, 9.42862127, 9.479917855, 9.5368739, 9.593431189, 9.649917519, 9.704482186, 9.750882949, 9.806001363, 9.860152537, 9.917498646, 9.968398129, 10.02382345, 10.07500199, 10.12708734, 
            10.18335224, 10.23706613, 10.28628773, 10.34146643, 10.39215013, 10.44200832, 10.49336256, 10.5517646, 10.60545522, 10.65817091, 10.70579031, 10.75807795, 10.80782605, 10.85926339, 10.9110202, 10.96181208, 11.01266681, 11.06849385, 11.11569439, 11.16984741, 
            11.21616325, 11.26655345, 11.31619114, 11.36079431, 11.41081797, 11.47288865, 11.51937378, 11.56250415, 11.61775711, 11.66829595, 11.71967858, 11.7737027, 11.82020872, 11.86438552, 11.91930196, 11.96737106, 12.01542787, 12.06389822, 12.1162431, 12.16532652, 
            12.21775953, 12.26700903, 12.99198306, 13.0402495, 13.08984959, 13.13438949, 13.19350911, 13.23424936, 13.2825952, 13.32973008, 13.37524914, 13.42119816, 13.46516297, 13.51960433, 13.56523813, 13.61515704, 13.66027168, 13.70964938, 13.75760575, 13.81378197, 
            13.8577198, 13.90548777, 13.94978109, 13.9955611, 14.0463704, 14.08906725, 14.13278052, 14.18605286, 14.2300396, 14.27204602, 14.33214219, 14.37325593, 14.41873986, 14.47146449, 14.51965833, 14.56653756, 14.60865354, 14.65292487, 14.70647543, 14.75635087, 
            14.82100212, 14.84862799, 14.8956765, 14.94712102, 14.99170484, 15.02392461, 15.08179888, 15.1223348, 15.17582154, 15.23233469, 15.2773787, 15.34740513, 15.38951869, 15.4724516, 15.49621661, 15.53351552, 15.55632073
        ])
        um_lam_array = lam_array * 1e6  # Convert from meters to micrometers
        n_interp = np.interp(um_lam_array, wl, n)
        k_interp = np.interp(um_lam_array, wl, k)
        return n_interp + 1j * k_interp
    
    @staticmethod
    def _get_silicon_n_interp(lam_array: np.ndarray) -> np.ndarray:
        """Static helper for Silicon interpolation."""
        # Wavelength
        wl = np.array([
            0.2  , 0.205, 0.21 , 0.215, 0.22 , 0.225, 0.23 , 0.235, 0.24 ,
            0.245, 0.25 , 0.255, 0.26 , 0.265, 0.27 , 0.275, 0.28 , 0.285,
            0.29 , 0.295, 0.3  , 0.305, 0.31 , 0.315, 0.32 , 0.325, 0.33 ,
            0.335, 0.34 , 0.345, 0.35 , 0.355, 0.36 , 0.365, 0.37 , 0.375,
            0.38 , 0.385, 0.39 , 0.395, 0.4  , 0.405, 0.41 , 0.415, 0.42 ,
            0.425, 0.43 , 0.435, 0.44 , 0.445, 0.45 , 0.455, 0.46 , 0.465,
            0.47 , 0.475, 0.48 , 0.485, 0.49 , 0.495, 0.5  , 0.505, 0.51 ,
            0.515, 0.52 , 0.525, 0.53 , 0.535, 0.54 , 0.545, 0.55 , 0.555,
            0.56 , 0.565, 0.57 , 0.575, 0.58 , 0.585, 0.59 , 0.595, 0.6  ,
            0.605, 0.61 , 0.615, 0.62 , 0.625, 0.63 , 0.635, 0.64 , 0.645,
            0.65 , 0.655, 0.66 , 0.665, 0.67 , 0.675, 0.68 , 0.685, 0.69 ,
            0.695, 0.7  , 0.705, 0.71 , 0.715, 0.72 , 0.725, 0.73 , 0.735,
            0.74 , 0.745, 0.75 , 0.755, 0.76 , 0.765, 0.77 , 0.775, 0.78 ,
            0.785, 0.79 , 0.795, 0.8  , 0.805, 0.81 , 0.815, 0.82 , 0.825,
            0.83 , 0.835, 0.84 , 0.845, 0.85 , 0.855, 0.86 , 0.865, 0.87 ,
            0.875, 0.88 , 0.885, 0.89 , 0.895, 0.9  , 0.905, 0.91 , 0.915,
            0.92 , 0.925, 0.93 , 0.935, 0.94 , 0.945, 0.95 , 0.955, 0.96 ,
            0.965, 0.97 , 0.975, 0.98 , 0.985, 0.99 , 0.995
        ])

        # Refractive index
        n = np.array([
            0.99209946, 1.05679451, 1.1247059 , 1.19675741, 1.27722801,
            1.38535671, 1.52747131, 1.62875164, 1.63909853, 1.62707801,
            1.64601992, 1.68801776, 1.74633876, 1.85337491, 2.08212245,
            2.4735713 , 2.9656414 , 3.56649116, 4.35679744, 4.8708617 ,
            5.01330782, 5.02935245, 5.02716921, 5.03689444, 5.06259965,
            5.09984833, 5.1443719 , 5.1951483 , 5.25560353, 5.33514986,
            5.45127151, 5.6517578 , 6.02356285, 6.52374449, 6.87267149,
            6.84601974, 6.55543307, 6.24018864, 5.98412014, 5.77345359,
            5.59501086, 5.44339996, 5.31408555, 5.20228723, 5.10406115,
            5.01639235, 4.93713938, 4.86484232, 4.79848793, 4.73734021,
            4.68082417, 4.6284844 , 4.57990747, 4.53475048, 4.49273461,
            4.45355981, 4.41697064, 4.38276264, 4.35068386, 4.32058236,
            4.29224812, 4.26553028, 4.24029527, 4.21640707, 4.19374113,
            4.17220154, 4.15169579, 4.13214078, 4.11346761, 4.09560382,
            4.07849896, 4.06209996, 4.04635866, 4.03123764, 4.01669679,
            4.00270204, 3.98922182, 3.97623369, 3.96371109, 3.95162474,
            3.93995781, 3.92869179, 3.91779841, 3.90727404, 3.89708879,
            3.8872389 , 3.87769996, 3.86846609, 3.85951807, 3.85084976,
            3.84244663, 3.83429486, 3.82639138, 3.81872234, 3.81127742,
            3.80404653, 3.79702965, 3.79021264, 3.78358765, 3.77714858,
            3.7708897 , 3.76480337, 3.75888499, 3.75312789, 3.7475284 ,
            3.74207895, 3.73677596, 3.73161441, 3.72659027, 3.72169952,
            3.71693645, 3.71229846, 3.70778143, 3.70338166, 3.69909399,
            3.69491721, 3.69084831, 3.686882  , 3.68301396, 3.67924181,
            3.67556356, 3.67197414, 3.66846842, 3.66504525, 3.66170004,
            3.65842781, 3.65522712, 3.65209297, 3.64902105, 3.64601161,
            3.64305773, 3.64015947, 3.63731223, 3.63451505, 3.63176571,
            3.62906222, 3.6264038 , 3.62378843, 3.62121527, 3.61868419,
            3.61619317, 3.61374248, 3.61133135, 3.60895882, 3.60662551,
            3.60432924, 3.60207111, 3.59985025, 3.59766563, 3.59551717,
            3.59340478, 3.5913274 , 3.58928395, 3.58727653, 3.58530219,
            3.58336061, 3.58145128, 3.57957473, 3.57773035, 3.57591637
        ])

        # Extinction coefficient
        k = np.array([
            2.76174038e+00, 2.85497250e+00, 2.95025410e+00, 3.04900630e+00,
            3.15533029e+00, 3.26589236e+00, 3.33478537e+00, 3.33603115e+00,
            3.35632220e+00, 3.45959923e+00, 3.61423292e+00, 3.79597908e+00,
            4.02092953e+00, 4.31690824e+00, 4.66931982e+00, 4.98761361e+00,
            5.19755414e+00, 5.34668177e+00, 5.19238204e+00, 4.63778673e+00,
            4.13187804e+00, 3.79431720e+00, 3.56934176e+00, 3.40894635e+00,
            3.28349133e+00, 3.17817651e+00, 3.08827837e+00, 3.01457274e+00,
            2.96066532e+00, 2.93113414e+00, 2.93162926e+00, 2.96467969e+00,
            2.95110454e+00, 2.68394590e+00, 2.08462042e+00, 1.39478546e+00,
            9.07631653e-01, 6.46454291e-01, 4.96816637e-01, 3.96557465e-01,
            3.27081427e-01, 2.78088325e-01, 2.41746765e-01, 2.12907830e-01,
            1.88834334e-01, 1.68177696e-01, 1.50277447e-01, 1.34765367e-01,
            1.21376009e-01, 1.09872270e-01, 1.00027231e-01, 9.16207929e-02,
            8.44391727e-02, 7.82906582e-02, 7.30095144e-02, 6.84384658e-02,
            6.44439206e-02, 6.09199956e-02, 5.77664822e-02, 5.49133069e-02,
            5.22955975e-02, 4.98668190e-02, 4.75917630e-02, 4.54423676e-02,
            4.33981573e-02, 4.14456985e-02, 3.95754268e-02, 3.77806583e-02,
            3.60576018e-02, 3.44031125e-02, 3.28160307e-02, 3.12951599e-02,
            2.98395382e-02, 2.84485037e-02, 2.71209756e-02, 2.58557972e-02,
            2.46515407e-02, 2.35073960e-02, 2.24216261e-02, 2.13916801e-02,
            2.04163258e-02, 1.94936365e-02, 1.86205006e-02, 1.77964179e-02,
            1.70176287e-02, 1.62834499e-02, 1.55904834e-02, 1.49379030e-02,
            1.43226704e-02, 1.37437559e-02, 1.31988553e-02, 1.26859127e-02,
            1.22040663e-02, 1.17512078e-02, 1.13256362e-02, 1.09259210e-02,
            1.05513014e-02, 1.01999467e-02, 9.87048914e-03, 9.56186861e-03,
            9.27294879e-03, 9.00252875e-03, 8.74962074e-03, 8.51316480e-03,
            8.29219701e-03, 8.08553428e-03, 7.89223338e-03, 7.71129486e-03,
            7.54168421e-03, 7.38234634e-03, 7.23215344e-03, 7.09004509e-03,
            6.95486952e-03, 6.82544146e-03, 6.70056333e-03, 6.57904254e-03,
            6.45961247e-03, 6.34096943e-03, 6.22189307e-03, 6.10120000e-03,
            5.97766049e-03, 5.85026357e-03, 5.71812625e-03, 5.58042611e-03,
            5.43649588e-03, 5.28616827e-03, 5.12911478e-03, 4.96550103e-03,
            4.79580306e-03, 4.62027633e-03, 4.43999933e-03, 4.25562175e-03,
            4.06837980e-03, 3.87926312e-03, 3.68949473e-03, 3.50014637e-03,
            3.31236955e-03, 3.12715383e-03, 2.94538046e-03, 2.76799668e-03,
            2.59545931e-03, 2.42861182e-03, 2.26772687e-03, 2.11313519e-03,
            1.96529982e-03, 1.82406525e-03, 1.68974638e-03, 1.56236018e-03,
            1.44165910e-03, 1.32771436e-03, 1.22044114e-03, 1.11950236e-03,
            1.02470198e-03, 9.36114029e-04, 8.53287408e-04, 7.75963126e-04,
            7.03904686e-04, 6.37026669e-04, 5.75044592e-04, 5.17624701e-04
        ])
        um_lam_array = lam_array * 1e6  # Convert from meters to micrometers
        n_interp = np.interp(um_lam_array, wl, n)
        k_interp = np.interp(um_lam_array, wl, k)
        return n_interp + 1j * k_interp
    
    @staticmethod
    def _get_titanium_dioxide_n_interp(lam_array: np.ndarray) -> np.ndarray:
        """Static helper for Titanium dioxide interpolation (Franta 2015)."""
        # Wavelengths (micrometers)
        wl = np.array([
            0.114114, 0.115436, 0.116772, 0.118124, 0.119492, 0.120876, 0.122276, 
            0.123692, 0.125124, 0.126573, 0.128038, 0.129521, 0.131021, 0.132538, 
            0.134073, 0.135625, 0.137196, 0.138784, 0.140391, 0.142017, 0.143661, 
            0.145325, 0.147008, 0.14871, 0.150432, 0.152174, 0.153936, 0.155718, 
            0.157522, 0.159346, 0.161191, 0.163057, 0.164945, 0.166855, 0.168787, 
            0.170742, 0.172719, 0.174719, 0.176742, 0.178789, 0.180859, 0.182953, 
            0.185072, 0.187215, 0.189383, 0.191575, 0.193794, 0.196038, 0.198308, 
            0.200604, 0.202927, 0.205277, 0.207654, 0.210058, 0.212491, 0.214951, 
            0.21744, 0.219958, 0.222505, 0.225082, 0.227688, 0.230324, 0.232991, 
            0.235689, 0.238418, 0.241179, 0.243972, 0.246797, 0.249655, 0.252546, 
            0.25547, 0.258428, 0.261421, 0.264448, 0.26751, 0.270608, 0.273741, 
            0.276911, 0.280117, 0.283361, 0.286642, 0.289961, 0.293319, 0.296715, 
            0.300151, 0.303627, 0.307142, 0.310699, 0.314297, 0.317936, 0.321618, 
            0.325342, 0.329109, 0.33292, 0.336775, 0.340675, 0.34462, 0.34861, 
            0.352647, 0.35673, 0.360861, 0.36504, 0.369266, 0.373542, 0.377868, 
            0.382243, 0.386669, 0.391147, 0.395676, 0.400258, 0.404893, 0.409581, 
            0.414324, 0.419121, 0.423975, 0.428884, 0.43385, 0.438874, 0.443956, 
            0.449097, 0.454297, 0.459558, 0.464879, 0.470262, 0.475707, 0.481216, 
            0.486788, 0.492425, 0.498127, 0.503895, 0.50973, 0.515632, 0.521603, 
            0.527643, 0.533752, 0.539933, 0.546185, 0.55251, 0.558907, 0.565379, 
            0.571926, 0.578549, 0.585248, 0.592025, 0.59888, 0.605815, 0.61283, 
            0.619926, 0.627104, 0.634366, 0.641712, 0.649142, 0.656659, 0.664263, 
            0.671955, 0.679735, 0.687606, 0.695568, 0.703623, 0.71177, 0.720012, 
            0.72835, 0.736783, 0.745315, 0.753945, 0.762676, 0.771507, 0.780441, 
            0.789478, 0.798619, 0.807867, 0.817222, 0.826685, 0.836257, 0.845941, 
            0.855736, 0.865645, 0.875669, 0.885809, 0.896066, 0.906442, 0.916938, 
            0.927555, 0.938296, 0.949161, 0.960152, 0.97127, 0.982517, 0.993894, 
            1.0054, 1.01704, 1.02882, 1.04073, 1.05279, 1.06498, 1.07731, 1.08978, 
            1.1024, 1.11517, 1.12808, 1.14114, 1.15436, 1.16772, 1.18124, 1.19492, 
            1.20876, 1.22276, 1.23692, 1.25124, 1.26573, 1.28038, 1.29521, 1.31021, 
            1.32538, 1.34073, 1.35625, 1.37196, 1.38784, 1.40391, 1.42017, 1.43661, 
            1.45325, 1.47008, 1.4871, 1.50432, 1.52174, 1.53936, 1.55718, 1.57522, 
            1.59346, 1.61191, 1.63057, 1.64945, 1.66855, 1.68787, 1.70742, 1.72719, 
            1.74719, 1.76742, 1.78789, 1.80859, 1.82953, 1.85072, 1.87215, 1.89383, 
            1.91575, 1.93794, 1.96038, 1.98308
        ])

        # Refractive index
        n = np.array([
            0.9542948 , 0.95578109, 0.95842858, 0.96222934, 0.96718989,
            0.97332988, 0.98068133, 0.98928814, 0.99920578, 1.01050088,
            1.0232508 , 1.03754281, 1.05347291, 1.07114393, 1.09066278,
            1.1121365 , 1.13566683, 1.161343  , 1.1892324 , 1.21936917,
            1.25174067, 1.2862725 , 1.32281312, 1.36112004, 1.40084992,
            1.44155587, 1.48269485, 1.52364727, 1.56374929, 1.60233541,
            1.63878644, 1.67257591, 1.70330771, 1.7307393 , 1.75478787,
            1.77552029, 1.79313061, 1.80791029, 1.82021633, 1.83044153,
            1.83898951, 1.84625571, 1.85261423, 1.85841005, 1.86395531,
            1.86952873, 1.87537713, 1.88171824, 1.8887442 , 1.89662531,
            1.90551376, 1.9155472 , 1.92685196, 1.93954594, 1.95374119,
            1.96954604, 1.987067  , 2.00641016, 2.02768234, 2.05099181,
            2.07644855, 2.10416402, 2.13425035, 2.16681874, 2.20197691,
            2.23982538, 2.28045239, 2.32392684, 2.3702893 , 2.41954031,
            2.471626  , 2.52642068, 2.58370672, 2.64315224, 2.70428831,
            2.76648795, 2.82895076, 2.89069816, 2.95058466, 3.00733052,
            3.05957909, 3.10597792, 3.14527734, 3.17643444, 3.1987059 ,
            3.21171358, 3.21547066, 3.21036469, 3.19710272, 3.17663104,
            3.15004456, 3.11850032, 3.08314482, 3.04506065, 3.00523302,
            2.96453402, 2.92372153, 2.88344929, 2.84428705, 2.80675459,
            2.77141028, 2.7389754 , 2.70959666, 2.68301845, 2.65891214,
            2.6369579 , 2.61687011, 2.59840289, 2.58134814, 2.56553096,
            2.55080455, 2.53704542, 2.52414932, 2.51202768, 2.5006049 ,
            2.48981592, 2.47960449, 2.46992159, 2.46072428, 2.4519747 ,
            2.4436393 , 2.43568818, 2.42809459, 2.42083444, 2.41388601,
            2.4072296 , 2.40084727, 2.39472266, 2.3888408 , 2.38318792,
            2.37775138, 2.37251948, 2.36748141, 2.36262715, 2.35794739,
            2.35343348, 2.34907733, 2.34487141, 2.34080866, 2.33688246,
            2.33308663, 2.32941532, 2.32586307, 2.32242471, 2.31909537,
            2.31587046, 2.31274563, 2.30971678, 2.30678   , 2.30393162,
            2.30116812, 2.2984862 , 2.29588267, 2.29335454, 2.29089894,
            2.28851315, 2.28619455, 2.28394067, 2.28174914, 2.27961768,
            2.27754413, 2.27552641, 2.27356254, 2.27165061, 2.2697888 ,
            2.26797535, 2.26620858, 2.26448687, 2.26280868, 2.26117251,
            2.25957692, 2.25802053, 2.25650201, 2.25502007, 2.25357347,
            2.25216103, 2.25078158, 2.24943401, 2.24811725, 2.24683025,
            2.24557202, 2.24434157, 2.24313797, 2.2419603 , 2.24080767,
            2.23967923, 2.23857415, 2.23749162, 2.23643085, 2.23539108,
            2.23437157, 2.23337161, 2.23239048, 2.23142752, 2.23048204,
            2.22955341, 2.228641  , 2.22774418, 2.22686236, 2.22599495,
            2.22514137, 2.22430107, 2.22347349, 2.22265811, 2.22185438,
            2.2210618 , 2.22027986, 2.21950807, 2.21874594, 2.21799298,
            2.21724874, 2.21651274, 2.21578453, 2.21506366, 2.2143497 ,
            2.21364219, 2.21294073, 2.21224487, 2.2115542 , 2.21086831,
            2.21018678, 2.20950921, 2.20883519, 2.20816432, 2.20749621,
            2.20683045, 2.20616667, 2.20550446, 2.20484345, 2.20418324,
            2.20352344, 2.20286368, 2.20220356, 2.20154271, 2.20088074,
            2.20021727, 2.1995519 , 2.19888426, 2.19821396, 2.19754061,
            2.19686382, 2.1961832 , 2.19549835, 2.19480888, 2.19411439,
            2.19341447, 2.19270873, 2.19199674, 2.1912781
        ])

        # Extinction coefficient
        k = np.array([
            7.24760280e-001, 7.50886490e-001, 7.77204350e-001, 8.03727290e-001,
            8.30465110e-001, 8.57423570e-001, 8.84603530e-001, 9.11999710e-001,
            9.39599090e-001, 9.67379000e-001, 9.95304770e-001, 1.02332697e+000,
            1.05137825e+000, 1.07936978e+000, 1.10718731e+000, 1.13468707e+000,
            1.16169173e+000, 1.18798671e+000, 1.21331761e+000, 1.23738944e+000,
            1.25986869e+000, 1.28038943e+000, 1.29856475e+000, 1.31400434e+000,
            1.32633861e+000, 1.33524859e+000, 1.34049916e+000, 1.34197178e+000,
            1.33969137e+000, 1.33384180e+000, 1.32476578e+000, 1.31294723e+000,
            1.29897812e+000, 1.28351455e+000, 1.26722930e+000, 1.25076761e+000,
            1.23471195e+000, 1.21955832e+000, 1.20570476e+000, 1.19345010e+000,
            1.18300045e+000, 1.17448050e+000, 1.16794693e+000, 1.16340220e+000,
            1.16080733e+000, 1.16009298e+000, 1.16116861e+000, 1.16392964e+000,
            1.16826291e+000, 1.17405053e+000, 1.18117245e+000, 1.18950805e+000,
            1.19893674e+000, 1.20933803e+000, 1.22059094e+000, 1.23257301e+000,
            1.24515884e+000, 1.25821834e+000, 1.27161456e+000, 1.28520125e+000,
            1.29882001e+000, 1.31229707e+000, 1.32543972e+000, 1.33803233e+000,
            1.34983205e+000, 1.36056422e+000, 1.36991758e+000, 1.37753962e+000,
            1.38303243e+000, 1.38594945e+000, 1.38579422e+000, 1.38202196e+000,
            1.37404562e+000, 1.36124798e+000, 1.34300175e+000, 1.31869939e+000,
            1.28779371e+000, 1.24984898e+000, 1.20460003e+000, 1.15201389e+000,
            1.09234521e+000, 1.02617454e+000, 9.54418280e-001, 8.78301820e-001,
            7.99294360e-001, 7.19011350e-001, 6.39099020e-001, 5.61118990e-001,
            4.86450640e-001, 4.16223470e-001, 3.51284130e-001, 2.92195610e-001,
            2.39261260e-001, 1.92564270e-001, 1.52013690e-001, 1.17390390e-001,
            8.83882600e-002, 6.46485500e-002, 4.57866700e-002, 3.14117900e-002,
            2.11360000e-002, 1.42398700e-002, 9.63155000e-003, 6.54028000e-003,
            4.45884000e-003, 3.05206000e-003, 2.09761000e-003, 1.44753000e-003,
            1.00302000e-003, 6.97860000e-004, 4.87540000e-004, 3.42000000e-004,
            2.40880000e-004, 1.70350000e-004, 1.20960000e-004, 8.62331577e-005,
            6.17205079e-005, 4.43502820e-005, 3.19934333e-005, 2.31690491e-005,
            1.68431512e-005, 1.22911005e-005, 9.00315357e-006, 6.61940432e-006,
            4.88480400e-006, 3.61795111e-006, 2.68935783e-006, 2.00626128e-006,
            1.50197119e-006, 1.12837268e-006, 8.50631127e-007, 6.43439444e-007,
            4.88349222e-007, 3.71866305e-007, 2.84087206e-007, 2.17719511e-007,
            1.67375805e-007, 1.29063077e-007, 9.98122807e-008, 7.74087162e-008,
            6.01951637e-008, 4.69276890e-008, 3.66696953e-008, 2.87138372e-008,
            2.25242936e-008, 1.76939629e-008, 1.39126268e-008, 1.09432028e-008,
            8.60397853e-009, 6.75528170e-009, 5.28945022e-009, 4.12326382e-009,
            3.19221699e-009, 2.44617339e-009, 1.84605923e-009, 1.36134053e-009,
            9.68093255e-010, 6.47522949e-010, 3.84826333e-010, 1.68313498e-010,
            1.52693020e-239, 9.57369220e-234, 4.38062832e-228, 1.47353198e-222,
            3.66982787e-217, 6.81428706e-212, 9.49816903e-207, 1.00044296e-201,
            8.01492780e-197, 4.91494635e-192, 2.32136546e-187, 8.49582595e-183,
            2.42368593e-178, 5.42085653e-174, 9.55949075e-170, 1.33651821e-165,
            1.48946791e-161, 1.33012530e-157, 9.56743308e-154, 5.57089140e-150,
            2.63885160e-146, 1.02176680e-142, 3.24917184e-139, 8.52448791e-136,
            1.85346107e-132, 3.35442625e-129, 5.07491709e-126, 6.44509246e-123,
            6.89907171e-120, 6.24948851e-117, 4.80929840e-114, 3.15612779e-111,
            1.77287101e-108, 8.55512397e-106, 3.55912012e-103, 1.28094712e-100,
            4.00186404e-098, 1.08886108e-095, 2.58860008e-093, 5.39399748e-091,
            9.88209766e-089, 1.59657232e-086, 2.28143097e-084, 2.89170571e-082,
            3.26023408e-080, 3.27856011e-078, 2.94863775e-076, 2.37794026e-074,
            1.72398218e-072, 1.12642512e-070, 6.64920801e-069, 3.55444151e-067,
            1.72471984e-065, 7.61377368e-064, 3.06465232e-062, 1.12721199e-060,
            3.79659784e-059, 1.17340616e-057, 3.33461903e-056, 8.73066157e-055,
            2.11003783e-053, 4.71623189e-052, 9.76703087e-051, 1.87747691e-049,
            3.35579405e-048, 5.58690071e-047, 8.67821846e-046, 1.25975558e-044,
            1.71172379e-043, 2.18048065e-042, 2.60798837e-041, 2.93320376e-040,
            3.10667088e-039, 3.10301056e-038, 2.92691732e-037, 2.61076042e-036,
            2.20510569e-035, 1.76587798e-034, 1.34248934e-033, 9.70101257e-033,
            6.67120163e-032, 4.37103563e-031, 2.73186030e-030, 1.63047981e-029,
            9.30320761e-029, 5.08015296e-028, 2.65768330e-027, 1.33338938e-026,
            6.42203522e-026
       ])
        um_lam_array = lam_array * 1e6  # Convert from meters to micrometers
        n_interp = np.interp(um_lam_array, wl, n)
        k_interp = np.interp(um_lam_array, wl, k)
        return n_interp + 1j * k_interp

    @staticmethod
    def _get_tantalum_pentoxide_n_interp(lam_array: np.ndarray) -> np.ndarray:
        """
        Static helper for Tantalum pentoxide interpolation.
        Data range: ~0.206 um to 1.0 um.
        """
        # Wavelengths (micrometers)
        wl = np.array([
            0.20667, 0.20701, 0.20736, 0.20771, 0.20805, 0.20840, 0.20875, 0.20911,
            0.20946, 0.20981, 0.21017, 0.21053, 0.21088, 0.21124, 0.21160, 0.21197,
            0.21233, 0.21269, 0.21306, 0.21343, 0.21379, 0.21416, 0.21453, 0.21490,
            0.21528, 0.21565, 0.21603, 0.21640, 0.21678, 0.21716, 0.21754, 0.21793,
            0.21831, 0.21869, 0.21908, 0.21947, 0.21986, 0.22025, 0.22064, 0.22103,
            0.22143, 0.22182, 0.22222, 0.22262, 0.22302, 0.22342, 0.22383, 0.22423,
            0.22464, 0.22505, 0.22545, 0.22587, 0.22628, 0.22669, 0.22711, 0.22752,
            0.22794, 0.22836, 0.22878, 0.22921, 0.22963, 0.23006, 0.23048, 0.23091,
            0.23134, 0.23178, 0.23221, 0.23265, 0.23308, 0.23352, 0.23396, 0.23440,
            0.23485, 0.23529, 0.23574, 0.23619, 0.23664, 0.23709, 0.23755, 0.23800,
            0.23846, 0.23892, 0.23938, 0.23985, 0.24031, 0.24078, 0.24125, 0.24172,
            0.24219, 0.24266, 0.24314, 0.24361, 0.24409, 0.24458, 0.24506, 0.24554,
            0.24603, 0.24652, 0.24701, 0.24750, 0.24800, 0.24850, 0.24900, 0.24950,
            0.25000, 0.25051, 0.25101, 0.25152, 0.25203, 0.25255, 0.25306, 0.25358,
            0.25410, 0.25462, 0.25514, 0.25567, 0.25620, 0.25673, 0.25726, 0.25780,
            0.25833, 0.25887, 0.25941, 0.25996, 0.26050, 0.26105, 0.26160, 0.26216,
            0.26271, 0.26327, 0.26383, 0.26439, 0.26496, 0.26552, 0.26609, 0.26667,
            0.26724, 0.26782, 0.26840, 0.26898, 0.26957, 0.27015, 0.27074, 0.27133,
            0.27193, 0.27253, 0.27313, 0.27373, 0.27434, 0.27494, 0.27556, 0.27617,
            0.27679, 0.27740, 0.27803, 0.27865, 0.27928, 0.27991, 0.28054, 0.28118,
            0.28182, 0.28246, 0.28311, 0.28375, 0.28440, 0.28506, 0.28571, 0.28637,
            0.28704, 0.28770, 0.28837, 0.28904, 0.28972, 0.29040, 0.29108, 0.29176,
            0.29245, 0.29314, 0.29384, 0.29454, 0.29524, 0.29594, 0.29665, 0.29736,
            0.29808, 0.29880, 0.29952, 0.30024, 0.30097, 0.30170, 0.30244, 0.30318,
            0.30392, 0.30467, 0.30542, 0.30617, 0.30693, 0.30769, 0.30846, 0.30923,
            0.31000, 0.31078, 0.31156, 0.31234, 0.31313, 0.31392, 0.31472, 0.31552,
            0.31633, 0.31714, 0.31795, 0.31877, 0.31959, 0.32041, 0.32124, 0.32208,
            0.32292, 0.32376, 0.32461, 0.32546, 0.32632, 0.32718, 0.32804, 0.32891,
            0.32979, 0.33067, 0.33155, 0.33244, 0.33333, 0.33423, 0.33514, 0.33604,
            0.33696, 0.33787, 0.33880, 0.33973, 0.34066, 0.34160, 0.34254, 0.34349,
            0.34444, 0.34540, 0.34637, 0.34734, 0.34831, 0.34930, 0.35028, 0.35127,
            0.35227, 0.35328, 0.35429, 0.35530, 0.35632, 0.35735, 0.35838, 0.35942,
            0.36047, 0.36152, 0.36257, 0.36364, 0.36471, 0.36578, 0.36686, 0.36795,
            0.36905, 0.37015, 0.37126, 0.37237, 0.37349, 0.37462, 0.37576, 0.37690,
            0.37805, 0.37920, 0.38037, 0.38154, 0.38272, 0.38390, 0.38509, 0.38629,
            0.38750, 0.38871, 0.38994, 0.39117, 0.39241, 0.39365, 0.39490, 0.39617,
            0.39744, 0.39871, 0.40000, 0.40129, 0.40260, 0.40391, 0.40523, 0.40656,
            0.40789, 0.40924, 0.41060, 0.41196, 0.41333, 0.41472, 0.41611, 0.41751,
            0.41892, 0.42034, 0.42177, 0.42321, 0.42466, 0.42612, 0.42759, 0.42907,
            0.43056, 0.43206, 0.43357, 0.43509, 0.43662, 0.43816, 0.43972, 0.44128,
            0.44286, 0.44444, 0.44604, 0.44765, 0.44928, 0.45091, 0.45255, 0.45421,
            0.45588, 0.45756, 0.45926, 0.46097, 0.46269, 0.46442, 0.46617, 0.46792,
            0.46970, 0.47148, 0.47328, 0.47510, 0.47692, 0.47876, 0.48062, 0.48249,
            0.48438, 0.48627, 0.48819, 0.49012, 0.49206, 0.49402, 0.49600, 0.49799,
            0.50000, 0.50202, 0.50407, 0.50612, 0.50820, 0.51029, 0.51240, 0.51452,
            0.51667, 0.51883, 0.52101, 0.52321, 0.52542, 0.52766, 0.52991, 0.53219,
            0.53448, 0.53680, 0.53913, 0.54148, 0.54386, 0.54626, 0.54867, 0.55111,
            0.55357, 0.55605, 0.55856, 0.56109, 0.56364, 0.56621, 0.56881, 0.57143,
            0.57407, 0.57674, 0.57944, 0.58216, 0.58491, 0.58768, 0.59048, 0.59330,
            0.59615, 0.59903, 0.60194, 0.60488, 0.60784, 0.61084, 0.61386, 0.61692,
            0.62000, 0.62312, 0.62626, 0.62944, 0.63265, 0.63590, 0.63918, 0.64249,
            0.64583, 0.64921, 0.65263, 0.65608, 0.65957, 0.66310, 0.66667, 0.67027,
            0.67391, 0.67760, 0.68132, 0.68508, 0.68889, 0.69274, 0.69663, 0.70056,
            0.70455, 0.70857, 0.71264, 0.71676, 0.72093, 0.72515, 0.72941, 0.73373,
            0.73810, 0.74251, 0.74699, 0.75152, 0.75610, 0.76074, 0.76543, 0.77019,
            0.77500, 0.77987, 0.78481, 0.78981, 0.79487, 0.80000, 0.80519, 0.81046,
            0.81579, 0.82119, 0.82667, 0.83221, 0.83784, 0.84354, 0.84932, 0.85517,
            0.86111, 0.86713, 0.87324, 0.87943, 0.88571, 0.89209, 0.89855, 0.90511,
            0.91176, 0.91852, 0.92537, 0.93233, 0.93939, 0.94656, 0.95385, 0.96124,
            0.96875, 0.97638, 0.98413, 0.99200, 1.00000
        ])

        # Refractive index
        n = np.array([
            2.58752, 2.59446, 2.60139, 2.60832, 2.61523, 2.62213, 2.62901, 2.63589,
            2.64274, 2.64958, 2.65640, 2.66321, 2.66999, 2.67675, 2.68348, 2.69019,
            2.69688, 2.70353, 2.71016, 2.71676, 2.72332, 2.72985, 2.73634, 2.74280,
            2.74922, 2.75560, 2.76193, 2.76822, 2.77447, 2.78067, 2.78682, 2.79292,
            2.79896, 2.80496, 2.81089, 2.81677, 2.82259, 2.82835, 2.83404, 2.83967,
            2.84523, 2.85072, 2.85614, 2.86149, 2.86676, 2.87196, 2.87708, 2.88212,
            2.88707, 2.89195, 2.89673, 2.90143, 2.90604, 2.91056, 2.91498, 2.91931,
            2.92354, 2.92767, 2.93170, 2.93563, 2.93945, 2.94317, 2.94678, 2.95029,
            2.95368, 2.95695, 2.96012, 2.96317, 2.96610, 2.96891, 2.97160, 2.97417,
            2.97662, 2.97895, 2.98115, 2.98322, 2.98516, 2.98698, 2.98866, 2.99022,
            2.99164, 2.99293, 2.99408, 2.99510, 2.99599, 2.99674, 2.99735, 2.99782,
            2.99816, 2.99836, 2.99842, 2.99835, 2.99813, 2.99777, 2.99728, 2.99664,
            2.99587, 2.99496, 2.99391, 2.99272, 2.99139, 2.98992, 2.98832, 2.98657,
            2.98469, 2.98268, 2.98053, 2.97825, 2.97583, 2.97328, 2.97059, 2.96778,
            2.96484, 2.96177, 2.95857, 2.95524, 2.95179, 2.94822, 2.94452, 2.94071,
            2.93677, 2.93272, 2.92855, 2.92427, 2.91988, 2.91538, 2.91076, 2.90605,
            2.90122, 2.89630, 2.89127, 2.88615, 2.88093, 2.87561, 2.87021, 2.86471,
            2.85913, 2.85346, 2.84771, 2.84188, 2.83597, 2.82999, 2.82394, 2.81782,
            2.81162, 2.80537, 2.79905, 2.79268, 2.78624, 2.77976, 2.77322, 2.76664,
            2.76001, 2.75335, 2.74664, 2.73990, 2.73313, 2.72632, 2.71950, 2.71265,
            2.70578, 2.69890, 2.69200, 2.68510, 2.67820, 2.67130, 2.66440, 2.65751,
            2.65063, 2.64377, 2.63693, 2.63012, 2.62334, 2.61660, 2.60990, 2.60325,
            2.59666, 2.59013, 2.58367, 2.57729, 2.57100, 2.56481, 2.55874, 2.55279,
            2.54700, 2.54141, 2.53609, 2.53096, 2.52599, 2.52115, 2.51644, 2.51183,
            2.50733, 2.50293, 2.49862, 2.49439, 2.49024, 2.48617, 2.48217, 2.47824,
            2.47438, 2.47058, 2.46684, 2.46317, 2.45955, 2.45598, 2.45247, 2.44901,
            2.44560, 2.44224, 2.43893, 2.43566, 2.43244, 2.42926, 2.42612, 2.42302,
            2.41997, 2.41695, 2.41397, 2.41102, 2.40811, 2.40524, 2.40240, 2.39960,
            2.39683, 2.39409, 2.39138, 2.38870, 2.38606, 2.38344, 2.38085, 2.37829,
            2.37576, 2.37325, 2.37077, 2.36832, 2.36589, 2.36349, 2.36112, 2.35876,
            2.35644, 2.35413, 2.35185, 2.34959, 2.34735, 2.34514, 2.34295, 2.34078,
            2.33862, 2.33649, 2.33438, 2.33229, 2.33022, 2.32817, 2.32614, 2.32413,
            2.32213, 2.32016, 2.31820, 2.31626, 2.31433, 2.31242, 2.31054, 2.30866,
            2.30681, 2.30497, 2.30314, 2.30133, 2.29954, 2.29776, 2.29600, 2.29425,
            2.29252, 2.29080, 2.28910, 2.28741, 2.28573, 2.28407, 2.28242, 2.28079,
            2.27917, 2.27756, 2.27597, 2.27438, 2.27281, 2.27126, 2.26971, 2.26818,
            2.26666, 2.26516, 2.26366, 2.26218, 2.26070, 2.25924, 2.25779, 2.25636,
            2.25493, 2.25351, 2.25211, 2.25071, 2.24933, 2.24796, 2.24660, 2.24524,
            2.24390, 2.24257, 2.24125, 2.23994, 2.23863, 2.23734, 2.23606, 2.23479,
            2.23352, 2.23227, 2.23102, 2.22979, 2.22856, 2.22734, 2.22613, 2.22493,
            2.22374, 2.22256, 2.22139, 2.22022, 2.21906, 2.21792, 2.21678, 2.21564,
            2.21452, 2.21340, 2.21230, 2.21120, 2.21010, 2.20902, 2.20794, 2.20688,
            2.20581, 2.20476, 2.20372, 2.20268, 2.20165, 2.20062, 2.19960, 2.19859,
            2.19759, 2.19660, 2.19561, 2.19463, 2.19365, 2.19269, 2.19172, 2.19077,
            2.18982, 2.18888, 2.18795, 2.18702, 2.18610, 2.18519, 2.18428, 2.18338,
            2.18248, 2.18159, 2.18071, 2.17983, 2.17896, 2.17810, 2.17724, 2.17638,
            2.17554, 2.17470, 2.17386, 2.17303, 2.17221, 2.17139, 2.17058, 2.16977,
            2.16897, 2.16818, 2.16739, 2.16661, 2.16583, 2.16505, 2.16429, 2.16353,
            2.16277, 2.16202, 2.16127, 2.16053, 2.15979, 2.15906, 2.15834, 2.15762,
            2.15690, 2.15619, 2.15549, 2.15479, 2.15409, 2.15340, 2.15272, 2.15204,
            2.15136, 2.15069, 2.15003, 2.14937, 2.14871, 2.14806, 2.14741, 2.14677,
            2.14613, 2.14550, 2.14487, 2.14425, 2.14363, 2.14301, 2.14240, 2.14180,
            2.14120, 2.14060, 2.14001, 2.13942, 2.13884, 2.13826, 2.13768, 2.13711,
            2.13655, 2.13598, 2.13543, 2.13487, 2.13432, 2.13378, 2.13324, 2.13270,
            2.13216, 2.13164, 2.13111, 2.13059, 2.13007, 2.12956, 2.12905, 2.12855,
            2.12805, 2.12755, 2.12706, 2.12657, 2.12608, 2.12560, 2.12512, 2.12465,
            2.12418, 2.12371, 2.12325, 2.12279, 2.12234, 2.12188, 2.12144, 2.12099,
            2.12055, 2.12012, 2.11968, 2.11926, 2.11883, 2.11841, 2.11799, 2.11758,
            2.11716, 2.11676, 2.11635, 2.11595, 2.11556, 2.11516, 2.11477, 2.11439,
            2.11400, 2.11362, 2.11325, 2.11288, 2.11251
        ])

        # Extinction coefficient (k) - Truncated to match wl
        k = np.array([
            1.31746, 1.31309, 1.30865, 1.30413, 1.29953, 1.29485, 1.29009, 1.28524,
            1.28031, 1.27530, 1.27020, 1.26502, 1.25976, 1.25441, 1.24897, 1.24345,
            1.23784, 1.23215, 1.22637, 1.22050, 1.21454, 1.20850, 1.20237, 1.19615,
            1.18984, 1.18345, 1.17697, 1.17039, 1.16374, 1.15699, 1.15015, 1.14323,
            1.13622, 1.12912, 1.12193, 1.11466, 1.10730, 1.09985, 1.09232, 1.08470,
            1.07700, 1.06921, 1.06134, 1.05338, 1.04535, 1.03723, 1.02903, 1.02074,
            1.01238, 1.00395, 0.99543, 0.98684, 0.97817, 0.96942, 0.96061, 0.95172,
            0.94276, 0.93373, 0.92464, 0.91548, 0.90625, 0.89696, 0.88761, 0.87820,
            0.86873, 0.85920, 0.84962, 0.83998, 0.83030, 0.82056, 0.81078, 0.80096,
            0.79109, 0.78118, 0.77123, 0.76124, 0.75123, 0.74118, 0.73110, 0.72099,
            0.71086, 0.70070, 0.69053, 0.68034, 0.67014, 0.65992, 0.64970, 0.63946,
            0.62923, 0.61899, 0.60875, 0.59852, 0.58830, 0.57808, 0.56788, 0.55769,
            0.54752, 0.53737, 0.52724, 0.51714, 0.50707, 0.49703, 0.48703, 0.47706,
            0.46713, 0.45725, 0.44741, 0.43762, 0.42788, 0.41820, 0.40857, 0.39900,
            0.38949, 0.38005, 0.37067, 0.36137, 0.35213, 0.34298, 0.33389, 0.32489,
            0.31597, 0.30714, 0.29839, 0.28973, 0.28117, 0.27269, 0.26432, 0.25604,
            0.24786, 0.23979, 0.23182, 0.22395, 0.21620, 0.20855, 0.20102, 0.19361,
            0.18631, 0.17912, 0.17206, 0.16512, 0.15831, 0.15161, 0.14505, 0.13861,
            0.13231, 0.12613, 0.12009, 0.11418, 0.10841, 0.10278, 0.09728, 0.09192,
            0.08671, 0.08164, 0.07671, 0.07192, 0.06728, 0.06279, 0.05844, 0.05424,
            0.05020, 0.04630, 0.04256, 0.03896, 0.03553, 0.03224, 0.02911, 0.02614,
            0.02332, 0.02066, 0.01816, 0.01582, 0.01364, 0.01161, 0.00975, 0.00805,
            0.00651, 0.00514, 0.00392, 0.00287, 0.00198, 0.00126, 0.00070, 0.00030,
            0.00007, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000,
            0.00000, 0.00000, 0.00000, 0.00000, 0.00000
        ])

        um_lam_array = lam_array * 1e6  # Convert from meters to micrometers
        n_interp = np.interp(um_lam_array, wl, n)
        k_interp = np.interp(um_lam_array, wl, k)
        return n_interp + 1j * k_interp
    
class SipmStackSimulator(OpticalStackSimulator):
    """
    A simulator for calculating the Photon Detection Efficiency (PDE) of Silicon Photomultipliers (SiPMs) given a coating stack.

    This class extends `OpticalStackSimulator` to model the optical transport through thin-film coatings 
    into a Silicon substrate. It calculates the PDE by combining optical transmittance with the 
    probability of electron-hole pair generation within the active depletion region.

    Parameters
    ----------
    layers : list of str
        List of material names for the coating stack (e.g., ``["Si3N4", "SiO2"]``).
    thicknesses : list of float
        List of layer thicknesses in meters.
    medium : str
        The incident medium material name (e.g., ``"Air"``).
    type_layers : list of str
        List of layer types corresponding to `layers`:
        - ``'c'``: Coherent (phase-sensitive, interference calculated).
        - ``'i'``: Incoherent (phase-averaged, intensity addition).
    depletion_layer_depth : float, optional
        Depth of the start of the depletion region ($x_1$) in nm. Default is 5.0 nm.
    depletion_layer_width : float, optional
        Depth extent of the depletion region ($x_2$) in nm. Default is 2100.0 nm.
    fill_factor : float, optional
        Geometric fill factor ($FF$). Default is 1.0.
    breakdown_probability : float, optional
        Avalanche triggering probability ($P_{br}$). Default is 1.0.
    ucell_size : float, optional
        Size of the micro-cell in meters. Default is 75e-6 m.
"""

    def __init__(self, layers: list, thicknesses: list, medium: str, type_layers: list, 
                 depletion_layer_depth: float = 5.0, 
                 depletion_layer_width: float = 2100.0, 
                 fill_factor: float = 1.0,
                 breakdown_probability: float = 1.0,
                 ucell_size = 75e-6):
        # Initialize base class with "Si" hardcoded as the substrate
        super().__init__(layers, thicknesses, medium, "Si", type_layers)
        
        self.depletion_layer_depth = depletion_layer_depth
        self.depletion_layer_width = depletion_layer_width
        self.fill_factor = fill_factor
        self.breakdown_probability = breakdown_probability
        self.ucell_size = ucell_size
        
        # Results
        self.qe = None
        self.pde = None

    def run(self, polarization: str = 'unpolarized') -> np.ndarray:
        """
        Execute the simulation to calculate quantum efficiency and PDE.

        The method performs the following steps:
        1. Calculate optical transmittance into the Silicon substrate.
        2. Calculate the internal path lengths correcting for refraction/incidence angle.
        3. Computes the Silicon absorption coefficient from the complex refractive index.
        4. Computes the probability of photon absorption strictly within the depletion region.
        5. Combines factors: $PDE = T \\times P_{int} \\times FF \\times P_{br}$.

        Parameters
        ----------
        polarization : str, optional
            Polarization mode: ``'s'``, ``'p'``, or ``'unpolarized'`` (default).
            If ``'unpolarized'``, the average of s and p transmittances is used.

        Returns
        -------
        np.ndarray
            The calculated PDE array with shape (n_angles, n_wavelengths).
        """
        super().run(polarization)

        # Silicon refractive index
        n_silicon_complex = self._material_db['Si'](self._wavelengths)
        n_silicon_real = np.real(n_silicon_complex)
        k_silicon = np.imag(n_silicon_complex)
        
        # Internal angle inside Silicon to get the correct path length
        # sin(theta2) = sin(theta1) * n1 / n2
        sin_theta_ext = np.sin(self._angles_rad[:, np.newaxis])
        n_air = np.real(self._material_db['Air'](self._wavelengths))
        sin_theta_si = sin_theta_ext * n_air / n_silicon_real
        sin_theta_si = np.clip(sin_theta_si, 0.0, 1.0)
        
        # Path length inside the Silicon
        cos_theta_si = np.sqrt(1 - sin_theta_si**2)
        cos_theta_si = np.clip(cos_theta_si, 1e-12, 1.0)
        max_thickness_limit = self.ucell_size * 1e9
        xx1 = self.depletion_layer_depth / cos_theta_si
        xx1[xx1 > max_thickness_limit] = max_thickness_limit
        
        # Path length inside the depletion layer
        xx2 = self.depletion_layer_width / cos_theta_si
        xx2[xx2 > max_thickness_limit] = max_thickness_limit

        # alpha = 4 * pi * k / lambda [1/nm]
        alpha = 4. * np.pi * k_silicon / self.wavelengths

        # (fraction absorbed in the non active region) -
        # - (fraction absorbed in the active region)
        interaction_prob = np.exp(-alpha * xx1) - np.exp(-alpha * xx2)

        # Quantum efficiency
        self.qe = self.transmittance * interaction_prob

        # PDE
        self._update_pde()
        
        return self.pde

    def constrain_pde(self, lambda0: float, pde0: float):
        """
        Adjusts the breakdown probability to force the PDE to match a specific value 
        at a specific wavelength (at normal incidence).

        This is useful for calibrating the model against a known experimental data point.
        It modifies ``self.breakdown_probability`` in place.

        Parameters
        ----------
        lambda0 : float
            The target wavelength in nanometers.
        pde0 : float
            The target PDE value (0.0 to 1.0) at that wavelength.
        
        Raises
        ------
        RuntimeError
            If ``run()`` has not been called yet.
        """
        if self.qe is None:
            raise(RuntimeError("Simulation not yet run. Running defaults..."))

        # Extract QE at normal incidence (index 0 assumed to be 0 degrees)
        qe_at_normal = self.qe[0]
        
        # Interpolate QE to the specific target wavelength
        qe0 = np.interp(lambda0, self.wavelengths, qe_at_normal)

        if qe0 <= 1e-9:
            raise(RuntimeError(f"Warning: QE at {lambda0}nm is effectively zero. Cannot constrain."))

        required_breakdown = pde0 / (qe0 * self.fill_factor)
        
        self.breakdown_probability = required_breakdown
        self._update_pde()

    def _update_pde(self):
        """Internal helper to re-compute PDE when factors change."""
        if self.qe is not None:
            self.pde = self.qe * self.fill_factor * self.breakdown_probability

    @iactsim_style
    def plot_pde_normal(self,
            compare_data: tuple = None,
            compare_model: tuple = None
    ) -> None:
        """
        Plots the simulated PDE at normal incidence against optional comparison data.

        Parameters
        ----------
        compare_data : tuple, optional
            Experimental data tuple ``(wavelengths, values, errors)``.
        compare_model : tuple, optional
            External model data tuple ``(wavelengths, values)``.
        """
        if self.pde is None:
            return

        import matplotlib.pyplot as plt

        plt.figure(figsize=(7, 4.5))
        
        plt.plot(self.wavelengths, self.pde[0], 
                 label='Simulated PDE (Stack)', linewidth=2, color='tab:blue')
        
        plt.plot(self.wavelengths, self.qe[0], 
                 label='Optical QE (No FF/Br)', ls=':', color='tab:blue', alpha=0.6)

        if compare_model:
            model_wl, model_val = compare_model
            plt.plot(model_wl, model_val, label='Reference Model', ls='--', color='black')
        
        if compare_data:
            meas_wl, meas_val, meas_std = compare_data
            plt.errorbar(meas_wl, meas_val, yerr=meas_std, 
                         label='Measurement', 
                         ms=5, fmt='o', capsize=3, mfc='none', mec='red', ecolor='red')

        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Efficiency")
        plt.title(f"SiPM PDE simulation\n"
                  f"$x_1={self.depletion_layer_depth:.2f}$ nm, $x_2={self.depletion_layer_width:.2f}$ nm, "
                  f"$FF={self.fill_factor:.3f}$, $P_{{br}}={self.breakdown_probability:.3f}$")
        plt.grid(True, which='both', alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()

    @iactsim_style
    def plot_pde_results(
        self,
        mode: str = 'R',
        cmap: str = "Spectral"
    ) -> None:
        """
        Plots simulation results for s-polarization, p-polarization, and unpolarized light.
        Automatically calculates axis extent from the stored simulation parameters.
    
        Parameters
        ----------
        mode : str
            'R' for Reflectance or 'T' for Transmittance. Determines which data key to use.
        cmap : str, optional
            The colormap to use for the plots.
        """
        if self.pde is None:
            return

        from mpl_toolkits.axes_grid1 import ImageGrid
        import matplotlib.pyplot as plt
        
        has_p = False
        has_s = False
        if self._tran_p is not None:
            has_p = True
        if self._tran_s is not None:
            has_s = True
        
        if not has_s and not has_p:
            return

        # Calculate extent
        wl_min_nm = self._wavelengths[0] * 1e9
        wl_max_nm = self._wavelengths[-1] * 1e9
        ang_min_deg = np.rad2deg(self._angles_rad[0])
        ang_max_deg = np.rad2deg(self._angles_rad[-1])
        extent = [wl_min_nm, wl_max_nm, ang_min_deg, ang_max_deg]
        
        # Calculate aspect ratio for figure sizing
        aspect_ratio = (wl_max_nm - wl_min_nm) / (ang_max_deg - ang_min_deg) / 3

        fig = plt.figure(figsize=(2*3.5*aspect_ratio, 3.5))  
        
        grid = ImageGrid(
            fig, 111,
            nrows_ncols=(1, 2),
            axes_pad=0.5,
            share_all=True,
            cbar_location="right",
            cbar_mode="each",
            cbar_size="5%",
            cbar_pad=0.15,
        )
        
        if mode.lower().startswith('t'):
            label_ax1 = "Transmittance"
            data_ax1 = self.transmittance
            cbar_label_ax1 = "Transmittance (%)"
        else:
            label_ax1 = "Reflectance"
            data_ax1 = self.reflectance
            cbar_label_ax1 = "Reflectance (%)"
         
        plot_data = [
            (label_ax1, cbar_label_ax1, data_ax1),
            ('PDE', "PDE (%)", self.pde),
        ]

        xlabel = "Wavelength (nm)"
        ylabel = "Incident angle (°)"
        
        for ax, cax, (title, cbar_label, data) in zip(grid, grid.cbar_axes, plot_data):
            im = ax.imshow(
                data * 100,
                cmap=cmap, 
                aspect=aspect_ratio,
                extent=extent,
                origin='lower',
                # vmin=0, vmax=100 
            )
            ax.set_title(title)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
        
            # Add colorbar to the specific cax (colorbar axis)
            cbar = cax.colorbar(im)
            # Set label on the colorbar axis
            cax.set_ylabel(cbar_label, rotation=-90, va="bottom")
        
        plt.tight_layout()
        plt.show()
    
    def get_surfcace_properties_obj(self, with_reflections=True, side='both'):
        """
        Creates a SurfaceProperties object from the simulation results.

        Parameters
        ----------
        with_reflections : bool, optional
            If True, the surface properties will include the simulated reflectance
            and absorption. The detection efficiency will be defined relative to
            absorbed photons ('absorbed' kind).
            If False, reflectance is set to zero, and detection efficiency is
            defined relative to incident photons ('incident' kind).
            Default is True.
        side : str, optional
            Specifies which side(s) of the surface to populate properties for.
            Options are 'front', 'back', or 'both'.
            Default is 'both'.

        Returns
        -------
        SurfaceProperties
            The populated surface properties object containing wavelength, incidence angle,
            reflectance, absorption, and efficiency data.
        """
        sipm_prop = SurfaceProperties()

        R_in_sipm = self.reflectance

        sipm_prop.wavelength = self.wavelengths
        sipm_prop.incidence_angle = self.incidence_angles
        sipm_prop.efficiency_wavelength = self.wavelengths
        sipm_prop.efficiency_incidence_angle = self.incidence_angles

        if with_reflections:
            # No transmittance since absorption in the photon path is not yet simulated.
            # So every photon not reflected is absorbed.
            if side in ['front', 'both']:
                sipm_prop.transmittance = np.zeros_like(R_in_sipm)
                sipm_prop.reflectance = R_in_sipm
                sipm_prop.absorption = 1. - R_in_sipm
            
            if side in ['back', 'both']:
                sipm_prop.transmittance_back = np.zeros_like(R_in_sipm)
                sipm_prop.reflectance_back = R_in_sipm
                sipm_prop.absorption_back = 1. - R_in_sipm

            # Since the surface reflects, the efficiency must be relative
            # to the number of absorbed photons (1-R).
            sipm_prop.efficiency_kind = 'absorbed'

            # absorption*efficiency = pde -> efficiency = pde / absorption
            absorption = 1. - R_in_sipm
            efficiency = np.zeros_like(absorption)
            efficiency[R_in_sipm<1] = self.pde[R_in_sipm<1] / absorption[R_in_sipm<1]
            efficiency[np.argwhere(self.incidence_angles>90-1e-3)] = 0.
            sipm_prop.efficiency = efficiency
            
        else:
            if side in ['front', 'both']:
                sipm_prop.transmittance = np.zeros_like(R_in_sipm)
                sipm_prop.reflectance = np.zeros_like(R_in_sipm)
            
            if side in ['back', 'both']:
                sipm_prop.transmittance_back = np.zeros_like(R_in_sipm)
                sipm_prop.reflectance_back = np.zeros_like(R_in_sipm)

            sipm_prop.efficiency_kind = 'incident'
            sipm_prop.efficiency = self.pde

        return sipm_prop