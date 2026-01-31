
import numpy as np
import matplotlib.pyplot as plt 
from scipy.integrate import quad
from scipy.interpolate import interp1d
import pandas as pd
from mpl_toolkits.axes_grid1 import make_axes_locatable
import math 
from matplotlib.widgets import Slider

import aotools

### Function from asgard-alignment/pyBaldr/utilities/


################ FOR TESTING SCINTILLATION 

def nice_heatmap_subplots( im_list , xlabel_list=None, ylabel_list=None, title_list=None, cbar_label_list=None, fontsize=15, cbar_orientation = 'bottom', axis_off=True, vlims=None, savefig=None):

    n = len(im_list)
    fs = fontsize
    fig = plt.figure(figsize=(5*n, 5))

    for a in range(n) :
        ax1 = fig.add_subplot(int(f'1{n}{a+1}'))

        if vlims is not None:
            im1 = ax1.imshow(  im_list[a] , vmin = vlims[a][0], vmax = vlims[a][1])
        else:
            im1 = ax1.imshow(  im_list[a] )
        if title_list is not None:
            ax1.set_title( title_list[a] ,fontsize=fs)
        if xlabel_list is not None:
            ax1.set_xlabel( xlabel_list[a] ,fontsize=fs) 
        if ylabel_list is not None:
            ax1.set_ylabel( ylabel_list[a] ,fontsize=fs) 
        ax1.tick_params( labelsize=fs ) 

        if axis_off:
            ax1.axis('off')
        divider = make_axes_locatable(ax1)
        if cbar_orientation == 'bottom':
            cax = divider.append_axes('bottom', size='5%', pad=0.05)
            cbar = fig.colorbar( im1, cax=cax, orientation='horizontal')
                
        elif cbar_orientation == 'top':
            cax = divider.append_axes('top', size='5%', pad=0.05)
            cbar = fig.colorbar( im1, cax=cax, orientation='horizontal')
                
        else: # we put it on the right 
            cax = divider.append_axes('right', size='5%', pad=0.05)
            cbar = fig.colorbar( im1, cax=cax, orientation='vertical')  
        
        if cbar_label_list is not None:
            cbar.set_label( cbar_label_list[a], rotation=0,fontsize=fs)
        cbar.ax.tick_params(labelsize=fs)
    if savefig is not None:
        plt.savefig( savefig , bbox_inches='tight', dpi=300) 



def azimuthal_average(psd2d, fx, fy, nbins=None):
    FX, FY = np.meshgrid(fx, fy, indexing='xy')
    fr = np.sqrt(FX**2 + FY**2)
    fmax = fr.max()
    if nbins is None:
        nbins = min(200, psd2d.shape[0] // 2)
    edges = np.linspace(0.0, fmax, nbins + 1)
    centers = 0.5*(edges[1:] + edges[:-1])
    idx = np.digitize(fr.ravel(), edges) - 1
    valid = (idx >= 0) & (idx < nbins)
    sums = np.bincount(idx[valid], weights=psd2d.ravel()[valid], minlength=nbins)
    cnts = np.bincount(idx[valid], minlength=nbins).astype(float)
    psd1d = sums / np.maximum(cnts, 1.0)
    return centers, psd1d

def periodogram2d(img, dx, use_hann=True):
    """
    2D periodogram with physical frequency axes (cycles/m).
    Normalized so that sum(PSD)*dfx*dfy ≈ mean(img_windowed^2).
    """
    if use_hann:
        win = np.hanning(img.shape[0])
        W = np.outer(win, win)
        imgw = img * W
        norm = (W**2).sum()
    else:
        imgw = img
        norm = img.size
    F = np.fft.fft2(imgw)
    fx = np.fft.fftfreq(img.shape[1], d=dx)  # cycles/m
    fy = np.fft.fftfreq(img.shape[0], d=dx)
    P2D = (np.abs(F)**2) * (dx**2) / norm     # units: img^2 * m^2
    return fx, fy, P2D

def check_scintillation_psd(U, wavelength, z, dx, r0, L0, ffit=(0.5, 5.0), title_suffix=""):
    """
    Compare measured PSD of δI with short-exposure theory.
    """
    I = np.abs(U)**2
    dI = I / I.mean() - 1.0

    fx, fy, P2D = periodogram2d(dI, dx=dx, use_hann=True)
    f, P1D = azimuthal_average(P2D, fx, fy)

    # theory up to a scale factor
    fresnel = 4.0 * np.sin(np.pi * wavelength * z * (f**2))**2
    Wphi = 0.0029 * r0**(-5/3.0) * (f**2 + (1.0/L0)**2)**(-11/6.0)
    W_I_th = Wphi * fresnel

    # scale theory to measured mid-band for overlay
    band = (f > 0) & (np.isfinite(P1D)) & (P1D > 0) & (f >= ffit[0]) & (f <= ffit[1])
    scale = np.median(P1D[band]) / np.median(W_I_th[band]) if band.sum() > 10 else 1.0
    W_I_th_scaled = 5 * scale * W_I_th

    # fit slope on measured PSD in band
    x = np.log10(f[band]); y = np.log10(P1D[band])
    slope = np.polyfit(x, y, 1)[0] if band.sum() > 5 else np.nan

    # plot
    fs = 15 # fontsize
    msk = (f > 0) & np.isfinite(P1D) & (P1D > 0)
    plt.figure(figsize=(6.4, 4.4))
    plt.loglog(f[msk], P1D[msk], label='simulated')
    plt.loglog(f[msk], W_I_th_scaled[msk], '--', label='theory (scaled)')
    fidx =  np.argmax( np.diff(P1D) ) 
    plt.loglog(f[msk], 100 * P1D[msk][fidx]/f[msk][fidx] * (f[msk])**(-11/3), '--', color='k',label=r'$f^{-11/3}$')
    #plt.axvspan(ffit[0], ffit[1], color='k', alpha=0.06, label='fit band')
    plt.xlabel('Spatial frequency [cycles/m]',fontsize=fs)
    plt.ylabel(r'Fractional Intensity PSD [$m^2$]',fontsize=fs)
    #plt.title(f'scintillation PSD vs theory{title_suffix} (slope~{slope:.2f})')
    plt.grid(True, which='both', ls=':', alpha=0.4)
    plt.legend(fontsize=fs)
    plt.gca().tick_params(labelsize=fs)
    plt.tight_layout()
    

    print(f"Fitted log–log slope in {ffit} cycles/m band: {slope:.3f}")
    return f, P1D, W_I_th_scaled, slope

def check_phase_psd(scrn, dx, L0, ffit=(0.5, 5.0), title='phase screen PSD (expect -11/3 slope mid-band)'):
    fx, fy, P2D = periodogram2d(scrn, dx=dx, use_hann=True)
    f, P1D = azimuthal_average(P2D, fx, fy)
    # fit slope in band away from DC and Nyquist; avoid outer-scale roll-off region (f < 1/L0)
    band = (f > max(1.0/L0, ffit[0])) & (f <= ffit[1]) & (P1D > 0) & np.isfinite(P1D)
    slope = np.polyfit(np.log10(f[band]), np.log10(P1D[band]), 1)[0] if band.sum() > 5 else np.nan

    msk = (f > 0) & (P1D > 0) & np.isfinite(P1D)
    plt.figure(figsize=(6.4, 4.4))
    plt.loglog(f[msk], P1D[msk], label='measured PSD $W_\\phi(f)$')
    # reference -11/3 line
    if np.any(msk):
        f_ref = np.array([max(1.0/L0, ffit[0]), ffit[1]])
        y_mid = np.exp(np.interp(np.log(np.sqrt(f_ref.prod())), np.log(f[msk]), np.log(P1D[msk])))
        ref = y_mid * (f_ref / np.sqrt(f_ref.prod()))**(-11/3)
        plt.loglog(f_ref, ref, ':', label='ref. slope $-11/3$')
    plt.axvline(1.0/L0, color='grey', lw=1, ls='--', label='$1/L_0$')
    plt.xlabel('spatial frequency  $f$  [cycles/m]')
    plt.ylabel('PSD of $\\phi$  [arb. units]')
    plt.title(f'{title}  (slope~{slope:.2f})')
    plt.grid(True, which='both', ls=':', alpha=0.4)
    plt.legend()
    plt.tight_layout()
    plt.show()
    print(f"Phase PSD fitted slope in {ffit} (≥1/L0) band: {slope:.3f}")
    return f, P1D, slope






#### SCINTILLATION 
#following example from AOtools paper 
nx_size = 2**7 #128
D = 1.8 #8.0
pxl_scale =  D/nx_size
r0 = 0.164
L0  = 10
#stencil_length_factor = 2**7 #4 #32
phasescreen =  aotools.turbulence.infinitephasescreen.PhaseScreenVonKarman(nx_size,pxl_scale,r0,L0)
#aotools.turbulence.infinitephasescreen.PhaseScreenKolmogorov(nx_size,pxl_scale,r0,L0,stencil_length_factor)

wavefront = np.exp(1J *  phasescreen.scrn )

wavelength = 500e-9
propagation_distance = 10000.0
propagated_screen = aotools.opticalpropagation.angularSpectrum(inputComplexAmp=wavefront,
                                                               z=propagation_distance, 
                                                               wvl=wavelength, 
                                                               inputSpacing= pxl_scale, 
                                                               outputSpacing =pxl_scale
                                                               )

#nice_heatmap_subplots(im_list=[phasescreen.scrn,abs(propagated_screen)**2],title_list=['phasescreen','scintillation'])
nice_heatmap_subplots(im_list=[abs(propagated_screen)**2],cbar_label_list=["Intensity [arb. units]"], savefig="/Users/bencb/Downloads/Scintillation_intensity_screen.jpeg")
plt.show()


# ---------- run checks  ----------

# choose a mid-band for slope fit (tune to your dx and z):
# Nyquist is 1/(2*dx). keep away from DC and too close to Nyquist / Fresnel zeros.
f_nyq = 1.0/(2.0*pxl_scale )
ffit_scint = (0.5, min(5.0, 0.5*f_nyq))   # cycles/m; adjust if needed
ffit_phase = (0.5, min(5.0, 0.5*f_nyq))

# 1) short-exposure scintillation PSD check
_ = check_scintillation_psd(propagated_screen, wavelength, propagation_distance, pxl_scale , r0, L0, ffit=ffit_scint,
                            title_suffix=f' (D={D} m, N={nx_size}, dx={pxl_scale:.3e} m)')

plt.savefig("/Users/bencb/Downloads/Scintillation_simulation_v_theory.jpeg", dpi=200, bbox_inches = 'tight')
plt.show()
# 2) phase-screen PSD check (expect -11/3 mid-band, roll-off below 1/L0)
# _ = check_phase_psd(phasescreen.scrn, dx=pxl_scale, L0=L0, ffit=ffit_phase)
