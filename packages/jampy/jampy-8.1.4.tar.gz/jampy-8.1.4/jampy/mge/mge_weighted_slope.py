"""
#############################################################################

Copyright (C) 2025, Michele Cappellari
E-mail: michele.cappellari_at_physics.ox.ac.uk

Updated versions of the software are available from my web page
http://purl.org/cappellari/

If you have found this software useful for your research,
I would appreciate an acknowledgement to the use of the
"JAM modelling package of Cappellari (2008)" and additionally 
refer to the specific references in the function docstring.

    https://ui.adsabs.harvard.edu/abs/2008MNRAS.390...71C

This software is provided as is without any warranty whatsoever.
Permission to use, for non-commercial purposes is granted.
Permission to modify for personal or internal use is granted,
provided this copyright and disclaimer are included unchanged
at the beginning of the file. All other rights are reserved.
In particular, redistribution of the code is not allowed.

#############################################################################

MODIFICATION HISTORY:
    V1.0.0: Written and tested. Michele Cappellari, Oxford, 25 October 2025

"""
import numpy as np

import jampy as jam

#------------------------------------------------------------------------------ 

def mge_weighted_slope(surf, sigma, qobs, inc, rad):
    """
    Computes the mass-weighted logarithmic slope of an MGE model.

    This function calculates the mass-weighted logarithmic slope of a spherical
    or axisymmetric Multi-Gaussian Expansion (MGE) density profile, averaged
    within a sphere of a given radius. 

    The mass-weighted slope is defined as ``gamma_mw = -<d(ln rho)/d(ln r)>``
    averaged within the given radius.

    Parameters
    ----------
    surf : array_like
        Peak surface brightness of each Gaussian (e.g., Lsun/pc^2).
    sigma : array_like
        Gaussian dispersion in angular units (e.g., arcsec).
    qobs : array_like
        Observed axial ratio of each Gaussian.
    inc : float
        Inclination of the MGE in degrees (90 for edge-on).
    rad : float or array_like
        Radius of the sphere in the same units as `sigma`.
        Can be a scalar or an array.

    Returns
    -------
    gamma_mw : float or ndarray
        Mass-weighted logarithmic slope within `rad` (dimensionless).
        Returns a scalar if `rad` is a scalar, otherwise returns an array.

    Notes
    -----
    The computation uses analytic expressions for the cumulative mass M(r)
    [1]_ and the spherically-averaged density rho(r) [2]_. The mass-weighted
    slope is computed as::

        gamma_mw = 3 - (4 * pi * r^3 * rho(r)) / M(r)

    This corresponds to the mass-weighted logarithmic slope definition used
    in [3]_.

    A very useful relation when using the mass-weighted slope is given by
    equation (6) of [4]_. It shows how the dark matter fraction `f_DM` within a
    sphere can be simply estimated from the measured mass-weighted slopes of
    the total (`gamma_tot`), stellar (`gamma_*`) and an assumed slope
    (`gamma_DM`) for the dark matter component::

        f_DM = (gamma_tot - gamma_*) / (gamma_DM - gamma_*)

    References
    ----------
    .. [1] Cappellari, M. et al. 2015, ApJL, 804, L21
       https://ui.adsabs.harvard.edu/abs/2015ApJ...804L..21C
    .. [2] Mitzkus, M. et al. 2017, MNRAS, 464, 4789
       https://ui.adsabs.harvard.edu/abs/2017MNRAS.464.4789M
    .. [3] Dutton, A. A. & Treu, T. 2014, MNRAS, 438, 3594
       https://ui.adsabs.harvard.edu/abs/2014MNRAS.438.3594D
    .. [4] Cappellari, M. 2026, Encyclopedia of Astrophysics, 4, 122, Elsevier
       https://ui.adsabs.harvard.edu/abs/2026enap....4..122C

    """
    # The distance cancels out in the final formula, so we can use any
    # arbitrary value for the intermediate calculations. We use 1 Mpc.
    distance = 1.0

    # Calculate M(r) and rho(r) for the given mass profile
    mass_at_rad = jam.mge.radial_mass(surf, sigma, qobs, inc, rad, distance=distance)
    dens_at_rad = jam.mge.radial_density(surf, sigma, qobs, inc, rad, distance=distance)

    # Convert radius from arcseconds to parsecs for consistency
    pc = distance * np.pi / 0.648
    r = np.atleast_1d(rad) * pc

    # Calculate gamma_mw (NB: for rho = r^{-1} --> gamma_mw = 1)
    gamma_mw = 3 - (4 * np.pi * r**3 * dens_at_rad) / mass_at_rad

    if np.isscalar(rad):
        gamma_mw = gamma_mw.item()

    return gamma_mw

#------------------------------------------------------------------------------
