"""
##############################################################################

Copyright (C) 2022-2024, Michele Cappellari
E-mail: michele.cappellari_at_physics.ox.ac.uk

Updated versions of the software are available from my web page
http://purl.org/cappellari/software

If you have found this software useful for your research,
I would appreciate an acknowledgement to the use of the
"JAM modelling method of Cappellari (2008)"

        https://ui.adsabs.harvard.edu/abs/2008MNRAS.390...71C

This software is provided as is without any warranty whatsoever.
Permission to use, for non-commercial purposes is granted.
Permission to modify for personal or internal use is granted,
provided this copyright and disclaimer are included unchanged
at the beginning of the file. All other rights are reserved.
In particular, redistribution of the code is not allowed.

##############################################################################

MODIFICATION HISTORY:
    V1.0.0: Written and tested.
       Michele Cappellari, Oxford, 3 October 2022
    Vx.x.x: Additional changes are documented in the CHANGELOG of the JamPy package.

"""

from time import perf_counter as clock
from scipy import special
import numpy as np

from jampy.util.quad1d import quad1d

##############################################################################

def integrand(t, sigma_lum, sigma_pot, dens_lum, mass, Mbh, r, beta, logistic, component):
    """
    Implements the integrand of equation (40) of Cappellari (2008, MNRAS, 390, 71).
    Also allows for an analytic radial variation of the anisotropy.

    """ 
    # TANH Change of variables for Jeans r-integral (Sec.6.2 of Cappellari 2020, MNRAS, 494, 4819)
    # np.log([1e-6*mds, 3*mxs]) -> [r, inf]
    drdt = np.exp(t)
    r1 = r + drdt[:, None]    # Broadcast over radii and MGE parameters

    if logistic:
        # Variable anisotropy, same for all Gaussians
        ra, beta0, betainf, alpha = beta
        fun = (r1/r)**(2*beta0)
        fun *= ((1 + (r1/ra)**alpha)/(1 + (r/ra)**alpha))**(2*(betainf - beta0)/alpha)
        beta = beta0 + (betainf - beta0)/(1 + (ra/r)**alpha)
    else:
        # Constant anisotropy, different per Gaussian
        fun = (r1/r)**(2*beta)

    G = 0.004301  # (km/s)^2 pc/Msun [6.674e-11 SI units (CODATA2018)]
    h = r1/(np.sqrt(2)*sigma_pot)
    mass_r = Mbh + (special.erf(h) - 2/np.sqrt(np.pi)*h*np.exp(-h**2)) @ mass  # eq.(49) of Cappellari (2008)
    nu_r = dens_lum*np.exp(-0.5*(r1/sigma_lum)**2)                             # eq.(47) of Cappellari (2008)
    nuf = nu_r*fun/r1**2                                                       # eq.(40) of Cappellari (2008)

    if component == 'sig2r':
        nuf = nuf.sum(1)
    elif component == 'sig2th':
        nuf = (nuf*(1 - beta)).sum(1)

    integ = G*nuf*mass_r   # Vector of values computed at different radii

    return integ*drdt

##############################################################################

class jam_sph_intr:

    """
    Purpose
    -------
    This procedure calculates a prediction for the intrinsic second moments
    <v_r^2> and <v_th^2> in the radial and tangential directions for a
    spherically symmetric MGE model.
    It implements the solution of the anisotropic Jeans equations
    presented in equation (40) of `Cappellari (2008, MNRAS, 390, 71).
    <https://ui.adsabs.harvard.edu/abs/2008MNRAS.390...71C>`_

    Calling Sequence
    ----------------
    .. code-block:: python

        import jampy as jam

        out = jam.sph.intr(dens_lum, sigma_lum, dens_pot, sigma_pot, mbh, rad,
                           beta=None, epsrel=1e-2)
        sigma_r, sigma_th = np.sqrt(out.model)

    Parameters
    ----------
    dens_lum:
        vector of length N containing the peak surface brightness of the
        MGE Gaussians describing the galaxy surface brightness in units of
        Lsun/pc^2 (solar luminosities per parsec^2).
    sigma_lum:
        vector of length N containing the dispersion in pc of
        the MGE Gaussians describing the galaxy surface brightness.
    surf_pot:
        vector of length M containing the peak value of the MGE Gaussians
        describing the galaxy surface density in units of Msun/pc^2 (solar
        masses per parsec^2). This is the MGE model from which the model
        potential is computed.

    sigma_pot:
        vector of length M containing the dispersion in pc of
        the MGE Gaussians describing the galaxy surface density.
    mbh:
        Mass of a nuclear supermassive black hole in solar masses.
    rad:
        Vector of length P with the (positive) radius from the galaxy center
        in pc at which one wants to compute the model predictions.

    Other parameters
    ----------------
    beta: array_like with shape (n,) or (4,)
        Radial anisotropy of the individual kinematic-tracer MGE Gaussians
        (Default: ``beta=np.zeros(n)``)::

            beta = 1 - (sigma_th/sigma_r)^2

        When ``logistic=True`` the procedure assumes::

            beta = [r_a, beta_0, beta_inf, alpha]

        and the anisotropy of the whole JAM model varies as a logistic
        function of the logarithmic spherical radius::

            beta(r) = beta_0 + (beta_inf - beta_0)/[1 + (r_a/r)^alpha]

        Here ``beta_0`` represents the anisotropy at ``r = 0``, ``beta_inf``
        is the anisotropy at ``r = inf`` and ``r_a`` is the anisotropy
        transition radius, with ``alpha`` controlling the sharpness of the
        transition. In the special case ``beta_0 = 0, beta_inf = 1, alpha = 2``
        the anisotropy variation reduces to the form by Osipkov & Merritt, but
        the extra parameters allow for much more realistic anisotropy profiles.
    epsrel: float, optional
        Relative error requested for the numerical quadrature
        (Default: ``epsrel=1e-2``)
    logistic: bool, optional
        When ``logistic=True``, JAM interprets the anisotropy parameter
        ``beta`` as defining a 4-parameters logistic function.
        See the documentation of the anisotropy keyword for details.
        (Default ``logistic=False``)

    Returns
    -------
    Returned as attributes of the ``jam.sph.intr`` class.

    .flux: array_like  with shape (p,)
        Vector with the MGE luminosity density at each ``r`` location in ``Lsun/pc^3``.
    .model: array_like with shape (2, p)
        Contains ``[sig2r, sig2th]`` defined as follows:

        sig2r: array_like with shape (p,)
            Squared intrinsic dispersion in ``(km/s)^2`` along the r
            direction at each ``r`` location.

        sig2th: array_like with shape (p,)
            Squared intrinsic dispersion in ``(km/s)^2`` along the th
            direction at each ``r`` location.

    """

    def __init__(self, dens_lum, sigma_lum, dens_pot, sigma_pot, mbh, rad,
                 beta=None, epsrel=1e-2, logistic=False, quiet=False):

        if beta is None:
            beta = np.zeros_like(dens_lum)
        assert (dens_lum.size == sigma_lum.size) and \
               ((len(beta) == 4 and logistic) or (len(beta) == dens_lum.size)), \
            "The luminous MGE components and anisotropies do not match"
        assert len(dens_pot) == len(sigma_pot), 'surf_pot and sigma_pot must have the same length'

        t = clock()

        mass = dens_pot*(np.sqrt(2*np.pi)*sigma_pot)**3
        lim = np.log([1e-6*np.median(sigma_lum), 3*np.max(sigma_lum)])
        nu_sig2r, nu_sig2th = np.empty((2, rad.size))

        for j, rj in enumerate(rad):
            args = [sigma_lum, sigma_pot, dens_lum, mass, mbh, rj, beta, logistic]
            nu_sig2r[j], nu_sig2th[j] = \
                [quad1d(integrand, lim, epsrel=epsrel, args=args+[txt]).integ
                 for txt in ['sig2r', 'sig2th']]

        self.rad = rad
        self.flux = np.exp(-0.5*(rad[:, None]/sigma_lum)**2) @ dens_lum
        self.model = nu_sig2r/self.flux, nu_sig2th/self.flux

        if not quiet:
            print(f'jam_sph_intr elapsed time (sec): {clock() - t:.2f}')

##############################################################################
