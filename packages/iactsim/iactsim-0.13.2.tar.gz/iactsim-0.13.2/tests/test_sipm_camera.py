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

import pytest

import iactsim
import numpy as np
import cupy as cp

def dummy_pulse(extent, resolution, peak_delay, sigma):
    t = np.arange(0, extent, resolution)
    z = (t - peak_delay) / sigma
    log_norm = -0.5 * (z**2 + np.log(2*np.pi)) - np.log(sigma)
    y = np.where(log_norm<10, t**2*np.exp(log_norm), 0)

    wave = iactsim.electronics.Waveform(t, y, 'AC')
    wave.normalize()
    return wave
    
class DummySiPMCamera(iactsim.electronics.CherenkovSiPMCamera):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.images = []

    def restart(self):
        super().restart()
        self.images = []
    
    def sampling_action(self):
        image = cp.max(self.get_channel_signals(1, reshape=True), axis=1)
        self.images.append(image)
    
    def trigger_action(self):
        pass

@pytest.fixture
def cam_fast_dc_signals():
    waveforms = (
        dummy_pulse(50, 0.1, 0, 5),
        dummy_pulse(50, 0.1, 3, 8),
    )
    cam = DummySiPMCamera(
        n_pixels = 64*25,
        waveforms = waveforms,
        trigger_channels=[0],
        sampling_channels=[1],
        channels_time_resolution=[1,1]
    )
    return cam

@pytest.fixture
def cam_fast_dc_signal_4channels():
    wave = dummy_pulse(50, 0.1, 0, 5)

    waveforms = (
        wave,
        wave,
        wave,
        wave,
    )

    cam = DummySiPMCamera(
        n_pixels = 64*4,
        waveforms = waveforms,
        trigger_channels=[0,1],
        sampling_channels=[2,3],
        channels_time_resolution=[1,1,1,1]
    )
    cam.sampling_window_extent = [1024, 1024]
    cam.sampling_delay = [0,0]
    return cam

@pytest.mark.parametrize("xt", [0.0, 0.2])
@pytest.mark.parametrize("ap", [0.0, 0.2])
@pytest.mark.parametrize("n_ucells", [0, 1024])
def test_background_signal_channel_seed(cam_fast_dc_signal_4channels, xt, ap, n_ucells):
    """Test if all channels see the same background.
    I.e., the same background must be generated at each compute_signals() call.
    """
    cam = cam_fast_dc_signal_4channels

    cam.source = None
    cam.background_rate = cp.full((cam.n_pixels,), 0.5, dtype=cp.float32)
    cam.cross_talk = cp.full((cam.n_pixels,), xt, dtype=cp.float32)
    cam.afterpulse = cp.full((cam.n_pixels,), ap, dtype=cp.float32)
    cam.afterpulse_inv_tau = cp.full((cam.n_pixels,), 1./250., dtype=cp.float32)
    cam.inv_tau_recovery = cp.full((cam.n_pixels,), 1./200., dtype=cp.float32)

    cam.simulate_ucells = n_ucells > 0
    cam.n_ucells = cp.full((cam.n_pixels,), n_ucells, dtype=cp.int32)

    # Fixed windows
    cam.fixed_time_windows = True
    cam.time_windows = [
        cp.arange(0,2048,1, dtype=cp.float32),
        cp.arange(0,2048,1, dtype=cp.float32),
        cp.arange(0,2048,1, dtype=cp.float32),
        cp.arange(0,2048,1, dtype=cp.float32)
    ]
    cam.compute_signals([0])
    cam.compute_signals([1])
    cam.compute_signals([2,3])

    signals = {i: cam.get_channel_signals(i, reshape=True) for i in range(cam.n_channels)}

    for i in range(cam.n_channels-1):
        for j in range(cam.n_pixels):
            cp.testing.assert_allclose(signals[i][j], signals[i+1][j], atol=1e-6)

    # Compare pixels of each channel, they must be different
    channel = 0
    rng_weights = cp.random.randn(signals[channel].shape[1])
    fingerprints = cp.dot(signals[channel], rng_weights) 
    fingerprints.sort(axis=0)
    diffs = fingerprints[1:] - fingerprints[:-1]
    min_diff = float(cp.min(cp.abs(diffs)))
    assert min_diff > 1e-6

@pytest.mark.parametrize("ap", [0.0, 0.2])
@pytest.mark.parametrize("xt", [0.0, 0.2])
@pytest.mark.parametrize("n_ucells", [0, 1024])
def test_source_signal_channel_seed(cam_fast_dc_signal_4channels, xt, ap, n_ucells):
    """Test if all channels see the same background.
    I.e., the same background must be generated at each compute_signals() call.
    """
    cam = cam_fast_dc_signal_4channels

    # No background, xt and ap
    cam.background_rate = cp.full((cam.n_pixels,), 0.0, dtype=cp.float32)
    cam.cross_talk = cp.full((cam.n_pixels,), xt, dtype=cp.float32)
    cam.afterpulse = cp.full((cam.n_pixels,), ap, dtype=cp.float32)
    cam.afterpulse_inv_tau = cp.full((cam.n_pixels,), 1./250., dtype=cp.float32)
    cam.inv_tau_recovery = cp.full((cam.n_pixels,), 1./200., dtype=cp.float32)
    cam.sigma_ucells = cp.full((cam.n_pixels,), 0.1, dtype=cp.float32) # Big since when xt_and_ap is 0 this is the only source of randomness

    cam.n_ucells = cp.full((cam.n_pixels,), n_ucells, dtype=cp.int32)
    cam.simulate_ucells = n_ucells > 0

    # Same discharge times for all pixels
    t0s = cp.tile(cp.random.uniform(100.,200.,100), cam.n_pixels)
    map_ = cp.asarray([100*i for i in range(0,cam.n_pixels+1)])
    ucell_ids = cp.tile(cp.random.uniform(0,n_ucells,100), cam.n_pixels).astype(cp.int32)
   
    cam.source = (t0s, map_, ucell_ids) if cam.simulate_ucells else (t0s, map_)

    cam.base_seed = 0

    # Fixed windows
    cam.fixed_time_windows = True
    cam.time_windows = [
        cp.arange(0,2048,1, dtype=cp.float32),
        cp.arange(0,2048,1, dtype=cp.float32),
        cp.arange(0,2048,1, dtype=cp.float32),
        cp.arange(0,2048,1, dtype=cp.float32)
    ]
    cam.compute_signals([0])
    cam.compute_signals([1])
    cam.compute_signals([2,3])

    signals = {i: cam.get_channel_signals(i, reshape=True) for i in range(cam.n_channels)}

    # Compare channels -> they should be the same
    for i in range(cam.n_channels-1):
        for j in range(cam.n_channels-1):
            if i == j: continue
            cp.testing.assert_allclose(signals[i], signals[j], atol=1e-10)

    # Compare pixels of each channel, they must be different
    channel = 0
    rng_weights = cp.random.randn(signals[channel].shape[1])
    fingerprints = cp.dot(signals[channel], rng_weights) 
    fingerprints.sort(axis=0)
    diffs = fingerprints[1:] - fingerprints[:-1]
    min_diff = float(cp.min(cp.abs(diffs)))
    assert min_diff > 1e-6

@pytest.mark.parametrize("n_ucells", [0, 10000])
def test_background_signal_stats(cam_fast_dc_signals, n_ucells):
    """Test if the singal mean and the signal variance follow the Campbell's theorem. Cross-talk and asfterpulse are not included.
    Assuming that the waveforms are computed correctly, this test fails if the inter-pixel randomness is broken.
    """
    cam = cam_fast_dc_signals
    cam.timer.active = False
    cam.fixed_time_windows = True
    cam.time_windows = [
        cp.asarray([0], dtype=cp.float32),
        cp.arange(0,2048,1, dtype=cp.float32)
    ]
    cam.increment_seed = True
    cam.source = None
    cam.enable_camera_trigger = False
    cam.trigger_time = 0.
    cam.base_seed = 0

    # Simulate ucell with a very fast recovery time
    cam.inv_tau_recovery = cp.full((cam.n_pixels,), 1./10., dtype=cp.float32)
    cam.n_ucells = cp.full((cam.n_pixels,), n_ucells, dtype=cp.int32)
    cam.simulate_ucells = n_ucells > 0

    for background in [0.06, 0.1, 0.15]:
        cam.restart()
        cam.background_rate = cp.full((cam.n_pixels,), background, dtype=cp.float32)
        var = []
        mean = []
        for _ in range(100):
            cam.simulate_response()
            var.append(cp.var(cam.get_channel_signals(1)).get())
            mean.append(cp.mean(cam.get_channel_signals(1)).get())
        var = np.mean(var)
        mean = np.mean(mean)
        cp.testing.assert_allclose(cam.waveforms[1].get_squared_integral()*background, var, rtol=1e-3)
        cp.testing.assert_allclose(cam.waveforms[1].get_integral()*background, mean, rtol=1e-3)

def test_cross_talk_effect_on_background_signal(cam_fast_dc_signals):
    """Test if the singal mean and the signal variance follow the generalized Campbell's theorem.
    Cross-talk is included. Afterpuls is not included.
    Assuming that the waveforms are computed correctly, this test fails if the inter-pixel randomness is broken.
    """
    cam = cam_fast_dc_signals
    cam.base_seed = 0
    cam.timer.active = False
    cam.fixed_time_windows = True
    cam.time_windows = [
        cp.asarray([0], dtype=cp.float32),
        cp.arange(0,2048,1, dtype=cp.float32)
    ]
    cam.increment_seed = True
    cam.source = None
    cam.enable_camera_trigger = False
    cam.trigger_time = 0.

    background = 0.05
    cam.background_rate = cp.full((cam.n_pixels,), background, dtype=cp.float32)

    xts = np.asarray([0.0, 0.1, 0.2, 0.3])
    expected_var = cam.waveforms[1].get_squared_integral()*background/(1-xts)**3
    expected_mean = cam.waveforms[1].get_integral()*background/(1-xts)
    for i in range(xts.shape[0]):
        cam.restart()
        cam.cross_talk = cp.full((cam.n_pixels,), xts[i], dtype=cp.float32)
        var = []
        mean = []
        for _ in range(100):
            cam.simulate_response()
            var.append(cp.var(cam.get_channel_signals(1)).get())
            mean.append(cp.mean(cam.get_channel_signals(1)).get())
        var = np.mean(var)
        mean = np.mean(mean)
        cp.testing.assert_allclose(expected_mean[i], mean, rtol=1e-3)
        cp.testing.assert_allclose(expected_var[i], var, rtol=1e-3)