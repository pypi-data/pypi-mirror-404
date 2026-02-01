"""
#############################################################################

Copyright (C) 2014-2024, Michele Cappellari
E-mail: michele.cappellari_at_physics.ox.ac.uk

Updated versions of the software are available from my web page
http://purl.org/cappellari/software

If you have found this software useful for your research,
I would appreciate an acknowledgement to the use of the
"JAM modelling package of Cappellari (2008)"

    https://ui.adsabs.harvard.edu/abs/2008MNRAS.390...71C
    
or a reference to Note 11 of Cappellari et al. (2015).

This software is provided as is without any warranty whatsoever.
Permission to use, for non-commercial purposes is granted.
Permission to modify for personal or internal use is granted,
provided this copyright and disclaimer are included unchanged
at the beginning of the file. All other rights are reserved.
In particular, redistribution of the code is not allowed.

#############################################################################

MODIFICATION HISTORY:
    V1.0.0: Written and tested. Michele Cappellari, Oxford, 8 April 2014
    V1.0.1: All input distances are converted to pc. MC, Oxford, 15 May 2015
    V1.0.2: Updated documentation. MC, Oxford, 2 March 2016

"""

import numpy as np
from scipy.special import erf

def mge_radial_density(surf, sigma, qobs, inc, rad, distance=1e-5):
    """
    Purpose
    -------    
    Calculates the spherically-averaged density of an axisymmetric MGE
    model, at a given set of radii, using the equation in Note 11 of
    `Cappellari et al. (2015, ApJL, 804, L21)
    <https://ui.adsabs.harvard.edu/abs/2015ApJ...804L..21C>`_

    Parameters
    ----------
    surf: array_like with shape (n,)
        Peak surface brightness of each Gaussian in ``Lsun/pc**2``.
    sigma: array_like with shape (n,)
        Gaussian dispersion in arcsec.
    qobs: array_like with shape (n,)
        Observed axial ratio of each Gaussian.
    inc: float
        Inclination of the MGE model, with ``i=90`` being edge-on.
    rad: array_like with shape (m,)
        radius for which the density is requested (scalar or vector).

    Other Parameters
    ----------------
    distance: float, optional
        Galaxy distance in Mpc (Default 10pc = 1e-5 Mpc)

    Returns
    -------
    dens: array_like with shape (m,)
        Spherical density calculated at the input radii ``rad``

    """

    assert surf.size == sigma.size == qobs.size, "The MGE components do not match"

    pc = distance*np.pi/0.648   # Constant factor to convert arcsec --> pc
    r = np.atleast_1d(rad)*pc   # Convert input radius to pc
    sigma = sigma*pc

    # Axisymmetric deprojection (eq.14 of Cappellari 2008, MNRAS, 390, 71)
    inc = np.radians(inc)
    qintr = qobs**2 - np.cos(inc)**2
    if np.any(qintr < 0):
        raise ValueError('Inclination too low q < 0')
    qintr = np.sqrt(qintr)/np.sin(inc)
    qintr = qintr.clip(0.001, 0.999) # Clip to avoid division by zero in dens
    
    # Average density rho(r) on spherical surfaces, without circularizing MGE.
    # Ths is the integral of a 3-dim axisymmetric Gaussian over the surface
    # of a sphere, divided by the surface of that sphere (4pi*r^2).
    # This is the formula in footnote 11 of Cappellari et al. (2015, ApJL)
    e = np.sqrt(1 - qintr**2)
    x = r[:, None] / (np.sqrt(2)*sigma)
    dens = (np.exp(-x**2)*erf(x*e/qintr)) @ (surf*qobs/e) / (2*r)
    
    if np.isscalar(rad):
        dens = dens.item()

    return dens

#------------------------------------------------------------------------------ 

