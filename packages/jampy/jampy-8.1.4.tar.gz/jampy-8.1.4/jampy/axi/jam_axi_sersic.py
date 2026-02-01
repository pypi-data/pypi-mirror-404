"""
    Copyright (C) 2022-2024, Michele Cappellari

    E-mail: michele.cappellari_at_physics.ox.ac.uk

    Updated versions of the software are available from my web page
    https://purl.org/cappellari/software

    This software is provided as is without any warranty whatsoever.
    Permission to use, for non-commercial purposes is granted.
    Permission to modify for personal or internal use is granted,
    provided this copyright and disclaimer are included unchanged
    at the beginning of the file. All other rights are reserved.
    In particular, redistribution of the code is not allowed.

    Changelog
    ---------

    V1.0.0: Michele Cappellari, Oxford, 17 January 2022
    +++++++++++++++++++++++++++++++++++++++++++++++++++

    - Written and tested as a separate procedure.

    Vx.x.x: MC, Oxford
    ++++++++++++++++++

    - Additional changes are documented in the CHANGELOG of the JamPy package.


"""

import numpy as np
from scipy.special import gammainccinv
import matplotlib.pyplot as plt

import jampy as jam
import mgefit as mge
from jampy.axi.jam_axi_proj import rotate_points
from plotbin.plot_velfield import plot_velfield

###############################################################################

def sersic_profile(n, rad):
    """Sersic profile with rad=R/Re"""

    bn = gammainccinv(2*n, 0.5)       # exact formula
    surf = np.exp(-bn*(rad)**(1/n))   # r^(1/n) Sersic profile

    return surf  # Profile is NOT normalized

###############################################################################

def sersic_mge(n_ser, ngauss, lg_rmax, plot, quiet):
    """MGE for a Sersic profile"""

    m = 300 # Number of values to sample the profile for the fit
    r = np.logspace(-lg_rmax, lg_rmax, m)
    rho = sersic_profile(n_ser, r)
    w = rho > rho[0]/1e40  # samples at most 40 orders of magnitude in density
    total_counts, sigma = mge.fit_1d(r[w], rho[w], ngauss=ngauss, plot=plot,
                                     rbounds=[np.min(r)/2, np.max(r)], quiet=quiet).sol
    surf = total_counts/(np.sqrt(2*np.pi)*sigma)  # Surface density in Msun/pc**2

    if plot:
        plt.pause(1)

    return surf, sigma

###############################################################################

class jam_axi_sersic_mass:
    """
    jam.axi.sersic_mass
    ===================

    Purpose
    -------
    Calculate the mass `M_Ser` and its uncertainty for a mass-follows-light
    Sersic model at a given distance. This model produces a specified second
    moment of the stellar velocity `sigma_ap` within a rectangular or
    elliptical aperture of sides `dxy_ap`, assuming an intrinsic axial ratio
    `qintr`.

    This procedure is detailed in Section 5.2 of 
    `Cappellari (2023) <https://ui.adsabs.harvard.edu/abs/2023MNRAS.526.3273C>`_.

    For optimal results, the Sersic model should be fitted to the photometry in
    a band close to the wavelength of the spectroscopic observations used to
    extract `sigma_ap`.

    The physical significance of the output `M_Ser` is as follows: when divided by 
    the total luminosity `L_Ser` of the Sersic model in a specific band, it yields::

        (M/L)_ap = M_Ser/L_Ser

    This closely approximates the average mass-to-light ratio in the same band
    within a sphere of radius `R_ap` centered on the galaxy nucleus (see Figure 9 of 
    `Cappellari et al. 2013 <https://ui.adsabs.harvard.edu/abs/2013MNRAS.432.1709C>`_).

    This method serves as a simple replacement to the less accurate virial mass
    estimators and should be used when only a single determination of `sigma`
    for a galaxy is available, rather than spatially-resolved data.

    Calling Sequence
    ----------------
    .. code-block:: python

        import jampy as jam

        out = jam.axi.sersic_mass(re_maj_ser, n_ser, qobs, qintr, sigma_ap,
                sigma_ap_err, dxy_ap, sigma_psf, distance, angle=0., beta=0., 
                ngauss=20, lg_rmax=2., plot=True, quiet=False)
        
        print(f"Sersic Mass (M_Sun): {10**out.lg_mjam:.3g}")

    Parameters
    ----------
    re_maj_ser: float
        Major axis of the ellipse containing half of the total luminosity of the
        Sersic (1968) model which describes the surface brightness of the galaxy
        under study::
            
            surf(m) = exp[-bn*m^(1/n_ser)]
            m^2 = x^2 + (y/qobs)^2

    n_ser: float
        Sersic index. ``n_ser=1`` corresponds to an exponential profile, while
        ``n_ser=4`` represents a de Vaucouleurs (1948) profile.
    qobs: float
        The observed axial ratio of the Sersic model.
    qintr: float
        Assumed intrinsic axial ratio of the galaxy model.
    sigma_ap:
        Observed second velocity moment within a rectangular aperture. This is
        generally the velocity dispersion measured from a spectrum within the
        aperture.
    sigma_ap_err: float
        ``1sigma`` uncertainty on ``sigma_ap``.
    dxy_ap: array_like with shape (2,)
        Sizes of the rectangular aperture ``[dx, dy]``.
        When ``ellipse=True``, these are the major and minor axes of the
        ellipse inscribed within the rectangular aperture.
    sigma_psf: float
        Dispersion of the PSF.
    distance: float
        Adopted distance of the galaxy in Mpc

    Other Parameters
    ----------------
    angle: float
        Angle in degrees between the first dimension of the rectangular
        aperture and the galaxy projected major axis.
    beta: float
        Adopted anisotropy ``beta = 1 - (sigma_z/sigma_R)^2``.
    ellipse : bool
        If ``True``, restrict the second moment integration to the ellipse
        inscribed within the rectangular aperture. The inscribed ellipse uses
        the width and height from ``dxy_ap`` as its major and minor axes,
        effectively replacing the full rectangular aperture with this
        elliptical region for the integration. Defaults to the full rectangular
        aperture if ``False``.
    lg_rmax: float
        The Sersic profile is fitted from ``1/10^lg_rmax`` to ``10^lg_rmax``.
    ngauss: int
        Number of Gaussians used to fit the Sersic model with an MGE.
    plot: bool
        Set to ``True`` to plot the model, for debugging purposes.
    quiet: bool
        Set to ``True`` to suppress printed output.
                
    Returns
    -------
    Stored as attributes of the ``jam.axi.sersic_mass`` class.

    .lg_mjam: float
        Logarithm (base 10) of the total dynamical mass.
    .d_lg_mjam: float
        1sigma uncertainty on lg_mjam from error propagation, only considering
        the uncertainty in the input ``sigma_ap``.
    .mge_pot: array like with shape (3, ngauss)
        (surf, sigma, qobs) parameters of the MGE parameters describing the
        mass distribution parametrized by the Sersic profile. `surf` is in
        units of `Lsun/pc^2`, `sigma` in arcsec, and `qobs` is the projected
        axial ratio.
    .sigma_e: float
        Aperture and seeing-corrected value of the luminosity-weighted second
        moment inside the half-light ellipse. This is computed from the JAM
        model and provides an estimate of the sigma_e that one could have
        measured from spatially-resolved high-resolution observations of the
        galaxy.
    """
    def __init__(self, re_maj_ser, n_ser, qobs, qintr, sigma_ap, sigma_ap_err,
                 dxy_ap, sigma_psf, distance, angle=0., beta=0., ellipse=False, 
                 ngauss=20, lg_rmax=2., plot=True, quiet=False):

        assert qintr <= qobs, "Must be `qintr <= qobs`"
        inc = np.degrees(np.arctan2(np.sqrt(1 - qobs**2), np.sqrt(qobs**2 - qintr**2)))

        # Adopt as reference an arbitrary galaxy mass and find how much I need
        # to scale it to match the observed sigma
        mass = 1e11

        pc = distance*np.pi/0.648  # Factor to convert arcsec --> pc (with distance in Mpc)
        surf, sigma = sersic_mge(n_ser, ngauss, lg_rmax, plot, quiet)
        sigma = sigma*re_maj_ser
        qobs_mge = np.full_like(sigma, qobs)            # projected axial ratio

        mtot = 2*np.pi*(surf*qobs_mge*(sigma*pc)**2).sum()
        surf *= mass/mtot  # Rescale MGE to have input total mass

        dx, dy = dxy_ap
        npix = 100    # pixels discretizing the aperture
        x, xstep = np.linspace(-dx/2, dx/2, npix, retstep=True)      # Avoids (0, 0)
        y, ystep = np.linspace(-dy/2, dy/2, npix, retstep=True)      # Avoids (0, 0)
        pixsize = np.sqrt(xstep*ystep)
        xbin, ybin = map(np.ravel, np.meshgrid(x, y))
        if ellipse:
            w = (xbin/dx)**2 + (ybin/dy)**2 < 0.25
        else:
            w = np.ones_like(xbin, dtype=bool)
        xbin, ybin = rotate_points(xbin, ybin, angle)
        beta = np.full_like(sigma, beta)
        mbh = mass*0.005   # 0.5% BH mass (eq.11 of Kormendy & Ho 2013, ARA&A)

        out = jam.axi.proj(surf, sigma, qobs_mge, surf, sigma, qobs_mge, inc, 
                           mbh, distance, xbin, ybin, beta=beta, step=pixsize,
                           sigmapsf=sigma_psf, quiet=quiet, pixsize=pixsize)

        if plot:
            plt.clf()        
            plot_velfield(xbin, ybin, out.model, flux=out.flux, nodots=1)
            plt.title("JAM $V_{\\rm rms}$")
            if ellipse:
                plt.plot(xbin[~w], ybin[~w], '+')
            plt.pause(1)

        sigma_ap2 = (out.flux[w]*out.model[w]**2).sum()/out.flux[w].sum()
        scale = sigma_ap**2/sigma_ap2
        lg_mjam = np.log10(mass*scale)
        d_lg_mjam = 2*sigma_ap_err/(sigma_ap*np.log(10))    # error propagation

        # Compute in output the effective velocity second 
        # moment sigma_e within the half-light ellipse
        x = np.linspace(-re_maj_ser, re_maj_ser, npix)      # Avoids (0, 0)
        xbin, ybin = map(np.ravel, np.meshgrid(x, x*qobs))

        out = jam.axi.proj(surf, sigma, qobs_mge, surf*scale, sigma, qobs_mge, 
                           inc, mbh, distance, xbin, ybin, beta=beta, quiet=quiet)

        w = xbin**2 + (ybin/qobs)**2 < re_maj_ser**2
        sigma_e2 = (out.flux[w]*out.model[w]**2).sum()/out.flux[w].sum()

        if plot:
            plt.clf()        
            plot_velfield(xbin, ybin, out.model, flux=out.flux, nodots=1)
            plt.plot(xbin[~w], ybin[~w], '+')
            plt.title("JAM $V_{\\rm rms}$")
            plt.pause(1)

        self.lg_mjam = lg_mjam
        self.d_lg_mjam = d_lg_mjam
        self.mge_pot = surf*scale, sigma, qobs_mge  # output mass MGE
        self.sigma_e = np.sqrt(sigma_e2)
        self.sigma_ap = sigma_ap

        if not quiet:
            print(f"Aperture {dx:.1f}x{dy:.1f} arcsec at angle = {angle:.0f} deg")
            print(f"Input sigma_ap within the aperture: ({sigma_ap:.0f} +/- {sigma_ap_err:.0f}) km/s")
            print(f"Corrected sigma_e within Re: {self.sigma_e:.3g} km/s")
            print(f'lg(M_JAM/M_Sun) = {lg_mjam:.2f} +/- {d_lg_mjam:.2f}')


###############################################################################

def jam_axi_sersic_mass_example():
    """Usage example for jam.axi.sersic_mass"""

    # Input parameters
    dxy_ap = [1.0, 0.5]     # sides of rectangular aperture in arcsec
    n_ser = 4.0             # Sersic exponent (e.g. n = 4 --> de Vaucouleurs)
    qobs = 0.7              # Observed axial ratio of the fitted Sersic model
    qintr = 0.4             # Assumed intrinsic axial ratio q = b/a
    beta = 0.2              # Anisotropy beta = 1 - (sig_z/sig_R)^2
    re_maj_ser = 2.0        # arcsec. Semimajor axis of half-light ellipse of Sersic model
    sigma_psf = 0.5/2.355   # Dispersion of the PSF in arcsec
    redshift = 0.8          # Galaxy redshift
    sigma_ap = 200.         # km/s. Observed second velocity moment (sigma)
    sigma_ap_err = 15       # km/s. 1sigma uncertainty on sigma_ap

    # Computation
    dist_ang = jam.util.angular_diameter_distance(redshift)  # D_A angular diameter distance

    out = jam.axi.sersic_mass(re_maj_ser, n_ser, qobs, qintr, sigma_ap, sigma_ap_err, 
                              dxy_ap, sigma_psf, dist_ang, angle=30, beta=beta)
    
    print(f"\nSersic Mass (M_Sun): {10**out.lg_mjam:.3g}")

###############################################################################

if __name__ == '__main__':

    jam_axi_sersic_mass_example()
