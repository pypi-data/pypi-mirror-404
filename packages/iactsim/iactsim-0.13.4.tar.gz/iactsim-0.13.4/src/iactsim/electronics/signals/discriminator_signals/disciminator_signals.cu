// Copyright (C) 2024- Davide Mollica <davide.mollica@inaf.it>
// SPDX-License-Identifier: GPL-3.0-or-later
//
// This file is part of iactsim.
//
// iactsim is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// iactsim is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with iactsim.  If not, see <https://www.gnu.org/licenses/>.

//////////////////////////////////////////////////////////////////
//////////////////////////// Content /////////////////////////////
////// Kernels                                                  //
//                                                              //
// __global__ ideal_discriminator                               //
// __global__ count_pixel_triggers                              //
//                                                              //
//////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////

extern "C"{

__device__ __forceinline__ int get_lane_id() {
    // % 32
    return threadIdx.x & 0x1f; 
}

/**
 * @brief Simulates an ideal discriminator response.
 *
 * This kernel processes an input signal and generates a discriminator output signal
 * based on a given threshold.  It also applies a minimum pulse width filter.
 *
 * @param input_signal Input signal data with n_pixels X time_window_size elements.
 * @param output_signal Output discriminator signal data.
 *                      This array should be pre-allocated with the same size as 
 *                      the relevant portion of the input signal.
 *                      The array does not need to be initialized.
 * @param threshold Threshold value for each pixels. The length of this array should equal ``n_pixels``.
 * @param offset Discriminator offset for each pixel. The length of this array should equal ``n_pixels``.
 * @param time_slices_over_threshold Minimum number of consecutive time slices that the
 *                                   input signal must be above the threshold to be generate a trigger signal.
 * @param mask Array indicating whether a pixel is masked (1) or active (0).
 *             Masked pixels will not generate triggers.
 * @param time_window_size The number of time slices in the signal time window.
 * @param n_pixels The total number of pixels.
 *
 * @details
 * The kernel operates with one block per pixel. Each thread within a block processes a portion of the pixel time window.
 *
 * Discriminator Logic:
 *   
 *   - If the ``input_signal`` is above the pixel ``threshold`` AND the pixel is not masked (``mask[bid] == 0``) 
 *     the ``output_signal`` for that time slice is set to 1.0; otherwise the ``output_signal`` is set to 0.0.
 *
 * Pulse Width Filter:
 * 
 *   - After the initial discriminator signal is computed, a pulse-width filter is applied within each block (pixel) 
 *     to search for consecutive time slices where the ``output_signal`` is 1.0. If the number of consecutive slices 
 *     over threshold is less than ``time_slices_over_threshold``, those slices in the ``output_signal`` are reset to 0.0. 
 *     This effectively removes short pulses.
 *
 * Assumptions/Approximations:
 * 
 *   - Zero rising and falling time.
 * 
*/
__global__ void ideal_discriminator(
    const float* input_signal,
    float* output_signal,
    const float* threshold,
    const float* offset,
    int time_slices_over_threshold,
    const int* mask,
    int time_window_size,
    int n_pixels
)
{    
    // Current block
    int bid = blockIdx.x;

    // One block per pixel
    if (bid > n_pixels-1) return;

    // Current thread
    int thid = threadIdx.x;
    int base_idx = bid * time_window_size;

    // Load pixel constants to registers
    float pixel_threshold = threshold[bid] + offset[bid];
    bool pixel_masked = (mask[bid] == 1);

    // Allocate shared memory (time_window_size * sizeof(float))
    extern __shared__ float s_signal[];
    
    // Compute discriminator signal
    for (int i = thid; i < time_window_size; i += blockDim.x) {
        float val = input_signal[base_idx + i];
        if (val > pixel_threshold && !pixel_masked) {
            s_signal[i] = 1.0f;
        } else {
            s_signal[i] = 0.0f;
        }
    }
    
    // Wait until all the signals are computed then remove signals
    // with a duration shorter than ``time_slices_over_threshold``
    __syncthreads();
    if (thid == 0 && time_slices_over_threshold > 1) {
        int i = 0;
        while (i < time_window_size) {
            // Skip zeros
            if (s_signal[i] < 0.5f) {
                i++;
                continue;
            }

            // Found a '1', count the length of the pulse
            int k = 1;
            // Check bounds and value
            while ((i + k < time_window_size) && (s_signal[i + k] > 0.5f)) {
                k++;
            }

            // If pulse is too short, zero it out
            if (k < time_slices_over_threshold) {
                for (int j = 0; j < k; j++) {
                    s_signal[i + j] = 0.0f;
                }
            }

            // Jump past this pulse
            i += k;
        }
    }

    // Wait for thread 0 to finish
    __syncthreads();

    // Write to gloabal memory
    for (int i = thid; i < time_window_size; i += blockDim.x) {
        output_signal[base_idx + i] = s_signal[i];
    }
}


/**
 * @brief Counts the number of rising edges (pixel triggers) in a discriminator signal.
 *
 * This kernel function takes an array of signals and counts the number of times
 * the signal crosses a threshold (0.5) from below to above, indicating a rising edge
 * or pixel trigger.  It operates on a per-pixel basis, processing a window of
 * the signal for each pixel. The kernel assumes ideal rising edges with negligible rising time.
 *
 * @param counts An output array of integers, where the count of rising edges for
 *               each pixel will be stored.  This array should have a size of
 *               ``n_pixels``.  The counts are added to the existing values in
 *               this array.
 * @param signals A constant input array of floats representing the signals for
 *                each pixel. This array should contain ``n_pixels`` X ``window_size`` 
 *                elements, where each pixel signal occupies a contiguous block 
 *                of ``window_size`` elements.
 * @param window_size An integer representing the size of the window for each pixel signal.
 * @param n_pixels An integer representing the number of pixels to process.
 *
*/
__global__ void count_pixel_triggers(
    int* counts,
    const float* signals,
    int window_size,
    int n_pixels
)
{
    int bid = blockIdx.x;
    if (bid >= n_pixels) return;
    
    // Current thread
    int thid = threadIdx.x;
    int lane = get_lane_id(); // Thread index within the warp
    int warp_id = thid >> 5; // Warp index
    int base_idx = bid * window_size;

    // Thread local rising-edge counting
    int local_count = 0;
    for (int i = thid; i < window_size; i += blockDim.x) {
        // Skip bounds as per original logic
        if (i == 0 || i >= window_size - 1) continue;

        float curr = signals[base_idx + i];
        float prev = signals[base_idx + i - 1];

        if (prev < 0.5f && curr > 0.5f) {
            local_count++;
        }
    }

    // Use register shuffling (no shared memory needed)
    for (int offset = 16; offset > 0; offset /= 2) {
        local_count += __shfl_down_sync(0xFFFFFFFF, local_count, offset);
    }

    static __shared__ int warp_sums[32];
    // The first thread of each warp writes its partial sum
    if (lane == 0) {
        warp_sums[warp_id] = local_count;
    }
    __syncthreads();

    // Final sum done only by the first warp
    if (warp_id == 0) {
        int val = 0;
        // Only load for warps that actually existed in the block
        int num_warps = (blockDim.x + 31) >> 5;

        // We are in the warp0 and we have 32 lanes
        // Let the first num_warps lane load the data
        if (lane < num_warps) {
            val = warp_sums[lane];
        }

        // Reduce the partial sums with register shuffling
        for (int offset = 16; offset > 0; offset /= 2) {
            val += __shfl_down_sync(0xFFFFFFFF, val, offset);
        }

        // Single atomic write per pixel
        if (lane == 0) {
            counts[bid] += val;
        }
    }
}

/**
 * @brief Counts clock cycles between the last pixel trigger and the camera trigger.
 * 
 * This function simulates a time-to-digital converter (TDC) counter to measure the time
 * between the last trigger of each pixel and the camera trigger.
 *
 * The trigger time for each pixel is determined by counting the number of clock cycles
 * (time bins) between the camera trigger and the last rising edge of the pixel
 * discriminator signal. The counting starts from the beginning of the window and continues 
 * up to ``stop_clock`` cycles after the camera trigger clock ``camera_trigger_time_index``.
 *
 * The result, representing the time difference, is stored as an integer in an array
 * that emulates a register with ``register_n_bits`` bits (maximum of 32).
 *
 * @param trigger_times Output array of integers. Stores the calculated trigger times for each pixel.
 *                      The size of this array should be equal to ``n_pixels``.  Each element
 *                      represents the time difference in clock cycles, mapped to the range
 *                      of the ``register_n_bits``-bit register.  A value of 0 indicates no trigger
 *                      was found within the search window. A value of ``(2^register_n_bits) - 1``
 *                      indicates an overflow.
 * @param signals Input array of floats representing the discriminator signals for each pixel.
 *                The size of this array should be ``n_pixels * window_size``. The signal for
 *                pixel ``i`` is stored in ``signals[i * window_size]`` to ``signals[(i + 1) * window_size - 1]``.
 *                A rising edge (transition from < 0.5 to > 0.5) indicates a trigger.
 * @param camera_trigger_time_index Integer representing the clock cycle index at which the camera
 *                                  trigger occurs. This serves as the reference time (time 0+2^(register_n_bits-1)))
 *                                  for all pixel trigger time calculations.
 * @param stop_clock Integer representing the number of clock cycles after the camera trigger
 *                   during which the function will search for pixel triggers. The search window
 *                   for each pixel is from ``camera_trigger_time_index`` to
 *                   ``camera_trigger_time_index + stop_clock``.
 * @param register_n_bits Integer representing the number of bits in the simulated TDC register.
 *                        This determines the range of values that can be stored in ``trigger_times``.
 *                        Valid values are between 1 and 32 (inclusive).
 * @param window_size Integer representing the number of time bins in the discriminator signal
 *                    for each pixel.
 * @param n_pixels Integer representing the total number of pixels.
 *
 * @warning
 * * The function assumes ideal rising edges with a negligible rise time (<<clock).
 * * The function uses shared memory for inter-thread communication within a block.
 * * The size of the shared memory required is ``4 * (window_size + blockDim.x)`` bytes.
 * 
 */
__global__ void last_trigger_time_counter_from_camera_trigger(
    int* trigger_times,
    const float* signals,
    int camera_trigger_time_index,
    int stop_clock,
    int register_n_bits,
    int window_size,
    int n_pixels
)
{
    int bid = blockIdx.x;
    if (bid >= n_pixels) return;

    int tid = threadIdx.x;
    int lane = get_lane_id();
    int warp_id = tid >> 5;
    int base_idx = bid * window_size;

    // Determine the search limit based on stop_clock
    int limit_index = camera_trigger_time_index + stop_clock;
    if (limit_index > window_size) limit_index = window_size;

    int last_rising_edge = -1;

    // Grid stride Loop
    for (int i = tid; i < limit_index; i += blockDim.x) {
        if (i == 0) continue;

        float curr = signals[base_idx + i];
        float prev = signals[base_idx + i - 1];

        if (prev < 0.5f && curr > 0.5f) {
            if (i > last_rising_edge) {
                last_rising_edge = i;
            }
        }
    }

    // Warp reduction (fine maximum within a warp)
    for (int offset = 16; offset > 0; offset /= 2) {
        int other = __shfl_down_sync(0xFFFFFFFF, last_rising_edge, offset);
        if (other > last_rising_edge) last_rising_edge = other;
    }

    // Block reduction (fine maximum accross warps)
    static __shared__ int warp_max[32];
    
    if (lane == 0) {
        warp_max[warp_id] = last_rising_edge;
    }
    __syncthreads();

    if (warp_id == 0) {
        // Only the first warp works now
        int val = -1;
        int num_warps = (blockDim.x + 31) >> 5;
        
        // Load existing warp maximums
        if (lane < num_warps) {
            val = warp_max[lane];
        }

        // Reduce within the first warp
        for (int offset = 16; offset > 0; offset /= 2) {
            int other = __shfl_down_sync(0xFFFFFFFF, val, offset);
            if (other > val) val = other;
        }
        
        if (lane == 0) {
            if (val > -1) {
                // Pre-compute limits
                int half_extent = 1 << (register_n_bits - 1);
                int max_extent = 1 << register_n_bits;
                
                int dt = val - camera_trigger_time_index;
                
                // Overflow check
                if (dt < -half_extent || dt >= half_extent) {
                    trigger_times[bid] = max_extent - 1; // Overflow value
                } else {
                    trigger_times[bid] = dt + half_extent;
                }
            } else {
                trigger_times[bid] = 0; // No trigger found
            }
        }
    }
}

} // extern "C"