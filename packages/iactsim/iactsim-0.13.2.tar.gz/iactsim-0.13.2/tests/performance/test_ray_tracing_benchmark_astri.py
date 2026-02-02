import pytest
import cupy as cp
import iactsim
import numpy as np

@pytest.fixture(scope="module")
def telescope_setup():
    """Initializes the telescope and GPU context."""
    astri = iactsim.models.astri.AstriTelescope()

    astri.optical_system.build_m1_segments()

    astri.optical_system.build_masts()

    astri.cuda_init()

    return astri

def test_ray_tracing_performance_astri(benchmark, telescope_setup):
    telescope = telescope_setup
    source = iactsim.optics.sources.Source(telescope)
    source.positions.radial_uniformity = False
    source.positions.random = True
    source.positions.r_max = 2500
    source.set_target(distance=11000)

    def setup_round_on_axis():
        ps, vs, wls, ts = source.generate(1_000_000)
        cp.cuda.Device().synchronize()
        return ((telescope, ps, vs, wls, ts), {})
    
    def run_trace(telescope, ps, vs, wls, ts):
        telescope.trace_photons(ps, vs, wls, ts)
        cp.cuda.Device().synchronize()
    
    benchmark.pedantic(run_trace, setup=setup_round_on_axis, rounds=100, iterations=1, warmup_rounds=5)

def test_ray_tracing_performance_astri_off_axis(benchmark, telescope_setup):
    telescope = telescope_setup
    source = iactsim.optics.sources.Source(telescope)
    source.positions.radial_uniformity = False
    source.positions.random = True
    source.positions.r_max = 2500
    source.directions.altitude += 1
    source.set_target(distance=11000)
    def setup_round_off_axis():
        ps, vs, wls, ts = source.generate(1_000_000)
        cp.cuda.Device().synchronize()
        return ((telescope, ps, vs, wls, ts), {})
    
    def run_trace(telescope, ps, vs, wls, ts):
        telescope.trace_photons(ps, vs, wls, ts)
        cp.cuda.Device().synchronize()
    
    benchmark.pedantic(run_trace, setup=setup_round_off_axis, rounds=100, iterations=1, warmup_rounds=5)

def test_ray_tracing_performance_astri_pdms(benchmark, telescope_setup):
    telescope = telescope_setup
    telescope.optical_system.build_camera_modules()
    telescope.cuda_init()
    source = iactsim.optics.sources.Source(telescope)
    source.positions.radial_uniformity = False
    source.positions.random = True
    source.positions.r_max = 2500
    source.directions.altitude += 1
    source.set_target(distance=11000)

    def setup_round_pdms():
        ps, vs, wls, ts = source.generate(1_000_000)
        cp.cuda.Device().synchronize()
        return ((telescope, ps, vs, wls, ts), {})
    
    def run_trace(telescope, ps, vs, wls, ts):
        telescope.trace_photons(ps, vs, wls, ts)
        cp.cuda.Device().synchronize()
    
    benchmark.pedantic(run_trace, setup=setup_round_pdms, rounds=100, iterations=1, warmup_rounds=5)

def test_ray_tracing_performance_astri_pdms_window(benchmark, telescope_setup):
    telescope = telescope_setup
    telescope.optical_system.build_camera_modules()
    telescope.optical_system.set_camera_window_parameters(
        240, 8.61, 1.5, 1, 17,
        layer_1_as_cylinder = True,
        layer_2_as_cylinder = True,
        layer_3_as_cylinder = True
    )
    telescope.cuda_init()
    source = iactsim.optics.sources.Source(telescope)
    source.positions.radial_uniformity = False
    source.positions.random = True
    source.positions.r_max = 2500
    source.directions.altitude += 1
    source.set_target(distance=11000)

    def setup_round_pdms_window():
        ps, vs, wls, ts = source.generate(1_000_000)
        cp.cuda.Device().synchronize()
        return ((telescope, ps, vs, wls, ts), {})
    
    def run_trace(telescope, ps, vs, wls, ts):
        telescope.trace_photons(ps, vs, wls, ts)
        cp.cuda.Device().synchronize()
    
    benchmark.pedantic(run_trace, setup=setup_round_pdms_window, rounds=100, iterations=1, warmup_rounds=5)

def test_ray_tracing_performance_astri_pdms_window_props(benchmark, telescope_setup):
    telescope = telescope_setup

    telescope.optical_system.build_camera_modules()

    telescope.optical_system.set_camera_window_parameters(
        240, 8.61, 1.5, 1, 17,
        layer_1_as_cylinder = True,
        layer_2_as_cylinder = True,
        layer_3_as_cylinder = True
    )

    gen = iactsim.optics.FresnelSurfacePropertiesGenerator()
    wls = np.arange(200,1001,1.)
    angls = np.arange(0,91,1.)
    gen.generate(telescope.optical_system['WindowLayer1'], wls, angls,inplace=True)
    gen.generate(telescope.optical_system['WindowLayer2'], wls, angls,inplace=True)
    gen.generate(telescope.optical_system['WindowLayer3'], wls, angls,inplace=True)
    telescope.cuda_init()

    source = iactsim.optics.sources.Source(telescope)
    source.positions.radial_uniformity = False
    source.positions.random = True
    source.positions.r_max = 2500
    source.directions.altitude += 1
    source.set_target(distance=11000)

    def setup_round_pdms_window():
        ps, vs, wls, ts = source.generate(1_000_000)
        cp.cuda.Device().synchronize()
        return ((telescope, ps, vs, wls, ts), {})
    
    def run_trace(telescope, ps, vs, wls, ts):
        telescope.trace_photons(ps, vs, wls, ts)
        cp.cuda.Device().synchronize()
    
    benchmark.pedantic(run_trace, setup=setup_round_pdms_window, rounds=100, iterations=1, warmup_rounds=5)

def test_ray_tracing_performance_astri_pdms_props_window_props(benchmark, telescope_setup):
    # SiPM optical properties
    sipm = iactsim.optics.SipmStackSimulator(
        layers=["SiO2", "ZrO2"],
        thicknesses=[3250, 35],
        medium="Air",
        type_layers=['c', 'c'],
        depletion_layer_depth=3.,
        depletion_layer_width=2600,
        fill_factor=0.75
    )
    sipm.set_simulation_params(
        wl_range=np.arange(200,1000,1),
        angle_range=np.arange(0,91,1)
    )
    sipm.run('u')
    sipm.constrain_pde(462, 0.582517*0.97)
    sipm_surface_prop = sipm.get_surfcace_properties_obj()

    telescope = telescope_setup

    telescope.optical_system.build_camera_modules()

    telescope.optical_system.set_camera_window_parameters(
        240, 8.61, 1.5, 1, 17,
        layer_1_as_cylinder = True,
        layer_2_as_cylinder = True,
        layer_3_as_cylinder = True
    )

    gen = iactsim.optics.FresnelSurfacePropertiesGenerator()
    wls = np.arange(200,1001,1.)
    angls = np.arange(0,91,1.)
    gen.generate(telescope.optical_system['WindowLayer1'], wls, angls,inplace=True)
    gen.generate(telescope.optical_system['WindowLayer2'], wls, angls,inplace=True)
    gen.generate(telescope.optical_system['WindowLayer3'], wls, angls,inplace=True)

    for s in telescope.optical_system:
        if s.name.startswith('PDM'):
            s.properties = sipm_surface_prop

    telescope.cuda_init()

    source = iactsim.optics.sources.Source(telescope)
    source.positions.radial_uniformity = False
    source.positions.random = True
    source.positions.r_max = 2500
    source.directions.altitude += 1
    source.set_target(distance=11000)
    
    def setup_round_pdms_window():
        ps, vs, wls, ts = source.generate(1_000_000)
        cp.cuda.Device().synchronize()
        return ((telescope, ps, vs, wls, ts), {})
    
    def run_trace(telescope, ps, vs, wls, ts):
        telescope.trace_photons(ps, vs, wls, ts)
        cp.cuda.Device().synchronize()
    
    benchmark.pedantic(run_trace, setup=setup_round_pdms_window, rounds=100, iterations=1, warmup_rounds=5)