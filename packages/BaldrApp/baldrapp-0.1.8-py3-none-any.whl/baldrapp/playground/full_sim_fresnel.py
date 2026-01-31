#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baldr optical chain (no post-CS lens):
Pupil(12 mm) -> OAP f=254 mm -> Phase Mask -> Collimator (30/15 mm, thin lens phase)
-> Imaging lens f=184 mm -> Cold Stop (2.145 mm) -> Fresnel z -> Detector pupil (~288 µm)

Deps: numpy, matplotlib, aotools
"""

import numpy as np
import matplotlib.pyplot as plt
import aotools

# -------------------- helpers --------------------

def circ_mask_xy(X, Y, radius, cx=0.0, cy=0.0):
    """Binary circular mask of radius (m) centered at (cx, cy)."""
    return (np.hypot(X - cx, Y - cy) <= radius).astype(float)

def lens_against_dx(dx_in, wvl, f, N):
    """AOtools lensAgainst output sampling: dx_out = (λ f) / (N dx_in)."""
    return (wvl * f) / (N * dx_in)

def apply_thin_lens(U, dx, wvl, f):
    """
    Multiply by thin-lens phase exp(-i k (x^2+y^2)/(2f)) at the current plane.
    Builds a grid with exactly the same shape as U, centered at 0.
    """
    Ny, Nx = U.shape
    k = 2*np.pi / wvl
    x = (np.arange(Nx) - (Nx - 1)/2.0) * dx
    y = (np.arange(Ny) - (Ny - 1)/2.0) * dx
    X, Y = np.meshgrid(x, y)
    phase = np.exp(-1j * k * (X**2 + Y**2) / (2.0 * f))
    return U * phase

def measure_pupil_diameter(I, dx, frac=0.5):
    """
    Estimate pupil diameter along the central horizontal line
    at fractional level 'frac' of the peak (default 0.5).
    """
    cy = I.shape[0] // 2
    prof = I[cy, :] / (np.max(I) + 1e-20)
    mid = I.shape[1] // 2
    right = np.where(prof[mid:] < frac)[0]
    if right.size == 0:
        return np.nan
    Rpix = right[0]
    return 2.0 * Rpix * dx

def calibrate_z_for_pupil(U_cs, dx_cs, wvl, target_diam_m, z0=0.020, iters=4, frac=0.5):
    """
    Calibrate free-space distance z (cold stop -> detector) so that the pupil
    diameter at the detector ~ target_diam_m. Simple proportional loop.
    """
    z = float(z0)
    for _ in range(iters):
        U_det = aotools.opticalpropagation.angularSpectrum(
            inputComplexAmp=U_cs, wvl=wvl,
            inputSpacing=dx_cs, outputSpacing=dx_cs, z=z
        )
        I_det = np.abs(U_det)**2
        d_meas = measure_pupil_diameter(I_det, dx_cs, frac=frac)
        if not np.isfinite(d_meas) or d_meas <= 0:
            break
        z *= (target_diam_m / d_meas)
        z = float(np.clip(z, 1e-3, 1.0))  # 1 mm .. 1 m
    U_det = aotools.opticalpropagation.angularSpectrum(
        inputComplexAmp=U_cs, wvl=wvl,
        inputSpacing=dx_cs, outputSpacing=dx_cs, z=z
    )
    return z, U_det

# -------------------- main simulation --------------------

def simulate_baldr_no_post_lens(
    mode="bright",                 # "bright" (f_coll=30 mm) or "faint" (f_coll=15 mm)
    wvl=1.65e-6,                   # 1.65 µm
    D_in=12e-3,                    # entrance pupil diameter = 12 mm
    f_oap=0.254,                   # OAP focal length = 254 mm
    f_coll_bright=0.030,           # bright mode collimator f = 30 mm
    f_coll_faint=0.015,            # faint  mode collimator f = 15 mm
    f_img=0.184,                   # imaging lens to produce cold-stop plane = 184 mm
    cold_stop_diam=2.145e-3,       # cold stop diameter = 2.145 mm
    target_pupil_diam=288e-6,      # target pupil diameter at detector = 288 µm
    mask_diam_lbd_over_D=1.0,      # ZWFS phase-dot diameter in λ/D
    phase_shift=0, #np.pi/2,           # ZWFS phase shift (rad)
    eta_sec=0.05,                   # central obscuration ratio r2/r1
    N=2**9 + 1,                    # base grid (odd preferred)
    padding=4,                     # zero-padding factor
    phi=None, amp=None,            # optional phase/amplitude
    debug=True                     # plots + prints
):
    # ----- entrance pupil -----
    pupil_radius = D_in / 2
    L_pupil = 2 * pupil_radius
    dx_pupil = L_pupil / N
    x = np.linspace(-L_pupil/2, L_pupil/2, N)
    Xp, Yp = np.meshgrid(x, x)
    R = np.hypot(Xp, Yp)

    U_pupil = ((R > eta_sec * pupil_radius) & (R <= pupil_radius)).astype(np.complex128)
    if phi is not None:
        U_pupil *= np.exp(1j * phi)
    if amp is not None:
        U_pupil *= amp

    # zero-padding (for finer image-plane sampling)
    Np = N * padding
    if (Np % 2) != (N % 2):
        Np += 1
    start = (Np - N)//2
    U_pad = np.zeros((Np, Np), np.complex128)
    U_pad[start:start+N, start:start+N] = U_pupil

    # ----- Plane A: OAP focus (phase mask plane) -----
    U_mask = aotools.opticalpropagation.lensAgainst(
        U_pad, wvl=wvl, d1=dx_pupil, f=f_oap
    )
    dx_mask = lens_against_dx(dx_pupil, wvl, f_oap, Np)

    # coordinates at mask plane (metres)
    ax = (np.arange(-Np/2, Np/2) * dx_mask)
    Xm, Ym = np.meshgrid(ax, ax)

    # ZWFS phase mask in λ/D using F# = f_oap / D_in
    Fnum = f_oap / D_in
    mask_radius_m = 0.5 * mask_diam_lbd_over_D * (Fnum * wvl)
    PM = 1.0 + (np.exp(1j * phase_shift) - 1.0) * circ_mask_xy(Xm, Ym, mask_radius_m)

    U_after_mask = PM * U_mask

    # ----- Collimator: thin-lens phase at mask plane -----
    f_coll = f_coll_bright if mode == "bright" else f_coll_faint
    U_post_coll = apply_thin_lens(U_after_mask, dx=dx_mask, wvl=wvl, f=f_coll)

    # ----- Plane B: cold-stop image plane via imaging lens f_img=184 mm -----
    U_cs = aotools.opticalpropagation.lensAgainst(
        U_post_coll, wvl=wvl, d1=dx_mask, f=f_img
    )
    dx_cs = lens_against_dx(dx_mask, wvl, f_img, Np)

    # apply cold stop (2.145 mm) at this plane
    Xc = (np.arange(-Np/2, Np/2) * dx_cs)
    Yc = (np.arange(-Np/2, Np/2) * dx_cs)
    Xc, Yc = np.meshgrid(Xc, Yc)
    CS = circ_mask_xy(Xc, Yc, cold_stop_diam/2.0)
    U_cs *= CS

    # ----- Plane C: detector (no lens after cold stop) — Fresnel to get ~288 µm pupil -----
    z_init = 0.020  # 20 mm initial guess
    z_det, U_det = calibrate_z_for_pupil(U_cs, dx_cs, wvl, target_pupil_diam, z0=z_init, iters=4, frac=0.5)
    I_det = np.abs(U_det)**2
    dx_det = dx_cs  # angularSpectrum preserves spacing

    # ----- diagnostics / plots -----
    if debug:
        fig, axs = plt.subplots(1, 3, figsize=(13, 3.8))
        axs[0].imshow((np.abs(U_mask)**2)/np.max(np.abs(U_mask)**2), cmap='magma')
        axs[0].contour(circ_mask_xy(Xm, Ym, mask_radius_m), levels=[0.5], colors='c', linewidths=1)
        axs[0].set_title("PSF @ phase mask")

        axs[1].imshow(np.abs(U_cs)**2/np.max(np.abs(U_cs)**2), cmap='gray')
        axs[1].contour(CS, levels=[0.5], colors='y', linewidths=1)
        axs[1].set_title("Image @ cold stop")

        axs[2].imshow(I_det/np.max(I_det), cmap='viridis')
        axs[2].set_title(f"Detector (pupil)\nz_cs→det ≈ {z_det*1e3:.1f} mm")
        for a in axs:
            a.set_xticks([]); a.set_yticks([])
        plt.tight_layout(); plt.show()

        d_meas = measure_pupil_diameter(I_det, dx_det, frac=0.5)
        print(f"[mask] dx = {dx_mask*1e6:.2f} um/px | mask radius = {mask_radius_m*1e6:.1f} µm")
        print(f"[CS  ] dx = {dx_cs*1e6:.2f} um/px | CS diam     = {cold_stop_diam*1e3:.3f} mm")
        print(f"[det ] dx = {dx_det*1e6:.2f} um/px | z_cs→det   = {z_det*1e3:.1f} mm | pupil ≈ {d_meas*1e6:.1f} µm")

    return dict(
        U_pupil_in=U_pad, dx_pupil=dx_pupil,
        U_mask_plane=U_mask, dx_mask=dx_mask,
        U_after_mask=U_after_mask,
        U_coldstop=U_cs, dx_cold=dx_cs,
        U_detector=U_det, dx_det=dx_det, z_cs_to_det=z_det,
        f_coll=f_coll
    )

# -------------------- example run --------------------

if __name__ == "__main__":
    # Bright mode (30 mm collimator)
    out_bright = simulate_baldr_no_post_lens(mode="bright", debug=True)

    # Faint mode (15 mm collimator) — uncomment to run
    # out_faint = simulate_baldr_no_post_lens(mode="faint", debug=True)