"""
#############################################################################

Copyright (C) 2011-2017, Michele Cappellari
E-mail: michele.cappellari_at_physics.ox.ac.uk

Updated versions of the software are available from my web page
http://purl.org/cappellari/software

If you have found this software useful for your research,
I would appreciate an acknowledgement to the use of the
"JAM modelling package of Cappellari (2008)"

    https://ui.adsabs.harvard.edu/abs/2008MNRAS.390...71C
    
or an explicit reference to the equations given below.

This software is provided as is without any warranty whatsoever.
Permission to use, for non-commercial purposes is granted.
Permission to modify for personal or internal use is granted,
provided this copyright and disclaimer are included unchanged
at the beginning of the file. All other rights are reserved.
In particular, redistribution of the code is not allowed.

#############################################################################

MODIFICATION HISTORY:
    V1.0.0: Michele Cappellari, Oxford, 12 January 2011
    V2.0.0: Translated from IDL into Python. MC, Oxford, 21 February 2014
    V2.0.1: Cleaned up code and documentation. MC, Oxford, 23 October 2015
    V2.0.2: Check input parameters. MC, Oxford, 2 March 2016
    V2.0.3: Refer to published equation. MC, Oxford, 7 February 2017

"""

import numpy as np
from scipy.special import erf

def mge_radial_mass(surf, sigma, qobs, inc, rad, distance=1e-5):
    """
    Calculates the analytic mass or luminosity of an axisymmetric
    MGE within a sphere of a given radius, using equation (14) of
    `Mitzkus, Cappellari & Walcher, 2017, MNRAS, 464, 4789
    <https://ui.adsabs.harvard.edu/abs/2017MNRAS.464.4789M>`_

    :param surf: Peak surface brightness of each Gaussian in Lsun/pc**2
    :param sigma: Gaussian dispersion in arcsec
    :param qobs: Observed axial ratio of each Gaussian
    :param inc: inclination of the MGE in degrees
    :param rad: radius of the sphere in arcsec (scalar or vector)
    :param distance: Galaxy distance in Mpc
    :return: mass of the MGE within spheres of radii rad (same size as rad)
    """
    assert surf.size == sigma.size == qobs.size, "The MGE components do not match"

    pc = distance*np.pi/0.648   # Constant factor to convert arcsec --> pc
    r = np.atleast_1d(rad)*pc   # Convert input radius to pc
    sigma = sigma*pc

    # total luminosity each Gaussian (eq.12 of Cappellari 2008, MNRAS, 390, 71)
    lum = 2*np.pi*surf*qobs*sigma**2

    # Axisymmetric deprojection (eq.14 of Cappellari 2008, MNRAS, 390, 71)
    inc = np.radians(inc)
    qintr = qobs**2 - np.cos(inc)**2
    if np.any(qintr < 0):
        raise ValueError('Inclination too low q < 0')
    qintr = np.sqrt(qintr)/np.sin(inc)
    qintr = qintr.clip(0.001, 0.999) # Clip to avoid division by zero in mass_r
    
    # Compute analytic integral of MGE inside a sphere
    e = np.sqrt(1 - qintr**2)
    x = r[:, None]/(np.sqrt(2)*sigma)
    h = x / qintr
    mass_r = (erf(h) - np.exp(-x**2)*erf(h*e)/e) @ lum

    if np.isscalar(rad):
        mass_r = mass_r.item()

    return mass_r

#------------------------------------------------------------------------------
