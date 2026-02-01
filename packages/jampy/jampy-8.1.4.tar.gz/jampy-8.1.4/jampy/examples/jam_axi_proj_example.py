"""
    Copyright (C) 2019-2024, Michele Cappellari

    E-mail: michele.cappellari_at_physics.ox.ac.uk

    Updated versions of the software are available from my web page
    http://purl.org/cappellari/software

CHANGELOG
---------

V1.1.1: MC, Oxford, 3 January 2023
    - Included comment about using the analytic anisotropy variation.
V1.1.0: MC, Oxford, 16 July 2020
    - Compute both Vrms and LOS velocity.
V1.0.1: MC, Oxford, 21 April 2020
    - Made a separate file
V1.0.0: Michele Cappellari, Oxford, 08 November 2019
    - Written and tested

"""
import numpy as np
import matplotlib.pyplot as plt

import jampy as jam

##############################################################################

def jam_axi_proj_example():
    """
    Usage example for jam_axi_proj.
    It takes about 2s on a 3GHz CPU

    """
    rng = np.random.default_rng(123)
    xbin, ybin = rng.uniform(low=[-55, -40], high=[55, 40], size=[500, 2]).T

    inc = 60.                                                # Assumed galaxy inclination
    r = np.sqrt(xbin**2 + (ybin/np.cos(np.radians(inc)))**2) # Radius in the plane of the disk
    a = 40                                                   # Scale length in arcsec
    vr = 2000*np.sqrt(r)/(r + a)                             # Assumed velocity profile (v_c of Hernquist 1990)
    vel = vr * np.sin(np.radians(inc))*xbin/r                # Projected velocity field
    sig = 8700/(r + a)                                       # Assumed velocity dispersion profile
    rms = np.sqrt(vel**2 + sig**2)                           # Vrms field in km/s

    # Until here I computed some fake input kinematics to fit with JAM.
    # In a real application, instead of the above lines one will read the measured
    # stellar kinematics `vel` and `sig`, e.g., from integral-field spectroscopy

    surf = np.array([39483., 37158., 30646., 17759., 5955.1, 1203.5, 174.36, 21.105, 2.3599, 0.25493])
    sigma = np.array([0.153, 0.515, 1.58, 4.22, 10, 22.4, 48.8, 105, 227, 525])
    qobs = np.full_like(sigma, 0.57)

    distance = 16.5     # Assume Virgo distance in Mpc (Mei et al. 2007)
    mbh = 1e8           # Black hole mass in solar masses

    # One can either specify the anisotropy for each Gaussian component
    # individually, or define a smooth radial variation for the anisotropy
    # using an analytic logistic function:
    #
    #   For spherical alignment (align='sph'):
    #
    #       beta(r) = beta_0 + (beta_inf - beta_0) / [1 + (r_a / r)^alpha]
    #
    #   For cylindrical alignment (align='cyl'):
    #
    #       beta(z) = beta_0 + (beta_inf - beta_0) / [1 + (z_a / |z|)^alpha]
    #
    # To use this option, set beta to a list with four elements and logistic=True: 
    #
    #   beta = [r_a, beta_0, beta_inf, alpha].
    #
    # See the documentation for further details.

    logistic = True    # Set to False to use constant anisotropy
    if logistic:        # Use an analytic radial variation for the anisotropy
        r_a = 20        # Anisotropy transition radius in arcsec
        beta_0 = 0.2    # Inner anisotropy
        beta_inf = 0.4  # Outer anisotropy
        alpha = 1       # Sharpness of the anisotropy transition
        beta = [r_a, beta_0, beta_inf, alpha]
    else:               # Use constant anisotropy
        beta = np.full_like(surf, 0.2)

    # Below I assume mass follows light, but in a real application one
    # will generally include a dark halo in surf_pot, sigma_pot, qobs_pot.
    # See jam_dark_halo_bayes_example.py and e.g. Cappellari et al. (2013) for 
    # an example https://ui.adsabs.harvard.edu/abs/2013MNRAS.432.1709C

    surf_lum = surf_pot = surf
    sigma_lum = sigma_pot = sigma
    qobs_lum = qobs_pot = qobs

    sigmapsf = [0.6, 1.2]
    normpsf = [0.7, 0.3]
    pixsize = 0.8
    goodbins = r > 10  # Arbitrarily exclude the center to illustrate how to use goodbins

    # I use a loop below, just to highlight the fact that all parameters
    # remain the same for the two JAM calls, except for 'moment' and 'data'
    plt.figure(1)
    for moment, data in zip(['zz', 'z'], [rms, vel]):

        print(" ")
        # The model is by design similar but not identical to the adopted kinematics!
        out = jam.axi.proj(surf_lum, sigma_lum, qobs_lum, surf_pot, sigma_pot, qobs_pot,
                           inc, mbh, distance, xbin, ybin, plot=True, data=data,
                           sigmapsf=sigmapsf, normpsf=normpsf, beta=beta, pixsize=pixsize,
                           moment=moment, goodbins=goodbins, align='cyl', ml=None, 
                           logistic=logistic)
        plt.pause(3)
        plt.figure(2)
        surf_pot *= out.ml  # Scale the density by the best fitting M/L from the previous step

##############################################################################

if __name__ == '__main__':

    jam_axi_proj_example()
