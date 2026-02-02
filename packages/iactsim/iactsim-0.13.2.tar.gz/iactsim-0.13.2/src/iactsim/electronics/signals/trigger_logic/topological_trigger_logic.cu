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
//                                                              //
////// Device functions                                         //
//                                                              //
// __device__ check_bit                                         //
// __device__ set_bit                                           //
// __device__ iterative_dfs_global                              //
// __device__ module_topological_trigger                        //
//                                                              //
////// Kernels                                                  //
//                                                              //
// __global__ topological_camera_trigger                        //
// __global__ count_topological_camera_triggers                 //
//                                                              //
//////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////

#include <cooperative_groups.h>
#include <limits.h> 

#include <curand_kernel.h>

namespace cg = cooperative_groups;

extern "C"{

/**
 * @brief Get the bit at position ``idx`` in the continuous block of memory of ``mask``.
 */
__device__ inline bool check_bit(const uint32_t* mask, int idx) {
    return (mask[idx / 32] >> (idx % 32)) & 1;
}

/**
 * @brief Set to 1 the bit at position ``idx`` in the continuous block of memory of ``mask``.
 */
__device__ inline void set_bit(uint32_t* mask, int idx) {
    mask[idx / 32] |= (1 << (idx % 32));
}

/**
 * @brief Performs an iterative Depth-First Search (DFS) to find contiguous triggered pixels.
 *
 * This function explores a group of contiguous pixels that have a signal value > 0.5.
 * The search uses 8-connectivity (checking horizontal, vertical, and diagonal neighbors).
 *
 * @param start_pixel  The linear index (0 to n_pixels-1) of the seed pixel to start the search.
 * @param signals      Pointer to the global signal array for the specific module and time window.
 *                     Data is accessed as ``signals[window_size * pixel_idx + time_slice]``.
 * @param stack_buffer Pointer to a slice of global memory dedicated to this thread DFS stack.
 *                     Must be large enough to hold ``dimension * dimension`` integers.
 * @param visited_mask Pointer to a slice of global memory acting as a bitmask for visited pixels.
 *                     Must be zeroed before calling this function for a new component search.
 * @param count        Pointer to an integer counter. On input, it holds the current component size (i.e. 1).
 *                     On output, it is updated with the total number of contiguous pixels found.
 * @param n_min        The threshold for component size. If ``count`` reaches this value during
 *                     search, the function returns immediately (early exit optimization).
 * @param dimension    The width/height of the square pixel grid (e.g., 8 for an 8x8 module).
 * @param window_size  The temporal window size (stride of the signal array).
 * @param time_slice   The specific time index within the window to check for signals.
 *
 * @note This function modifies ``visited_mask``, by setting bits for all reachable triggered pixels, and ``count`` in place.
 * 
 */
__device__ void iterative_dfs_global(
    int start_pixel,
    const float* signals,
    int* stack_buffer,
    uint32_t* visited_mask,
    int* count,
    int n_contiguous,
    int dimension,
    int window_size,
    int time_slice
)
{
    // Number of pixels in the stack
    int stack_pointer = 0;

    // Push the start pixel onto the stack
    stack_buffer[stack_pointer++] = start_pixel;

    // Set as visited
    set_bit(visited_mask, start_pixel);

    // Copy dimension for readability
    int dim = dimension;

    // Infinite loop until stack is empty
    while (stack_pointer > 0) {
        // Pop the top pixel from the stack
        // That is, read and decrement the counter
        int pixel = stack_buffer[--stack_pointer];

        int row = pixel / dim;
        int col = pixel % dim;

        // Check 3x3 window around (row, col)
        for (int dy = -1; dy <= 1; dy++) {
            for (int dx = -1; dx <= 1; dx++) {
                // Skip the current pixel
                if (dy == 0 && dx == 0) continue; 

                // Calculate neighbor coordinates
                int n_row = row + dy;
                int n_col = col + dx;

                // Boundary check
                if (n_row < 0 || n_row >= dim) continue;
                if (n_col < 0 || n_col >= dim) continue;

                int n_idx = n_row * dim + n_col;
                
                // Is it unvisited?
                if (!check_bit(visited_mask, n_idx)) {
                    // Mark as visited
                    set_bit(visited_mask, n_idx);

                    // Is it triggered?
                    if (signals[window_size * n_idx + time_slice] > 0.5f) {
                        // Update the contiguous counter
                        count[0]++;
                        // Push to the stack (to repeat the same search on it)
                        stack_buffer[stack_pointer++] = n_idx;
                        // Premature exit if the minimal number of contiguous pixels is reached
                        if (count[0] >= n_contiguous) return;
                    }
                }
            }
        }
    }
}

/**
 * @brief Determines if a module triggers at a specific time slice based on a topological trigger logic.
 *
 * This device function checks the discriminator signals of a specific module at a given ``time_slice``.
 * It iterates through the pixels of the module and, upon finding an active pixel (signal > 0.5),
 * launches an iterative Depth-First Search to determine the size of the continuous pixels of active pixels.
 *
 * If any group size equals or exceeds ``n_contiguous``, the function immediately returns ``true``.
 *
 * @param signals Pointer to the start of the discriminator signals array for the specific module being processed.
 *                Data is accessed as ``signals[window_size * pixel_idx + time_slice]``.
 * @param thread_workspace Pointer to a pre-allocated global memory buffer dedicated to the calling thread.
 *                         This workspace is used to store the DFS stack and the visited pixel bitmask,
 *                         avoiding local memory allocation, recursion overhead and stack limit increase.
 *                         The required size is ``n_pixels + (n_pixels / 32) + 2`` integers.
 * @param n_contiguous The minimum number of spatially contiguous active pixels required to generate a trigger.
 * @param dimension The linear dimension of the square module (e.g., 8 for an 8x8 grid).
 *                  The total number of pixels is ``dimension * dimension``.
 * @param window_size The size of the time window.
 * @param time_slice The specific time index within the window to evaluate.
 *
 * @return true If a contiguous group of at least ``n_contiguous`` active pixels is found at ``time_slice``.
 * @return false Otherwise.
 */
__device__ bool module_topological_trigger(
    const float* signals,
    int* thread_workspace,
    int n_contiguous,
    int dimension,
    int window_size,
    int time_slice
)
{
    int n_pixels = dimension * dimension;
    
    // Divide Workspace into:
    // 1. Stack (Int array, size = n_pixels)
    // 2. Visited Mask (Uint32 array, size = n_pixels / 32 + 1)
    
    int* stack_buffer = thread_workspace;
    
    // Visited mask. Align to 32 bits, just in case
    uint32_t* visited_mask = (uint32_t*)&stack_buffer[n_pixels];
    
    // Clear visited mask
    int mask_ints = (n_pixels + 31) / 32;
    for(int k=0; k < mask_ints; k++) {
        visited_mask[k] = 0;
    }

    // Check for the contiguous group of active pixels
    for (int i = 0; i < n_pixels; i++) {
        // If the pixel is triggered check how many contiguous pixels there are
        if (signals[window_size * i + time_slice] > 0.5f) {
            
            // Look only if has not been visited before
            if (!check_bit(visited_mask, i)) {
                
                // The triggered (central) pixel
                int count = 1;
                
                // Run DFS using the global buffers
                iterative_dfs_global(
                    i, 
                    signals, 
                    stack_buffer, 
                    visited_mask, 
                    &count, 
                    n_contiguous,
                    dimension, 
                    window_size, 
                    time_slice
                );
                
                // Check if there are enough contiguous pixels in the group
                if (count >= n_contiguous) return true;
            }
        }
    }
    // No trigger found
    return false;
}

/**
 * @brief Computes topological triggers for the entire camera and identifies the earliest trigger time and module.
 *
 * This kernel processes the discriminator signals for all modules in parallel. Each thread block handles a specific
 * module (determined by ``blockIdx.x``), and threads within the block iterate over the time window in a grid-stride loop.
 *
 * For every time slice, the kernel checks if the module satisfies the topological trigger condition (a contiguous group
 * of active pixels >= ``n_contiguous``) using ``module_topological_trigger``.
 *
 * The kernel performs two main outputs:
 * 
 *     1. **Signal Generation:** Populates ``module_trigger_signals`` with a 1.0/0.0 trace indicating trigger status for every module and time step.
 * 
 *     2. **Global Trigger Identification:** Finds the *earliest* trigger occurrence across the entire camera.
 * 
 *         - It uses atomic operations to find the global minimum of a packed 64-bit integer encoding ``(Time << 32) | (RandomSkip << 16) | (ModuleID)``
 * 
 *         - The "RandomSkip" is used to chose randomly a module when multiple modules trigger at the exact same time, preventing bias toward lower module IDs.
 * 
 *         - The result is unpacked into the ``trigger`` input array.
 *
 * @param disc_signals Pointer to the global signal array with layout ``[n_modules * n_pixels * window_size]``.
 *                     Contains the raw discriminator outputs (float).
 * @param n_contiguous The minimum number of contiguous pixels required to form a trigger.
 * @param module_trigger_signals Output array of size ``[n_modules * window_size]``.
 *                               Stores the binary trigger result (1.0 or 0.0) for each module/time.
 * @param trigger Output array of size 2 (int) (must be initialized to ``{-1, -1}`` before kernel launch):
 *                    - ``trigger[0]``: Time index of the earliest trigger (or -1 if none);
 *                    - ``trigger[1]``: Module ID of the earliest trigger (or 0 if none).
 * @param workspace Global memory buffer for DFS operations.
 *                  Must be large enough to hold stack and mask data for every thread.
 *                  Size: ``n_modules * n_threads * (n_pixels + n_pixels/32 + 2)``.
 * @param window_size The length of the readout window (number of time slices).
 * @param module_dimension The width/height of a module (e.g., 8).
 * @param n_modules Total number of modules in the camera.
 * @param seed Seed for the random number generator used to randomly pick a module ID when multiple modules trigger at the same time.
 *
 * @note This kernel requires ``cg::sync(grid)`` and thus must be launched using a cooperative launch API
 * if the grid size exceeds the device's maximum resident blocks, or if global synchronization is strictly required.
 * However, the current implementation only strictly requires grid sync for the final unpacking step on thread 0.
 * 
 * @warning
 * * ``trigger`` must be initialized to ``{-1, -1}`` before kernel launch;
 * * ``workspace_buffer`` must have a size of ``n_modules * n_threads * (n_pixels + n_pixels/32 + 2)``.
 * 
 */
__global__ void topological_camera_trigger(
    float* disc_signals,
    int n_contiguous,
    float* module_trigger_signals,
    int* trigger,
    int* workspace_buffer,
    int window_size,
    int module_dimension,
    int n_modules,
    long long int seed
)
{
    cg::thread_block block = cg::this_thread_block();
    cg::grid_group grid = cg::this_grid();
    
    int bid = blockIdx.x;
    int thid = block.thread_rank();

    // Generate random skip (one per module)
    __shared__ unsigned int random_module_skip;
    
    if (thid == 0) {
        curandStatePhilox4_32_10_t state;
        curand_init(seed, bid, 0, &state);
        // Only need 16 bits of randomness
        random_module_skip = curand(&state) & 0xFFFF;
    }
    // Wait for all threads
    block.sync();

    unsigned long long local_min = ~0ULL; 

    int n_pixels = module_dimension * module_dimension;
    
    // Per thread requirement: 
    //      stack (n_pixels ints) + visited mask (n_pixels/32 ints) + safety marging
    int ints_per_thread = n_pixels + (n_pixels / 32) + 2; 

    // Offset for this thread in global memory buffer
    long long thread_offset = ((long long)bid * blockDim.x + thid) * ints_per_thread;
    int* my_workspace_buffer = &workspace_buffer[thread_offset];

    // Pointer to signals for this module
    const float* my_signals = &disc_signals[n_pixels * bid * window_size];

    // Grid stride loop on time window
    for (int i = thid; i < window_size; i += blockDim.x) {
        // Look for a trigger in this time slice
        bool trg = module_topological_trigger(
            my_signals,
            my_workspace_buffer,
            n_contiguous,
            module_dimension,
            window_size,
            i 
        );
        
        // Update the module trigger signals
        module_trigger_signals[bid * window_size + i] = trg ? 1.0f : 0.0f;

        if (trg) {
            // High 32 bits: trigger time slice
            unsigned long long time_part = (unsigned long long)i << 32;
            // Mid  16 bits: random skip
            unsigned long long skip_part = (unsigned long long)random_module_skip << 16;
            // Low  16 bits: triggered module ID
            unsigned long long mod_part  = (unsigned long long)(bid & 0xFFFF);
            
            // Create a value: MSB | time | random | module | LSB
            unsigned long long entry = time_part | skip_part | mod_part;
            
            // At this point the entry value is dictated by the time_slice
            // If two trigger occurs at the same time in different modules
            // the module with the smallest skip_part will be chosen.
            if (entry < local_min) local_min = entry;
        }
    }

    // Get the minimum value within the warp
    unsigned mask = __activemask(); // Get active threads in the warp
    for (int offset = 16; offset > 0; offset /= 2) {
        // Move to the lower lane
        unsigned long long other = __shfl_down_sync(mask, local_min, offset);
        if (other < local_min) local_min = other;
    }

    // If a min has been found use thread0, which holds the minimum value
    if (thid == 0 && local_min != ~0ULL) {
        // Update global memory with the minimum value
        atomicMin((unsigned long long*)trigger, local_min);
    }

    // Unpacking the local value
    cg::sync(grid);
    if (blockIdx.x == 0 && threadIdx.x == 0) {
        // ``trigger`` now holds the packed value
        // Read it as an ULL and unpack it if necessary
        unsigned long long packed = *((unsigned long long*)trigger);
        
        // No Trigger
        if (packed == ~0ULL) {
            trigger[0] = -1;
            trigger[1] = -1;
        // Trigger -> unpack time and module ID
        } else {
            // High 32 bits -> trigger time
            int time_found = packed >> 32;
            
            // Last 16 bit (0xFFFF) -> module ID
            int mod_found  = packed & 0xFFFF; 

            // Write to global memory
            trigger[0] = time_found;       
            trigger[1] = mod_found;
        }
    }
}

/**
 * @brief Counts the number of camera triggers within a time window.
 *
 * This kernel computes a global camera trigger signal by performing a logical OR operation across 
 * all module trigger signals for each time slice. If *any* module is triggered at time ``t`` (signal > 0.5), 
 * the camera is considered triggered at time ``t``.
 *
 * After constructing this global signal in shared memory, the kernel identifies and counts the number 
 * of rising edges (transitions from logical 0 to 1).
 *
 * The kernel is designed to operate within a single thread block.
 *
 * @param counts Pointer to an integer global counter. The detected number of triggers is added to this 
 *               value using atomic operations. Ensure this is initialized to 0 before use.
 * @param signals Pointer to the global array of module trigger signals. 
 *                Layout is assumed to be ``[n_modules * window_size]``, accessed as 
 *                ``signals[module_idx * window_size + time_idx]``.
 * @param window_size The number of time slices in the time window.
 * @param n_modules The total number of modules in the camera.
 *
 * @warning
 * * Shared Memory: this kernel requires dynamic shared memory. The kernel launch must allocate 
 *   at least ``window_size * sizeof(float)`` bytes of dynamic shared memory.
 * * Single Block: this kernel explicitly checks ``blockIdx.x``. Computation only occurs in Block 0. Launching with ``gridDim.x > 1`` is valid but wasteful.
 * * Edge Cases: a rising edge is defined as ``signal > 0.5`` and ``previous <= 0.5``. 
 * * ``counts`` must be initialized to 0 before kernel launch.
 * 
 */
__global__ void count_topological_camera_triggers(
    int* counts, const float* signals, int window_size, int n_modules
)
{
    if (blockIdx.x > 0) return;

    // Allocate shared memory
    extern __shared__ float shared_buffer[];
    float* camera_trigger = shared_buffer;
    
    int thid = threadIdx.x;

    // Generate the camera trigger signal
    for (int i = thid; i < window_size; i += blockDim.x) {
        bool triggered = false;
        for (int j = 0; j < n_modules; j++) {
            if (signals[j * window_size + i] > 0.5f) {
                triggered = true;
                break;
            }
        }
        camera_trigger[i] = triggered ? 1.0f : 0.0f;
    }
    // Wait all threads
    __syncthreads();

    // Count the number of rising edges for this thread
    int local_rising_edges = 0;
    for (int i = thid; i < window_size; i += blockDim.x) {
        if (i == 0) continue;
        if (camera_trigger[i-1] < 0.5f && camera_trigger[i] > 0.5f) local_rising_edges++;
    }

    // Sum the number of rising edges across all active threads in each warp
    unsigned mask = __activemask();
    for (int offset = warpSize / 2; offset > 0; offset /= 2) 
        local_rising_edges += __shfl_down_sync(mask, local_rising_edges, offset);

    // Share the number of rising edges across all warps (done by a thread per warp)
    static __shared__ int warp_sums[32]; 
    if ((thid % 32) == 0) warp_sums[thid / 32] = local_rising_edges;
    __syncthreads();

    // The first warp sums all numbers of rising edges
    if (thid < 32) {
        int sum = (thid < (blockDim.x / 32 + (blockDim.x%32?1:0))) ? warp_sums[thid] : 0;
        for (int offset = warpSize / 2; offset > 0; offset /= 2) 
            sum += __shfl_down_sync(0xFFFFFFFF, sum, offset);
        
        // Update the global counter
        if (thid == 0) atomicAdd(counts, sum);
    }
}

} // extern "C"