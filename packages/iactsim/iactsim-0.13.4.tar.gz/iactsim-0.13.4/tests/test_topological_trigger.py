import pytest
import cupy as cp
import numpy as np
from iactsim.electronics.signals.trigger_logic import topological_camera_trigger

CONSTANTS = {
    "WINDOW_SIZE": 50,
    "MODULE_DIM": 8,
    "N_MODULES": 5,
    "N_THREADS": 128,
    "SEED": 12345
}

SHAPES = {
    'line_v_3': [(0,0), (1,0), (2,0)],             
    'line_v_4': [(0,0), (1,0), (2,0), (3,0)],      
    'square_2x2': [(0,0), (0,1), (1,0), (1,1)],    
    'L_shape_4': [(0,0), (1,0), (2,0), (2,1)],     
    'T_shape_4': [(0,0), (1,0), (2,0), (1,1)],     
    'cross_5':   [(1,0), (0,1), (1,1), (2,1), (1,2)], 
    'disjoint_4': [(0,0), (0,1), (5,5), (5,6)]     
}

def xy_to_id(x, y, dim=8):
    """Convert (x, y) to flat pixel index."""
    if 0 <= x < dim and 0 <= y < dim:
        return x * dim + y
    return None

@pytest.fixture
def gpu_memory():
    """
    Allocates GPU memory. Returns a dict containing the arrays.
    """
    n_pixels = CONSTANTS["MODULE_DIM"] ** 2
    total_size = CONSTANTS["N_MODULES"] * n_pixels * CONSTANTS["WINDOW_SIZE"]
    
    # Inputs
    disc_signals = cp.zeros(total_size, dtype=cp.float32)
    
    # Pixel stack buffer
    ints_per_thread = n_pixels + (n_pixels // 32) + 2
    stack_size = CONSTANTS["N_MODULES"] * CONSTANTS["N_THREADS"] * ints_per_thread
    stack_buffer = cp.empty(stack_size, dtype=cp.int32)
    
    # Outputs
    mod_trig_sig = cp.zeros(CONSTANTS["N_MODULES"] * CONSTANTS["WINDOW_SIZE"], dtype=cp.float32)
    dummy_1 = cp.full((2,), -1, dtype=cp.int32)
    
    return {
        "disc_signals": disc_signals,
        "stack_buffer": stack_buffer,
        "mod_trig_sig": mod_trig_sig,
        "dummy_1": dummy_1,
    }

def run_trigger_kernel(gpu_mem, n_contiguous):
    """Launch the kernel with current memory and config."""
    topological_camera_trigger(
        (CONSTANTS["N_MODULES"],), (CONSTANTS["N_THREADS"],),
        (
            gpu_mem["disc_signals"], 
            n_contiguous, 
            gpu_mem["mod_trig_sig"],
            gpu_mem["dummy_1"], 
            gpu_mem["stack_buffer"],
            CONSTANTS["WINDOW_SIZE"], 
            CONSTANTS["MODULE_DIM"], 
            CONSTANTS["N_MODULES"], 
            CONSTANTS["SEED"]
        )
    )

def inject_shape(gpu_mem, mod_id, time, shape_coords, offset=(0,0)):
    """Injects a shape into the signals array."""
    dim = CONSTANTS["MODULE_DIM"]
    win = CONSTANTS["WINDOW_SIZE"]
    n_pix = dim * dim
    base_idx = mod_id * n_pix * win

    active_pixels = []
    for (sx, sy) in shape_coords:
        px, py = sx + offset[0], sy + offset[1]
        pid = xy_to_id(px, py, dim)
        if pid is not None:
            idx = base_idx + win * pid + time
            gpu_mem["disc_signals"][idx] = 1.0
            active_pixels.append(pid)
    return active_pixels

@pytest.mark.parametrize("shape_name, n_contiguous, should_trigger", [
    # Basic threshold checks
    ('line_v_3',   3, True),   # 3-pixel line, thresh 3 -> Pass
    ('line_v_3',   4, False),  # 3-pixel line, thresh 4 -> Fail
    ('line_v_4',   4, True),   # 4-pixel line, thresh 4 -> Pass
    ('square_2x2', 4, True),   # 4-pixel square, thresh 4 -> Pass
    ('cross_5',    4, True),   # 5-pixel cross, thresh 4 -> Pass
    ('cross_5',    6, False),  # 5-pixel cross, thresh 6 -> Fail
    
    # Topology logic checks
    ('disjoint_4', 3, False),  # 4 pixels total, but separated
    ('L_shape_4',  4, True),   # L-shape is contiguous
    ('T_shape_4',  4, True),   # T-shape is contiguous
])
def test_shapes_and_thresholds(gpu_memory, shape_name, n_contiguous, should_trigger):
    """
    Verifies that various shapes trigger (or don't) based on pixel count and contiguous logic.
    """
    mod_id = 0
    time = 20
    
    inject_shape(gpu_memory, mod_id, time, SHAPES[shape_name])
    
    run_trigger_kernel(gpu_memory, n_contiguous)
    
    # Check result
    res_idx = mod_id * CONSTANTS["WINDOW_SIZE"] + time
    triggered = gpu_memory["mod_trig_sig"][res_idx] > 0
    
    assert triggered == should_trigger, \
        f"Shape {shape_name} with n={n_contiguous} failed. Expected {should_trigger}, got {triggered}"


@pytest.mark.parametrize("offset_x, offset_y", [
    (0, 0),  # Top-Left
    (6, 6),  # Bottom-Right (for 2x2 shape in 8x8 grid)
    (0, 6),  # Edge
    (6, 0),  # Edge
    (3, 3)   # Center
])
def test_sliding_window_robustness(gpu_memory, offset_x, offset_y):
    """
    Verifies a 2x2 Square triggers correctly regardless of position in the module.
    """
    mod_id = 1
    time = 15
    n_contiguous = 4
    
    # Inject Square
    inject_shape(gpu_memory, mod_id, time, SHAPES['square_2x2'], offset=(offset_x, offset_y))
    
    run_trigger_kernel(gpu_memory, n_contiguous)
    
    res_idx = mod_id * CONSTANTS["WINDOW_SIZE"] + time
    triggered = gpu_memory["mod_trig_sig"][res_idx] > 0
    
    assert triggered, f"Failed to trigger at offset {offset_x},{offset_y}"


def test_inter_module_isolation(gpu_memory):
    """
    Verifies that pixels split between two modules do not sum up to trigger.
    """
    time = 25
    n_contiguous = 4
    
    # Module 0 Right edge
    inject_shape(gpu_memory, 0, time, [(0,0), (1,0)], offset=(6, 7))

    p_mod0 = [(0, 7), (1, 7)]
    inject_shape(gpu_memory, 0, time, p_mod0)

    # Module 1: Left Edge (2 pixels)
    p_mod1 = [(0, 0), (1, 0)]
    inject_shape(gpu_memory, 1, time, p_mod1)

    run_trigger_kernel(gpu_memory, n_contiguous)
    
    # Assertions
    idx_0 = 0 * CONSTANTS["WINDOW_SIZE"] + time
    idx_1 = 1 * CONSTANTS["WINDOW_SIZE"] + time
    
    assert gpu_memory["mod_trig_sig"][idx_0] == 0, "Module 0 triggered incorrectly on partial shape"
    assert gpu_memory["mod_trig_sig"][idx_1] == 0, "Module 1 triggered incorrectly on partial shape"


def test_time_isolation(gpu_memory):
    """
    Verifies that a shape spread across two different time slices does not trigger.
    """
    mod_id = 2
    n_contiguous = 4
    
    # Inject 2 pixels at T=10
    inject_shape(gpu_memory, mod_id, 10, [(0,0), (0,1)])
    
    # Inject 2 pixels at T=11 (physically adjacent to previous ones, but different time)
    inject_shape(gpu_memory, mod_id, 11, [(1,0), (1,1)])
    
    run_trigger_kernel(gpu_memory, n_contiguous)
    
    idx_10 = mod_id * CONSTANTS["WINDOW_SIZE"] + 10
    idx_11 = mod_id * CONSTANTS["WINDOW_SIZE"] + 11
    
    assert gpu_memory["mod_trig_sig"][idx_10] == 0, "Triggered at T=10 incorrectly"
    assert gpu_memory["mod_trig_sig"][idx_11] == 0, "Triggered at T=11 incorrectly"