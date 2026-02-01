"""
    Copyright (C) 2019-2024, Michele Cappellari

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

V1.0.0: Michele Cappellari, Oxford, 08 November 2019
    - Written and tested.
Vx.x.x: Additional changes are documented in the CHANGELOG of the JamPy package.

"""
import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage, special
from time import perf_counter as clock

from plotbin.plot_velfield import plot_velfield
from jampy.util.quad1d import quad1d
from jampy.util.quad2d import quad2d

##############################################################################

def bilinear_interpolate(xv, yv, im, xout, yout):
    """
    The input array has size im[ny, nx] as in the output
    of im = f(meshgrid(xv, yv))
    xv and yv are vectors of size nx and ny respectively.

    """
    ny, nx = im.shape
    assert (nx, ny) == (xv.size, yv.size), "Input arrays dimensions do not match"

    xi = (nx - 1.)/(xv[-1] - xv[0]) * (xout - xv[0])
    yi = (ny - 1.)/(yv[-1] - yv[0]) * (yout - yv[0])

    return ndimage.map_coordinates(im.T, [xi, yi], order=1, mode='nearest')

##############################################################################

def density(R, z, dens, sigma, qintr):
    """Density for each luminous Gaussian at (R, z)"""

    nu = dens*np.exp(-0.5/sigma**2*(R**2 + (z/qintr)**2))  # Cappellari (2008) eq.(13)

    return nu

##############################################################################

def intrinsic_moments_cyl_bh(R, z, dens_lum, sigma_lum, qintr_lum, mbh, beta, gamma, all_mom):
    """Compute analytic intrinsic moments for the black hole alone"""

    G = 0.004301    # (km/s)^2 pc/Msun [6.674e-11 SI units (CODATA2018)]
    h = sigma_lum*qintr_lum*np.sqrt(2)
    r = np.sqrt(R**2 + z**2)
    nu = density(R, z, dens_lum, sigma_lum, qintr_lum)
    nu /= nu.sum()
    bani = 1/(1 - beta)  # Anisotropy ratio b = (sig_R/sig_z)**2

    sig2z = G*mbh*nu*(1/r - special.erfcx(r/h)*np.sqrt(np.pi)/h)
    v2phi = G*mbh*R**2/r**3*(1 - bani)*nu + (
            1 + (1 - qintr_lum**2)*(R/(sigma_lum*qintr_lum))**2)*bani*sig2z
    arr = [sig2z, v2phi]

    if all_mom:
        sig2R = bani*sig2z
        sig2phi = (1 - gamma)*sig2R
        arr.extend([sig2R, sig2phi])

    return np.sum(arr, 1)

##############################################################################

def integrand_cyl(u, R, z,
                  dens_lum, sigma_lum, qintr_lum,
                  dens_pot, sigma_pot, qintr_pot,
                  beta, gamma, logistic, all_mom):
    """
    Compute all the non-zero JAM first and second intrinsic velocity moments
    using the formulas from Cappellari (2008, MNRAS, 390, 71; hereafter C08).
    https://ui.adsabs.harvard.edu/abs/2008MNRAS.390...71C

    """
    dens_lum = dens_lum[:, None, None]
    sigma_lum = sigma_lum[:, None, None]
    qintr_lum = qintr_lum[:, None, None]

    dens_pot = dens_pot[None, :, None]
    sigma_pot = sigma_pot[None, :, None]
    qintr_pot = qintr_pot[None, :, None]

    # DE Change of variables for Chandrasekhar u-integral (Sec.6.2 of Cappellari 2020)
    # np.arcsinh(np.log([rmin, rmax])*2/np.pi) -> [0, inf]
    x = np.exp(np.sinh(u)*np.pi/2)
    duds = x*np.cosh(u)*np.pi/2
    u = x[None, None, :]

    if logistic:  # Variable anisotropy, same for all Gaussians
        zab, beta0, betainf, alpha = beta
        beta = (beta0 + betainf*(abs(z)/zab)**alpha)/(1 + (abs(z)/zab)**alpha)
        bani = 1/(1 - beta)  # Anisotropy ratio b = (sig_R/sig_z)**2
    else:  # Constant anisotropy, different per Gaussian
        bani = 1/(1 - beta[:, None, None]) if np.ptp(beta) else 1/(1 - beta[0])

    # Tracer Gaussians
    R2, z2 = R**2, z**2
    a = -1/(2*sigma_lum**2)
    b = a/qintr_lum**2
    exp1 = dens_lum*np.exp(a*R2 + b*z2)

    # Mass Gaussians
    G = 0.004301    # (km/s)^2 pc/Msun [6.674e-11 SI units (CODATA2018)]
    u1, qu = 1 + u, qintr_pot**2 + u
    tmp = -1/(2*sigma_pot**2)
    c, d = tmp/u1, tmp/qu
    cst = 2*np.pi*G*dens_pot*qintr_pot*sigma_pot**2
    exp2 = cst*np.exp(c*R2 + d*z2)/(u1*np.sqrt(qu))

    bd = d/(b + d)
    sig2z = exp1*exp2*bd
    v2phi = (bani + 2*R2*((a + c)*bani - c/bd))*sig2z
    arr = [sig2z, v2phi]

    if all_mom:
        gamma = gamma[:, None, None] if np.ptp(gamma) else gamma[0]
        sig2R = bani*sig2z
        sig2phi = (1 - gamma)*sig2R
        arr.extend([sig2R, sig2phi])

    return duds*np.sum(arr, (1, 2))

##############################################################################

def intrinsic_moments_cyl(R, z,
                          dens_lum, sigma_lum, qintr_lum,
                          dens_pot, sigma_pot, qintr_pot,
                          mbh, beta, gamma, logistic, epsrel):
    """Numerical quadratures of the Jeans solution"""

    xlim = [-3.7, 3.7]
    nu = density(R, z, dens_lum, sigma_lum, qintr_lum).sum()

    all_mom = True if (not logistic) and (np.ptp(beta) or np.ptp(gamma)) else False
    args = [R, z, dens_lum, sigma_lum, qintr_lum, dens_pot, sigma_pot, qintr_pot,
            beta, gamma, logistic, all_mom]
    mom = quad1d(integrand_cyl, xlim, epsrel=epsrel, args=args).integ/nu

    if logistic:
        zab, beta0, betainf, alpha = beta   # Avoid writing as zab/z to prevent zero division
        beta = (beta0 + betainf*(abs(z)/zab)**alpha)/(1 + (abs(z)/zab)**alpha)
        zag, gamma0, gammainf, alpha = gamma
        gamma = (gamma0 + gammainf*(abs(z)/zag)**alpha)/(1 + (abs(z)/zag)**alpha)
    else:
        if not np.ptp(beta): beta = beta[0]
        if not np.ptp(gamma): gamma = gamma[0]

    if mbh > 0:  
        mom += intrinsic_moments_cyl_bh(
            R, z, dens_lum, sigma_lum, qintr_lum, mbh, beta, gamma, all_mom)

    if all_mom:
        sig2z, v2phi, sig2R, sig2phi = mom
    else:
        sig2z, v2phi = mom
        sig2R = sig2z/(1 - beta)
        sig2phi = sig2R*(1 - gamma)

    return sig2R, sig2z, sig2phi, v2phi, nu

##############################################################################

def integrand_sph_bh(t, r, th, dens_lum, sigma_lum, qintr_lum, beta, gamma, logistic, mbh, all_mom):
    """Solution of the spherically-aligned Jeans equations for a black hole alone"""

    # TANH Change of variables for Jeans r-integral (Sec.6.2 of Cappellari 2020)
    # np.log([rmin, rmax]) -> [r, inf]
    drdt = np.exp(t)
    r1 = r + drdt[:, None]

    if logistic:    # Variable anisotropy, same for all Gaussians
        rab, beta0, betainf, alpha = beta
        fun = (r1/r)**(2*beta0)   
        fun *= ((1 + (r1/rab)**alpha)/(1 + (r/rab)**alpha))**(2*(betainf - beta0)/alpha)
        beta = beta0 + (betainf - beta0)/(1 + (rab/r)**alpha)
    else:           # Constant anisotropy, different per Gaussian
        fun = (r1/r)**(2*beta)

    # Tracer Gaussians
    s2_lum = sigma_lum**2
    q2_lum = qintr_lum**2
    rs = fun*(r*np.sin(th))**2
    aa = -r1**2/(2*q2_lum*s2_lum)
    bb = (1 - q2_lum)/(2*q2_lum*s2_lum)*rs
    ex1 = dens_lum*np.exp(aa + bb)

    G = 0.004301    # (km/s)^2 pc/Msun [6.674e-11 SI units (CODATA2018)]
    sig2r = G*fun*ex1*mbh/r1**2
    v2phi = (1 - beta)*(1 + 2*bb)*sig2r
    arr = [sig2r, v2phi]

    if all_mom:
        sig2th = (1 - beta)*sig2r       # Anisotropy beta = 1 - (sig_th/sig_r)**2
        sig2phi = (1 - gamma)*sig2r     # Anisotropy gamma = 1 - (sig_phi/sig_r)**2
        arr.extend([sig2th, sig2phi])

    return drdt*np.sum(arr, 2)

##############################################################################

def integrand_tan_dth_pot(u, R2, z2, dens_pot, sigma_pot, qintr_pot):
    """
    Returns the integrand of the tan(th)*D[pot, th] derivative
    of the MGE potential at (r, th).
    This is equation (51) of Cappellari (2020, MNRAS, 494, 4819)
    https://ui.adsabs.harvard.edu/abs/2020MNRAS.494.4819C

    """
    # DE Change of variables for Chandrasekhar u-integral (Sec.6.2 of Cappellari 2020)
    # np.arcsinh(np.log([rmin, rmax])*2/np.pi) -> [0, inf]
    x = np.exp(np.sinh(u)*np.pi/2)
    duds = x*np.cosh(u)*np.pi/2
    u = x[:, None]

    G = 0.004301    # (km/s)^2 pc/Msun [6.674e-11 SI units (CODATA2018)]
    u1, qu = 1 + u, qintr_pot**2 + u
    d = 2*np.pi*G*dens_pot*qintr_pot*(qintr_pot**2 - 1)*R2
    e = np.exp(-0.5/sigma_pot**2*(R2/u1 + z2/qu))
    tan_dth_pot = d*e/(u1**2*qu**1.5)

    return duds*tan_dth_pot.sum(1)   # u.size

##############################################################################

def integrand_sph(s, t, r, th, dens_lum, sigma_lum, qintr_lum, beta, gamma,
                  logistic, dens_pot, sigma_pot, qintr_pot, all_mom):
    """
    Solution of the spherically-aligned Jeans equations for an MGE
    from eq.(52)-(54) of Cappellari (2020, MNRAS, 494, 4819)
    https://ui.adsabs.harvard.edu/abs/2020MNRAS.494.4819C

    """
    dens_lum = dens_lum[:, None, None]
    s2_lum = (sigma_lum**2)[:, None, None]
    q2_lum = (qintr_lum**2)[:, None, None]

    dens_pot = dens_pot[None, :, None]
    s2_pot = (sigma_pot**2)[None, :, None]
    qintr_pot = qintr_pot[None, :, None]

    # DE Change of variables for Chandrasekhar u-integral (Sec.6.2 of Cappellari 2020)
    # np.arcsinh(np.log([rmin, rmax])*2/np.pi) -> [0, inf]
    x = np.exp(np.sinh(s)*np.pi/2)
    duds = x*np.cosh(s)*np.pi/2
    u = x[None, None, :]

    # TANH Change of variables for Jeans r-integral (Sec.6.2 of Cappellari 2020)
    # np.log([rmin, rmax]) -> [r, inf]
    drdt = np.exp(t)
    r1 = r + drdt[None, None, :]

    if logistic:        # Variable anisotropy, same for all Gaussians
        rab, beta0, betainf, alpha = beta
        fun = (r1/r)**(2*beta0)
        fun *= ((1 + (r1/rab)**alpha)/(1 + (r/rab)**alpha))**(2*(betainf - beta0)/alpha)
        beta = beta0 + (betainf - beta0)/(1 + (rab/r)**alpha)
    else:               # Constant anisotropy, different per Gaussian
        beta = beta[:, None, None] if np.ptp(beta) else beta[0]
        fun = (r1/r)**(2*beta)

    # Tracer Gaussians
    rs = fun*(r*np.sin(th))**2
    aa = -r1**2/(2*q2_lum*s2_lum)
    bb = (1 - q2_lum)/(2*q2_lum*s2_lum)*rs
    ex1 = dens_lum*np.exp(aa + bb)

    # Mass Gaussians
    G = 0.004301    # (km/s)^2 pc/Msun [6.674e-11 SI units (CODATA2018)]
    u1, qu = 1 + u, qintr_pot**2 + u
    cc = -r1**2/(2*qu*s2_pot)
    dd = (u1 - qu)/(2*qu*s2_pot*u1)*rs
    cst = 2*np.pi*G*dens_pot*qintr_pot*r1
    ex2 = cst*np.exp(cc + dd)/(u1*qu**1.5)

    sig2r = fun*ex1*ex2
    v2phi = (1 - beta)*(1 + 2*(bb + dd))*sig2r
    arr = [sig2r, v2phi]

    if all_mom:
        gamma = gamma[:, None, None] if np.ptp(gamma) else gamma[0]
        sig2th = (1 - beta)*sig2r       # Anisotropy beta = 1 - (sig_th/sig_r)**2
        sig2phi = (1 - gamma)*sig2r     # Anisotropy gamma = 1 - (sig_phi/sig_r)**2
        arr.extend([sig2th, sig2phi])

    return duds*drdt*np.sum(arr, (1, 2))

##############################################################################

def intrinsic_moments_sph(R, z,
                          dens_lum, sigma_lum, qintr_lum,
                          dens_pot, sigma_pot, qintr_pot,
                          mbh, beta, gamma, logistic, epsrel):
    """Numerical quadratures of the Jeans solution"""

    r = np.sqrt(R**2 + z**2)
    th = np.arctan2(R, z)  # Angle from symmetry axis z

    mds, mxs = np.median(sigma_lum), np.max(sigma_lum)
    xlim = [-3.7, 3.7]                  # u-integral limits
    ylim = np.log([1e-6*mds, 3*mxs])    # r-integral limits
    args = [r, th, dens_lum, sigma_lum, qintr_lum, beta, gamma, logistic]
    nu = density(R, z, dens_lum, sigma_lum, qintr_lum).sum()

    all_mom = True if (not logistic) and (np.ptp(beta) or np.ptp(gamma)) else False
    args_mge = args + [dens_pot, sigma_pot, qintr_pot, all_mom]
    mom = quad2d(integrand_sph, xlim, ylim, epsrel=epsrel, args=args_mge).integ
    if mbh > 0:
        mom += quad1d(integrand_sph_bh, ylim, epsrel=epsrel, args=args+[mbh, all_mom]).integ

    if all_mom:
        sig2r, v2phi, sig2th, sig2phi = mom/nu
    else:
        sig2r, v2phi = mom/nu
        if logistic:
            rab, beta0, betainf, alpha = beta
            beta = beta0 + (betainf - beta0)/(1 + (rab/r)**alpha)
            rag, gamma0, gammainf, alpha = gamma
            gamma = gamma0 + (gammainf - gamma0)/(1 + (rag/r)**alpha)
        else:
            beta = beta[0]
            gamma = gamma[0]
        sig2th = sig2r*(1 - beta)
        sig2phi = sig2r*(1 - gamma)

    v2phi += quad1d(integrand_tan_dth_pot, xlim, epsrel=epsrel,
                    args=(R**2, z**2, dens_pot, sigma_pot, qintr_pot)).integ

    return sig2r, sig2th, sig2phi, v2phi, nu

##############################################################################

def intrinsic_moments(Rbin, zbin, dens_lum, sigma_lum, qintr_lum, dens_pot,
                      sigma_pot, qintr_pot, mbh, beta, gamma, logistic, nrad,
                      nang, epsrel, interp, proj_cyl, align):

    fun = intrinsic_moments_cyl if align == 'cyl' else intrinsic_moments_sph

    if nrad*nang > Rbin.size or (not interp):  # Just calculate values
        mom = [fun(Rj, zj, dens_lum, sigma_lum, qintr_lum, dens_pot,
                   sigma_pot, qintr_pot, mbh, beta, gamma, logistic, epsrel)
               for (Rj, zj) in zip(Rbin, zbin)]
        sig2r, sig2th, sig2phi, v2phi, nu = np.array(mom).T
    else:
        irp = mom_interp(Rbin, zbin, dens_lum, sigma_lum, qintr_lum, dens_pot,
                         sigma_pot, qintr_pot, mbh, beta, gamma, logistic, nrad,
                         nang, epsrel=epsrel, align=align)
        sig2r, sig2th, sig2phi, v2phi, nu = irp.get_moments(Rbin, zbin)

    # Project the velocity dispersion tensor to cylindrical coordinates
    if proj_cyl and (align == 'sph'):
        th = np.arctan2(Rbin, zbin)  # Angle from symmetry axis z
        sig2R = sig2th*np.cos(th)**2 + sig2r*np.sin(th)**2
        sig2z = sig2th*np.sin(th)**2 + sig2r*np.cos(th)**2
        sig2r, sig2th = sig2R, sig2z

    return sig2r, sig2th, sig2phi, v2phi, nu

##############################################################################

class mom_interp:

    def __init__(self, xbin, ybin,
                 dens_lum, sigma_lum, qintr_lum,
                 dens_pot, sigma_pot, qintr_pot,
                 mbh, beta, gamma, logistic, nrad, nang, epsrel=1e-2,
                 rmin=None, rmax=None, align='cyl'):
        """ Initializes model values on a grid for subsequent interpolation """

        fun = intrinsic_moments_cyl if align == 'cyl' else intrinsic_moments_sph

        # Define parameters of polar grid for interpolation
        w = sigma_lum < np.max(np.abs(xbin))  # Characteristic MGE axial ratio in observed range
        self.qmed = np.median(qintr_lum) if w.sum() < 3 else np.median(qintr_lum[w])

        if rmin is None or rmax is None:
            rell2 = xbin**2 + (ybin/self.qmed)**2

        self.rmin = np.sqrt(np.min(rell2)) if rmin is None else rmin
        self.rmax = np.sqrt(np.max(rell2)) if rmax is None else rmax

        # Make linear grid in log of elliptical radius RAD and eccentric anomaly ECC
        rad =  np.geomspace(self.rmin, self.rmax, nrad)
        self.logRad = np.log(rad)
        self.ang = np.linspace(0, np.pi/2, nang)
        rellGrid, eccGrid = map(np.ravel, np.meshgrid(rad, self.ang))
        R = rellGrid*np.cos(eccGrid)
        z = rellGrid*np.sin(eccGrid)*self.qmed  # ecc=0 on equatorial plane

        mom = [fun(Rj, zj, dens_lum, sigma_lum, qintr_lum, dens_pot,
                   sigma_pot, qintr_pot, mbh, beta, gamma, logistic, epsrel)
               for (Rj, zj) in zip(R, z)]

        self.sig2r, self.sig2th, self.sig2phi, self.v2phi, nu = np.array(mom).T.reshape((5, nang, nrad))
        self.dens_lum = dens_lum
        self.sigma_lum = sigma_lum
        self.qintr_lum = qintr_lum

##############################################################################

    def get_moments(self, R, z):
        """
        Fast linearly-interpolated model values at the set
        of (R, z) coordinates from pre-computed values.
        Interpolation of non-weighted kinematics for accuracy.
        The returned density is analytic, not interpolated.

        """
        r1 = 0.5*np.log((R**2 + (z/self.qmed)**2).clip(self.rmin**2))  # Log elliptical radius of input (R,z)
        e1 = np.arctan2(np.abs(z/self.qmed), np.abs(R))  # Eccentric anomaly of input (R,z)
        bint = lambda x: bilinear_interpolate(self.logRad, self.ang, x, r1, e1)
        sig2r, sig2th, sig2phi, v2phi = map(bint, [self.sig2r, self.sig2th, self.sig2phi, self.v2phi])
        nu = density(R[:, None], z[:, None], self.dens_lum, self.sigma_lum, self.qintr_lum).sum(-1)

        return sig2r, sig2th, sig2phi, v2phi, nu

##############################################################################

class jam_axi_intr:
    """
    jam.axi.intr
    ============

    Purpose
    -------
    This procedure calculates all the intrinsic first and second velocity
    moments for an anisotropic axisymmetric galaxy model.

    This program is useful e.g. to model the kinematics of galaxies
    like our Milky Way, for which the intrinsic moments can be observed
    directly, or to compute starting conditions for N-body numerical
    simulations of galaxies.

    Two assumptions for the orientation of the velocity ellipsoid are supported:

    - The cylindrically-aligned ``(R, z, phi)`` solution was presented in
      `Cappellari (2008) <https://ui.adsabs.harvard.edu/abs/2008MNRAS.390...71C>`_

    - The spherically-aligned ``(r, th, phi)`` solution was presented in
      `Cappellari (2020) <https://ui.adsabs.harvard.edu/abs/2020MNRAS.494.4819C>`_

    Calling Sequence
    ----------------
    .. code-block:: python

        import jampy as jam

        out = jam.axi.intr(
                 dens_lum, sigma_lum, qintr_lum, dens_pot, sigma_pot, qintr_pot,
                 mbh, Rbin, zbin, align='cyl', beta=None, data=None, epsrel=1e-2,
                 errors=None, gamma=None, goodbins=None, interp=True,
                 logistic=False, ml=None, nang=10, nodots=False, nrad=20,
                 plot=True, proj_cyl=False, quiet=False)

        # The meaning of the output is different depending on `align`
        sig2R, sig2z, sig2phi, v2phi = out.model  # with align='cyl'
        sig2r, sig2th, sig2phi, v2phi = out.model  # with align='sph'

        out.plot()   # Generate data/model comparison

    Parameters
    ----------
    dens_lum: array_like with shape (n,)
        vector containing the peak value of the MGE Gaussians describing
        the intrinsic density of the tracer population for which the kinematics
        is derived.
        The units are arbitrary as they cancel out in the final results.
        Typical units are e.g. ``Lsun/pc^3`` (solar luminosities per ``parsec^3``)
    sigma_lum: array_like with shape (n,)
        vector containing the dispersion (sigma) in ``pc`` of the MGE
        Gaussians describing the galaxy kinematic-tracer population.
    qintr_lum: array_like with shape (n,)
        vector containing the intrinsic axial ratio (q) of the MGE
        Gaussians describing the galaxy kinematic-tracer population.
    surf_pot: array_like with shape (m,)
        vector containing the peak value of the MGE Gaussians
        describing the galaxy total-mass density in units of ``Msun/pc^3``
        (solar masses per ``parsec^3``). This is the MGE model from which the
        model gravitational potential is computed.
    sigma_pot: array_like with shape (m,)
        vector containing the dispersion in ``pc`` of the MGE
        Gaussians describing the galaxy total-mass density.
    qintr_pot: array_like with shape (m,)
        vector containing the intrinsic axial ratio of the MGE
        Gaussians describing the galaxy total-mass density.
    mbh: float
        Mass of a nuclear supermassive black hole in solar masses.
    Rbin: array_like with shape (p,)
        Vector with the ``R`` coordinates in ``pc`` of the bins (or pixels) at
        which one wants to compute the model predictions. This is the first
        cylindrical coordinate ``(R, z)`` with the galaxy center at ``(0,0)``.

        There is a singularity at ``(0, 0)`` which should be avoided by the user
        in the input coordinates.
    zbin: array_like with shape (p,)
        Vector with the ``z`` coordinates in ``pc`` of the bins (or pixels) at
        which one wants to compute the model predictions. This is the second
        cylindrical coordinate ``(R, z)``, with the z-axis coincident with the
        galaxy symmetry axis.

    Other Parameters
    ----------------
    align: {'cyl', 'sph'} optional
        If ``align='cyl'`` the program computes the solution of the Jeans
        equations with cylindrically-aligned velocity ellipsoid, presented
        in `Cappellari (2008)`_. If ``align='sph'`` the spherically-aligned
        solution of `Cappellari (2020)`_ is returned.
    beta: array_like with shape (n,) or (4,)
        Vector with the axial anisotropy of the individual kinematic-tracer
        MGE Gaussians (Default: ``beta=np.zeros(n)``)::

            beta = 1 - (sigma_th/sigma_r)^2  # with align='sph'
            beta = 1 - (sigma_z/sigma_R)^2   # with align='cyl'

        When ``logistic=True`` the procedure assumes::

            beta = [r_a, beta_0, beta_inf, alpha]

        and the anisotropy of the whole JAM model varies as a logistic
        function of the logarithmic spherical radius (with ``align='sph'``) or
        of the logarithmic distance from the equatorial plane (with ``align='cyl'``)::

            beta(r) = beta_0 + (beta_inf - beta_0)/[1 + (r_a/r)^alpha]    # with align='sph'
            beta(z) = beta_0 + (beta_inf - beta_0)/[1 + (z_a/|z|)^alpha]  # with align='cyl'

        Here ``beta_0`` represents the anisotropy at ``r = 0``, ``beta_inf`` is
        the anisotropy at ``r = inf`` and ``r_a`` is the anisotropy transition
        radius (in arcsec like ``sigma_lum``), with ``alpha`` controlling the
        sharpness of the transition. 
        In the special case ``beta_0 = 0, beta_inf = 1, alpha = 2`` the
        anisotropy variation reduces to the form by Osipkov & Merritt, but the
        extra parameters allow for much more realistic anisotropy profiles. See
        details and an application in `Simon, Cappellari & Hartke (2024)
        <https://ui.adsabs.harvard.edu/abs/2024MNRAS.527.2341S>`_.
    data: array_like of shape (4, p), optional
        Four input vectors with the observed values of:

        - ``[sigR, sigz, sigphi, vrms_phi]`` in ``km/s``, when ``align='cyl'``
          (or ``align='sph'`` and ``proj_cyl=True``).

          ``vrms_phi`` is the square root of the velocity second moment in the
          tangential direction. If the velocities ``vphi_j`` are measured from
          individual stars then ``vrms_phi = sqrt(mean(vphi_j^2))``.
          One can also use the relation ``vrms_phi = sqrt(vphi^2 + sigphi^2)``,
          where ``vphi = mean(vphi_j)`` and ``sigphi = std(vphi_j)``

        - ``[sigr, sigth, sigphi, vrms_phi]`` in ``km/s``, when ``align='sph'``,
          where ``vrms_phi`` is defined above.

    epsrel: float, optional
        Relative error requested for the numerical quadratures, before
        interpolation (Default: ``epsrel=1e-2``).
    errors: array_like of shape (4, p), optional
        ``1sigma`` uncertainties on ``data``, in the same format (default 5 ``km/s``).
    gamma: array_like with shape (n,)
        Vector with the tangential anisotropy of the individual kinematic-tracer
        MGE Gaussians (Default: ``gamma=np.zeros(n)``)::

            gamma = 1 - (sigma_phi/sigma_r)^2  # with align='sph'
            gamma = 1 - (sigma_phi/sigma_R)^2  # with align='cyl'

        When ``logistic=True`` the procedure assumes::

            gamma = [r_a, gamma_0, gamma_inf, alpha]

        and the anisotropy of the whole JAM model varies as a logistic
        function of the logarithmic spherical radius (with ``align='sph'``) or
        of the logarithmic distance from the equatorial plane (with ``align='cyl'``)::

            gamma(r) = gamma_0 + (gamma_inf - gamma_0)/[1 + (r_a/r)^alpha]    # with align='sph'
            gamma(z) = gamma_0 + (gamma_inf - gamma_0)/[1 + (z_a/|z|)^alpha]  # with align='cyl'

        Here ``gamma_0`` represents the anisotropy at ``r = 0``, ``gamma_inf``
        is the anisotropy at ``r = inf`` and ``r_a`` is the anisotropy
        transition radius (in arcsec like ``sigma_lum``), with ``alpha``
        controlling the sharpness of the transition. In the special case
        ``gamma_0 = 0, gamma_inf = 1, alpha = 2`` the anisotropy variation
        reduces to the form by Osipkov & Merritt, but the extra parameters
        allow for much more realistic anisotropy profiles.

        IMPORTANT: ``gamma`` only affects the projected first velocity moments.
        The projected second moments are rigorously independent of ``gamma``.
    goodbins: array_like with shape (4, p), optional
        Boolean vector of the same shape as ``data`` with values ``True``
        for the bins which have to be included in the fit (if requested) and
        ``chi^2`` calculation (Default: fit all bins).
    interp: bool, optional
        If ``interp=False`` no interpolation is performed and the model is
        computed at every set of input (R, z) coordinates.
        If ``interp=True`` (default), the model is interpolated if the number
        of requested input (R, z) coordinates is larger than ``nang*nrad``.
    logistic: bool, optional
        When ``logistic=True``, JAM interprets the anisotropy parameters
        ``beta`` and ``gamma`` as defining a 4-parameters logistic function.
        See the documentation of the anisotropy keywords for details.
        (Default ``logistic=False``)
    ml: float, optional
        Mass-to-light ratio M/L. If ``ml=None`` (default) the M/L is fitted to
        the data and the best-fitting value is returned in output.
        The ``mbh`` is also scaled and becomes ``mbh*ml``.
        If ``ml=1`` no scaling is applied to the model.
    nang: int, optional
        The number of linearly-spaced intervals in the eccentric anomaly at
        which the model is evaluated before interpolation (default: ``nang=10``).
    nodots: bool, optional
        Set to ``True`` to hide the dots indicating the centers of the bins in
        the two-dimensional map (default ``False``).
    nrad: int, optional
        The number of logarithmically spaced radial positions at which the
        model is evaluated before interpolation. One may want to increase this
        value if the model has to be evaluated over many orders of magnitude in
        radius (default: ``nrad=20``).
    plot: bool, optional
        If ``plot=True`` (default) and ``data is not None``, produce a plot of
        the data-model comparison at the end of the calculation.
    proj_cyl: bool, optional
        If ``align='sph'`` and ``proj_cyl=True``, the function projects the
        spherically-aligned moments to cylindrical coordinates and returns the
        ``[sig2R, sig2z, sig2phi, v2phi]`` components as in the case
        ``align='cyl'``. This is useful for a direct comparison of results with
        either the spherical or cylindrical alignment, as it allows one to fit
        the same data with both modelling assumptions.
    quiet: bool, optional
        If ``quiet=False`` (default), print the best-fitting M/L and chi2 at
        the end for the calculation.

    Returns
    -------
    Returned as attributes of the ``jam.axi.intr`` class.

    .chi2: float
        Reduced chi^2 (chi^2/DOF) describing the quality of the fit::

            d = (data/errors)[goodbins]
            m = (model/errors)[goodbins]
            chi2 = ((d - m)**2).sum()/goodbins.sum()

    .flux: array_like  with shape (p,)
        Vector with the MGE luminosity density at each ``(R, z)`` location in
        ``Lsun/pc^3``, used to plot the isophotes on the model results.
    .ml: float
        Best fitting M/L. This value is fitted while ignoring ``sigphi`` and it
        is strictly independent of the adopted tangential anisotropy ``gamma``.
    .model: array_like with shape (4, p)
        - Contains ``[sig2R, sig2z, sig2phi, v2phi]`` with ``align='cyl'``

        - Contains ``[sig2r, sig2th, sig2phi, v2phi]`` with ``align='sph'``

        where the above quantities are defined as follows:

        sig2R (sig2r): array_like with shape (p,)
            squared intrinsic dispersion in ``(km/s)^2`` along the R (r)
            direction at each ``(R, z)`` location.

        sig2z (sig2th): array_like with shape (p,)
            squared intrinsic dispersion in ``(km/s)^2`` along the z (th)
            direction at each ``(R, z)`` location.

        sig2phi: array_like with shape (p,)
            squared intrinsic dispersion in ``(km/s)^2``  along the
            tangential ``phi`` direction at each ``(R, z)`` location.

        v2phi: array_like with shape (p,)
            the second velocity moment in ``(km/s)^2`` along the
            tangential ``phi`` direction at each ``(R, z)`` location.

        The mean velocity along the tangential direction can be computed as
        ``vphi = np.sqrt(v2phi - sig2phi)``

        NOTE: I return squared velocities instead of taking the square root,
        to allow for negative values (unphysical solutions).

    ###########################################################################
    """

    def __init__(self, dens_lum, sigma_lum, qintr_lum, dens_pot, sigma_pot,
                 qintr_pot, mbh, Rbin, zbin, align='cyl', beta=None, data=None,
                 epsrel=1e-2, errors=None, gamma=None, goodbins=None,
                 interp=True, logistic=False, ml=None, nang=10, nodots=False,
                 nrad=20, plot=True, proj_cyl=False, quiet=False):

        assert align in ['sph', 'cyl'], "`align` must be 'sph' or 'cyl'"
        assert (ml is None) or (ml > 0), "The input `ml` must be positive"
        if beta is None:
            beta = np.zeros_like(dens_lum)  # Anisotropy parameter beta = 1 - (sig_th/sig_r)**2  (beta=0-->circle)
        if gamma is None:  # Anisotropy parameter beta = 1 - (sig_th/sig_r)**2
            if logistic:
                gamma = [1, 0, 0, 1]    # [r_a, gamma_0, gamma_inf, alpha]
            else:
                gamma = np.zeros_like(beta)
        assert (dens_lum.size == sigma_lum.size == qintr_lum.size) \
               and ((len(beta) == 4 and logistic) or (len(beta) == dens_lum.size)) \
               and (len(beta) == len(gamma)), "The luminous MGE components and anisotropies do not match"
        assert dens_pot.size == sigma_pot.size == qintr_pot.size, "The total mass MGE components do not match"
        assert Rbin.size == zbin.size, "Rbin and zbin do not match"

        if data is not None:
            assert len(data) == 4, "`data` must contain four vectors"
            if errors is None:
                errors = np.full_like(data, 5)  # Constant 5 km/s errors
            if goodbins is None:
                goodbins = np.ones_like(data, dtype=bool)
            else:
                assert goodbins.dtype == bool, "goodbins must be a boolean vector"
                assert np.any(goodbins), "goodbins must contain some True values"
            assert Rbin.size == len(data[0]) == len(errors[0]) == len(goodbins[0]), \
                "(data, errors, goodbins) and (Rbin, zbin) do not match"
        if goodbins is None:
            goodbins = np.ones_like(data, dtype=bool)
        else:
            assert goodbins.dtype == bool, "goodbins must be a boolean vector"
            assert np.any(goodbins), "goodbins must contain some True values"

        t = clock()

        # model contains [sig2r, sig2th, sig2phi, v2phi]
        *model, nu = intrinsic_moments(Rbin, zbin, dens_lum, sigma_lum,
            qintr_lum, dens_pot, sigma_pot, qintr_pot, mbh, beta, gamma,
            logistic, nrad, nang, epsrel, interp, proj_cyl, align)

        if not quiet:
            if nrad*nang > Rbin.size or (not interp):
                print("Just computed values")
            else:
                print("Performed interpolation")
            print(f'jam.axi.intr_{align} elapsed time (sec): {clock() - t:.2f}')

        if data is None:
            chi2 = np.nan
            if ml is None:
                ml = 1.
        else:
            model0 = np.sqrt(np.clip(model, 0, None))   # sqrt([sig2r, sig2th, sig2phi, v2phi])

            # Exclude sig2phi from M/L calculation
            if (ml is None) or (ml <= 0):
                m = np.delete(model0, 2, 0).ravel()     # sqrt([sig2r, sig2th, v2phi])
                d = np.delete(data, 2, 0).ravel()
                e = np.delete(errors, 2, 0).ravel()
                ok = np.delete(goodbins, 2, 0).ravel()
                d, m = (d/e)[ok], (m/e)[ok]
                ml = ((d @ m)/(m @ m))**2   # eq. (51) of Cappellari (2008, MNRAS)

            # Use full data for chi2 calculation
            model0 *= np.sqrt(ml)
            d, m, e, ok = map(np.ravel, [data, model0, errors, goodbins])
            chi2 = (((d[ok] - m[ok])/e[ok])**2).sum()/ok.sum()

        self.Rbin = Rbin
        self.zbin = zbin
        self.align = align
        self.model = np.array(model)*ml  # model ~ V^2
        self.data = data
        self.errors = errors
        self.flux = nu
        self.ml = ml
        self.chi2 = chi2
        self.goodbins = goodbins

        if plot and (data is not None):
            self.plot(nodots)

##############################################################################

    def plot(self, nodots=False):
        """ Data-model comparison for jam.axi.intr """

        plt.figure('jam')
        plt.clf()
        fig, ax = plt.subplots(4, 2, sharex=True, sharey=True, num='jam', gridspec_kw={'hspace': 0})

        if self.align == 'cyl':
            txt = [r"$\sigma_R$", r"$\sigma_z$", r"$\sigma_\phi$", r"$V^{\rm rms}_\phi$"]
        else:
            txt = [r"$\sigma_r$", r"$\sigma_\theta$", r"$\sigma_\phi$", r"$V^{\rm rms}_\phi$"]

        ax[0, 0].set_title("Data")
        ax[0, 1].set_title(f"JAM$_{{\\rm {self.align}}}$ Model")

        for j, (d, m, t) in enumerate(zip(self.data, np.sqrt(self.model.clip(0)), txt)):
            plt.sca(ax[j, 0])
            mn, mx = np.percentile(d, [1, 99])
            plot_velfield(self.Rbin, self.zbin, d, vmin=mn, vmax=mx, flux=self.flux, nodots=nodots)

            plt.sca(ax[j, 1])
            plot_velfield(self.Rbin, self.zbin, m, vmin=mn, vmax=mx, flux=self.flux,
                          colorbar=1, label=t, nodots=nodots)

##############################################################################
