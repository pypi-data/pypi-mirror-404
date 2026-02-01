"""
Copyright (C) 2010-2025, Michele Cappellari

E-mail: michele.cappellari_at_physics.ox.ac.uk

Updated versions of the software are available from my web page
https://purl.org/cappellari/software

If you have found this software useful for your research, 
I would appreciate an acknowledgement to the use of
"the MGE fitting method and software by Cappellari (2002)".

https://ui.adsabs.harvard.edu/abs/2002MNRAS.333..400C

This software is provided as is without any warranty whatsoever.
Permission to use, for non-commercial purposes is granted.
Permission to modify for personal or internal use is granted,
provided this copyright and disclaimer are included unchanged
at the beginning of the file. All other rights are reserved.
In particular, redistribution of the code is not allowed.

#####################################################################

Changelog
---------

V1.0.0 - Michele Cappellari, Oxford, 24 April 2010
    - Written and tested.
V1.0.1 - MC, Oxford, 27 July 2011
    - Use major axis fluxes as reference for isophotes.
V2.0.0 - MC, Oxford, 21 February 2014
    - Translated from IDL into Python.
V2.1.0 - MC, Oxford, 11 March 2016
    - Major speedup using histogram.
    - Updated documentation.
V2.2.0 - MC, Oxford, 22 March 2017
    - Scale image based on circularized reff.
    - Interpolate reff_maj for increased accuracy.
    - Removed now-unnecessary ``npix`` keyword.
V2.2.1 - MC, Oxford, 22 January 2018
    - Broadcast image creation.

"""

import numpy as np

##############################################################################

def mge_half_light_radius(surf, sigma, q_obs, distance=1e-5):
    """
    Computes the circularized projected half-light radius of an
    MGE model using the approach described after equation (11)
    in Cappellari et al. (2013, MNRAS, 432, 1709)
    https://ui.adsabs.harvard.edu/abs/2013MNRAS.432.1709C

    Parameters
    ----------
    surf : array_like (n,)
        Peak surface brightness for each projected Gaussian (Lsun pc^-2).
    sigma : array_like (n,)
        Dispersion of each Gaussian in arcsec.
    q_obs : array_like (n,)
        Observed axial ratio of every Gaussian component.
    distance : float, optional
        Galaxy distance in Mpc; only needed when absolute luminosity is required.

    Returns
    -------
    reff : float
        Circularized effective radius Re (same units as `sigma`).
    lum_tot : float
        Total analytic luminosity (Lsun if `distance` is given).
    
    """
    assert surf.size == sigma.size == q_obs.size, "The MGE components do not match"

    pc = distance*np.pi/0.648         # Constant factor to convert arcsec --> pc
    sigma = sigma*np.sqrt(q_obs)      # Circularize while conserving luminosity
    lum = 2*np.pi*surf*(sigma*pc)**2  # Keep peak surface brightness of each Gaussian
    lum_tot = lum.sum()               # If distance is given, lum_tot is in Lsun

    nrad = 50
    rad = np.geomspace(np.min(sigma), np.max(sigma),  nrad)  # arcsec
    lum_r = (1 - np.exp(-0.5*(rad[:, None]/sigma)**2)) @ lum  
    reff = np.interp(lum_tot/2, lum_r, rad)

    return reff, lum_tot

##############################################################################

def mge_half_light_isophote(surf, sigma, q_obs, distance=1e-5):
    """
    Computes the half-light radius, the major axis and ellipticity of
    the MGE isophote containing 1/2 of the analytic MGE total light.

    This procedure implements the steps (i)-(iv) described above
    equation (12) in `Cappellari et al. (2013)
    <https://ui.adsabs.harvard.edu/abs/2013MNRAS.432.1709C>`_

    Calling Sequence
    ----------------
    .. code-block:: python

        import jampy as jam

        reff, reff_maj, eps_e, lum_tot = jam.mge.half_light_isophote(
                surf, sigma, q_obs, distance=distance)

    Parameters
    ----------
    surf: array_like with shape (n,)
        Peak surface brightness of each Gaussian in Lsun/pc**2.
        One can use arbitrary units if only the half-light radius is required.
    sigma: array_like with shape (n,)
        Gaussian dispersion in arcsec
    q_obs: array_like with shape (n,)
        Observed axial ratio of each Gaussian

    distance: optional
        Galaxy distance in Mpc. This is only required to obtain
        the total luminosity of the MGE model in proper units.

        If the distance is not given, 10pc is assumed. In this case the
        following expression gives the galaxy apparent total magnitude:
        ``mag = sunMag - 2.5*np.log10(lum_tot)``

    Returns
    -------
    reff: float
        Effective (projected half-light) radius Re. This is the
        "circularized" Re=sqrt(Area/pi), where the area is the one
        of the isophote containing 1/2 of the analytic total MGE light.
        This is in the same units as ``sigma`` (typically arcsec).
    reff_maj: float
        Major axis (largest size) of the isophote containing
        1/2 of the total MGE light.
    eps_e: float
        Ellipticity of the isophote containing 1/2 of the total MGE
        light, computed from the inertia tensor within the isophote.
    lum_tot: float
        Analytic total luminosity in solar luminosities if the
        optional distance in Mpc is provided.
    """
    assert surf.size == sigma.size == q_obs.size, "The MGE components do not match"

    # Scale image based on the circularized Reff and an extreme axial ratio
    reff1, lum_tot = mge_half_light_radius(surf, sigma, q_obs, distance=distance)
    rmax = reff1/np.sqrt(np.min(q_obs).clip(0.1))

    # Create image from MGE model. Only compute one quadrant for symmetry
    npix = 100                   # This gives better than 0.1% accuracy
    scale = rmax/(npix - 0.5)    # image scale in arcsec/pix
    x = np.linspace(scale/2, rmax, npix)  # open interval for bi-symmetry
    xx2, yy2 = np.meshgrid(x**2, x**2)
    image = np.exp(-0.5/sigma**2*(xx2[..., None] + yy2[..., None]/q_obs**2)) @ surf

    # Find enclosed light inside isophotes defined by the MGE flux for the
    # pixels on the major axis, then interpolate to find half-light isophote
    h = np.histogram(image, bins=image[0, ::-1], weights=image)[0]
    lum_r = np.cumsum(h[::-1])
    pc = distance*np.pi/0.648  # Constant factor to convert arcsec --> pc
    surf_e = np.interp(lum_tot/8/(pc*scale)**2, lum_r, image[0, 1:])

    mask = image >= surf_e                                  # Pixels inside half-light isophote
    reff = np.sqrt(4*mask.sum()/np.pi)*scale                # Radius of same-area circle
    reff_maj = np.interp(surf_e, image[0, ::-1], x[::-1])   # Sample points must be increasing

    # Compute coefficients of the diagonal moment of inertia tensor
    # using equation (12) of Cappellari et al. (2013, MNRAS, 432, 1709)
    x2 = image[mask] @ xx2[mask]
    y2 = image[mask] @ yy2[mask]
    eps_e = 1 - np.sqrt(y2/x2)

    return reff, reff_maj, eps_e, lum_tot

##############################################################################
