import pytest
import numpy as np
import cupy as cp
import iactsim

def dummy_pulse(extent, resolution, peak_delay, sigma):
    t = np.arange(0, extent, resolution)
    z = (t - peak_delay) / sigma
    log_norm = -0.5 * (z**2 + np.log(2*np.pi)) - np.log(sigma)
    y = np.where(log_norm < 10, t**2 * np.exp(log_norm), 0)

    wave = iactsim.electronics.Waveform(t, y, 'AC')
    wave.normalize()
    return wave

class DummySiPMCamera(iactsim.electronics.CherenkovSiPMCamera):
    def __init__(self):
        self.n_modules = 1
        self.module_side = 32
        self.pixels_per_module = self.module_side * self.module_side
        self.images = []
        self.threshold = 50
        
        waveforms = (
            dummy_pulse(500, 0.1, 4, 10),
            dummy_pulse(500, 0.1, 9, 45),
        )
        
        super().__init__(
            n_pixels=self.pixels_per_module * self.n_modules,
            waveforms=waveforms,
            trigger_channels=[0],
            sampling_channels=[1],
            channels_time_resolution=[1, 1]
        )
        
        # Let the trigger window last a bit longer
        self.trigger_window_end_offset = [128]
        # And start a bit earlier
        self.trigger_window_start_offset = [-10]

        # Sampling window starts immediately after trigger
        self.sampling_delay = [0]
        # And lasts 256 ns
        self.sampling_window_extent = [256]
        
    
    def restart(self):
        super().restart()
        self.images = []
    
    def sampling_action(self):
        # Integrate over the whole sampling window
        image = cp.trapz(self.get_channel_signals(1, reshape=True), axis=1)
        self.images.append(image)
    
    def trigger_action(self):
        # Majority trigger logic
        tr_signals = self.get_channel_signals(0, reshape=True).reshape((self.n_modules, self.pixels_per_module, -1))
        
        # Calculate sum over modules
        sum_signals = cp.sum(tr_signals, axis=0)
        
        # Check threshold
        modules_over_threshold = cp.argmax(sum_signals > self.threshold, axis=0)
        
        # Find first time slice where threshold is exceeded
        trigger_time_slice = cp.argmax(modules_over_threshold > 0).get()
        
        if trigger_time_slice > 0:
            self.triggered = True
            self.trigger_time = self.time_windows[0][trigger_time_slice]
        else:
            self.triggered = False

@pytest.fixture(scope="module")
def camera():
    """
    Initialize the camera once for the module to save overhead.
    """
    cam = DummySiPMCamera()
    cam.n_ucells = cp.full((cam.n_pixels,), 8464, dtype=cp.int32)
    return cam

# Define parameter combinations
@pytest.mark.parametrize("cross_talk", [0., 0.1])
@pytest.mark.parametrize("nsb_rate", [0.05, 1.])
@pytest.mark.parametrize("window_extent", [128, 512])
def test_dummy_sipm_camera_performance(benchmark, camera, window_extent, nsb_rate, cross_talk):
    """
    Benchmarks the simulate_response() method across different noise/crosstalk levels.
    """
    # Reset camera state
    camera.restart()

    flash_width = 30
    
    tr_extent = window_extent - flash_width - 10
    camera.trigger_window_end_offset = [tr_extent]
    camera.trigger_window_start_offset = [-10]

    camera.sampling_delay = [0]
    camera.sampling_window_extent = [window_extent]
    
    # Apply NSB rate
    camera.background_rate = cp.full((camera.n_pixels,), nsb_rate, dtype=cp.float32)
    
    # Apply cross-talk
    camera.cross_talk = cp.full((camera.n_pixels,), cross_talk, dtype=cp.float32)

    camera.afterpulse = cp.full((camera.n_pixels,), 0.05, dtype=cp.float32)
    camera.afterpulse_inv_tau = cp.full((camera.n_pixels,), 1./250., dtype=cp.float32)
    camera.inv_tau_recovery = cp.full((camera.n_pixels,), 1./200., dtype=cp.float32)
    
    # Generate a flash
    # pe_per_pixels, 0ns delay, 30ns width
    source = iactsim.electronics.sources.generate_poisson_flash(camera.n_pixels, 200, 0., flash_width)

    def run_simulation():
        camera.simulate_response(source)
    
    benchmark.pedantic(
        target=run_simulation,
        rounds=100,
        iterations=1,
        warmup_rounds=5
    )

# Define parameter combinations
@pytest.mark.parametrize("nsb_rate", [0.1, 1., 2.])
@pytest.mark.parametrize("simulate_ucells", [False, True])
def test_dummy_sipm_camera_performance_w_ucells(benchmark, camera, nsb_rate, simulate_ucells):
    """
    Benchmarks the simulate_response() method across different noise/crosstalk levels.
    """
    # Reset camera state
    camera.restart()

    afterpulse = 0.05
    cross_talk = 0.05
    window_extent = 128
    pe_per_pixel = 128

    flash_width = 30
    
    tr_extent = window_extent - flash_width - 10
    camera.trigger_window_end_offset = [tr_extent]
    camera.trigger_window_start_offset = [-10]

    camera.sampling_delay = [0]
    camera.sampling_window_extent = [window_extent]
    
    # Apply NSB rate
    camera.background_rate = cp.full((camera.n_pixels,), nsb_rate, dtype=cp.float32)
    
    # Apply cross-talk
    camera.cross_talk = cp.full((camera.n_pixels,), cross_talk, dtype=cp.float32)

    camera.afterpulse = cp.full((camera.n_pixels,), afterpulse, dtype=cp.float32)
    camera.afterpulse_inv_tau = cp.full((camera.n_pixels,), 1./250., dtype=cp.float32)
    camera.inv_tau_recovery = cp.full((camera.n_pixels,), 1./200., dtype=cp.float32)

    camera.simulate_ucells = simulate_ucells
    
    # Generate a flash
    # pe_per_pixels, 0ns delay, 30ns width
    source = iactsim.electronics.sources.generate_poisson_flash(camera.n_pixels, pe_per_pixel, 0., flash_width)
    
    if simulate_ucells:
        ucell_ids = cp.random.uniform(
            0, camera.n_ucells[0],
            size=source[0].shape
        )
        source = (*source, ucell_ids.astype(cp.int32))
    
    def run_simulation():
        camera.simulate_response(source)
    
    benchmark.pedantic(
        target=run_simulation,
        rounds=100,
        iterations=1,
        warmup_rounds=5
    )