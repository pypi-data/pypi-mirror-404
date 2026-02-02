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
// __device__ aspherical_sag                                    //
// __device__ aspherical_sag_derivative                         //
// __device__ spherical_sag                                     //
// __device__ aspherical_surface_normal                         //
// __device__ spherical_surface_normal                          //
// __device__ cylindrical_surface_normal                        //
// __device__ aspherical_sag_and_derivative                     //
// __device__ find_ray_aspheric_intersection                    //
// __device__ interp1d                                          //
// __device__ interp2d                                          //
// __device__ unregular_interp2d                                //
// __device__ reject_photon                                     //
// __device__ rotate                                            //
// __device__ rotate_back                                       //
// __device__ transform                                         //
// __device__ transform_back                                    //
// __device__ inside_circle                                     //
// __device__ inside_square                                     //
// __device__ inside_hexagon                                    //
// __device__ check_aperture                                    //
// __device__ distance_to_flat_surface                          //
// __device__ distance_to_spherical_surface                     //
// __device__ distance_to_aspherical_surface                    //
// __device__ distance_to_cylindrical_surface                   //
// __device__ next_surface                                      //
// __device__ interp1d_text                                     //
// __device__ interp2d_text                                     //
// __device__ apply_reflection                                  //
// __device__ apply_refraction                                  //
// __device__ apply_scattering                                  //
// __device__ save_last_surface                                 //
// __device__ detection                                         //
//                                                              //
////// Kernels                                                  //
//                                                              //
// __global__ trace                                             //
// __global__ atmospheric_transmission                          //
// __global__ telescope_transform                               //
//                                                              //
//////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////

#include <curand_kernel.h>

constexpr float RAD2DEG = 57.29577951f;
constexpr float INV_C_LIGHT = 0.0033356409f; // invers speed of light in vacuum (ns/mm)

// Surface types
constexpr int REFLECTIVE = 0;
constexpr int REFLECTIVE_FRONT = 1;
constexpr int REFLECTIVE_BACK = 2;
constexpr int REFRACTIVE = 3;
constexpr int SENSITIVE = 4;
constexpr int SENSITIVE_BACK = 5;
constexpr int SENSITIVE_FRONT = 6;
constexpr int OPAQUE = 7;
constexpr int DUMMY = 8;
constexpr int REFLECTIVE_SENSITIVE = 9;
constexpr int REFLECTIVE_SENSITIVE_FRONT = 10;
constexpr int REFLECTIVE_SENSITIVE_BACK = 11;

// Sensor types
constexpr int NONE = 0;
constexpr int SIPM_TILE = 1;

// Surface shape
constexpr int ASPHERICAL = 0;
constexpr int CYLINDRICAL = 1;
constexpr int FLAT = 2;
constexpr int SPHERICAL = 3;

// Surface aperture shape
constexpr int CIRCULAR = 0;
constexpr int HEXAGONAL = 1;
constexpr int SQUARE = 2;
constexpr int HEXAGONAL_PT = 3;

// Constants for sag calculation
constexpr float CURVATURE_EPS = 1e-8f;
constexpr float ERROR_VALUE = 1e9f;
constexpr float R_EPS = 1e-3f;
constexpr float DIST_EPS = 1e-3f;

#define NUM_ASPHERIC_COEFFS 10 // Number of aspheric coefficients
#define ROT_MATRIX_SIZE 9

// Constants for intersection calculation
#define MAX_ITERATIONS 30
constexpr float DERIVATIVE_EPS = 1e-9f;
constexpr float ON_AXIS_EPS = 1e-9f;
constexpr float TOLERANCE0 = 1e-4f; // 0.1 um
constexpr float TOLERANCE1 = 1e-3f; // 1 um
constexpr float TOLERANCE2 = 1e-2f; // 10 um
constexpr float TOLERANCE3 = 1e-1f; // 100 um

#define WEIGHT_MASK 0x0000FFFF
#define SURFACE_ID_SHIFT 16

extern "C"{

/**
 * @brief Calculates the sagitta of an aspheric optical surface.
 *
 * This function computes the sagitta of an aspheric surface defined by its curvature,
 * conic constant, and aspheric coefficients. It assumes a fixed maximum number
 * of aspheric coefficients, defined by the variable NUM_ASPHERIC_COEFFS.
 *
 * The sagitta equation is a combination of the conic section formula and a even polynomial
 * series representing the aspheric terms:
 *
 * sag = (c * r^2) / (1 + sqrt(1 - (1 + k) * c^2 * r^2)) + A_2 * r^2 + A_4 * r^4 + ...
 *
 * where:
 *   - c is the curvature (1/radius of curvature)
 *   - r is the radial distance from the optical axis
 *   - k is the conic constant
 *   - A_2, A_4, ... are the aspheric coefficients
 *
 * The aspheric coeafficients are the standard aspheric coefficients multiplied by the aperture: A_i = a_i * ra^(2i).
 * The function includes optimizations for special cases like flat surfaces, Fresnel
 * surfaces, and calculations near the optical axis.
 *
 * @param r The radial distance from the optical axis.
 * @param curvature The curvature of the surface (1/radius of curvature).
 * @param conic_constant The conic constant of the surface.
 * @param aspheric_coeffs Pointer to an array of aspheric coefficients. The array
 *                       is expected to have a size of NUM_ASPHERIC_COEFFS.
 *                       If a surface has fewer coefficients, the array must be
 *                       padded with zeros. The coefficients are ordered
 *                       corresponding to increasing even powers of the radial
 *                       distance (A_2, A_4, A_6, ...).
 * @param is_fresnel Boolean flag indicating whether the surface is a Fresnel surface.
 *                  If true, the sagitta is considered to be 0 (flat).
 * @param half_aperture The half-aperture of the surface.
 *
 * @return The calculated sagitta of the aspheric surface. If an error occurs (e.g.,
 *         negative argument under the square root), returns ERROR_VALUE.
 */
__device__ float 
aspherical_sag(
    float r,
    float curvature,
    float conic_constant,
    const float* aspheric_coeffs,
    bool is_fresnel,
    float half_aperture
)
{
    if ((fabsf(curvature) < CURVATURE_EPS) || (is_fresnel) || (fabsf(r) < R_EPS)) {
        return 0.f;
    }

    // Calculate normalized radius squared (u = (r/R)^2)
    float normalized_radius = r / half_aperture;
    float normalized_radius_squared = normalized_radius * normalized_radius;
    
    // Horner's method for aspheric terms
    // A_2 * u + A_4 * u^2 + ... = u * (A_2 + u * (A_4 + ...))
    float tot_aspher = 0.f;

    #pragma unroll
    for (int i = NUM_ASPHERIC_COEFFS - 1; i >= 0; i--) {
        tot_aspher = fmaf(tot_aspher, normalized_radius_squared, aspheric_coeffs[i]);
    }
    tot_aspher *= normalized_radius_squared;

    float r_squared = r * r;
    float arg_sqrt = 1.f - (1.f + conic_constant) * curvature * curvature * r_squared;

    if (arg_sqrt < 0.f) {
        return ERROR_VALUE;
    }

    return curvature * r_squared / (1.f + sqrtf(arg_sqrt)) + tot_aspher;
}

/**
 * @brief Calculates the derivative of the sagitta of an aspheric surface with respect to the radial distance (r).
 *
 * This function computes the derivative of the sagitta (dsag/dr) for an aspheric
 * surface. The aspheric surface is defined by its curvature, conic constant,
 * and aspheric coefficients. It supports a fixed number of aspheric
 * coefficients (NUM_ASPHERIC_COEFFS).
 *
 * The sagitta equation is a combination of the conic section formula and a polynomial
 * series representing the aspheric terms:
 *
 * sagitta = (c * r^2) / (1 + sqrt(1 - (1 + k) * c^2 * r^2)) + A_2 * r^2 + A_4 * r^4 + ...
 *
 * and its derivative with respect to r is:
 *
 * dsag/dr = (c*r) / sqrt(1 - (1 + k) * c^2 * r^2) + 2*A_2 * r + 4*A_4 * r^3 + ...
 *
 * where:
 *   - c is the curvature (1/radius of curvature)
 *   - r is the radial distance from the optical axis
 *   - k is the conic constant
 *   - A_2, A_4, ... are the aspheric coefficients
 *
 * @param r The radial distance from the optical axis.
 * @param curvature The curvature of the surface (1/radius of curvature).
 * @param conic_constant The conic constant of the surface.
 * @param aspheric_coeffs Pointer to an array of aspheric coefficients.
 *                       The coefficients are ordered corresponding to
 *                       increasing even powers of the radial distance
 *                       (A_2, A_4, A_6, ...). The array must have a size
 *                       of at least NUM_ASPHERIC_COEFFS, padded with zeros
 *                       if necessary.
 * @param half_aperture The aperture radius of the surface.
 *
 * @return The calculated derivative of the sagitta (dsag/dr). If an error occurs
 *         (e.g., negative argument under the square root), returns ERROR_VALUE.
 */
__device__ float 
aspherical_sag_derivative(
    float r,
    float curvature,
    float conic_constant,
    const float* aspheric_coeffs,
    float half_aperture
)
{
    if ((fabsf(curvature) < CURVATURE_EPS) || (r < R_EPS)) {
        return 0.f;
    }

    // Calculate normalized radius squared (u = (r/R)^2)
    float normalized_radius = r / half_aperture;
    float normalized_radius_squared = normalized_radius * normalized_radius;

    // Horner's method for derivative
    float tot_aspher_deriv = 0.f;

    #pragma unroll
    for (int i = NUM_ASPHERIC_COEFFS - 1; i >= 0; i--) {
        float coeff = (float)(i + 1) * aspheric_coeffs[i];
        tot_aspher_deriv = fmaf(tot_aspher_deriv, normalized_radius_squared, coeff);
    }
    // Multiply by the common factor 2 * (r/R)
    tot_aspher_deriv *= 2.f * normalized_radius;

    // Calculate the conic section part
    float r_squared = r * r;
    float c2 = curvature * curvature;
    float arg_sqrt = 1.f - (1.f + conic_constant) * c2 * r_squared;

    if (arg_sqrt < 0.f) {
        return ERROR_VALUE;
    }
    
    return curvature * r * rsqrtf(arg_sqrt) + tot_aspher_deriv / half_aperture;
}

/**
 * @brief Computes the sagitta of a spherical surface at a given radial distance squared:
 * * sag = (c * r^2) / (1 + sqrt(1 - (c*r)^2))
 *
 * @param r_sq      Radial distance squared (x^2 + y^2) from the vertex.
 * @param curvature Curvature of the sphere (1/Radius).
 * 
 * @return          The sagitta z. Returns 0.0f if r_sq is outside the sphere's definition.
 * 
 */
__device__ inline float spherical_sag(float r_sq, float curvature)
{
    if (fabsf(curvature) < CURVATURE_EPS) return 0.0f;

    float c2 = curvature * curvature;
    float arg_sqrt = 1.0f - c2 * r_sq;

    if (arg_sqrt < 0.0f) { // That is r^2 > 1/c^2
        return ERROR_VALUE;
    }

    float denom = 1.0f + sqrtf(arg_sqrt);
    return (curvature * r_sq) / denom;
}

/**
 * @brief Calculates the upward-pointing normal for an aspherical surface.
 *
 * This function computes the partial derivative of the saggita of a rotationally symmetric aspheric surface. 
 * The surface is defined by a conic constant, curvature, and aspheric coefficients.
 *
 * @param x The x-coordinate.
 * @param y The y-coordinate.
 * @param curvature The curvature (reciprocal of the radius of curvature) of the surface at the vertex.
 * @param conic_constant The conic constant of the surface.
 * @param aspheric_coeffs Pointer to an array of 10 aspheric coefficients. The coefficients are assumed to be normalized by the half-aperture.
 * @param half_aperture The half-aperture used for normalizing aspheric coefficients.
 *
 * @return The upward-pointing normal direction vector at the given (x, y) point.
 */
__device__ float3 aspherical_surface_normal(
    float x,
    float y,
    float curvature,
    float conic_constant,
    const float* aspheric_coeffs,
    float half_aperture
)
{
    float3 n = {0.f,0.f,1.f};

    // Flat surface
    if (fabsf(curvature) < CURVATURE_EPS) return n;

    // Square radius and normalized u
    float r2 = x*x + y*y;
    float inv_half_aperture2 = 1.f / (half_aperture * half_aperture);
    float u = r2 * inv_half_aperture2; 

    // Horner's method
    float total_aspheric_term = 0.f;

    #pragma unroll
    for (int i = NUM_ASPHERIC_COEFFS - 1; i >= 0; i--) {
        float coeff = 2.f * (float)(i + 1) * aspheric_coeffs[i];
        total_aspheric_term = fmaf(total_aspheric_term, u, coeff);
    }
    // Apply common factor 1/R^2
    total_aspheric_term *= inv_half_aperture2;

    float arg_sqrt = 1.f - (1.f + conic_constant) * curvature * curvature * r2;

    // This function is called after the intersection point has been found,
    // the point cannot be outside the surface domain

    float factor = curvature * rsqrtf(arg_sqrt);

    n.x = -fmaf(factor, x, total_aspheric_term*x);
    n.y = -fmaf(factor, y, total_aspheric_term*y);

    float inv_norm = rnorm3df(n.x,n.y,n.z);

    n.x *= inv_norm;
    n.y *= inv_norm;
    n.z *= inv_norm;

    return n;
}

/**
 * @brief Calculates the upward-pointing normal for a spherical surface.
 *
 *
 * @param x The x-coordinate.
 * @param y The y-coordinate.
 * @param curvature The curvature (reciprocal of the radius of curvature) of the surface at the vertex.
 *
 * @return The upward-pointing normal direction vector at the given (x, y) point.
 *
 */
__device__ float3 spherical_surface_normal(
    float x,
    float y,
    float curvature
)
{
    float3 n = {0.f,0.f,1.f};

    // Flat surface
    if (fabsf(curvature) < CURVATURE_EPS) return n;
    
    // This function is called after the intersection point has been found
    // in the surface reference frame
    float r2 = x*x + y*y;

    // From the center of the surface
    float3 p_on_surface = {x, y, spherical_sag(r2, curvature)-1.f/curvature};

    // Normalize the vector and point it to the positive z-direction
    float sign = copysignf(1.0f, p_on_surface.z);
    float inv_norm = rnorm3df(p_on_surface.x,p_on_surface.y,p_on_surface.z);

    n.x = sign * inv_norm * p_on_surface.x;
    n.y = sign * inv_norm * p_on_surface.y;
    n.z = sign * inv_norm * p_on_surface.z;

    return n;
}

__device__ float3 cylindrical_surface_normal(
    float3 p,
    float radius,
    float height
)
{
    // Top or bottom surface normal
    float3 n = {0.f,0.f,1.f};

    // Compute quantities
    float half_height = 0.5f * height;
    float r = hypotf(p.x, p.y);
    
    // Check if the point is on flat surfaces
    bool on_top = (p.z > half_height-DIST_EPS) && (r < radius-R_EPS);
    bool on_bottom = (p.z < -half_height+DIST_EPS) && (r < radius-R_EPS);

    // Flat surface normal
    if (on_top)
        return n;

    if (on_bottom) {
        n.z = -1.f;
        return n;
    }

    // Cylindrical surface normal
    float inv_norm = 1/r;
    n.x = p.x * inv_norm;
    n.y = p.y * inv_norm;
    n.z = 0.f;

    return n;
}

/**
 * @brief Calculates the sagitta and derivative of an aspheric surface.
 *
 *
 * @param r The radial distance from the optical axis.
 * @param curvature The curvature of the surface (1/radius of curvature).
 * @param conic_constant The conic constant of the surface.
 * @param aspheric_coeffs Pointer to an array of aspheric coefficients.
 *                       The coefficients are ordered corresponding to
 *                       increasing even powers of the radial distance
 *                       (A_2, A_4, A_6, ...). The array must have a size
 *                       of at least NUM_ASPHERIC_COEFFS, padded with zeros
 *                       if necessary.
 * @param half_aperture The aperture radius of the surface.
 * @param is_fresnel Boolean flag indicating whether the surface is a Fresnel surface.
 *                   If true, the sagitta is considered to be 0 (flat).
 * @param sag_out Pointer to a float variable to store the calculated sagitta.
 * @param deriv_out Pointer to a float variable to store the calculated derivative of the sagitta.
 * 
 */
__device__ void 
aspherical_sag_and_derivative(
    float r,
    float curvature,
    float conic_constant,
    const float* aspheric_coeffs,
    float half_aperture,
    bool is_fresnel,
    float* sag_out,
    float* deriv_out
)
{
    // Early exit for flat/fresnel/center cases
    if ((fabsf(curvature) < CURVATURE_EPS) || (is_fresnel) || (r < R_EPS)) {
        *sag_out = 0.f;
        *deriv_out = 0.f;
        return;
    }

    float normalized_radius = r / half_aperture;
    float normalized_radius_squared = normalized_radius * normalized_radius;

    // We calculate the sag sum and derivative sum in parallel to keep pipelines full
    float tot_aspher = 0.f;       // For sag
    float tot_aspher_deriv = 0.f; // For derivative

    #pragma unroll
    for (int i = NUM_ASPHERIC_COEFFS - 1; i >= 0; i--) {
        tot_aspher = fmaf(tot_aspher, normalized_radius_squared, aspheric_coeffs[i]);
        float deriv_coeff = (float)(i + 1) * aspheric_coeffs[i];
        tot_aspher_deriv = fmaf(tot_aspher_deriv, normalized_radius_squared, deriv_coeff);
    }
    tot_aspher *= normalized_radius_squared;
    tot_aspher_deriv *= 2.f * normalized_radius;

    float r_squared = r * r;
    float c2 = curvature * curvature;
    float arg_sqrt = 1.f - (1.f + conic_constant) * c2 * r_squared;

    if (arg_sqrt < 0.f) {
        *sag_out = ERROR_VALUE;
        *deriv_out = ERROR_VALUE;
        return;
    }

    float sqrt_val = sqrtf(arg_sqrt);

    // Sagitta
    *sag_out = (curvature * r_squared) / (1.f + sqrt_val) + tot_aspher;
    
    // Derivative
    *deriv_out = (curvature * r) / sqrt_val + (tot_aspher_deriv / half_aperture); 
}

/**
 * @brief Finds the intersection parameter of a ray with an aspheric surface using an iterative method.
 *
 * This function iteratively refines an initial guess for the parameter 't' along a ray
 * to find the intersection point with an aspheric surface. It uses a modified Newton-Raphson
 * method with the Kahan-Babushka-Neumaier (KBN) summation algorithm for improved numerical accuracy 
 * with float32.
 *
 * The ray is defined by its origin (p) and direction (v).
 * The aspheric surface is defined by its curvature, conic constant, aspheric coefficients,
 * Fresnel flag, and aperture radius.
 *
 * @param p A float3 representing the origin (starting point) of the ray.
 * @param v A float3 representing the direction vector of the ray.
 * @param initial_guess The initial guess for the intersection parameter 't'.
 * @param curvature The curvature of the surface (1/radius of curvature).
 * @param conic_constant The conic constant of the surface.
 * @param aspheric_coeffs Pointer to an array of aspheric coefficients.
 * @param is_fresnel Boolean flag indicating whether the surface is a Fresnel surface.
 * @param half_aperture The half-aperture of the surface.
 *
 * @return The calculated intersection parameter 't' along the ray. Returns ERROR_VALUE if
 *         the method fails to converge within MAX_ITERATIONS or if the derivative is too close to zero.
 */
__device__ float 
find_ray_aspheric_intersection(
    float3& p,
    float3& v,
    float initial_guess,
    float curvature,
    float conic_constant,
    const float* aspheric_coeffs,
    bool is_fresnel,
    float half_aperture
)
{
    float t_change = ERROR_VALUE;
    float prev_t = initial_guess;
    float new_t;
    
    // Variable to compute residuals and derivatives
    float sag, sag_derivative; 
    float residual, residual_derivative;

    // Kahan-Babushka-Neumaier sum variables
    volatile float kbn_sum = prev_t;
    volatile float kbn_comp = 0.f;
    volatile float kbn_temp, kbn_input;

    float tolerance = TOLERANCE0;
    
    // Start iteration
    #pragma unroll
    for (int i = 0; i < MAX_ITERATIONS; i++) {
        // Dynamic tolerance
        if (i > 10) tolerance = TOLERANCE1;
        if (i > 15) tolerance = TOLERANCE2;
        if (i > 25) tolerance = TOLERANCE3;

        // Move to the next point
        float x = fmaf(v.x, prev_t, p.x);
        float y = fmaf(v.y, prev_t, p.y);
        float r = sqrtf(x*x + y*y);

        // Compute sagitta and its derivative
        aspherical_sag_and_derivative(
            r,
            curvature,
            conic_constant,
            aspheric_coeffs, 
            half_aperture,
            is_fresnel, 
            &sag,
            &sag_derivative
        );

        if (sag == ERROR_VALUE) return ERROR_VALUE;

        // Residual: sag(r) - ray_z(t)
        residual = sag - p.z - v.z * prev_t;

        // Derivative: d(sag)/dr * dr/dt - v.z
        // dr/dt = (x*v.x + y*v.y) / r
        float dot_prod_r_v = fmaf(x, v.x, y * v.y); 
        float r_prime = (r > R_EPS) ? (dot_prod_r_v / r) : 0.f;
        residual_derivative = sag_derivative * r_prime - v.z;

        // Update kbn step
        kbn_input = -residual / residual_derivative;
        
        kbn_temp = kbn_sum + kbn_input;
        if (fabsf(kbn_sum) >= fabsf(kbn_input)) {
            kbn_comp += (kbn_sum - kbn_temp) + kbn_input;
        } else {
            kbn_comp += (kbn_input - kbn_temp) + kbn_sum;
        }
        kbn_sum = kbn_temp;
        new_t = kbn_sum + kbn_comp;

        t_change = new_t - prev_t;
        
        if (fabsf(t_change) < tolerance) {
            return new_t;
        }

        prev_t = new_t;
    }
    return ERROR_VALUE;
}

/**
 * @brief Performs linear interpolation on a 1D dataset containing multiple curves.
 *
 * This function performs linear interpolation to estimate the value of a function at a given point ``x0``,
 * based on a set of known data points (``xs``, ``ys``) that represent multiple curves. The specific curve
 * to use for interpolation is defined by ``start_x``, ``start_y``, and ``n_points``.
 *
 * @param x0 The x-coordinate at which to interpolate the value.
 * @param xs An array of x-coordinates of the known data points for multiple curves.
 *           The x-coordinates for each curve must be sorted in ascending order.
 * @param ys An array of y-coordinates (function values) corresponding to the ``xs`` values for multiple curves.
 * @param n_points The number of data points in the specific curve to be used for interpolation.
 * @param inv_dx The inverse of the spacing between consecutive x-coordinates in the curve (1 / (xs[i+1] - xs[i])).
 *               Assumes uniform spacing between points within each curve.
 * @param start_x The starting index in the ``xs`` array for the curve to be used.
 * @param start_y The starting index in the ``ys`` array for the curve to be used.
 *
 * @return The interpolated value at ``x0``. Returns 0.f if ``x0`` is outside the range of the specified curve or if any error occurs.
 */
__device__ float 
interp1d(
    float x0,
    const float* xs,
    const float* ys,
    int n_points,
    float inv_dx,
    int start_x,
    int start_y
)
{
    // Distance the first input position
    float dx = x0 - xs[start_x];

    if (dx < 0.f) return 0.f;
    
    // Index of the nearest lower neighbor
    int xi = __float2int_rz(dx * inv_dx);

    if (xi>=n_points-1) return 0.f;

    // Values of the nearest neighbors
    float f0 = ys[start_y+xi];
    float f1 = ys[start_y+xi+1];

    // Calculate weights for linear interpolation
    float t = dx * inv_dx - truncf(dx * inv_dx);

    // Linear interpolation
    // See https://en.wikipedia.org/wiki/Linear_interpolation#Programming_language_support
    return fmaf(t, f1, fmaf(-t, f0, f0));
}

/**
 * @brief Performs bilinear interpolation on a 2D dataset containing multiple grids.
 *
 * This function performs bilinear interpolation to estimate the value of a function at a given point (``x1_0``, ``x2_0``),
 * based on a set of known data points (``x1s``, ``x2s``, ``ys``) that represent multiple 2D grids. The specific grid
 * to use for interpolation is defined by ``start_x1``, ``start_x2``, ``start_y``, ``n``, and ``m``.
 *
 * @param x1_0 The x1-coordinate at which to interpolate the value.
 * @param x2_0 The x2-coordinate at which to interpolate the value.
 * @param x1s An array of x1-coordinates of the known data points for multiple grids.
 *            The x1-coordinates for each grid must be sorted in ascending order and have uniform spacing.
 * @param x2s An array of x2-coordinates of the known data points for multiple grids.
 *            The x2-coordinates for each grid must be sorted in ascending order and have uniform spacing.
 * @param ys An array of y-values (function values) corresponding to the ``x1s`` and ``x2s`` values for multiple grids.
 * @param n The number of data points in the x1-direction for the specific grid to be used.
 * @param m The number of data points in the x2-direction for the specific grid to be used.
 * @param inv_dx1 The inverse of the spacing between consecutive x1-coordinates in the grid (1 / (x1s[i+1] - x1s[i])).
 * @param inv_dx2 The inverse of the spacing between consecutive x2-coordinates in the grid (1 / (x2s[i+1] - x2s[i])).
 * @param start_x1 The starting index in the ``x1s`` array for the grid to be used.
 * @param start_x2 The starting index in the ``x2s`` array for the grid to be used.
 * @param start_y The starting index in the ``ys`` array for the grid to be used.
 *
 * @return The interpolated value at (``x1_0``, ``x2_0``). Returns 0.f if (``x1_0``, ``x2_0``) is outside the range of the
 *         specified grid or if any error occurs.
 */
__device__ float 
interp2d(
    float x1_0, 
    float x2_0,
    const float* x1s,
    const float* x2s,
    const float* ys,
    int n,
    int m,
    float inv_dx1,
    float inv_dx2,
    int start_x1,
    int start_x2,
    int start_y)
{
    // Distance from x1_0 to the first x1-coordinate of the grid
    float dx1 = x1_0 - x1s[start_x1];
    // Distance from x2_0 to the first x2-coordinate of the grid
    float dx2 = x2_0 - x2s[start_x2];

    // If x1_0 or x2_0 is before the start of the grid, return 0.f
    if ((dx1 < 0.f) | (dx2 < 0.f)) return 0.f;

    // Index of the nearest lower neighbor to x1_0 within the grid
    int x1i = __float2int_rz(dx1 * inv_dx1);

    // Index of the nearest lower neighbor to x2_0 within the grid
    int x2i = __float2int_rz(dx2 * inv_dx2);

    // If x1_0 or x2_0 is beyond the end of the grid, return 0.f
    if ((x1i >= n - 1) | (x2i >= m - 1)) return 0.f;

    // Values of the four nearest neighbors
    float f00 = ys[start_y + x2i * n + x1i];
    float f01 = ys[start_y + (x2i + 1) * n + x1i];
    float f10 = ys[start_y + x2i * n + x1i + 1];
    float f11 = ys[start_y + (x2i + 1) * n + x1i + 1];

    // Calculate the interpolation weights (fractional parts of the distances)
    float t1 = dx1 * inv_dx1 - truncf(dx1 * inv_dx1);
    float t2 = dx2 * inv_dx2 - truncf(dx2 * inv_dx2);

    // Bilinear interpolation formula
    float res = f00 * (1.f - t1) * (1.f - t2) + f01 * (1.f - t1) * t2 + f10 * t1 * (1.f - t2) + f11 * t1 * t2;

    return res;
}

/**
 * @brief Performs bilinear interpolation on a 2D dataset containing multiple grids.
 *
 * This function performs bilinear interpolation to estimate the value of a function at a given point (``x1_0``, ``x2_0``),
 * based on a set of known data points (``x1s``, ``x2s``, ``ys``) that represent multiple 2D grids. The specific grid
 * to use for interpolation is defined by ``start_x1``, ``start_x2``, ``start_y``, ``n``, and ``m``.
 *
 * @param x1_0 The x1-coordinate at which to interpolate the value.
 * @param x2_0 The x2-coordinate at which to interpolate the value.
 * @param x1s An array of x1-coordinates of the known data points for multiple grids.
 *            The x1-coordinates for each grid must be sorted in ascending order.
 * @param x2s An array of x2-coordinates of the known data points for multiple grids.
 *            The x2-coordinates for each grid must be sorted in ascending order.
 * @param ys An array of y-values (function values) corresponding to the ``x1s`` and ``x2s`` values for multiple grids.
 * @param n The number of data points in the x1-direction for the specific grid to be used.
 * @param m The number of data points in the x2-direction for the specific grid to be used.
 * @param start_x1 The starting index in the ``x1s`` array for the grid to be used.
 * @param start_x2 The starting index in the ``x2s`` array for the grid to be used.
 * @param start_y The starting index in the ``ys`` array for the grid to be used.
 *
 * @return The interpolated value at (``x1_0``, ``x2_0``). Returns 0.f if (``x1_0``, ``x2_0``) is outside the range of the
 *         specified grid or if any error occurs.
 */
__device__ float 
unregular_interp2d(
    float x1_0, 
    float x2_0,
    const float* x1s,
    const float* x2s,
    const float* ys,
    int n,
    int m,
    int start_x1,
    int start_x2,
    int start_y)
{
    // Distance from x1_0 to the first x1-coordinate of the grid
    float dx1 = x1_0 - x1s[start_x1];

    // Distance from x2_0 to the first x2-coordinate of the grid
    float dx2 = x2_0 - x2s[start_x2];

    // If x1_0 or x2_0 is before the start of the grid, return 0.f
    if ((dx1 < 0.f) || (dx2 < 0.f)) return 0.f;

    // If x1_0 or x2_0 is after the end of the grid, return 0.f
    if ((x1_0 >= x1s[start_x1+n-1]) || (x2_0 >= x2s[start_x2+m-1])) return 0.f;

    // Index of the nearest lower neighbor to x1_0 within the grid
    int left = start_x1;
    int right = start_x1 + n - 1;
    int x1i, mid;
    while (left <= right) {
        mid = (left + right) >> 1;
        if ((x1_0 >= x1s[mid]) && (x1_0 < x1s[mid+1])) {
            x1i = mid;
            break;
        }
        else if (x1s[mid] < x1_0) {
            left = mid + 1;
        }
        else {
            right = mid - 1;
        }
    }

    // Index of the nearest lower neighbor to x2_0 within the grid
    left = start_x2;
    right = start_x2 + m - 1;
    int x2i;
    while (left <= right) {
        mid = (left + right) >> 1;
        if ((x2_0 >= x2s[mid]) && (x2_0 < x2s[mid+1])) {
            x2i = mid;
            break;
        }
        else if (x2s[mid] < x2_0) {
            left = mid + 1;
        }
        else {
            right = mid - 1;
        }
    }

    // Reciprocal of the local step
    float inv_dx1 = 1.f/(x1s[x1i+1]-x1s[x1i]);
    float inv_dx2 = 1.f/(x1s[x2i+1]-x2s[x2i]);

    // Values of the four nearest neighbors
    float f00 = ys[start_y + x2i * n + x1i];
    float f01 = ys[start_y + (x2i + 1) * n + x1i];
    float f10 = ys[start_y + x2i * n + x1i + 1];
    float f11 = ys[start_y + (x2i + 1) * n + x1i + 1];

    // Calculate the interpolation weights (fractional parts of the distances)
    float t1 = dx1 * inv_dx1 - truncf(dx1 * inv_dx1);
    float t2 = dx2 * inv_dx2 - truncf(dx2 * inv_dx2);

    // Bilinear interpolation formula
    float res = f00 * (1.f - t1) * (1.f - t2) + f01 * (1.f - t1) * t2 + f10 * t1 * (1.f - t2) + f11 * t1 * t2;

    return res;
}

/**
 * @brief Rejects a photon by setting its position, direction, wavelength, and time to NaN.
 *
 * This function is used to mark a photon as invalid or rejected. It achieves this by setting
 * all components of the photon position (``p``), direction (``v``), wavelength (``wl``), and time (``t``)
 * to ``NaN`` (Not a Number).
 *
 * @param p A float3 reference representing the photon position (x, y, z).
 * @param v A float3 reference representing the photon direction vector (vx, vy, vz).
 * @param wl A float reference representing the photon wavelength.
 * @param t A float reference representing the photon time.
 */
__device__ void 
reject_photon(
    float3& p, 
    float3& v, 
    float& wl, 
    float& t
) 
{
    p.x = nanf("");
    p.y = nanf("");
    p.z = nanf("");
    v.x = nanf("");
    v.y = nanf("");
    v.z = nanf("");
    wl = nanf("");
    t = nanf("");
}

/**
 * @brief Rotates a 3D vector using a rotation matrix.
 *
 * This function rotates the vector ``v`` using the provided 3x3 rotation matrix ``r_mat``.
 * The rotation is performed in-place, modifying the original vector ``v``.
 * The rotation matrix is assumed to be stored in row-major order:
 *
 *     | r_mat[0] r_mat[1] r_mat[2] |
 *     | r_mat[3] r_mat[4] r_mat[5] |
 *     | r_mat[6] r_mat[7] r_mat[8] |
 *
 * @param v A reference to a float3 representing the 3D vector to be rotated. This vector will be modified in-place.
 * @param r_mat A pointer to a 9-element array representing the 3x3 rotation matrix in row-major order.
 */
__device__ void 
rotate(
    float3& v,
    const float* r_mat
)
{
    float x = v.x;
    float y = v.y;
    float z = v.z;
    v.x = r_mat[0]*x + r_mat[1]*y + r_mat[2]*z;
    v.y = r_mat[3]*x + r_mat[4]*y + r_mat[5]*z;
    v.z = r_mat[6]*x + r_mat[7]*y + r_mat[8]*z;
}

/**
 * @brief Rotates a 3D vector using the inverse of a rotation matrix.
 *
 * This function rotates the vector ``v`` using the inverse (transpose) of the provided 3x3 rotation matrix ``r_mat``.
 * The rotation is performed in-place, modifying the original vector ``v``.
 * The rotation matrix is assumed to be stored in row-major order:
 *
 *     | r_mat[0] r_mat[1] r_mat[2] |
 *     | r_mat[3] r_mat[4] r_mat[5] |
 *     | r_mat[6] r_mat[7] r_mat[8] |
 *
 * @param v A reference to a float3 representing the 3D vector to be rotated. This vector will be modified in-place.
 * @param r_mat A pointer to a 9-element array representing the 3x3 rotation matrix in row-major order.
 */
__device__ void 
rotate_back(
    float3& v, 
    const float* r_mat
)
{
    float x = v.x;
    float y = v.y;
    float z = v.z;
    v.x = r_mat[0]*x + r_mat[3]*y + r_mat[6]*z;
    v.y = r_mat[1]*x + r_mat[4]*y + r_mat[7]*z;
    v.z = r_mat[2]*x + r_mat[5]*y + r_mat[8]*z;
}

/**
 * @brief Transforms a point and a direction vector into a new coordinate system.
 *
 * This function first translates the point ``p`` by subtracting the origin point ``p0``, effectively
 * shifting the origin of the coordinate system. Then, it rotates both the translated point ``p``
 * and the direction vector ``v`` using the provided rotation matrix ``r_mat``. The transformations
 * are performed in-place, modifying the original ``p`` and ``v``.
 *
 * The rotation matrix ``r_mat`` is assumed to be stored in row-major order:
 *
 *     | r_mat[0] r_mat[1] r_mat[2] |
 *     | r_mat[3] r_mat[4] r_mat[5] |
 *     | r_mat[6] r_mat[7] r_mat[8] |
 *
 * @param p A reference to a float3 representing the point to be transformed. This point will be modified in-place.
 * @param v A reference to a float3 representing the direction vector to be transformed. This vector will be modified in-place.
 * @param r_mat A pointer to a 9-element array representing the 3x3 rotation matrix in row-major order.
 * @param p0 A reference to a float3 representing the origin point of the original coordinate system.
 */
__device__ void 
transform(
    float3& p,
    float3& v,
    const float* r_mat,
    const float3& p0
)
{
    p.x -= p0.x;
    p.y -= p0.y;
    p.z -= p0.z;
    rotate(v, r_mat);
    rotate(p, r_mat);
}

/**
 * @brief Transforms a point and a direction vector back to the original coordinate system.
 *
 * This function first rotates both the point ``p`` and the direction vector ``v`` using the inverse
 * (transpose) of the provided rotation matrix ``r_mat``. Then, it translates the rotated point ``p``
 * by adding the origin point ``p0``, effectively shifting the origin back to its original position.
 * The transformations are performed in-place, modifying the original ``p`` and ``v``.
 *
 * The rotation matrix ``r_mat`` is assumed to be stored in row-major order:
 *
 *     | r_mat[0] r_mat[1] r_mat[2] |
 *     | r_mat[3] r_mat[4] r_mat[5] |
 *     | r_mat[6] r_mat[7] r_mat[8] |
 *
 * @param p A reference to a float3 representing the point to be transformed back. This point will be modified in-place.
 * @param v A reference to a float3 representing the direction vector to be transformed back. This vector will be modified in-place.
 * @param r_mat A pointer to a 9-element array representing the 3x3 rotation matrix in row-major order.
 * @param p0 A reference to a float3 representing the origin point of the original coordinate system.
 */
__device__ void 
transform_back(
    float3& p,
    float3& v,
    const float* r_mat,
    const float3& p0
)
{
    rotate_back(v, r_mat);
    rotate_back(p, r_mat);
    p.x += p0.x;
    p.y += p0.y;
    p.z += p0.z;
}

/**
 * @brief Checks if a point is inside a circle.
 *
 * @param r_sq Pre-calculated squared radial distance (x*x + y*y).
 * @param radius The circlle radius.
 *
 * @return True if the point is inside the circle, false otherwise.
 *
 */
__device__ inline bool 
inside_circle(float r_sq, float radius)
{
    float limit = radius + DIST_EPS;
    return r_sq < (limit * limit);
}

/**
 * @brief Checks if a point is inside a square.
 *
 * @param x x-coordinate.
 * @param y y-coordinate.
 * @param half_width The half-width of the square (from center to edge).
 *
 * @return True if the point is inside the square, false otherwise.
 *
 */
__device__ inline bool 
inside_square(float x, float y, float half_width)
{
    float limit = half_width + DIST_EPS;
    return (fabsf(x) < limit) && (fabsf(y) < limit);
}

/**
 * @brief Checks if a point is inside a hexagon defined by its inradius (apothem).
 *
 * @param x x-coordinate.
 * @param y x-coordinate.
 * @param inradius The distance from center to the middle of the flat edge.
 * @param pointy_top Whether the hexagon is pointy-top (y-axis) or flat-top.
 *
 * @return True if the point is inside the hexagon, false otherwise.
 *
 */
__device__ inline bool 
inside_hexagon(float x, float y, float inradius, bool pointy_top)
{
    float px = fabsf(x);
    float py = fabsf(y);
    float limit = inradius + DIST_EPS;

    // If pointy top, swap x and y
    if (pointy_top) {
        float temp = px;
        px = py;
        py = temp;
    }

    // Stright side
    if (py > limit) return false;

    // Inequality for a regular hexagon
    // |x|*sqrt(3) + |y| < 2*inradius
    return fmaf(px, 1.73205081f, py) < (2.0f * limit);
}

/**
 * @brief Checks if a point lies within the defined aperture.
 *
 * @param x The x-coordinate on the surface.
 * @param y The y-coordinate on the surface.
 * @param outer_aperture The outer dimension (radius or half-width).
 * @param inner_aperture The inner dimension (hole radius or half-width).
 * @param aperture_shape The shape of the outer aperture (CIRCULAR, HEXAGONAL, SQUARE, etc.).
 * @param central_hole_shape The shape of the central hole.
 *
 * @return true if the point is inside the valid surface area, false otherwise.
 *
 */
__device__ bool 
check_aperture(
    float x,
    float y,
    float outer_aperture,
    float inner_aperture,
    int aperture_shape,
    int central_hole_shape
)
{
    // Pre-calculate r_sq as it is used often and cheap to compute once
    float r_sq = x*x + y*y;

    // Outer aperture
    bool is_inside = true;

    switch(aperture_shape) {
        case CIRCULAR:
            is_inside = inside_circle(r_sq, outer_aperture);
            break;
        case SQUARE:
            is_inside = inside_square(x, y, outer_aperture);
            break;
        case HEXAGONAL:
            is_inside = inside_hexagon(x, y, outer_aperture, false); // Flat top
            break;
        case HEXAGONAL_PT:
            is_inside = inside_hexagon(x, y, outer_aperture, true);  // Pointy top
            break;
    }

    if (!is_inside) return false;

    // Central hole
    if (inner_aperture > 0.f) {
        bool is_in_hole = false;

        switch(central_hole_shape) {
            case CIRCULAR:
                is_in_hole = inside_circle(r_sq, inner_aperture);
                break;
            case SQUARE:
                is_in_hole = inside_square(x, y, inner_aperture);
                break;
            case HEXAGONAL:
                is_in_hole = inside_hexagon(x, y, inner_aperture, false);
                break;
            case HEXAGONAL_PT:
                is_in_hole = inside_hexagon(x, y, inner_aperture, true);
                break;
        }

        if (is_in_hole) return false;
    }

    return true;
}


/**
 * @brief Calculates the intersection distance of a ray with a flat surface.
 *
 * @param t Output intersection distance.
 * @param p Ray origin.
 * @param v Ray direction.
 * @param outer_aperture Outer aperture dimension.
 * @param inner_aperture Inner aperture dimension.
 * @param aperture_shape Shape of the aperture.
 * @param central_hole_shape Shape of the central hole.
 * @param surface_position Position of the surface center.
 * @param rotation_matrix Rotation matrix for the surface.
 */
__device__ void 
distance_to_flat_surface(
    float& t,
    float3 p,
    float3 v,
    float outer_aperture,
    float inner_aperture,
    int aperture_shape,
    int central_hole_shape,
    float3 surface_position,
    const float* __restrict__ rotation_matrix
)
{
    // Transform into the surface reference frame 
    transform(p, v, rotation_matrix, surface_position);

    // Ray perpendicular to the optical axis (parallel to plane)
    if (fabsf(v.z) < ON_AXIS_EPS) {
        t = ERROR_VALUE;
        return;
    }

    // Intersection with the plane z = 0
    t = -p.z / v.z;

    // If intersection is behind the ray origin it's invalid
    if (t < DIST_EPS) {
        t = ERROR_VALUE;
        return;
    }

    // Calculate intersection point on the surface plane
    float xa = fmaf(v.x, t, p.x);
    float ya = fmaf(v.y, t, p.y);

    // Check Aperture
    if (!check_aperture(xa, ya, outer_aperture, inner_aperture, aperture_shape, central_hole_shape)) {
        t = ERROR_VALUE;
    }
}

/**
 * @brief Calculates the intersection distance of a ray with a spherical surface.
 * * Assumes the sphere is centered at (0, 0, 1/curvature) in the local frame
 * and vertex at (0, 0, 0).
 *
 * @param t Output intersection distance.
 * @param p Ray origin.
 * @param v Ray direction.
 * @param offset Segment offset.
 * @param curvature Curvature of the sphere (1/R).
 * @param is_fresnel Whether the surface is a Fresnel surface (treated as flat).
 * @param outer_aperture Outer aperture dimension.
 * @param inner_aperture Inner aperture dimension.
 * @param aperture_shape Shape of the aperture.
 * @param central_hole_shape Shape of the central hole.
 * @param surface_position Position of the surface vertex.
 * @param rotation_matrix Rotation matrix for the surface.
 */
__device__ void 
distance_to_spherical_surface(
    float& t_out,
    float3 p,
    float3 v,
    float2 offset,
    float curvature,
    bool is_fresnel,
    float outer_aperture,
    float inner_aperture,
    int aperture_shape,
    int central_hole_shape,
    float3 surface_position,
    const float* __restrict__ rotation_matrix
)
{
    // Transform into the surface reference frame 
    transform(p, v, rotation_matrix, surface_position);

    // Check if it is a segment
    float r_off_sq = offset.x * offset.x + offset.y * offset.y;
    float z0 = 0.0f;
    
    // Segment: move to the "mother surface" origin (since we are in the segment origin)
    if (!is_fresnel && r_off_sq > R_EPS) {
        z0 = spherical_sag(r_off_sq, curvature);
        p.x += offset.x;
        p.y += offset.y;
        p.z += z0;
    } else if (r_off_sq > R_EPS) { // Fresnel flat segment: just apply offset
        p.x += offset.x;
        p.y += offset.y;
    }

    // Shift near the surface to increase precision
    float t_shift = 0.0f;
    
    if (fabsf(v.z) > ON_AXIS_EPS) {
        t_shift = -p.z / v.z;
        // Update p to be exactly on the z=0 plane
        p.x = fmaf(v.x, t_shift, p.x);
        p.y = fmaf(v.y, t_shift, p.y);
        p.z = 0.0f; 
    }
    else if (fabsf(v.x) > ON_AXIS_EPS) {
        t_shift = -p.x / v.x;
        // Update p to be exactly on the x=0 plane
        p.x = 0.0f;
        p.y = fmaf(v.y, t_shift, p.y);
        p.z = fmaf(v.z, t_shift, p.z);
    }
    else if (fabsf(v.y) > ON_AXIS_EPS) {
        t_shift = -p.y / v.y;
        // Update p to be exactly on the y=0 plane
        p.x = fmaf(v.x, t_shift, p.x);
        p.y = 0.0f;
        p.z = fmaf(v.z, t_shift, p.z);
    }

    // Fresnel surfaces have 0 curvature for intersection purposes
    float A = is_fresnel ? 0.0f : curvature;
    
    t_out = ERROR_VALUE;

    if (fabsf(A) < CURVATURE_EPS) {
        if (fabsf(v.z) > ON_AXIS_EPS) {
            if (t_shift > DIST_EPS) {
                // Aperture check
                float x_seg = p.x - offset.x;
                float y_seg = p.y - offset.y;
                if (check_aperture(x_seg, y_seg, outer_aperture, inner_aperture, aperture_shape, central_hole_shape)) {
                    t_out = t_shift;
                }
            }
        }
    } 
    else {
        // Solve quadratic equation

        float dot_pp = fmaf(p.x, p.x, fmaf(p.y, p.y, p.z * p.z));
        float dot_pv = fmaf(p.x, v.x, fmaf(p.y, v.y, p.z * v.z));

        float B = fmaf(A, dot_pv, -v.z);
        float C = fmaf(A, dot_pp, -2.0f * p.z);

        float discriminant = fmaf(B, B, -A * C);

        if (discriminant >= 0.0f) {
            float sqrt_d = sqrtf(discriminant);
            float inv_A = 1.0f / A;

            float t1_local = (-B - sqrt_d) * inv_A;
            float t2_local = (-B + sqrt_d) * inv_A;

            // Check root 1
            float t1_final = ERROR_VALUE;
            {
                // Hit position relative to mother sphere
                float x_hit = fmaf(v.x, t1_local, p.x);
                float y_hit = fmaf(v.y, t1_local, p.y);
                float z_hit = fmaf(v.z, t1_local, p.z);

                // Hit position relative to segment center
                float x_seg = x_hit - offset.x;
                float y_seg = y_hit - offset.y;

                if (check_aperture(x_seg, y_seg, outer_aperture, inner_aperture, aperture_shape, central_hole_shape)) {
                    // Check if hit is within the valid hemisphere (sag < Radius)
                    if (fabsf(z_hit) < fabsf(inv_A)) {
                        t1_final = t_shift + t1_local;
                        if (t1_final <= DIST_EPS) t1_final = ERROR_VALUE;
                    }
                }
            }

            // Check root 2
            float t2_final = ERROR_VALUE;
            {
                float x_hit = fmaf(v.x, t2_local, p.x);
                float y_hit = fmaf(v.y, t2_local, p.y);
                float z_hit = fmaf(v.z, t2_local, p.z); 

                float x_seg = x_hit - offset.x;
                float y_seg = y_hit - offset.y;

                if (check_aperture(x_seg, y_seg, outer_aperture, inner_aperture, aperture_shape, central_hole_shape)) {
                    if (fabsf(z_hit) < fabsf(inv_A)) {
                        t2_final = t_shift + t2_local;
                        if (t2_final <= DIST_EPS) t2_final = ERROR_VALUE;
                    }
                }
            }

            // Select the solution
            if (t1_final != ERROR_VALUE && t2_final != ERROR_VALUE) {
                t_out = fminf(t1_final, t2_final);
            } else if (t1_final != ERROR_VALUE) {
                t_out = t1_final;
            } else {
                t_out = t2_final;
            }
        }
    }
}
/**
 * @brief Calculates the distance along a ray to an aspherical surface intersection, considering surface shape and aperture.
 *
 * This function computes the distance ``t`` along a ray (defined by origin ``p`` and direction ``v``)
 * to a surface. The function also handles aperture checking for circular and hexagonal shapes.
 *
 * The ray is first transformed into the surface's local coordinate system using ``transform``. Then, the intersection
 * distance ``t`` is calculated based on the surface type. Finally, an aperture check is performed if ``aperture_shape``
 * is either ``CIRCULAR``, ``HEXAGONAL`` or ``SQUARE``. If the intersection point lies outside the defined aperture, ``t`` is set to a large value (1e9f).
 *
 * After the intersection and aperture checks, the ray is transformed back into the original coordinate system using ``transform_back``.
 *
 * @param t The calculated distance along the ray to the surface (output parameter).
 *          Set to 1e9f if no valid intersection is found (outside aperture or ray misses surface).
 * @param p The starting point of the ray. It is both an input and output parameter.
 *                   Input: Ray origin in the global coordinate system.
 *                   Output: Ray origin transformed back into the global coordinate system after being temporarily transformed into the surface's local coordinate system.
 * @param v The direction vector of the ray. It is both an input and output parameter.
 *                      Input: Ray direction in the global coordinate system.
 *                      Output: Ray direction transformed back into the global coordinate system after being temporarily transformed into the surface's local coordinate system.
 * @param curvature The curvature of the surface (1/radius for spherical surfaces, 0 for flat surfaces).
 * @param conic_constant The conic constant of the surface.
 * @param aspheric_coeffs A pointer to an array of aspheric coefficients for the surface.
 * @param is_fresnel A boolean flag indicating whether the surface is a Fresnel surface (treated as flat).
 * @param outer_aperture The outer radius of the surface aperture.
 * @param inner_aperture The inner radius of the surface aperture.
 * @param aperture_shape An integer representing the shape of the aperture:
 *                       - 0 (CIRCULAR): Circular aperture.
 *                       - 1 (HEXAGONAL): Hexagonal aperture.
 *                       - 2 (SQUARE): Hexagonal aperture.
 *                       - Other values: No aperture check is performed.
 * @param surface_position A float3 representing the origin of the surface's local coordinate system in the global coordinate system.
 * @param rotation_matrix A pointer to a 9-element array representing the 3x3 rotation matrix to transform from the global
 *                       coordinate system to the surface's local coordinate system. The matrix is assumed to be stored in
 *                       row-major order:
 *
 *                           | rotation_matrix[0] rotation_matrix[1] rotation_matrix[2] |
 *                           | rotation_matrix[3] rotation_matrix[4] rotation_matrix[5] |
 *                           | rotation_matrix[6] rotation_matrix[7] rotation_matrix[8] |
 */
__device__ void 
distance_to_aspherical_surface(
    float& t,
    float3 p,
    float3 v,
    float2 offset,
    float curvature,
    float conic_constant,
    const float* aspheric_coeffs,
    bool is_fresnel,
    float outer_aperture,
    float inner_aperture,
    int aperture_shape,
    int central_hole_shape,
    float3 surface_position,
    const float* rotation_matrix
)
{
    // Transform into the surface reference frame 
    transform(p, v, rotation_matrix, surface_position);

    // Check if it is a segment
    float r_off = sqrtf(offset.x*offset.x + offset.y*offset.y);

    // Segment: move to the "mother surface" origin (since we are in the segment origin)
    if (r_off > R_EPS) {
        float z0 = aspherical_sag(
            r_off,
            curvature,
            conic_constant,
            aspheric_coeffs,
            is_fresnel,
            outer_aperture
        );
        p.x += offset.x;
        p.y += offset.y;
        p.z += z0;
    }

    // At this point the distance to the surface 
    // will be computed regardless if it is a segment
    // or a monolithic surface.
    // The segment is by default oriented like the
    // mother surface. A tilt angle represents only a deviation.

    // Handle special cases (on-axis rays and fresnel/flat surfaces)
    bool done = false;

    // Distance to the tangential plane
    float a = ERROR_VALUE;
    float inv_vz = ERROR_VALUE;
    if (fabsf(v.z) > ON_AXIS_EPS) {
        inv_vz = 1.f / v.z;
        a = -p.z * inv_vz;
    }

    // Flat or Fresnel surface
    if ((fabsf(curvature) < CURVATURE_EPS) || (is_fresnel == true)) {
        t = a;
        done = true;
        if (t == ERROR_VALUE) 
            return;
    }

    // On-axis ray
    if (1.f - fabsf(v.z) < ON_AXIS_EPS) {
        float r = sqrtf(p.x*p.x + p.y*p.y);
        float sag = aspherical_sag(
            r,
            curvature,
            conic_constant,
            aspheric_coeffs,
            is_fresnel,
            outer_aperture
        );
        t = (sag - p.z) * inv_vz;
        done = true;
    }
    
    if (done == false) { 
        // Distance to the aperture plane
        float b = ERROR_VALUE;
        if (fabsf(v.z) > ON_AXIS_EPS) {
            float border_sag = aspherical_sag(
                outer_aperture,
                curvature,
                conic_constant,
                aspheric_coeffs,
                is_fresnel,
                outer_aperture
            );
            b = (border_sag - p.z) * inv_vz;
        }
        
        // Not true at all but works for most cases
        // TODO: FIX THIS APPROXIMATION
        //       Maybe just using as start: c*v.z<0 ? b : a
        float max_surf_radius = 1.f/curvature;
        float max_surf_radius_sq = max_surf_radius*max_surf_radius;

        bool simple_case;
        if ((a == ERROR_VALUE) || (b == ERROR_VALUE)) {
            simple_case = false;
        }
        else {
            float xa = fmaf(v.x, a, p.x);
            float ya = fmaf(v.y, a, p.y);    
            float ra_sq = xa*xa + ya*ya; 

            float xb = fmaf(v.x, b, p.x);
            float yb = fmaf(v.y, b, p.y);    
            float rb_sq = xb*xb + yb*yb; 
            simple_case = (rb_sq <= max_surf_radius_sq) && (ra_sq <= max_surf_radius_sq);
        }

        // If the ray intersects both reference planes inside the aperture
        if (simple_case == true) {
            t = find_ray_aspheric_intersection(
                p,
                v,
                fminf(a, b),
                curvature,
                conic_constant,
                aspheric_coeffs,
                is_fresnel,
                outer_aperture
            );
        }
        else { // Double intersection
            if (1.f - fabsf(v.z) > ON_AXIS_EPS) {
                float a = v.x*v.x + v.y*v.y;
                float b = -2.f * (p.x*v.x + p.y*v.y);
                float c = p.x*p.x + p.y*p.y - max_surf_radius*max_surf_radius;

                float delta = b*b - 4.f*a*c;

                // Intersection with the reference cylinder
                if (delta >= 0.f) {
                
                    float sqrt_delta = sqrtf(delta);

                    float t1_cyl = -0.5f*(-b - copysignf(sqrt_delta, b))/a;
                    float t2_cyl = c / a / t1_cyl;

                    float t1 = find_ray_aspheric_intersection(
                        p,
                        v,
                        t1_cyl,
                        curvature,
                        conic_constant,
                        aspheric_coeffs,
                        is_fresnel,
                        outer_aperture
                    );
                    float t2 = find_ray_aspheric_intersection(
                        p,
                        v,
                        t2_cyl,
                        curvature,
                        conic_constant,
                        aspheric_coeffs,
                        is_fresnel,
                        outer_aperture
                    );
                    t = t1 < 0.f ? t2 : (t2 < 0.f ? t1 : fminf(t1, t2));
                }
                else {
                    t = ERROR_VALUE;
                    return;
                }
            }
        }
    }

    // Move to the intersection
    // If the surface is a segment move back to its origin.
    float x = fmaf(v.x, t, p.x) - offset.x;
    float y = fmaf(v.y, t, p.y) - offset.y;

    // Check Aperture using the extracted function
    if (!check_aperture(x, y, outer_aperture, inner_aperture, aperture_shape, central_hole_shape)) {
        t = ERROR_VALUE;
        return;
    }
}

/**
 * @brief Calculates the distance from a point to a cylindrical surface along a given direction.
 *
 * This function determines the distance ``t`` that a ray, starting at point ``p`` and traveling in 
 * direction ``v``, must travel to intersect a cylindrical surface. The cylinder is defined by its 
 * ``radius``, ``height``, ``surface_position`` (the center of the cylinder
 * ), and a ``rotation_matrix``
 * that orients it in 3D space.
 *
 * The function first transforms the ray into the cylinder's local coordinate system to simplify
 * the intersection calculation. It then solves the quadratic equation resulting from the 
 * intersection of a line and a cylinder. The function returns the smallest positive solution for ``t``,
 * indicating the nearest intersection point. If no intersection occurs, or if the intersection 
 * point falls outside the cylinder's height, ``t`` is set to ``ERROR_VALUE`` (likely a predefined 
 * constant, e.g., -1.0f).
 *
 * @param t Output parameter. The calculated distance to the intersection point. Set to ``ERROR_VALUE``
 *          if no intersection is found or if the intersection is outside the cylinder's height.
 * @param p The starting point of the ray (float3, likely a struct or class representing a 
 *          3D point with x, y, z coordinates).
 * @param v The direction vector of the ray (float3).
 * @param radius The radius of the cylinder.
 * @param height Half the total height of the cylinder (the cylinder extends from -height to +height along its local z-axis, centered at ``surface_position``).
 * @param is_hollow Whether a ray can pass inside the cylinder curved surface.
 * @param surface_position The position of the **center** of the cylinder in the global 
 *                       coordinate system (float3).
 * @param rotation_matrix A pointer to a flattened 3x3 rotation matrix that transforms from the 
 *                        global coordinate system to the cylinder's local coordinate system.
 *
 * @note The function uses a small epsilon value ``ON_AXIS_EPS`` (likely a predefined constant) to handle 
 *       the special case where the ray is nearly parallel to the cylinder's axis.
 * @note The function assumes the cylinder's axis is aligned with the z-axis in its local coordinate system.
 * @note The ``transform`` and ``transform_back`` functions are assumed to be defined elsewhere and handle 
 *       the coordinate transformations between the global and local coordinate systems.
 */
__device__ void 
distance_to_cylindrical_surface(
    float& t,
    float3 p,
    float3 v,
    float radius,
    float height,
    bool top,
    bool bottom,
    float3 surface_position,
    const float* __restrict__ rotation_matrix
)
{
    // Transform into the surface local reference frame (cylinder centered at 0,0,0)
    transform(p, v, rotation_matrix, surface_position);

    float half_height = 0.5f * height;

    float t_flat = -ERROR_VALUE;
    
    // Check if ray is not parallel to the caps
    if (fabsf(v.z) > ON_AXIS_EPS) {
        float inv_vz = 1.0f / v.z;
        float t_up   = ( half_height - p.z) * inv_vz;
        float t_down = (-half_height - p.z) * inv_vz;

        // If the ray is moving away from both caps, no intersection
        if ((t_up < 0.f) && (t_down < 0.f)) {
            t = ERROR_VALUE;
            return; 
        }

        // Logic for which cap to pick
        if (top && bottom) {
            if (t_up * t_down <= 0.f) 
                t_flat = fmaxf(t_up, t_down);
            else 
                t_flat = fminf(t_up, t_down);
        } else if (top) {
            t_flat = t_up;
        } else {
            t_flat = t_down;
        }

        // Check if the intersection with the plane is within the radius
        if (t_flat > 0.f) {
            float x_flat = fmaf(v.x, t_flat, p.x);
            float y_flat = fmaf(v.y, t_flat, p.y);
            if ((x_flat*x_flat + y_flat*y_flat) > (radius*radius)) {
                t_flat = -ERROR_VALUE; // Missed the cap disk
            }
        } else {
            t_flat = -ERROR_VALUE;
        }
    }

    // Cylinder intersection
    float t_cyl = -ERROR_VALUE;
    
    // Squared length of the ray direction vector in the XY plane
    float a = fmaf(v.x, v.x, v.y*v.y); 

    // Only compute if ray is not parallel to the cylinder axis
    if (a > ON_AXIS_EPS) { 
        
        // To increase precision:
        //     - shift 'p' along the ray 'v' to the point closest to the Z-axis.
        float t_shift = -(p.x * v.x + p.y * v.y) / a;

        // Calculate the coordinates of the ray at this shifted position
        float3 p_sh = {
            fmaf(v.x, t_shift, p.x),
            fmaf(v.y, t_shift, p.y),
            0.f // Z doesn't matter for the 2D circle intersection
        };

        // c = x^2 + y^2 - r^2
        float dist = hypotf(p_sh.x, p_sh.y);
        float c_shifted = (dist - radius) * (dist + radius);

        // a*t_local^2 + c_shifted = 0 -> t_local^2 = -c_shifted / a
        float discr = -c_shifted / a;

        if (discr >= 0.f) {
            float sqrt_discr = sqrtf(discr);
            
            // The two intersections relative to t_shift
            float t1_local = -sqrt_discr;
            float t2_local =  sqrt_discr;

            // Convert back to absolute distance from original P
            float t1 = t_shift + t1_local;
            float t2 = t_shift + t2_local;

            // Select the smallest positive t
            if (t1 > DIST_EPS) 
                t_cyl = t1;
            else if (t2 > DIST_EPS)
                t_cyl = t2;
            
            // Check height constraint
            if (t_cyl > 0.f) {
                float z_hit = fmaf(v.z, t_cyl, p.z);
                if (fabsf(z_hit) > half_height) {
                    t_cyl = -ERROR_VALUE;
                }
            }
        }
    }

    // Combine results (cylinder and caps)
    if (top || bottom) {
        // No intersection
        if ((t_cyl < 0.f) && (t_flat < 0.f)) {
            t = ERROR_VALUE;
        // Cap intersection
        } else if (t_cyl < 0.f) {
            t = t_flat;
        // Cylinder intersection
        } else if (t_flat < 0.f) {
            t = t_cyl;
        // Both intersections, select the smallest
        } else {
            t = fminf(t_cyl, t_flat);
        }
    // Cylinder with no caps, only t_cyl
    } else {
        t = (t_cyl < 0.f) ? ERROR_VALUE : t_cyl;
    }
}

/**
 * @brief Represents an intersection between a ray and a surface.
 */
struct Intersection {
    int surface_index;  /**< Index of the intersected surface. */
    float distance;     /**< Distance along the ray to the intersection point. */
};

struct SurfaceOpticalTables {
    // Optical front side (v.z < 0)
    unsigned long long transmittance_front; 
    unsigned long long reflectance_front;

    // Optical back side (v.z > 0)
    unsigned long long transmittance_back; 
    unsigned long long reflectance_back;

    // Detection efficiency (side independent)
    unsigned long long efficiency;

    // Optical grid info
    float inv_dwl;    // inverse wavelength spacing
    float start_wl;   // start wavelength
    float inv_dang;   // inverse angle spacing
    float start_ang;  // start angle

    // Efficiency grid info
    float eff_inv_dwl;    // inverse wavelength spacing
    float eff_start_wl;   // start wavelength
    float eff_inv_dang;   // inverse angle spacing
    float eff_start_ang;  // start angle
};

/**
 * @brief Refractive index structure. 
 * 
 */
struct RefractiveIndexTable {
    unsigned long long texture; // Texture object handle
    float inv_dwl;  // inverse wavelength spacing
    float start_wl; // start wavelength
};

/**
 * @brief Surface data structure.
 * 
 */
struct SurfaceData {
    float3 position;
    float _pad1;
    float2 offset; // Segment offset
    float rotation_matrix[9]; 
    float curvature;
    float conic_constant;
    float aspheric_coefficients[NUM_ASPHERIC_COEFFS];
    float _pad2;
    float2 aperture_size;
    // For aspherical, spherical and flat surfaces:
    // the outer and inner surface dimensions. 
    // The interpretation depends on the outer and inner shape:
    //   - Circular: radius
    //   - Hexagonal: inradius
    //   - Squared: half-side
    // For a cylindrical surface they represent radius and height.
    int2 aperture_shape;
    // flags:
    // - Circular: flags[0] = is_fresnel.
    // - Aspheric: flags[0] = is_fresnel.
    // - Cylindrical: flags[0] = is_top_open, flags[1] = is_bottom_open.
    bool flags[2];
    char _pad3[2];
    int type;
    int shape;
    int material1;
    // For a 2D surface: material from which a ray with v.z<0 is coming.
    // For a 3D solid: material outside the solid.
    int material2;
    // For a 2D surface: material from which a ray with v.z>0 is coming.
    // For a 3D solid: material inside the solid.
    float scattering_dispersion;
    // Cache for specific sensor info 
    // SiPM tile:
    //    - [0] -> sensor type
    //    - [1] -> sensor start counter
    //    - [2] -> pixels per side
    //    - [3] -> pixel active side
    //    - [4] -> pixels separation
    //    - [5] -> border to active area
    //    - [6] -> ucell size
    //    - [7] -> number of ucells per side
    float sensor_info[8];
};

/**
 * @brief Finds the next surface that a ray intersects.
 * 
 * This function iterates through all surfaces in the system (skipping the ``last_surface``)
 * and calculates the intersection distance between the ray defined by origin ``p`` and
 * direction ``v``. It returns an ``Intersection`` struct containing the index of the 
 * closest intersected surface and the corresponding intersection distance.
 * 
 * Before performing the computationally expensive intersection calculation 
 * the function checks if the ray passes within the bounding sphere of the surface. 
 * If the ray misses the bounding sphere defined by ``bounding_radii_sq``, the surface is skipped.
 *
 * @param intersection Output parameter. An Intersection struct containing the index of the next 
 *   intersected surface and the distance to it. If no valid intersection is 
 *   found, ``intersection.surface_index`` will be -1 and ``intersection.distance`` 
 *   will be ERROR_VALUE.
 * @param last_surface The index of the last intersected surface (to prevent immediate self-intersection).
 * @param p The origin of the ray. 
 * @param v The direction of the ray (should be normalized). 
 * @param surfaces Array of SurfaceData structures containing geometry and physical properties for each surface.
 * 
 * @param num_surfaces The total number of surfaces in the system.
 * @param bounding_radii_sq Array containing the squared radius of the bounding sphere for each surface,
 * used for early ray rejection optimization.
 * @param shapes_cache Array containing the cached surface ID of each surface.
 * 
 */
__device__ 
void next_surface(
    Intersection& intersection,
    int last_surface,
    float3 p,
    float3 v,
    const SurfaceData* surfaces,
    int num_surfaces,
    const float4* __restrict__ bounding_radii_cache, // x,y,z and w=radius
    const int* __restrict__ shapes_cache
)
{
    intersection.surface_index = -1;
    intersection.distance = ERROR_VALUE;

    float t;

    for (int i = 0; i < num_surfaces; i++) {
        // Get just a pointer to surface info
        const SurfaceData* __restrict__ surface = &surfaces[i];

        if ((i == last_surface) && (shapes_cache[i] != CYLINDRICAL))
            continue;

        //////////////////////////////////////////////////////////////////////////////////////////////
        /////////////////////// Check if the ray passes near the surface /////////////////////////////
        //////////////////////////////////////////////////////////////////////////////////////////////
        float4 cached_data = bounding_radii_cache[i]; 
        float3 surf_pos = make_float3(cached_data.x, cached_data.y, cached_data.z);
        float radius_sq = cached_data.w;

        float3 oc = {
            surf_pos.x - p.x,
            surf_pos.y - p.y,
            surf_pos.z - p.z
        };

        // Projection of center onto ray direction
        float t_closest = oc.x * v.x + oc.y * v.y + oc.z * v.z;

        // Closest point on ray to surface center
        float3 closest_p = {
            p.x + t_closest * v.x,
            p.y + t_closest * v.y,
            p.z + t_closest * v.z
        };

        // Closest distance from the ray path to the surface center
        float dist_sq = (closest_p.x - surf_pos.x)*(closest_p.x - surf_pos.x) + 
                        (closest_p.y - surf_pos.y)*(closest_p.y - surf_pos.y) + 
                        (closest_p.z - surf_pos.z)*(closest_p.z - surf_pos.z);

        // If the ray passes outside the bounding sphere, skip computing distance to the surface
        if (dist_sq > radius_sq) {
            continue; 
        }
        /////////////////////////////////////////////////////////////////////////////////////////////
        /////////////////////////////////////////////////////////////////////////////////////////////

        switch(shapes_cache[i]) {
            case CYLINDRICAL: {
                // Here double itersection is possible,
                // so we move away from the last intersection just a bit
                float3 tmp_p = p;
                float add_t = 0.f;
                if (i == last_surface) {
                    add_t = 1e-4; // 100 nm
                    tmp_p.x = fmaf(v.x, add_t, p.x);
                    tmp_p.y = fmaf(v.y, add_t, p.y);
                    tmp_p.z = fmaf(v.z, add_t, p.z);
                }
                distance_to_cylindrical_surface(
                    t, tmp_p, v,
                    surface->aperture_size.x,
                    surface->aperture_size.y,
                    surface->flags[0],
                    surface->flags[1],
                    surface->position,
                    surface->rotation_matrix
                );
                if (i == last_surface) {
                    t = t + add_t;
                }
                break;
            }
            case FLAT:
                distance_to_flat_surface(
                    t, p, v,
                    surface->aperture_size.x,
                    surface->aperture_size.y,
                    surface->aperture_shape.x,
                    surface->aperture_shape.y,
                    surface->position,
                    surface->rotation_matrix
                );
                break;

            case SPHERICAL:
                distance_to_spherical_surface(
                    t, p, v,
                    surface->offset,
                    surface->curvature,
                    surface->flags[0],
                    surface->aperture_size.x,
                    surface->aperture_size.y,
                    surface->aperture_shape.x,
                    surface->aperture_shape.y,
                    surface->position,
                    surface->rotation_matrix
                );
                break;

            default: // ASPHERICAL
                distance_to_aspherical_surface(
                    t, p, v,
                    surface->offset,
                    surface->curvature,
                    surface->conic_constant,
                    surface->aspheric_coefficients,
                    surface->flags[0],
                    surface->aperture_size.x,
                    surface->aperture_size.y,
                    surface->aperture_shape.x,
                    surface->aperture_shape.y,
                    surface->position,
                    surface->rotation_matrix
                );
                break;
        }

        // Check if it is a valid intersection (inside the aperture and positive distance)
        if ((t >= DIST_EPS) && (t < intersection.distance)) {
            intersection.distance = t;
            intersection.surface_index = i;
        }
    }
}

/**
 * @brief Performs linear interpolation on a 1D texture.
 *
 * @param x The coordinate at which to interpolate.
 * @param inv_dx Inverse step size (1/dx) of the texture grid.
 * @param start_x Starting coordinate of the texture grid.
 * @param tex The CUDA texture object.
 * @return The interpolated value.
 */
__device__ float interp1d_text(float x, float inv_dx, float start_x, cudaTextureObject_t& tex) {
    float u = (x-start_x)*inv_dx;
    return tex1D<float>(tex, u+0.5f);
}

/**
 * @brief Performs bilinear interpolation on a 2D texture.
 *
 * @param x The x-coordinate.
 * @param y The y-coordinate.
 * @param inv_dx Inverse step size in x (1/dx).
 * @param inv_dy Inverse step size in y (1/dy).
 * @param start_x Starting x value of the grid.
 * @param start_y Starting y value of the grid.
 * @param tex The CUDA texture object.
 * @return The interpolated value.
 */
__device__ float interp2d_text(float x, float y, float inv_dx, float inv_dy, float start_x, float start_y, cudaTextureObject_t& tex) {
    float u = (x-start_x)*inv_dx;
    float v = (y-start_y)*inv_dy;
    return tex2D<float>(tex, u+0.5f, v+0.5f);
}

/**
 * @brief Applies specular reflection to a photon vector.
 * * v_new = v - 2 * (v . n) * n
 */
__device__ inline void apply_reflection(
    float3& v, 
    const float3& normal, 
    float cosine_incident_angle
)
{
    float factor = 2.f * cosine_incident_angle;
    v.x = fmaf(factor, normal.x, v.x);
    v.y = fmaf(factor, normal.y, v.y);
    v.z = fmaf(factor, normal.z, v.z);
}

/**
 * @brief Applies refraction using Snell's law in vector form.
 * 
 * @return true if refraction was successful.
 * @return false if Total Internal Reflection (TIR) occurred.
 *
 */
__device__ inline bool apply_refraction(
    float3& v, 
    const float3& normal, 
    float cosine_incident_angle, 
    float ri_in, 
    float ri_out
)
{
    float refractive_index_ratio = ri_in / ri_out;
    float refractive_index_ratio2 = refractive_index_ratio * refractive_index_ratio;

    // Related to the normal part of the transmitted direction
    // 1 - (n1/n2)^2 * (1 - cos(theta)^2)
    // Note: cosine_incident_angle is guaranteed positive by the caller (dot product check)
    float sqrt_argument = 1.f - refractive_index_ratio2 * (1.f - cosine_incident_angle*cosine_incident_angle);

    // Total Internal Reflection check
    if (sqrt_argument <= 0.f) {
        return false;
    }
    
    // Orthogonal factor
    // n1/n2 * cos(theta_i) - sqrt( ... )
    float factor = refractive_index_ratio * cosine_incident_angle - sqrtf(sqrt_argument);

    // Update vector
    v.x = fmaf(refractive_index_ratio, v.x, factor * normal.x);
    v.y = fmaf(refractive_index_ratio, v.y, factor * normal.y);
    v.z = fmaf(refractive_index_ratio, v.z, factor * normal.z);

    return true;
}

__device__ void apply_scattering(
    float3& v, 
    float scattering_dispersion, // in fraction of pi (degrees/180)
    curandStatePhilox4_32_10_t& state
)
{
    if (scattering_dispersion <= 1.e-6f) return;

    float scattering_angle = scattering_dispersion * sqrtf(-2.f * __logf(curand_uniform(&state)));
    float scattering_azimuth = curand_uniform(&state) * 2.f;

    float sin_theta, cos_theta;
    sincospif(scattering_angle, &sin_theta, &cos_theta);
    float sin_phi, cos_phi;
    sincospif(scattering_azimuth, &sin_phi, &cos_phi);

    float3 v_scat = {sin_theta*cos_phi, -sin_theta*sin_phi, cos_theta};

    float invnorm = rsqrtf(v_scat.x*v_scat.x + v_scat.y*v_scat.y + v_scat.z*v_scat.z);
    float invden = invnorm / (1.f + v.z);
    
    float rot[9] = {
        1.f + v.z - v.x*v.x,      -v.x*v.y,               v.x + v.x*v.z,
               -v.x*v.y,          1.f + v.z - v.y*v.y,    v.y + v.y*v.z,
           -v.x - v.x*v.z,        -v.y - v.y*v.z,         1.f + v.z - v.x*v.x - v.y*v.y
    };

    float nx = (rot[0]*v_scat.x + rot[1]*v_scat.y + rot[2]*v_scat.z) * invden;
    float ny = (rot[3]*v_scat.x + rot[4]*v_scat.y + rot[5]*v_scat.z) * invden;
    float nz = (rot[6]*v_scat.x + rot[7]*v_scat.y + rot[8]*v_scat.z) * invden;

    v.x = nx;
    v.y = ny;
    v.z = nz;
}

__device__ void save_last_surface(
    float& time,
    int& weight,
    int current_surface
)
{
    // Prepare ID to store (Surface Index + 1)
    // Add 1 because 0 is reserved for "no surface"
    int id_to_store = current_surface + 1;
    
    // Re-read weight (in case propagation reduced the bunch size)
    int current_weight = weight;
    
    // Re-pack: | surface ID in upper 16 bits | Weight in lower 16 bits |
    weight = (id_to_store << SURFACE_ID_SHIFT) | (current_weight & WEIGHT_MASK);
}

/**
 * @brief Handles the logic when a photon is detected by a sensitive surface.
 *
 * This function performs the necessary coordinate transformations when a photon terminates on a sensitive surface.
 * 1. If requested (or if saving the last bounce), it transforms the photon from the surface refrence frame back to the telescope frame.
 * 2. If ``save_last_bounce`` is true, it further transforms the photon from the telescope frame
 *    back to the the local (world) reference frame and sets the wavelength to NaN (marking it as a surface hit).
 *
 * @param p Photon position (modified in-place).
 * @param v Photon direction (modified in-place).
 * @param wl Photon wavelength (set to NaN if save_last_bounce is true).
 * @param surface The surface object where detection occurred.
 * @param telescope_rotation_matrix Rotation matrix of the telescope (local frame).
 * @param telescope_position Position of the telescope (local frame).
 * @param save_last_bounce If true, stores the position of the last bounce in the local (world) frame.
 * @param transform_to_telescope_frame If true, transforms the photon back to the telescope frame.
 */
__device__ bool 
detection(
    float3& p, 
    float3& v, 
    float& wl,
    float& time,
    int& weight,
    float thetai,
    int& pixel_id,
    int& sub_pixel_id,
    int current_surface,
    const SurfaceData& surface,
    const SurfaceOpticalTables& optical_tables,
    curandStatePhilox4_32_10_t& state,
    const float* telescope_rotation_matrix, 
    const float3& telescope_position,
    bool save_last_bounce, 
    bool transform_to_telescope_frame
) 
{
    const int sensor_type = __float2int_rn(surface.sensor_info[0]);

    switch(sensor_type) {
        case SIPM_TILE: {
            const float half_side = surface.aperture_size.x;
            const float pixel_active_side = surface.sensor_info[3];
            const float pixels_sep = surface.sensor_info[4];
            const float tile_border_width = surface.sensor_info[5];
            const float dpix = pixel_active_side + pixels_sep;
            const float inv_dpix = 1.0f / dpix;

            // Move origin to the bottom-left corner of the tile
            // on_tile_x>=0 and on_tile_y>=0
            // x=0,y=0 is on pixel1 non-active side
            float offset = half_side - tile_border_width;
            float on_tile_x = p.x + offset;
            float on_tile_y = p.y + offset;
            
            // Find pixel coordinate (i-colomun, j-row)
            const int i = static_cast<int>(floorf(on_tile_x * inv_dpix));
            const int j = static_cast<int>(floorf(on_tile_y * inv_dpix));
            const int n_pix_per_side = __float2int_rn(surface.sensor_info[2]);

            if (i < 0 || i >= n_pix_per_side || j < 0 || j >= n_pix_per_side) {
                return false;
            }

            // Check if the photon reaches the unactive region of the pixel
            // x=0,y=0 is on the lower-left active-side corner
            float local_x = on_tile_x - (static_cast<float>(i) * dpix);
            float local_y = on_tile_y - (static_cast<float>(j) * dpix);

            if ((local_x > pixel_active_side) | (local_y > pixel_active_side)) {
                return false;
            }
            
            const float inv_ucell_size = surface.sensor_info[6];
            if (inv_ucell_size > 1e-4) {
                int n_ucells_per_side = surface.sensor_info[7];
                const int i_ucell = static_cast<int>(floorf(local_x * inv_ucell_size));
                const int j_ucell = static_cast<int>(floorf(local_y * inv_ucell_size));
                sub_pixel_id = j_ucell*n_ucells_per_side + i_ucell;
            }
            
            const int first_pixel_id = __float2int_rn(surface.sensor_info[1]);

            pixel_id = first_pixel_id + j * n_pix_per_side + i;
            
            break;
        }
        default:
            break;
    }

    if ((optical_tables.eff_inv_dang > 1e-6f) || (optical_tables.eff_inv_dwl > 1e-6f)){
        cudaTextureObject_t efficiency = optical_tables.efficiency;
        float detection_p = interp2d_text(
            wl,
            thetai,
            optical_tables.eff_inv_dwl,
            optical_tables.eff_inv_dang,
            optical_tables.eff_start_wl,
            optical_tables.eff_start_ang,
            efficiency
        );
        
        float u = curand_uniform(&state);
        if (u > detection_p) {
            return false;
        }
    }

    // Transform back to the telescope reference system
    // This is done if explicitly requested or if we need to go back to global (save_last_bounce)
    if (transform_to_telescope_frame || save_last_bounce) {
        transform_back(p, v, surface.rotation_matrix, surface.position);
    }

    // Transform back to the global reference system (for visualization)
    // The sensitive surface ID is also registered here
    if (save_last_bounce) {
        transform_back(p, v, telescope_rotation_matrix, telescope_position);
        save_last_surface(
            time,
            weight,
            current_surface
        );
        time = nanf("");
    }

    return true;
}

__device__ inline float3 
get_surface_normal(
    const SurfaceData& surface,
    float3& p
)
{
    float3 surface_normal;
    switch(surface.shape) {
        case FLAT:
            surface_normal = {0.f,0.f,1.f};
            break;

        case SPHERICAL:
            surface_normal = spherical_surface_normal(
                p.x + surface.offset.x,
                p.y + surface.offset.y,
                surface.curvature
            );
            break;
        
        case CYLINDRICAL:
            surface_normal = cylindrical_surface_normal(
                p,
                surface.aperture_size.x,
                surface.aperture_size.y
            );
            break;

        default: // ASPHERICAL
            surface_normal = aspherical_surface_normal(
                p.x + surface.offset.x,
                p.y + surface.offset.y,
                surface.curvature,
                surface.conic_constant,
                surface.aspheric_coefficients,
                surface.aperture_size.x
            );
            break;
    }
    return surface_normal;
}

/**
 * @brief The main ray tracing kernel.
 *
 * This kernel traces individual photons through an optical system, simulating their interactions with surfaces.
 * Surface properties are consolidated into an array of SurfaceData structures.
 * 
 * Interpretation of SurfaceData members depends on surface type:
 * 
 * 1. Aperture Size (SurfaceData.aperture_size):
 * 
 *   - For aspherical, spherical and flat surfaces: half-aperture of the 
 *     surface (aperture_size.x) and half-aperture of the central hole (aperture_size.y).
 *     The interpretation depends on the outer and inner shape: 
 *     the radius for "circular", inradius for "hexagonal" and half-side for "square".
 *   - For a cylindrical surface they represent radius (aperture_size.x) and height (aperture_size.y).
 * 
 * 2. Flags (SurfaceData.flags):
 * 
 *   - For aspherical and spherical surfaces: flags[0] indicates if a surface is a Fresnel surface 
 *     (i.e. is flat, but has the same normal of a non-flat surface).
 *   - For cylindrical surfaces: flags[0] indicates if the surface has a top flat surface; 
 *     flags[1] indicates if the surface has a bottom flat surface. 
 *     If both are true the surface is a solid cylinder.
 * 
 * @param ps Array of photon positions (x, y, z).
 * @param vs Array of photon directions (normalized vectors, x, y, z).
 * @param wls Array of photon wavelengths.
 * @param times Array of photon times (time elapsed since the start of the trace).
 * @param weights Array of photon weights (initially 1).
 * @param pixel_ids ID of the pixel reached by the photon.
 * @param sub_pixel_ids ID of the sub-pixel reached by the photon.
 * @param num_surfaces The total number of surfaces in the optical system.
 * @param telescope_rotation_matrix Rotation matrix of the telescope (global system).
 * @param telescope_position Position of the telescope (global system).
 * @param surfaces Array of SurfaceData structures containing geometry and physical properties for each surface.
 * @param optical_tables Structure containing texture objects and scaling factors for surface transmittance/reflectance.
 * @param refractive_tables Array of RefractiveIndexTable structures (one per material) for refractive index lookups.
 * @param num_photons The total number of photons to trace.
 * @param max_bounces Maximum number of interactions allowed per photon.
 * @param save_last_bounce If true, stores the position of the last bounce (updates weight to store surface ID).
 * @param trans_det_back_to_telescope Whether to move detected photons into the telescope reference system.
 * @param seed Random number generator seed.
 * 
 */
__global__ 
void 
__launch_bounds__(128) 
trace(
    float3* ps,
    float3* vs,
    float* wls,
    float* times,
    int* weights,
    int* pixel_ids,
    int* sub_pixel_ids,
    const float3* telescope_position,
    const float* telescope_rotation_matrix,
    const SurfaceData* surfaces,
    const SurfaceOpticalTables* optical_tables,
    const RefractiveIndexTable* refractive_tables,
    int num_surfaces,
    int num_photons,
    int max_bounces,
    bool save_last_bounce, 
    bool trans_det_back_to_telescope, 
    unsigned long long seed
)
{
    ////////////////////////////////////////////////////////////////////////////
    ////////////////////// Pre-calculate bounding radii ////////////////////////
    ////////////////////////////////////////////////////////////////////////////
    extern __shared__ char sh_mem[]; 
    
    float4* sh_surface_data = (float4*)sh_mem; // .x, .y, .z = pos, .w = radius_sq
    int* sh_surface_shapes = (int*)&sh_surface_data[num_surfaces];

    int t_idx = threadIdx.x;
    for (int i = t_idx; i < num_surfaces; i += blockDim.x) {
        const SurfaceData surf = surfaces[i];

        float sq_radius_bounding_sphere;
        float radius = surf.aperture_size.x;

        if (surf.shape == CYLINDRICAL) {
            float half_height = 0.5f*surf.aperture_size.y;
            sq_radius_bounding_sphere = fmaf(radius, radius, half_height*half_height);
        } else {
            float factor = 1.0f;
            if (surf.aperture_shape.x == HEXAGONAL || surf.aperture_shape.x == HEXAGONAL_PT) 
                factor = 1.15470053f;
            else if (surf.aperture_shape.x == SQUARE)    
                factor = 1.41421356f;
            
            radius *= factor;
            float radius_sq = radius * radius;
            
            if (surf.shape == ASPHERICAL) {
                float sag = aspherical_sag(
                    radius,
                    surf.curvature,
                    surf.conic_constant, 
                    surf.aspheric_coefficients,
                    surf.flags[0],
                    surf.aperture_size.x
                );
                sq_radius_bounding_sphere = fmaf(radius, radius, sag*sag);
            } else {
                // FLAT and SPHERICAL
                sq_radius_bounding_sphere = radius_sq;
            }
        }
        sh_surface_data[i] = make_float4(
            surf.position.x, 
            surf.position.y, 
            surf.position.z, 
            sq_radius_bounding_sphere
        );
        sh_surface_shapes[i] = surf.shape;
    }
    __syncthreads();

    //////////////////////////////////////////////////////////////////////////////
    ////////////////////////// Check thread early exit ///////////////////////////
    //////////////////////////////////////////////////////////////////////////////

    // Photon index
    int k = blockIdx.x * blockDim.x + threadIdx.x;
    if (k >= num_photons) return;

    // No pixel hit by default
    pixel_ids[k] = -1;
    sub_pixel_ids[k] = -1;

    // Optimized rejection: check only time
    if (isnan(times[k])) {
        return;
    }

    //////////////////////////////////////////////////////////////////////////////
    ////////////////////////// Check thread early exit ///////////////////////////
    //////////////////////////////////////////////////////////////////////////////
    
    // Initialize random number generator
    curandStatePhilox4_32_10_t state;
    curand_init(seed, k, 0, &state);

    // Load registers
    float3 p = ps[k];
    float3 v = vs[k];
    float time = times[k];
    float wl = wls[k];
    int pixel_id = pixel_ids[k];
    int sub_pixel_id = sub_pixel_ids[k];

    // Transform into telescope reference system
    transform(p, v, telescope_rotation_matrix, telescope_position[0]);

    // Start couting bounces
    int bounces_counter = 0;

    // Intersection cache
    Intersection intersection;

    //////////////////////////////////////////////////////////////////////////////
    ////////////// Get last surface from the last 16 bit of weigths //////////////
    //////////////////////////////////////////////////////////////////////////////

    // No previous surface by default
    int current_surface = -1; 

    // Extract surface ID from upper 16 bits (SURFACE_ID_SHIFT)
    int packed_val = weights[k];
    int stored_id = packed_val >> SURFACE_ID_SHIFT;
    if (stored_id > 0) {
        current_surface = stored_id - 1;
    }

    // Set the correct weight
    int local_weight = packed_val & WEIGHT_MASK;

    //////////////////////////////////////////////////////////////////////////////
    ////////////////////////////// Start main loop ///////////////////////////////
    //////////////////////////////////////////////////////////////////////////////

    while (true) {

        //////////////////////////////////////////////////////////////////////////////
        /////////////////////////// Find the next surface  ///////////////////////////
        //////////////////////////////////////////////////////////////////////////////

        next_surface(
            intersection,
            current_surface,
            p,
            v,
            surfaces,
            num_surfaces,
            sh_surface_data,
            sh_surface_shapes
        );
        
        int next_surface_index = intersection.surface_index;
        float next_surface_distance = intersection.distance;

        // Reject the photon right away in the following cases
        //   - it reaches an opaque surface
        //   - it doeas not reach any surface
        if ((next_surface_index == -1) || (surfaces[next_surface_index].type == OPAQUE)) {
            reject_photon(ps[k], vs[k], wls[k], times[k]);
            weights[k] = 0;
            break;
        }

        //////////////////////////////////////////////////////////////////////////////
        ////// Move to the next surface and transform into its reference system //////
        //////////////////////////////////////////////////////////////////////////////

        // Get surface info
        const SurfaceData& surface = surfaces[next_surface_index];
        const SurfaceOpticalTables& surface_opt = optical_tables[next_surface_index];

        // Move to the found intersection (i.e. on the surface)
        p.x = fmaf(v.x, next_surface_distance, p.x);
        p.y = fmaf(v.y, next_surface_distance, p.y);
        p.z = fmaf(v.z, next_surface_distance, p.z);

        // Surface rotation (inside the telescope reference system)
        // After this call we are in the surface coordinate system
        transform(p, v, surface.rotation_matrix, surface.position);

        // Update the current surface
        current_surface = next_surface_index;

        //////////////////////////////////////////////////////////////////////////////
        ////////////// Compute surface normal and check incidence angle //////////////
        //////////////////////////////////////////////////////////////////////////////

        // Compute surface normal
        float3 surface_normal = get_surface_normal(
            surface,
            p
        );

        // Cosine of the incidence angle on the surface
        float cosine_incident_angle = - (
            surface_normal.x*v.x + 
            surface_normal.y*v.y + 
            surface_normal.z*v.z
        );

        // cos(theta_i)<0 -> same orientation of the normal
        // Exit point from a 3D solid:
        //     - material1 is the material ouside the volume
        //     - material2 is the material inside the volume
        // For a 2D surface:
        //     - material1 is the material from which 
        //       the photon comes when v.z<0
        //     - material2 is the material into which
        //       the photon goes when v.z>0
        //
        // Since the normal is outward for solids and with
        // n.z>0 for surfaces, we need to swap indices
        // when the ray has the same orientation as the normal.
        
        bool on_back = cosine_incident_angle < 0.f;
        bool switch_refractive_index = false;
        if (on_back) {
            switch_refractive_index = true;
            // Ensure normal is against the incoming ray
            // This is needed to calculate
            surface_normal.x = -surface_normal.x;
            surface_normal.y = -surface_normal.y;
            surface_normal.z = -surface_normal.z;
            cosine_incident_angle = -cosine_incident_angle;
        }

        //////////////////////////////////////////////////////////////////////////////
        ////////// Get refractive index (swap if necessary) and update time //////////
        //////////////////////////////////////////////////////////////////////////////

        int material_in = surface.material1;
        int material_out = surface.material2;

        if (switch_refractive_index) {
            int tmp = material_in;
            material_in = material_out;
            material_out = tmp;
        }

        // Get refractive index
        cudaTextureObject_t texture_ri_in = refractive_tables[material_in].texture;
        float ri_in = interp1d_text(
            wl,
            refractive_tables[material_in].inv_dwl,
            refractive_tables[material_in].start_wl,
            texture_ri_in
        );
        
        // Update time
        time += next_surface_distance * ri_in * INV_C_LIGHT;

        //////////////////////////////////////////////////////////////////////////////
        ///////// Check if the photon reaches an opaque side of the surface //////////
        ///////// or if it reaches a sensitive surface                      //////////
        //////////////////////////////////////////////////////////////////////////////

        int surface_type = surface.type;

        // Check if the photon has reached the sensitive surface side
        bool on_sensitive = false;

        // Sensitive on both side
        if ((surface_type == SENSITIVE) || (surface_type == REFLECTIVE_SENSITIVE)) {
            on_sensitive = true;
        }
        else {
            bool sensitive_back = (surface_type == SENSITIVE_BACK) || (surface_type == REFLECTIVE_SENSITIVE_BACK);
            bool sensitive_front = (surface_type == SENSITIVE_FRONT) || (surface_type == REFLECTIVE_SENSITIVE_FRONT);

            bool reject = false;
            if (on_back) {
                if (sensitive_back) on_sensitive = true;
                else if ((surface_type == REFLECTIVE_FRONT) || (sensitive_front)) reject = true;
            }
            else {
                if (sensitive_front) on_sensitive = true;
                else if ((surface_type == REFLECTIVE_BACK) || (sensitive_back)) reject = true;
            }

            if (reject) {
                reject_photon(ps[k], vs[k], wls[k], times[k]);
                weights[k] = 0;
                break;
            }
        }

        //////////////////////////////////////////////////////////////////////////////
        ////// Get surface optical properties (if any) and decide if the photon //////
        ////// is going to be reflected, refracted or absorbed at the interface //////
        //////////////////////////////////////////////////////////////////////////////

        bool is_reflected = false;

        bool has_optical_props = (surface_opt.inv_dang > 1e-6f) || (surface_opt.inv_dwl > 1e-6f);
        
        // Compute theta only if needed
        float thetai = 0.0f;
        if (has_optical_props || on_sensitive) {
            thetai = acosf(cosine_incident_angle) * RAD2DEG;
        }

        // No surface optical properties
        if (!has_optical_props) {
            if (on_sensitive) {
                bool detected = detection(
                    p, v, wl, time, local_weight,
                    thetai,
                    pixel_id,
                    sub_pixel_id,
                    current_surface,
                    surface,
                    surface_opt,
                    state,
                    telescope_rotation_matrix,
                    telescope_position[0], 
                    save_last_bounce,
                    trans_det_back_to_telescope
                );

                if (!detected) {
                    reject_photon(p, v, wl, time);
                    local_weight = 0;
                }
                ps[k] = p; vs[k] = v; wls[k] = wl; times[k] = time;
                weights[k] = local_weight; pixel_ids[k] = pixel_id;
                sub_pixel_ids[k] = sub_pixel_id;
                break;
            }

            if (surface_type == REFRACTIVE) {
                is_reflected = false;
            }
            else { // opaque and dummy surfaces do not reach this point
                is_reflected = true;
            }
        }
        else { // Surface optical properties
            {
                // Random number to sample the process
                float u = curand_uniform(&state);

                // Get transmittance and reflectance textures
                cudaTextureObject_t transmittance, reflectance;
                
                if (on_back) {
                    transmittance = surface_opt.transmittance_back;
                    reflectance = surface_opt.reflectance_back;
                } 
                else {
                    transmittance = surface_opt.transmittance_front;
                    reflectance = surface_opt.reflectance_front;
                }
                
                // Transmission probability for refractive surfaces
                float transmission_p;
                if (surface_type != REFRACTIVE) {
                    transmission_p = 0.f;
                }
                else {
                    transmission_p = interp2d_text(
                        wl,
                        thetai,
                        surface_opt.inv_dwl,
                        surface_opt.inv_dang,
                        surface_opt.start_wl,
                        surface_opt.start_ang,
                        transmittance
                    );
                }
                
                // Reflection probability for reflective surfaces
                float reflection_p = interp2d_text(
                    wl,
                    thetai,
                    surface_opt.inv_dwl,
                    surface_opt.inv_dang,
                    surface_opt.start_wl,
                    surface_opt.start_ang,
                    reflectance
                );
                
                // Compute absorption probability
                // For non-refractive surfaces this it is just 1 - reflection_p
                float absorption_p = 1.f - reflection_p - transmission_p;

                // Decide which process the photon is going to follow
                //  - absorption
                //  - reflection
                //  - transmission
                if (u < absorption_p) {
                    // Handle absorption by sensitive surfaces
                    bool is_reflective_sensitive = 
                        (surface_type == REFLECTIVE_SENSITIVE) || 
                        (surface_type == REFLECTIVE_SENSITIVE_BACK) || 
                        (surface_type == REFLECTIVE_SENSITIVE_FRONT);
                    
                    if (is_reflective_sensitive) {
                        bool detected = detection(
                            p, v, wl, time, local_weight,
                            thetai,
                            pixel_id,
                            sub_pixel_id,
                            current_surface,
                            surface, 
                            surface_opt,
                            state,
                            telescope_rotation_matrix,
                            telescope_position[0], 
                            save_last_bounce, 
                            trans_det_back_to_telescope
                        );
                        if (!detected) {
                            reject_photon(p, v, wl, time);
                            local_weight = 0;
                        }
                    }
                    else { // Absorbtion by a non sensitive surfaces
                        reject_photon(p, v, wl, time);
                        local_weight = 0;
                    }
                    // Break in any case
                    ps[k] = p; vs[k] = v; wls[k] = wl; times[k] = time;
                    weights[k] = local_weight; pixel_ids[k] = pixel_id;
                    sub_pixel_ids[k] = sub_pixel_id;
                    break;
                }
                else if (u < absorption_p + reflection_p) {
                    is_reflected = true;
                }
            }
        }

        // Optical processes at the interface
        // A dummy surface can have properties, but can only absorb photons
        if (surface_type != DUMMY) {
            if (!is_reflected) {
                cudaTextureObject_t texture_ri_out = refractive_tables[material_out].texture;
                float ri_out = interp1d_text(
                    wl,
                    refractive_tables[material_out].inv_dwl,
                    refractive_tables[material_out].start_wl,
                    texture_ri_out
                );

                // Apply refraction
                bool not_internally_reflected = apply_refraction(
                    v,
                    surface_normal,
                    cosine_incident_angle,
                    ri_in,
                    ri_out
                );
                
                // Do not kill internally reflected photons
                if (!not_internally_reflected) {
                    is_reflected = true;
                }
            }
            // Reflect also internally refleceted photons
            if (is_reflected) {
                apply_reflection(
                    v,
                    surface_normal,
                    cosine_incident_angle
                );
            }
        }

        // Gaussian scattering
        if (surface.scattering_dispersion > 1e-6f) {
            apply_scattering(
                v, 
                surface.scattering_dispersion, 
                state
            );
        }

        // Transform back to the telescope system and look for the next surface
        transform_back(p, v, surface.rotation_matrix, surface.position);

        bounces_counter += 1;

        if (bounces_counter == max_bounces) {
            // Normal behaviour (to kill internally reflected photons)
            if (!save_last_bounce) {
                reject_photon(p, v, wl, time);
                local_weight = 0;
            }
            else { // For visualization
                transform_back(p, v, telescope_rotation_matrix, telescope_position[0]);    
                save_last_surface(
                    time,
                    local_weight,
                    current_surface
                );
            }
            ps[k] = p; vs[k] = v; wls[k] = wl; times[k] = time; weights[k] = local_weight;
            break;
        }

    } // main while loop
}

/**
 * @brief Simulates atmospheric transmission.
 *
 * This kernel function applies atmospheric transmission rejecting photons based on a 2D transmission curve (wavelength and emission altitude).
 *
 * @param ps Array of photon positions.
 * @param vs Array of photon directions.
 * @param wls Array of photon wavelengths.
 * @param ts Array of photon times.
 * @param zems Array of photon zenith angles.
 * @param tr_curves Array containing the 2D transmission curve data.
 * @param tr_curve_wl Array of wavelength values for the transmission curve.
 * @param tr_curve_zem Array of emission altitude values for the transmission curve.
 * @param tr_curve_sizes Array containing the dimensions (x1_size, x2_size) of the 2D transmission curve.  ``tr_curve_sizes[0]`` is the wavelength size, and ``tr_curve_sizes[1]`` is the emission altitude size.
 * @param n_ph The total number of photons.
 * 
 */
__global__
void
atmospheric_transmission(
    float3* ps,
    float3* vs,
    float* wls,
    float* ts,
    const float* zems,
    const float* tr_curves,
    const float* tr_curve_wl,
    const float* tr_curve_zem,
    const int* tr_curve_sizes,
    int n_ph,
    unsigned long long seed
)
{
    int k = blockIdx.x*blockDim.x + threadIdx.x;
    if (k >= n_ph) return;

    // Transmission interpolation
    int x1_size = tr_curve_sizes[0];
    int x2_size = tr_curve_sizes[1];

    // Only one 2D transmission
    int start_x1 = 0;
    int start_x2 = 0;
    int start_curve = 0;

    // tau(wl,zem) interpolate the optical depth curve 
    float tau = unregular_interp2d(
        wls[k],
        zems[k],
        tr_curve_wl,
        tr_curve_zem,
        tr_curves,
        x1_size,
        x2_size,
        start_x1,
        start_x2,
        start_curve
    );

    // Take into account zenith angle
    float transmission = expf(tau/vs[k].z);
    
    // Initialize generator
    curandStatePhilox4_32_10_t state;
    curand_init(seed, k, 0, &state);

    // Apply transmission to the bunch
    float u = curand_uniform(&state);
    if (u > transmission) 
        reject_photon(ps[k], vs[k], wls[k], ts[k]);
}

/**
 * @brief Transforms photon positions and directions based on a telescope position and orientation.
 *
 * This kernel performs a coordinate transformation on a set of photons, effectively simulating
 * the observation of those photons by a telescope located at a specific position and 
 * with a specific orientation.  The transformation consists of a translation and a rotation.
 * Is assumed that the altitude axis is not displaced with respect to the azimuth axis and intersect 
 * at the telescope origin.
 *
 * @param ps  An array of float3 representing the positions of the photons.  Modified in-place.
 * @param vs  An array of float3 representing the direction vectors of the photons. Modified in-place.
 * @param p0  A float3 representing the position of the telescope.
 * @param r_mat A float array representing the rotation matrix.
 * @param n_ph The number of photons to transform.
 */
__global__ void telescope_transform(float3* ps, float3* vs, float3 p0, float* r_mat, int n_ph)
{
    int i = blockIdx.x*blockDim.x + threadIdx.x;
    if (i >= n_ph) return;
    
    // Translate position
    ps[i].x -= p0.x;
    ps[i].y -= p0.y;
    ps[i].z -= p0.z;
    
    // Rotate position and direction
    rotate(ps[i], r_mat);
    rotate(vs[i], r_mat);
}

} // extern C