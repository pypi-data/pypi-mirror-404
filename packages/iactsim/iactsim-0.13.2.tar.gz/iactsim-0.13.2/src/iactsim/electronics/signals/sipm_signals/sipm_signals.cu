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
// __device__ interp1d_text                                     //
// __device__ borel_generator                                   //
// __device__ waveform_normalization                            //
// __device__ poisson_interarrival_time                         //
// __device__ get_lane_id                                       //
// __device__ block_prefix_sum                                  //
// __device__ accumulate_waveform                               //
// __device__ update_cell_logic                                 //
// __device__ extract_xt_ucell                                //
//                                                              //
////// Kernels                                                  //
//                                                              //
// __global__ sipm_signals                                      //
// __global__ sipm_signals_w_ucells                             //
//                                                              //
//////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////

#include <curand_kernel.h>
#include <cuda_fp16.h>

extern "C"{

/**
 * @brief Performs linear interpolation on a 1D texture.
 *
 * @param x The coordinate at which to interpolate.
 * @param inv_dx The inverse of the spacing between texture elements (1/dx).
 * @param start_x The starting coordinate of the texture data.
 * @param tex The CUDA texture object to sample from.
 *
 * @return The interpolated value from the texture.
 */
__device__ float interp1d_text(float x, float inv_dx, float start_x, cudaTextureObject_t& tex) {
    float u = (x-start_x)*inv_dx;
    return tex1D<float>(tex, u+0.5f);
}

/**
 * @brief Generates a random variate from the Borel distribution using inversion sampling.
 *
 * This function implements the inversion sampling method to generate a random
 * number from the Borel distribution with parameter ``l`` (lambda).
 *
 * @param l The parameter of the Borel distribution (lambda).  Must be in the range (0, 1).
 * @param s A reference to a ``curandStatePhilox4_32_10_t`` object, representing the
 *          state of the Philox4x32-10 pseudo-random number generator. This state
 *          must be initialized before calling this function.
 *
 * @return A random float from the Borel distribution with parameter ``l``.
 *          Returns 1.0f if ``l`` is very small (< 1e-4f).
 *
 * @details
 * The function generates a uniform random number ``u`` and accumulates the probabilities
 * ``P(k)`` until the cumulative sum exceeds ``u``. To avoid expensive calls to the
 * gamma function in each step, it uses the recurrence relation:
 *
 *   P(k+1) / P(k) = lambda * exp(-lambda) * (1 + 1/k)^(k-1)
 *
 * This allows for computation of successive probabilities starting from P(1).
 */
__device__ float borel_generator(float l, curandStatePhilox4_32_10_t &s)
{
    if (l<1e-4f) return 1.f;

    // Use a recurrence relation that can be derived from the borel pmf
    //
    // P(n+1)/P(n) = l * exp(-l) * (1 + 1/k)^(k-1) 
    //
    float u = curand_uniform(&s);

    // Start from P(0)
    float p = __expf(-l);

    // Perform the first check right away (no xt discarghes)
    if (u <= p) {
        return 1.f;
    }

    // Precompiute the constant part of the recurrence factor
    float lexpl = p*l;

    // We ar going to compute P(k+1)
    // staring from P(1)
    float k = 1.f;
    float current_cdf = p;

    while (k < 1000.f) {
        float recurrence_factor = lexpl * __powf(1.0f + 1.0f/k, k - 1.0f);
        p *= recurrence_factor;
        current_cdf += p;
        if (u <= current_cdf) {
            return k + 1.f;
        }
        
        // We do not need this level of precision
        if (p < 1e-6f) return k + 1.f;

        k += 1.f;
    }

    // Unlikely
    return k;
}

/**
 * @brief Calculates a normalization factor for a waveform, accounting for prompt cross-talk and micro-cells gain dispersion.
 *
 * This function simulates the effects of cross-talk and variations in micro-cell gain
 * on the overall normalization of a waveform.
 *
 * @param state A reference to a ``curandStatePhilox4_32_10_t`` object, representing the
 *              state of the Philox4x32-10 pseudo-random number generator.  This state
 *              must be initialized before calling this function.
 * @param n_discharges  The number of events to simulate (main discharge + xt discharges).  This effectively controls
 *              how many random samples are summed to produce the normalization factor.
 * @param std_ucells The standard deviation of the micro-cell gain.  This parameter
 *                   scales the contribution of each random sample.
 *
 * @return The calculated normalization factor (a float).
 *
 * @details
 * The normalization factor is computed as the sum of ``n_discharges`` independent random
 * variables, each drawn from a normal distribution with mean 1.0 and standard
 * deviation ``std_ucells``.
 *
 */
__device__ float waveform_normalization(curandStatePhilox4_32_10_t &state, float n_discharges, float std_ucells)
{
    float normalization_factor = 0.0f;
    for (int k=0; k<(int)n_discharges; k++) normalization_factor += fmaf(curand_normal(&state), std_ucells, 1.0f);
    return normalization_factor;
}

/**
 * @brief Generates a Poisson inter-arrival time.
 *
 * This function calculates a random inter-arrival time from an exponential
 * distribution, which is equivalent to the inter-arrival times in a Poisson process.
 *
 * @param state A reference to a ``curandStatePhilox4_32_10_t`` object, representing the
 *              state of the Philox4x32-10 pseudo-random number generator. This state
 *              must be initialized before calling this function.
 * @param inv_bkg_rate The inverse of the background rate of the Poisson process.
 *                     This represents the mean inter-arrival time.
 *
 * @return A random float representing the inter-arrival time.
 * 
 */
__device__ float poisson_interarrival_time(curandStatePhilox4_32_10_t &state, float inv_bkg_rate)
{
    return -fmaf(__logf(curand_uniform(&state)),  inv_bkg_rate, 0.f);
}

__device__ __forceinline__ int get_lane_id() {
    // threadIdx.x % 32
    return threadIdx.x & 0x1f; 
}

/**
 * @brief Block-level parallel prefix sum (cumulative sym).
 * 
 * This function converts all the generated interarrival times 
 * into an absolute timing:
 *      
 * E.g:
 *     
 *     - [dt0, dt1, dt2] -> [dt0, dt0+dt1, dt0+dt1+dt2]
 * 
 * @param pe_dt A thread generated inter-arrival time.
 * @param shared_temp A temporary array where to compute all warps cumulative sum.
 * 
 */
__device__ float block_prefix_sum(float pe_dt, float* shared_temp) {
    // Cumulative sum of the whole warp
    // At each step get 'pe_dt' from the warp 'lane - offset'
    // and sum its own 'pe_dt' only if the offset is valid
    for (int offset = 1; offset < 32; offset *= 2) {
        float up = __shfl_up_sync(0xFFFFFFFF, pe_dt, offset);
        if (get_lane_id() >= offset) 
            pe_dt += up;
    }
    
    // Write the sum (the last element of the cumulative) to shared memory
    if (get_lane_id() == 31) 
        shared_temp[threadIdx.x >> 5] = pe_dt;
    
    // Wait until all warps have finished
    // Now shared_temp[warp0,warp1,...,warpN] is filled 
    // with the maximum temporal extention of each warp
    __syncthreads();
    
    // Just the first warp
    if (threadIdx.x < 32) {
        // Here threadIdx.x is equivalent to the lane
        int lane = threadIdx.x;
        // so this skips non-existing wraps
        int n_warps = blockDim.x >> 5;
        // Get from shared memory
        float warp_sum = (lane < n_warps) ? shared_temp[lane] : 0.0f;

        // Cumulative sum of warps
        for (int offset = 1; offset < 32; offset *= 2) {
            float up = __shfl_up_sync(0xFFFFFFFF, warp_sum, offset);
            if (lane >= offset)
                warp_sum += up;
        }

        // Write to shared memory
        if (lane < n_warps)
            shared_temp[lane] = warp_sum;
    }
    // Now shared_temp[warp0,warp1,...,warpN] is filled
    // with the actual last time of each warp (e.g. [0.007, 0.04, ..., 1.2])
    __syncthreads();
    
    // Each thread has a relative (to the warp) time offset pe_dt
    // Now add the cumulative sum of warps to have the absolute timing
    // (i.e. add the last cumulative time of the previous warp, in shared memory)
    if (threadIdx.x >= 32)
        pe_dt += shared_temp[threadIdx.x / 32 - 1];
    
    // This is the poissonian-event time in the specified time window
    return pe_dt;
}

/**
 * @brief Helper to add a waveform to the shared memory buffer.
 */
__device__ void accumulate_waveform(
    float* sm_signal,           // Shared memory buffer
    int n_window,               // Size of the window
    float t_event,              // Time of the event
    float amplitude,            // Amplitude (in photo-electrons unit)
    const float* t_window,      // Time window
    float inv_dt_waveform,      // Waveform properties
    float t_start_waveform,     // Waveform properties
    cudaTextureObject_t tex,    // Waveform texture
    int thid,                   // Thread ID
    int bdim                    // Block dim
) 
{
    for (int i = thid; i < n_window; i += bdim) {
        float tdiff = t_window[i] - t_event;

        // Skip if we are before the event
        if (tdiff < 0.0f) continue;

        float single_waveform = interp1d_text(
            tdiff,
            inv_dt_waveform,
            t_start_waveform,
            tex
        );

        // Update waveform
        sm_signal[i] += single_waveform * amplitude;
    }
}

/**
 * @brief Computes the formed SiPM signals.
 *
 * This kernel function simulates the response of Silicon Photo-Multipliers (SiPMs)
 * by superimposing single photo-electron (PE) waveforms based on PE arrival time,
 * SiPM cross-talk, SiPM microcells gain dispersion and SiPM PE-background noise.  
 * It operates on a per-pixel and per-channel basis, assigning a CUDA block per pixel per channel.
 *
 * @param windows Array of time windows for each channel.  Defines the time ranges
 *                over which signals are computed. ``windows[windows_map[channel] : windows_map[channel+1]]``
 *                is the time window for ``channel``.
 * @param windows_map Array indicating the starting  and ending index of the time window for each channel
 *                      within the ``windows`` array.
 * @param signals Output array where the computed SiPM signals are stored.  The signal for
 *                a given channel and pixel is stored in a contiguous block.
 *                ``signals[start_signals[channel] + pixel_id * n_window : start_signals[channel] + (pixel_id + 1) * n_window]``
 *                where n_window = windows_map[channel+1] - windows_map[channel].
 *                The array does not need to be initialized before the kernel invocation.
 * @param signals_map Array indicating the starting index and ending index of each channel inside the array signals.
 * @param n_channels Number of channels.
 * @param t0s Array of discharge times for each pixel.
 * @param map Array that maps pixel indices to the range of their corresponding
 *            discharge times in the ``t0s`` array.  Specifically, ``t0s[map[pixel_id]:map[pixel_id+1]]``
 *            provides the discharge times for ``pixel_id``.
 * @param waveforms Array containing the texture pointer of all channel waveforms.
 * @param inv_dt_waveforms Array containing the inverse of the time spacing (dt) for each
 *                         waveform.
 * @param t_start_waveforms Array indicating the starting time of each waveform.
 * @param gains Array containing the pulse peak amplitued for each pixel for each channel (n_pixels*n_channels size)
 * @param xt Array of cross-talk probabilities for each pixel.  This represents the probability
 *           that a discharge in one microcell will trigger a discharge in an adjacent microcell.
 * @param std_ucells Array of microcell gain dispersions for each pixel. This models the
 *                   variation in the charge produced by different microcells for a single photon.
 * @param mask Array indicating whether a pixel is masked (1) or active (0). Masked pixels
 *             will have zero signal.
 * @param inv_bkg_rate Array of inverse background rates for each pixel (in units of time).  This is
 *                     used to generate background noise events.
 * @param bkg_start Start time for background noise generation.
 * @param bkg_end End time for background noise generation.
 * @param seed Array of random number generator seeds, one for each pixel.
 * @param n_pixels Number of pixels.
 *
 * 
 * @warning
 * 1. The number of blocks must be at least ``n_pixels*n_channels`` (i.e. a block per pixel per channel)
 * 2. The size of the shared memory buffer must be equal to ``(max_window_size+n_threads*2 + 32) * sizeof(float)``.
 *
 * @details
 * The kernel is launched with a 1D grid of blocks, where each block is responsible for
 * computing the signal for a single (pixel, channel) combination.  Each block uses
 * shared memory (``shared_buffer``) to store the intermediate signal, improving performance
 * by reducing global memory accesses.
 * 
 * The signal computation involves the following steps:
 * 
 * 1. Determine the block assigned channel and pixel. Initialize the shared memory buffer to zero.
 * 
 * 2. Input signal
 * 
 *      2a. Initialize a ``curandStatePhilox4_32_10_t`` random number generator for the pixel using the provided seed.
 *          Each pixel has a unique seed per event. This allows the signals of each channel to be computed in different stages.
 * 
 *      2b. Iterate through the photon arrival times associated with the current pixel. For each photon:
 *   
 *          - calculate the number of cross-talk photons using a Borel distribution;
 *          - calculate the microcell gain variation, incorporating gain dispersion using a normal distribution;
 *          - superimpose the single-photon waveform onto the shared memory buffer, interpolating the channel waveform.
 * 
 * 3. Background signal
 * 
 *      3a. Re-initialize the ``curandStatePhilox4_32_10_t`` random number generator with a seed per thread.
 *
 *      3b. Heach thread generates a background noise event extracting
 *          - a number of cross-talk photons;
 *          - a micro-cell gain;
 *          - a poissoninan inter-arrival time;
 *
 *      3c. The actual time is computed with a parallel cumulative sum of all extracted times.
 *          All generated events are stored in shared memory.
 * 
 *      3d. Generated events are processed one-by-one. The signal accross the time-window 
 *          is updated in parallel in the shared memory buffer.
 * 
 * 4. Copy the computed signal from the shared memory buffer to the global ``signals`` array.
 * 
 */
__global__ void sipm_signals(
    // Time windows
    const float* windows, // windows where to compute the signals for each channel
    const int* windows_map, // where the window of each channel starts and ends in the ``windows`` array
    // Channels signals
    float* signals, // computed signals
    const int* signals_map, // where the signals of each channel starts and ends in ``signals``
    bool* skip_channel,
    int n_channels, // number of channels
    // Arrival times
    const float* t0s, // discharge times
    const int* map, // discharge times of pixel n: t0s[map[n]:map[n+1]]
    // Waveforms
    const unsigned long long* textures, // one for each channel
    const float* inv_dt_waveforms, // invers of the x-spacing of each waveform
    const float* t_start_waveforms, // start time of each waveform
    const float* gains, // gain of each pixel for each channel
    // SiPM details
    const float* xt, // cross-talk of each pixel
    const float* std_ucells, // ucells gain dispersion of each pixel
    const int* mask, // pixel mask
    const float* ap_prob, // Afterpulsing probability 
    const float* inv_tau_ap, // 1.0 / AP_time_constant
    const float* inv_tau_rec, // 1.0 / recovery_time_constant
    // Background
    const float* inv_bkg_rate, // inverse of the background rate for each pixel
    float bkg_start, // time from which generate backgorund
    float bkg_end, // time at which stop background generation
    // Random seed
    unsigned long long* seed, // seed for each pixel
    // Number of pixels
    int n_pixels
)
{
    // Current block
    int bid = blockIdx.x;

    // A block for each pixel channel -> n_pixels*n_channels blocks
    if (bid > n_channels*n_pixels - 1) return;

    // Channel assigned to this block
    int channel = bid / n_pixels;

    if (skip_channel[channel]) return;

    // Pixel assigned to this block
    int pixel_id = bid - n_pixels * channel;

    // Channel window length
    int n_window = windows_map[channel+1] - windows_map[channel];

    // Pointer to the current channel signal
    float* y = &signals[signals_map[channel]];

    // Pointer to the current channel time-window
    const float* t = &windows[windows_map[channel]];

    // Shared memory allocation
    // The size is:
    //    shared_mem_size = (max_window_size+n_threads*3 + 32) * sizeof(float)
    extern __shared__ float shared_mem[];

    // Pointer to the shared channel signal
    float* sm_signal = shared_mem;

    // Pointers for batch queues
    float* queue_t = (float*)&sm_signal[n_window]; // Generated times
    float* queue_amp = (float*)&queue_t[blockDim.x]; // Generated amplitudes
    float* queue_n_xt = (float*)&queue_amp[blockDim.x]; // Generated number of xt discharges (including primary)
    float* scan_temp = (float*)&queue_n_xt[blockDim.x]; // Temporary array for cumulative time

    // Initialize shared signal to 0
    for (int i = threadIdx.x; i < n_window; i += blockDim.x) {
        sm_signal[i] = 0.0f;
    }

    // Write into global memory zero-filled waveforms for masked pixels
    if (mask[pixel_id] == 1) {
        for (int i = threadIdx.x; i < n_window; i += blockDim.x) {
             y[pixel_id*n_window + i] = 0.0f;
        }
        return;
    }

    // RNG initialization used when multiple threads operate on the same event
    curandStatePhilox4_32_10_t pix_state;
    curand_init(seed[pixel_id], blockDim.x, 0, &pix_state);

    // RNG initialization used when each thread operate on a different event
    curandStatePhilox4_32_10_t state;
    curand_init(seed[pixel_id], threadIdx.x, 0, &state);

    // Load constants to registers
    float local_xt = xt[pixel_id];
    float local_std_ucells = std_ucells[pixel_id];
    float local_ap_prob = ap_prob[pixel_id];
    float local_inv_tau_ap = inv_tau_ap[pixel_id];
    float local_inv_tau_rec = inv_tau_rec[pixel_id];

    cudaTextureObject_t current_waveform_texture = textures[channel];
    float inv_dt_waveform = inv_dt_waveforms[channel];
    float t_start_waveform = t_start_waveforms[channel];

    // Loop over source photo-electrons arrival time splitting into multiple batches
    int j_start = map[pixel_id];
    int j_end = map[pixel_id+1];
    int n_events = j_end - j_start;

    // Process n_threads PEs per cycle
    for (int batch_offset = 0; batch_offset < n_events; batch_offset += blockDim.x) 
    {
        int thid = threadIdx.x;
        int idx = j_start + batch_offset + thid;
        // How many PEs are in this buch
        int pes_in_batch = min(blockDim.x, n_events - batch_offset);

        // Each thread calculates properties for one photon in the batch
        if (thid < pes_in_batch) {
            // Get arrival time
            float t0 = t0s[idx];
            // Number of cross-talk photo-electrons
            float n_xt = borel_generator(local_xt, state);
            // Micro-cells gain dispersion
            float xt_pe = waveform_normalization(state, n_xt, local_std_ucells);

            // Enqueue this pe
            queue_t[thid] = t0;
            queue_amp[thid] = xt_pe;
            queue_n_xt[thid] = n_xt;
        }
        
        // Wait for the queue to be filled
        __syncthreads();
        
        // Iterate through the filled queue
        for (int k = 0; k < pes_in_batch; k++) {
            float t_event = queue_t[k];
            float pe_amp = queue_amp[k];
            int n_xt = (int)queue_n_xt[k];

            // Each thread help computing the signal of the whole window
            accumulate_waveform(
                sm_signal,
                n_window,
                t_event,
                pe_amp,
                t, 
                inv_dt_waveform,
                t_start_waveform, 
                current_waveform_texture,
                threadIdx.x,
                blockDim.x
            );
            
            // Afterpulse
            if (local_ap_prob > 1e-6f) {
                for (int xt_i=0; xt_i<n_xt; xt_i++) {
                    if (curand_uniform(&pix_state) < local_ap_prob) {
                        // Generate after-pulse delay
                        float dt_ap = -__logf(curand_uniform(&pix_state)) / local_inv_tau_ap;
                        float t_ap = t_event + dt_ap;
                        float ap_amp = 1.0f - __expf(-dt_ap * local_inv_tau_rec);
                        
                        accumulate_waveform(
                            sm_signal,
                            n_window,
                            t_ap,
                            ap_amp,
                            t, 
                            inv_dt_waveform,
                            t_start_waveform, 
                            current_waveform_texture,
                            threadIdx.x,
                            blockDim.x
                        );
                    }
                }
            }
        }
        // Wait for accumulation to finish before overwriting queue in next batch
        __syncthreads();
    }

    // Load constants to registers
    float local_inv_bkg_rate = inv_bkg_rate[pixel_id];
    float current_batch_start_time = local_inv_bkg_rate > 1e6f ? bkg_end + 1.f : bkg_start;

    /////// Batched background loop ///////
    while (current_batch_start_time < bkg_end) {
        
        // Each thread generates:
        //    - a poisson inter-arrival time
        //    - the number of borel discharge
        //    - the gain of the micro-cell
        float pe_dt = poisson_interarrival_time(state, local_inv_bkg_rate);
        float pe_n_xt = borel_generator(local_xt, state);
        float pe_amp = waveform_normalization(state, pe_n_xt, local_std_ucells);

        // Parallel prefix sum to get the correct time for this thread
        float total_dt = block_prefix_sum(pe_dt, scan_temp);
        float batch_t = current_batch_start_time + total_dt;

        // Store the time generated by this thread
        queue_t[threadIdx.x] = batch_t;
        queue_amp[threadIdx.x] = pe_amp;
        queue_n_xt[threadIdx.x] = pe_n_xt;
        
        // Wait untile all times are generated
        __syncthreads();

        // Update the while loop (latest time at the last thread id)
        float last_time = queue_t[blockDim.x - 1]; 
        current_batch_start_time = last_time;

        // Iterate through all the generated times
        // now that they are visibile to all threads
        for (int k = 0; k < blockDim.x; k++) {
            float t_noise = queue_t[k];
            float xt_pe = queue_amp[k];
            int n_xt = (int)queue_amp[k];

            if (t_noise > bkg_end) break;

            // Update the waveform
            accumulate_waveform(
                sm_signal,
                n_window,
                t_noise,
                xt_pe,
                t, 
                inv_dt_waveform,
                t_start_waveform, 
                current_waveform_texture,
                threadIdx.x,
                blockDim.x
            );
        
            // Afterpulse
            if (local_ap_prob > 1e-6f) {
                for (int k=0; k<n_xt; k++) {
                    if (curand_uniform(&pix_state) < local_ap_prob) {
                        // Generate AP delay
                        float dt_ap = -__logf(curand_uniform(&pix_state)) / local_inv_tau_ap;
                        float t_ap = t_noise + dt_ap;
                        float ap_amp = 1.0f - __expf(-dt_ap * local_inv_tau_rec);
                        // Update the waveform
                        accumulate_waveform(
                            sm_signal,
                            n_window,
                            t_ap,
                            ap_amp,
                            t, 
                            inv_dt_waveform,
                            t_start_waveform, 
                            current_waveform_texture,
                            threadIdx.x,
                            blockDim.x
                        );
                    }
                }
            }
        } // current butch done: sync end go to the next
        __syncthreads();
    }

    // Write back to global memory
    float local_gain = gains[bid];
    for (int i = threadIdx.x; i < n_window; i += blockDim.x) {
        y[pixel_id*n_window + i] = sm_signal[i] * local_gain;
    }
}

/**
 * @brief Check the last discharge time of a microcell. Return the normalized amplitude of the response.
 * Last discarge time are relative to a t_ref to increase __half precision.
 *
 */
__device__ float update_cell_logic(
    float t_now, int cell_id, float inv_tau_rec, __half* last_discharge_times, float u_prob, float t_ref
) {
    // Get the last ucell discharge time
    float t_last = __half2float(last_discharge_times[cell_id]) + t_ref;

    float dt = t_now - t_last;

    // The cell fired in the future (unlikely)
    if (dt < 0.0f) return 0.f;

    // Recovery factor
    float rec_factor = 1.0f - __expf(-dt * inv_tau_rec);
    
    // Breakdown probability decrease (linear)
    if (u_prob > rec_factor) {
        return 0.0f;  
    }

    // Update last discharge time
    last_discharge_times[cell_id] = __float2half(t_now - t_ref);
    
    return rec_factor;
}

/**
 * @brief Selects a neighboring microcell for cross-talk discharge.
 *
 * This function determines the location of a cross-talk discharge given the location
 * of the primary discharge. It models the spatial distribution of cross-talk
 * using a normal distribution centered at the primary cell.
 *
 * @param row The row index of the primary discharged microcell.
 * @param col The column index of the primary discharged microcell.
 * @param width The width (and height) of the microcell grid (assumed square).
 * @param spread The standard deviation of the spatial spread of cross-talk photons (in cell units).
 * @param state A reference to the random number generator state.
 *
 * @return The linear index of the microcell selected for the cross-talk discharge.
 *
 * @details
 * The function generates random offsets ``d_row`` and ``d_col`` from a normal distribution.
 * To prevent intra-cell cross-talk (where the cross-talk photon triggers the same cell that emitted it),
 * if the generated offsets are both zero, the function forces a displacement to one of the
 * four immediate neighbors (up, down, left, or right) chosen uniformly at random.
 * The resulting coordinates are clamped to the grid boundaries ``[0, width-1]``.
 * 
 */
__device__ inline int extract_xt_ucell(
    int row,
    int col,
    int width,
    float spread,
    curandStatePhilox4_32_10_t& state
)
{
    // Round to nearest integer
    int d_row = (int)rintf(curand_normal(&state) * spread);
    int d_col = (int)rintf(curand_normal(&state) * spread);

    // Prevent intra-cell cross-talk
    if (d_row == 0 && d_col == 0) {
        // Pick a random direction: 0=Up, 1=Down, 2=Right, 3=Left
        int dir = (int)(curand_uniform(&state) * 4.0f);
        d_row = (dir == 0) - (dir == 1); //  1 if 0, -1 if 1,  0 otherwise
        d_col = (dir == 2) - (dir == 3); //  1 if 2, -1 if 3,  0 otherwise
    }

    // We must clamp (min/max) because SiPM edges don't wrap physically.
    int xt_row = max(0, min(width - 1, row + d_row));
    int xt_col = max(0, min(width - 1, col + d_col));

    // Ucell where the cross-talk occured
    return xt_row * width + xt_col;
}

/**
 * @brief Computes the formed SiPM signals.
 *
 * This kernel function simulates the response of Silicon Photo-Multipliers (SiPMs)
 * by superimposing single photo-electron (PE) waveforms based on PE arrival time,
 * SiPM cross-talk, SiPM microcells gain dispersion and SiPM PE-background noise.  
 * It operates on a per-pixel and per-channel basis, assigning a CUDA block per pixel per channel.
 *
 * @param windows Array of time windows for each channel.  Defines the time ranges
 *                over which signals are computed. ``windows[windows_map[channel] : windows_map[channel+1]]``
 *                is the time window for ``channel``.
 * @param windows_map Array indicating the starting  and ending index of the time window for each channel
 *                    within the ``windows`` array.
 * @param signals Output array where the computed SiPM signals are stored.  The signal for
 *                a given channel and pixel is stored in a contiguous block.
 *                ``signals[start_signals[channel] + pixel_id * n_window : start_signals[channel] + (pixel_id + 1) * n_window]``
 *                where n_window = windows_map[channel+1] - windows_map[channel].
 *                The array does not need to be initialized before the kernel invocation.
 * @param signals_map Array indicating the starting index and ending index of each channel inside the array signals.
 * @param n_channels Number of channels.
 * @param t0s Array of discharge times for each pixel.
 * @param map Array that maps pixel indices to the range of their corresponding
 *            discharge times in the ``t0s`` array.  Specifically, ``t0s[map[pixel_id]:map[pixel_id+1]]``
 *            provides the discharge times for ``pixel_id``.
 * @param microcell_ids Discharged microcell IDs (matches t0s).
 * @param n_microcells Total number of microcells per pixel.
 * @param waveforms Array containing the texture pointer of all channel waveforms.
 * @param inv_dt_waveforms Array containing the inverse of the time spacing (dt) for each
 *                         waveform.
 * @param t_start_waveforms Array indicating the starting time of each waveform.
 * @param gains Array containing the pulse peak amplitued for each pixel for each channel (n_pixels*n_channels size)
 * @param xt Array of cross-talk probabilities for each pixel.  This represents the probability
 *           that a discharge in one microcell will trigger a discharge in an adjacent microcell.
 * @param std_ucells Array of microcell gain dispersions for each pixel. This models the
 *                   variation in the charge produced by different microcells for a single photon.
 * @param mask Array indicating whether a pixel is masked (1) or active (0). Masked pixels
 *             will have zero signal.
 * @param inv_bkg_rate Array of inverse background rates for each pixel (in units of time).  This is
 *                     used to generate background noise events.
 * @param bkg_start Start time for background noise generation.
 * @param bkg_end End time for background noise generation.
 * @param seed Array of random number generator seeds, one for each pixel.
 * @param n_pixels Number of pixels.
 *
 * 
 * @warning
 * 1. The number of blocks must be at least ``n_pixels*n_channels`` (i.e. a block per pixel per channel)
 * 2. The size of the shared memory buffer must be equal to ``(max_window_size+n_threads*6 + 32 + 4) * sizeof(float)``.
 *
 * @details
 * The kernel is launched with a 1D grid of blocks, where each block is responsible for
 * computing the signal for a single (pixel, channel) combination.  Each block uses
 * shared memory (``shared_buffer``) to store the intermediate signal, microcell states and intermediate values, improving performance
 * by reducing global memory accesses.
 * 
 * The signal computation involves the following steps:
 * 
 * 1. Determine the block assigned channel and pixel. Initialize the shared memory buffer to zero. Initialize the last discharge time to -inf.
 * 
 * 2. Initialize a ``curandStatePhilox4_32_10_t`` random number generator for the pixel using the provided seed.
 * 
 * 3. Iterate through input and background discharges:
 *   
 *     3a. Create two batches of input and background events. For each batch, if the queue is empty
 *         
 *         - load n_threads event into the batch queue (with Poissonian inter-arrival times for background);
 *         - compute the number of cross-talk photons using a Borel distribution;
 *     
 *     3b. While both queues are not empty process events in chronological order. For each event:
 *         
 *         - compute the amplitude checking the last microcell discharge time and update it
 *         - do the same for prompt cross-talk events, but in different microcells
 *         - compute afterpulse amplitude and time, only for the primary event and 
 *           assuming negligible the probability that another discharge occurs
 *           between the primary and afterpulse discharge.
 *         - update the waveform signal with the (primary+cross-talk) and the afterpulse.
 *         - move to the next event (background or source).
 * 
 * 4. Copy the computed signal from the shared memory buffer to the global ``signals`` array.
 * 
 */
__global__ void sipm_signals_w_ucells(
    // Time windows
    const float* windows, // windows where to compute the signals for each channel
    const int* windows_map, // where the window of each channel starts and ends in the ``windows`` array
    // Channels signals
    float* signals, // computed signals
    const int* signals_map, // where the signals of each channel starts and ends in ``signals``
    bool* skip_channel,
    int n_channels, // number of channels
    // Arrival times
    const float* t0s, // discharge times
    const int* map, // discharge times of pixel n: t0s[map[n]:map[n+1]]
    // Microcells
    const int* microcell_ids, // dischrged microcells (match t0s)
    const int* n_microcells, // number of microcells per pixel
    // Waveforms
    const unsigned long long* textures, // one for each channel
    const float* inv_dt_waveforms, // invers of the x-spacing of each waveform
    const float* t_start_waveforms, // start time of each waveform
    const float* gains, // gain of each pixel for each channel
    // SiPM details
    const float* xt, // cross-talk of each pixel
    const float* std_ucells, // ucells gain dispersion of each pixel
    const int* mask, // pixel mask
    const float* ap_prob, // Afterpulsing probability 
    const float* inv_tau_ap, // 1.0 / AP_time_constant
    const float* inv_tau_rec, // 1.0 / recovery_time_constant
    // Background
    const float* inv_bkg_rate, // inverse of the background rate for each pixel
    float bkg_start, // time from which generate backgorund
    float bkg_end, // time at which stop background generation
    // Random seed
    unsigned long long* seed, // seed for each pixel
    // Number of pixels
    int n_pixels
)
{
    // Current block
    int bid = blockIdx.x;

    // A block for each pixel channel -> n_pixels*n_channels blocks
    if (bid > n_channels*n_pixels - 1) return;

    // Channel assigned to this block
    int channel = bid / n_pixels;

    if (skip_channel[channel]) return;

    // Pixel assigned to this block
    int pixel_id = bid - n_pixels * channel;
    
    // Channel window length
    int n_window = windows_map[channel+1] - windows_map[channel];

    // Pointer to the current channel signal
    float* y = &signals[signals_map[channel]];

    // Pointer to the current channel time-window
    const float* t = &windows[windows_map[channel]];

    // Number of micro-cells of this pixel
    int pixel_n_cells = n_microcells[pixel_id];
    int width = (int)__fsqrt_rn((float)pixel_n_cells); // truncate

    // Shared memory allocation
    // The size is:
    //    shared_mem_size = 
    //        (   max_window_size
    //          + n_threads*2
    //          + 32 + 4 
    //          + max(n_microcells)
    //        ) * sizeof(float)
    extern __shared__ float shared_mem[];

    // Pointer to the shared channel signal
    float* sm_signal = shared_mem;

    // Cache where to put the discharge time of background events 
    float* queue_bkg = (float*)&sm_signal[n_window];

    // Cache where to put the discharge time of source events 
    float* queue_src = (float*)&queue_bkg[blockDim.x];

    // Temporary array for cumulative sum of background inter-arrival times
    float* scan_temp = (float*)&queue_src[blockDim.x];

    // Temporary array where to store information computed by one thread
    float* broadcast = (float*)&scan_temp[32]; 

    // Microcell last discharge times
    __half* sm_cell_states = (__half*)&broadcast[4]; 

    // Initialize shared signal to 0
    for (int i = threadIdx.x; i < n_window; i += blockDim.x) {
        sm_signal[i] = 0.0f;
    }
    // Initialize last discharge times to -inf
    unsigned short half_neg_inf_bits = 0xFC00; 
    __half sm_cell_initial_state = *(__half*)&half_neg_inf_bits;
    for (int i = threadIdx.x; i < pixel_n_cells; i += blockDim.x) {
        sm_cell_states[i] = sm_cell_initial_state;
    }
    // If a pixel is masked write 0 to global memory and return
    if (mask[pixel_id] == 1) {
        for (int i = threadIdx.x; i < n_window; i += blockDim.x) {
            y[pixel_id*n_window + i] = 0.0f;
        }
        return;
    }

    __syncthreads(); // wait for initialization

    // RNG initialization 
    // Each thread computes the physics, so this will give the same results for all channels
    curandStatePhilox4_32_10_t state;
    curand_init(seed[pixel_id], threadIdx.x, 0, &state);

    // Copy pixel constants to registers
    float local_xt = xt[pixel_id];
    float local_std_ucells = std_ucells[pixel_id];
    float local_inv_bkg_rate = inv_bkg_rate[pixel_id];
    float local_ap_prob = ap_prob[pixel_id];
    float local_inv_tau_ap = inv_tau_ap[pixel_id];
    float local_inv_tau_rec = inv_tau_rec[pixel_id];

    // Copy channel constants to registers
    cudaTextureObject_t tex = textures[channel];
    float inv_dt_wf = inv_dt_waveforms[channel];
    float t_start_wf = t_start_waveforms[channel];

    // Pointers to source events
    int global_src_ptr = map[pixel_id];
    int global_src_end = map[pixel_id+1];

    // Starting time for background events#
    // Set after the end if the background is negligible
    float sim_time = (local_inv_bkg_rate > 1e6f) ? bkg_end + 1.0f : bkg_start;

    // Reference time for last discharge times
    // This increases the fp16 ucell state precision
    float t_ref = 0.5f * (bkg_start + bkg_end);

    // Indexes to iterate through the queue (blockDim.x events per batch)
    int bkg_idx = blockDim.x; 
    int src_idx = blockDim.x; 

    // Counter of the batched source events
    int src_count_loaded = 0;

    // Here we use register instead of shared memory
    //  - fill these value for each thread in the fill scopes
    //  - use threadIdx.x == src_idx and threadIdx.x == bkg_idx to access them
    int my_bkg_cell; // In which cell the background is generated
    int my_src_cell; // In which cell the source has induced a discharge

    // Main loop
    // Keep going until 
    //    - there are no more background to process
    //    - or there are no more source events to rocess
    //    - or there are no more source events loaded into shared memory
    while (sim_time < bkg_end || global_src_ptr < global_src_end || src_idx < src_count_loaded) {

        // Fill the background queue
        if (bkg_idx == blockDim.x) {
            
            // Generate poisson inter-arrival time
            float pe_dt = poisson_interarrival_time(state, local_inv_bkg_rate);

            // Parallel prefix sum to get the correct time for this thread
            float t_gen = sim_time + block_prefix_sum(pe_dt, scan_temp);

            // Enqueue this time
            queue_bkg[threadIdx.x] = t_gen;
            
            // Extract a microcell (uniformly)
            my_bkg_cell = min((int)(curand_uniform(&state) * pixel_n_cells), pixel_n_cells - 1);

            // Reset the index to the start of the queue
            bkg_idx = 0;

            // Wait untile all times are generated
            __syncthreads();
            
            // Update the background simulation time
            sim_time = queue_bkg[blockDim.x - 1]; 
        }

        // Fill the source queue
        if (src_idx == blockDim.x) {

            // Compute the remaining source events
            int remaining = global_src_end - global_src_ptr;

            // Compute the number of source events loaded into shared memory
            src_count_loaded = (remaining > blockDim.x) ? blockDim.x : remaining;

            // Load the source events into shared memory
            if (threadIdx.x < src_count_loaded) {
                // Enqueue this time
                queue_src[threadIdx.x] = t0s[global_src_ptr + threadIdx.x];

                // Read the microcell id
                my_src_cell = microcell_ids[global_src_ptr + threadIdx.x];
                
            } else {
                // Dummy value for out of bounds 
                // (i.e.: when the number of source events is not a multiple of blockDim.x)
                queue_src[threadIdx.x] = 1.0e20f;
            }
            
            // Update the pointer to the next source event 
            // from which start the next loading into shared memory
            global_src_ptr += src_count_loaded;

            // Reset the index to the start of the queue
            src_idx = 0;

            // Wait untile all times are generated
            __syncthreads();
        }

        // Start processing the generated events until one of the queues is empty
        while (bkg_idx < blockDim.x && src_idx < blockDim.x) {
            // Read the next background event from the queue
            float t_next_bkg = queue_bkg[bkg_idx];

            // Check if the background is generated outside the range
            if (t_next_bkg > bkg_end) t_next_bkg = 1.0e20f;
            
            // Read the next source event from the queue
            float t_next_src = queue_src[src_idx];

            if (t_next_bkg >= 1.0e19f && t_next_src >= 1.0e19f) {
                bkg_idx = blockDim.x; 
                break;
            }
            
            bool src_wins = (t_next_src < t_next_bkg);
            
            // Process the source discharge
            if (src_wins) {
                // Thread src_idx, becouse is the thread that generated the value
                if (threadIdx.x == src_idx) {
                    // Total number of pe (corrected for the recovery time) including cross-talk
                    float total_amp = 0.0f;

                    // After-pulse time and amplitude
                    float t_ap_out = 0.0f; 
                    float amp_ap_out = 0.0f;

                    // Primary discharge amplitude (and update cell last discarge time)
                    float rec = update_cell_logic(
                        t_next_src,
                        my_src_cell,
                        local_inv_tau_rec,
                        sm_cell_states,
                        curand_uniform(&state),
                        t_ref
                    );
                    
                    // If any discharge occurred simulate cross-talk and ucells gain dispersion
                    if (rec > 1e-6f) {
                        // Primary ucell dispersion
                        total_amp += rec * fmaf(curand_normal(&state), local_std_ucells, 1.0f);
                        
                        // Assume square packing for spatial logic
                        int row = my_src_cell / width;
                        int col = my_src_cell - (row * width);
                        
                        // Cross-talk discharges
                        int n_xt = (int)borel_generator(local_xt*rec, state) - 1;
                        for (int k=0; k<n_xt; k++) {
                            // Ucell where the cross-talk occured
                            int xt_cell = extract_xt_ucell(row, col, width, 3.f, state);
                            // Cross-talk discharge amplitude (and update cell last discarge time)
                            float xt_rec = update_cell_logic(
                                t_next_src,
                                xt_cell,
                                local_inv_tau_rec,
                                sm_cell_states,
                                curand_uniform(&state),
                                t_ref
                            );
                            // Sum pixel signal ampltidue
                            if (xt_rec > 1e-6f) total_amp += xt_rec * fmaf(curand_normal(&state), local_std_ucells, 1.0f);
                        }

                        // After-pulse only for the primary discharge
                        // Nowadays xt and ap probabilty are low (xt<0.1, ap<0.05)
                        //
                        // N.B.: here we are also assuming that the probability
                        //       that a background discharge occurs between the 
                        //       primary source discharge and the after-pulse discharge is negligible
                        //
                        if (local_ap_prob > 1e-6f && curand_uniform(&state) < local_ap_prob*rec) {
                            // After-pulse inter-arrival time
                            float dt = -__logf(curand_uniform(&state)) / local_inv_tau_ap;

                            // After-pulse time
                            float t_ap = t_next_src + dt;

                            // After-pulse amplitude (and update cell last discarge time)
                            float ap_rec = update_cell_logic(
                                t_ap,
                                my_src_cell,
                                local_inv_tau_rec,
                                sm_cell_states,
                                curand_uniform(&state),
                                t_ref
                            );
                            
                            // Apply ucells gain dispersion
                            if (ap_rec > 1e-6f) {
                                amp_ap_out = ap_rec * fmaf(curand_normal(&state), local_std_ucells, 1.0f);
                                t_ap_out = t_ap;
                            }
                        }
                    }
                    // Update cache
                    broadcast[0] = total_amp; broadcast[1] = t_ap_out; broadcast[2] = amp_ap_out;
                }
                // Move to next source event
                src_idx++;
            
            // Process the background discharge
            } else {
                // Thread bkg_idx, becouse is the thread that generated the value
                if (threadIdx.x == bkg_idx) {
                    // Total number of pe (corrected for the recovery time) including cross-talk
                    float total_amp = 0.0f;

                    // After-pulse time and amplitude
                    float t_ap_out = 0.0f; 
                    float amp_ap_out = 0.0f;

                    // Primary discharge amplitude (and update cell last discarge time)
                    float rec = update_cell_logic(
                        t_next_bkg,
                        my_bkg_cell,
                        local_inv_tau_rec,
                        sm_cell_states,
                        curand_uniform(&state),
                        t_ref
                    );

                    // If any discharge occurred simulate cross-talk and ucells gain dispersion
                    if (rec > 1e-6f) {
                        // Primary ucell dispersion
                        total_amp += rec * fmaf(curand_normal(&state), local_std_ucells, 1.0f);

                        // Assume square packing for spatial logic
                        int row = my_bkg_cell / width;
                        int col = my_bkg_cell - (row * width);

                        // Cross-talk discharges
                        int n_xt = (int)borel_generator(local_xt * rec, state) - 1;                
                        for (int k=0; k<n_xt; k++) {
                            // Ucell where the cross-talk occured
                            int xt_cell = extract_xt_ucell(row, col, width, 3.f, state);
                            // Cross-talk discharge amplitude (and update cell last discarge time)
                            float xt_rec = update_cell_logic(
                                t_next_bkg,
                                xt_cell,
                                local_inv_tau_rec,
                                sm_cell_states,
                                curand_uniform(&state),
                                t_ref
                            );
                            // Sum pixel signal ampltidue
                            if (xt_rec > 1e-6f) total_amp += xt_rec * fmaf(curand_normal(&state), local_std_ucells, 1.0f);
                        }

                        // After-pulse only for the primary discharge
                        // Nowadays xt and ap probabilty are low (xt<0.1, ap<0.05)
                        //
                        // N.B.: here we are also assuming that the probability
                        //       that a source discharge occurs between the 
                        //       primary bkg discharge and the after-pulse discharge is negligible
                        //
                        if (local_ap_prob > 1e-6f && curand_uniform(&state) < local_ap_prob) {
                            // After-pulse inter-arrival time
                            float dt = -__logf(curand_uniform(&state)) / local_inv_tau_ap;
                            
                            // After-pulse time
                            float t_ap = t_next_bkg + dt;

                            // After-pulse amplitude (and update cell last discarge time)
                            float ap_rec = update_cell_logic(
                                t_ap,
                                my_bkg_cell,
                                local_inv_tau_rec,
                                sm_cell_states,
                                curand_uniform(&state),
                                t_ref
                            );
                            
                            // Apply ucells gain dispersion
                            if (ap_rec > 1e-6f) {
                                amp_ap_out = ap_rec * fmaf(curand_normal(&state), local_std_ucells, 1.0f);
                                t_ap_out = t_ap;
                            }
                        }
                    }
                    // Update cache
                    broadcast[0] = total_amp; broadcast[1] = t_ap_out; broadcast[2] = amp_ap_out;
                }
                // Move to next background event
                bkg_idx++;
            }
            __syncthreads();

            // Read broadcasted data
            float primary_amp = broadcast[0];
            float afterpulse_time = broadcast[1];
            float afterpulse_amp = broadcast[2];

            __syncthreads();
            
            // Accumulate primary event (including cross-talk events)
            if (primary_amp > 1e-6f) {
                float event_time = src_wins ? t_next_src : t_next_bkg;
                accumulate_waveform(sm_signal, n_window, event_time, primary_amp, t, inv_dt_wf, t_start_wf, tex, threadIdx.x, blockDim.x);
            }

            // Accumulate the after-pulse event
            if (afterpulse_amp > 1e-6f) {
                accumulate_waveform(sm_signal, n_window, afterpulse_time, afterpulse_amp, t, inv_dt_wf, t_start_wf, tex, threadIdx.x, blockDim.x);
            }
            
        }
    }

    // Write signals into global memory
    float local_gain = gains[bid];
    for (int i = threadIdx.x; i < n_window; i += blockDim.x) {
        y[pixel_id*n_window + i] = sm_signal[i] * local_gain;
    }
}

} // extern C