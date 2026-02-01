#!/usr/bin/env python

"""
V1.0.0: Example for jam_sph_rms. Michele Cappellari, Oxford, 17 April 2018
V1.0.1: Adapted for the new jam_sph_proj. MC Oxford, 3 October 2022
V1.1.0: Illustrate usage of analytic anisotropy variation.
    MC, Oxford, 3 January 2023

"""

import numpy as np
import matplotlib.pyplot as plt

import jampy as jam

##############################################################################
def jam_sph_proj_example():
    """
    Usage example for jam_sph_proj().
    It takes about 1s on a 2.5 GHz computer.

    """
    # Realistic MGE galaxy surface brightness.
    # The surface brightness is in L_sun/pc^2 and the sigma in arcsec
    #
    surf_pc = np.array([6229., 3089., 5406., 8443., 4283., 1927., 708.8, 268.1, 96.83])
    sigma_arcsec = np.array([0.0374, 0.286, 0.969, 2.30, 4.95, 8.96, 17.3, 36.9, 128.])

    # Realistic observed stellar kinematics. It comes from AO observations
    # at R < 2" and seeing-limited long slit observations at larger radii.
    # The galaxy has negligible rotation, and we can use sigma as V_RMS
    #
    sig = np.array([395., 390., 387., 385., 380., 365., 350., 315., 310., 290., 260.])  # km/s
    dsig = sig*0.02  # assume 2% errors in sigma
    rad = np.array([0.15, 0.2, 0.3, 0.4, 0.5, 1, 1.5, 3, 5, 9, 15])  # arcsec

    # Assume the anisotropy variation is described by the function
    # beta(r) = beta_0 + (beta_inf - beta_0)/[1 + (r_a/r)^alpha]
    r_a = 1         # Anisotropy transition radius in arcsec
    beta_0 = -0.1   # Inner anisotropy
    beta_inf = 0.5  # Outer anisotropy
    alpha = 1       # Sharpness of the anisotropy transition
    beta = [r_a, beta_0, beta_inf, alpha]

    # Compute V_RMS profiles and optimize M/L to best fit the data.
    # Assume self-consistency: same MGE for luminosity and potential.
    #
    pixSize = 0.1           # Spaxel size in arcsec
    sigmapsf = [0.1, 0.6]   # sigma of the PSF in arcsec from AO observations
    normpsf = [0.7, 0.3]
    mbh = 2e8               # Black hole mass in solar masses before multiplication by M/L
    distance = 20.          # Mpc

    out = jam.sph.proj(surf_pc, sigma_arcsec, surf_pc, sigma_arcsec, mbh,
                       distance, rad, beta=beta, sigmapsf=sigmapsf,
                       normpsf=normpsf, pixsize=pixSize, data=sig, errors=dsig,
                       plot=True, tensor='los', logistic=True)
    rms = out.model

##############################################################################

if __name__ == '__main__':

    plt.clf()
    jam_sph_proj_example()
    plt.pause(5)
