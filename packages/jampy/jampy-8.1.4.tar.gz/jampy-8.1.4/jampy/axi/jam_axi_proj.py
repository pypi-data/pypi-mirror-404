"""
    Copyright (C) 2019-2024, Michele Cappellari

    E-mail: michele.cappellari_at_physics.ox.ac.uk

    Updated versions of the software are available from my web page
    http://purl.org/cappellari/software

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
from scipy import special, signal, ndimage
from time import perf_counter as clock

from plotbin.plot_velfield import plot_velfield
from plotbin.symmetrize_velfield import symmetrize_velfield

from jampy.axi.jam_axi_intr import mom_interp
from jampy.util.quad1d import quad1d

##############################################################################

def integrand_cyl_los(u1,
                      dens_lum, sigma_lum, q_lum,
                      dens_pot, sigma_pot, q_pot,
                      x1, y1, inc, beta, tensor):
    """
    Computes the integrand of Eq.(28) of Cappellari (2008 MNRAS; C08
    https://ui.adsabs.harvard.edu/abs/2008MNRAS.390...71C) for a model with
    constant anisotropy per Gaussian sigma_R**2 = b*sigma_z**2 and <V_R*V_z> = 0.

    The components of the proper motion dispersions tensor are calculated as
    described in note 5 of C08. I later gave explicit formulas in
    Cappellari (2012; C12 http://arxiv.org/abs/1211.7009).
    
    I collected all formulas in Appendix A3 of Cappellari (2020 MNRAS, C20)
    https://ui.adsabs.harvard.edu/abs/2020MNRAS.494.4819C
    """
    dens_lum = dens_lum[:, None, None]
    sigma_lum = sigma_lum[:, None, None]
    q_lum = q_lum[:, None, None]
    beta = beta[:, None, None]

    dens_pot = dens_pot[None, :, None]
    sigma_pot = sigma_pot[None, :, None]
    q_pot = q_pot[None, :, None]

    u = u1[None, None, :]

    kani = 1./(1 - beta)  # Anisotropy ratio b = (sig_R/sig_z)**2
    ci = np.cos(inc)
    si = np.sin(inc)
    si2 = si**2
    ci2 = ci**2
    x2 = x1**2
    y2 = y1**2
    u2 = u**2

    s2_lum = sigma_lum**2
    q2_lum = q_lum**2
    e2_lum = 1 - q2_lum
    s2q2_lum = s2_lum*q2_lum

    s2_pot = sigma_pot**2
    e2_pot = 1 - q_pot**2

    # Double summation over (j, k) of eq.(28) for all values of integration variable u.
    # The triple loop in (j, k, u) is replaced by broadcast Numpy array operations.
    e2u2_pot = e2_pot*u2
    a = 0.5*(u2/s2_pot + 1/s2_lum)               # equation (29) in C08
    b = 0.5*(e2u2_pot*u2/(s2_pot*(1 - e2u2_pot)) + e2_lum/s2q2_lum) # equation (30) in C08
    c = e2_pot - s2q2_lum/s2_pot                  # equation (22) in C08
    d = 1 - kani*q2_lum - ((1 - kani)*c + e2_pot*kani)*u2  # equation (23) in C08
    e = a + b*ci2
    match tensor:
        case 'xx':
            f = kani*s2q2_lum + d*((y1*ci*(a+b)/e)**2 + si2/(2*e)) # equation (4) in C12
        case 'yy':
            f = s2q2_lum*(si2 + kani*ci2) + d*x2*ci2  # equation (5) in C12
        case 'zz':
            f = s2q2_lum*(ci2 + kani*si2) + d*x2*si2  # z' LOS equation (28) in C08
        case 'xy':
            f = -d*np.abs(x1*y1)*ci2*(a+b)/e          # equation (6) in C12
        case 'xz':
            f = -d*np.abs(x1*y1)*si*ci*(a+b)/e        # -equation (7) in C12
        case 'yz':
            f = -si*ci*(s2q2_lum*(1 - kani) - d*x2)   # -equation (8) in C12

    # arr has the dimensions (q_lum.size, q_pot.size, u.size)

    arr = q_pot*dens_pot*dens_lum*u2*f*np.exp(-a*(x2 + y2*(a + b)/e))/(
            (1 - c*u2)*np.sqrt((1 - e2u2_pot)*e))

    G = 0.004301  # (km/s)^2 pc/Msun [6.674e-11 SI units (CODATA2018)]

    return 4*np.pi**1.5*G*arr.sum((0, 1))

##############################################################################

def surf_v2los_cyl(x1, y1, inc,
                   dens_lum, sigma_lum, qintr_lum,
                   dens_pot, sigma_pot, qintr_pot,
                   beta, tensor):
    """Compute the projected weighted second moment Sigma*<V^2_los>"""

    sb_mu2 = [quad1d(integrand_cyl_los, [0., 1.], singular=1,
                     args=(dens_lum, sigma_lum, qintr_lum,
                           dens_pot, sigma_pot, qintr_pot,
                           xj, yj, inc, beta, tensor)).integ
              for (xj, yj) in zip(x1, y1)]

    return sb_mu2

##############################################################################

def vmom_proj(x1, y1, inc, mbh, beta, gamma, logistic,
              dens_lum, sigma_lum, qintr_lum,
              dens_pot, sigma_pot, qintr_pot,
              nrad, nang, nlos, epsrel, align, step):
    """
    This routine gives the projected first velocity moments
    and the second velocity moments tensor for a JAM model with
    either cylindrically or spherically-aligned velocity ellipsoid.
    The projection formulas given below are described in
    Sec.3 and the numerical quadrature in Sec.6.2 of
    Cappellari (2020, MNRAS, 494, 4819; hereafter C20)
    https://ui.adsabs.harvard.edu/abs/2020MNRAS.494.4819C
    """
    # TANH Change of variables for LOS integral (Sec.6.2 of Cappellari 2020)
    rmax = 3*np.max(sigma_lum)
    tmax = 8    # break is rmax/tmax
    t, dt = np.linspace(-tmax, tmax, nlos, retstep=True)
    scale = rmax/np.sinh(tmax)

    # Shift the center of the integration interval to the peak of the MGE Gaussian density
    # along the line of sight. This improves convergence by centering the density peak
    # at t=0, which is the center of the DE quadrature.
    q = np.median(qintr_lum)
    denom = np.sin(inc)**2 + np.cos(inc)**2 / q**2
    numer = np.sin(inc) * np.cos(inc) * (1/q**2 - 1)
    z_shift_factor = numer / denom
    z_cen = y1 * z_shift_factor

    z1 = z_cen[:, None] + scale*np.sinh(t)
    dxdt = dt*scale*np.cosh(t)

    # Initialize moment values for interpolation
    irp = mom_interp(x1, y1,
                     dens_lum, sigma_lum, qintr_lum,
                     dens_pot, sigma_pot, qintr_pot,
                     mbh, beta, gamma, logistic, nrad, nang, epsrel,
                     rmin=step/np.sqrt(2), rmax=rmax, align=align)

    x = x1[:, None]
    y = z1*np.sin(inc) + y1[:, None]*np.cos(inc)                    # C20 eq.(29)
    z = z1*np.cos(inc) - y1[:, None]*np.sin(inc)
    R = np.hypot(x, y)
    r = np.hypot(R, z)
    cos_phi, sin_phi, sin_th, cos_th = x/R, y/R, R/r, z/r           # C20 eq.(30)

    mom = irp.get_moments(R.ravel(), z.ravel())
    sig2r, sig2th, sig2phi, v2phi, nu = np.reshape(mom, (5,) + z.shape)
    vphi = np.sqrt((v2phi - sig2phi).clip(0))   # Clip unphysical solutions
    diag = np.array([sig2r, sig2th, v2phi])
    zero = np.zeros_like(nu)
    one = np.ones_like(nu)

    if align == 'cyl':
        R = np.array([[cos_phi, zero, -sin_phi],
                      [sin_phi, zero, cos_phi],                     # C20 eq.(24)
                      [zero,    one,  zero]])                       # swap 2<->3 columns
    else:  # align == 'sph'
        R = np.array([[sin_th*cos_phi, cos_th*cos_phi, -sin_phi],
                      [sin_th*sin_phi, cos_th*sin_phi, cos_phi],    # C20 eq.(16)
                      [cos_th,         -sin_th,        zero]])

    S = np.array([[1,           0,            0],
                  [0, np.cos(inc), -np.sin(inc)],                   # C20 eq.(17)
                  [0, np.sin(inc), np.cos(inc)]])

    Q = np.tensordot(S, R, 1)
    integ1 = vphi*Q[:, 2]                                           # C20 eq.(21)
    integ2 = np.einsum('ji...,i...,ki...->jk...', Q, diag, Q)       # C20 eq.(22)

    surf = nu @ dxdt                # DE quadrature
    nu_vlos = nu*integ1 @ dxdt      # DE quadrature
    nu_v2los = nu*integ2 @ dxdt     # DE quadrature
    vel = nu_vlos/surf
    vel2 = nu_v2los/surf

    return vel, vel2

##############################################################################

def mge_surf(x, y, surf, sigma, qobs):
    """MGE surface brightness for a set of coordinates (x, y)"""

    mge = np.exp(-0.5/sigma**2*(x[..., None]**2 + (y[..., None]/qobs)**2)) @ surf

    return mge

##############################################################################

def bilinear_interpolate(xv, yv, im, xout, yout):
    """
    Interpolate the array `im` with values on a regular grid of coordinates
    `(xv, yv)` onto a new set of generic coordinates `(xout, yout)`.
    The input array has size `im[ny, nx]` like `im = f(meshgrid(xv, yv))`.
    `xv` and `yv` are vectors of size `nx` and `ny` respectively.
    """
    ny, nx = im.shape
    assert (nx, ny) == (xv.size, yv.size), "Input arrays dimensions do not match"

    xi = (nx - 1.)/(xv[-1] - xv[0])*(xout - xv[0])
    yi = (ny - 1.)/(yv[-1] - yv[0])*(yout - yv[0])

    return ndimage.map_coordinates(im.T, [xi, yi], order=1, mode='nearest')

##############################################################################

def rotate_points(x, y, ang):
    """
    Rotates points counter-clockwise by an angle ANG in degrees.
    Michele cappellari, Paranal, 10 November 2013
    """
    theta = np.radians(ang)
    xNew = x*np.cos(theta) - y*np.sin(theta)
    yNew = x*np.sin(theta) + y*np.cos(theta)

    return xNew, yNew

##############################################################################

def psf_conv(x, y, inc_deg,
             surf_lum, sigma_lum, qobs_lum,
             surf_pot, sigma_pot, qobs_pot,
             mbh, beta, gamma, logistic, moment, align, sigmaPsf, normPsf,
             pixSize, pixAng, step, nrad, nang, nlos, epsrel, interp, analytic_los):
    """
    This routine gives the velocity moment after convolution with a PSF.
    The convolution is done using interpolation of the model on a
    polar grid, as described in Appendix A of Cappellari (2008, MNRAS, 390, 71)
    https://ui.adsabs.harvard.edu/abs/2008MNRAS.390...71C
    """
    # Axisymmetric deprojection of both luminous and total mass.
    # See equation (12)-(14) of Cappellari (2008)
    inc = np.radians(inc_deg)
    qmin = 0.05   # Minimum desired intrinsic axial ratio
    qobsmin = np.hypot(np.cos(inc), qmin*np.sin(inc))

    assert np.all(qobs_lum >= qobsmin), f'Inclination too low q_lum < {qmin}'
    qintr_lum = np.sqrt(qobs_lum**2 - np.cos(inc)**2)/np.sin(inc)
    dens_lum = surf_lum*qobs_lum/(sigma_lum*qintr_lum*np.sqrt(2*np.pi))

    assert np.all(qobs_pot >= qobsmin), f'Inclination too low q_pot < {qmin}'
    qintr_pot = np.sqrt(qobs_pot**2 - np.cos(inc)**2)/np.sin(inc)
    dens_pot = surf_pot*qobs_pot/(sigma_pot*qintr_pot*np.sqrt(2*np.pi))

    # Define parameters of polar grid for interpolation
    w = sigma_lum < np.max(np.abs(x))  # Characteristic MGE axial ratio in observed range
    qmed = np.median(qobs_lum) if w.sum() < 3 else np.median(qobs_lum[w])
    rell = np.hypot(x, y/qmed)  # Elliptical radius of input (x, y)

    psf_convolution = (np.max(sigmaPsf) > 0) and (pixSize > 0)

    if not interp or ((nrad*nang > x.size) and (not psf_convolution)):  # Just calculate values

        assert np.all((x != 0) | (y != 0)), "One must avoid the singularity at `(xbin, ybin) = (0, 0)`"

        interp = False
        x_pol = x
        y_pol = y
        step = np.min(rell)  # Minimum radius

    else:  # Interpolate values on polar grid

        # Kernel step is 1/4 of largest between sigma(min) and 1/2 pixel side.
        # Kernel half size is the sum of 3*sigma(max) and 1/2 pixel diagonal.

        if psf_convolution:         # PSF convolution
            if step == 0:
                step = np.min(sigmaPsf)/4
            mx = 3*np.max(sigmaPsf) + pixSize/np.sqrt(2)
        else:                       # No convolution
            step = np.min(rell)     # Minimum radius
            mx = 0

        # Make linear grid in log of elliptical radius RAD and eccentric anomaly ANG
        # See Appendix A of Cappellari (2008)
        rmax = np.max(rell) + mx  # Major axis of ellipse containing all data + convolution
        rad = np.geomspace(step/np.sqrt(2), rmax, nrad)  # Linear grid in np.log(rell)
        ang = np.linspace(0, np.pi/2, nang)  # Linear grid in eccentric anomaly
        radGrid, angGrid = map(np.ravel, np.meshgrid(rad, ang))
        x_pol = radGrid*np.cos(angGrid)
        y_pol = radGrid*np.sin(angGrid)*qmed

    # The model computation is only performed on the polar grid
    # which is then used to interpolate the values at any other location
    if analytic_los:
        # Analytic line-of-sight integral
        sb_mu2 = surf_v2los_cyl(x_pol, y_pol, inc,
                                dens_lum, sigma_lum, qintr_lum,
                                dens_pot, sigma_pot, qintr_pot, beta, moment)
        model = sb_mu2/mge_surf(x_pol, y_pol, surf_lum, sigma_lum, qobs_lum)
        vel = vel2 = None
    else:
        # Numeric line-of-sight integral
        vel, vel2 = vmom_proj(x_pol, y_pol, inc, mbh, beta, gamma, logistic,
                              dens_lum, sigma_lum, qintr_lum,
                              dens_pot, sigma_pot, qintr_pot,
                              nrad, nang, nlos, epsrel, align, step)
        match moment:
            case 'xx': model = vel2[0, 0]
            case 'yy': model = vel2[1, 1]
            case 'zz': model = vel2[2, 2]
            case 'xy': model = vel2[0, 1]
            case 'xz': model = vel2[0, 2]
            case 'yz': model = vel2[1, 2]
            case 'x': model = vel[0]
            case 'y': model = vel[1]
            case 'z': model = vel[2]

    if interp and psf_convolution:  # PSF convolution

        nx = int(np.ceil(rmax/step))
        ny = int(np.ceil(rmax*qmed/step))
        x1 = np.linspace(0.5 - nx, nx - 0.5, 2*nx)*step
        y1 = np.linspace(0.5 - ny, ny - 0.5, 2*ny)*step
        x_car, y_car = np.meshgrid(x1, y1)  # Cartesian grid for convolution
        mge_car = mge_surf(x_car, y_car, surf_lum, sigma_lum, qobs_lum)

        # Interpolate moment over cartesian grid.
        # Interpolating "nu_v2/surf" instead of "nu_v2" or "np.log(nu_v2)" reduces interpolation error.
        r1 = 0.5*np.log(x_car**2 + (y_car/qmed)**2)  # Log elliptical radius of cartesian grid
        e1 = np.arctan2(np.abs(y_car/qmed), np.abs(x_car))    # Eccentric anomaly of cartesian grid
        model_car = mge_car*bilinear_interpolate(np.log(rad), ang, model.reshape(nang, nrad), r1, e1)

        # Calculation was done in positive quadrant: use symmetries
        match moment:
            case 'xy' | 'xz':
                model_car *= np.sign(x_car*y_car)
            case 'y' | 'z':
                model_car *= np.sign(x_car)
            case 'x':
                model_car *= np.sign(y_car)

        nk = int(np.ceil(mx/step))
        kgrid = np.linspace(-nk, nk, 2*nk + 1)*step
        xgrid, ygrid = np.meshgrid(kgrid, kgrid)  # Kernel is square
        if pixAng != 0:
            xgrid, ygrid = rotate_points(xgrid, ygrid, pixAng)

        # Compute kernel with equation (A6) of Cappellari (2008).
        # Normalization is irrelevant here as it cancels out.
        dx = pixSize/2
        sp = np.sqrt(2)*sigmaPsf
        xg, yg = xgrid[..., None], ygrid[..., None]
        kernel = (special.erf((dx - xg)/sp) + special.erf((dx + xg)/sp)) \
                *(special.erf((dx - yg)/sp) + special.erf((dx + yg)/sp)) @ normPsf

        # Seeing and aperture convolution with equation (A3) of Cappellari (2008)
        m1, m2 = signal.fftconvolve([model_car, mge_car], kernel[None, ...], mode='same')
        muCar = np.divide(m1, m2, out=np.zeros_like(m1), where=m2 > 0)

        # Interpolate convolved image at observed apertures.
        # Aperture integration was already included in the kernel.
        mu = bilinear_interpolate(x1, y1, muCar, x, y)

    else:  # No PSF convolution

        if not interp or (nrad*nang > x.size):      # Just returns values
            mu = model
        else:                      # Interpolate values
            r1 = 0.5*np.log(x**2 + (y/qmed)**2) # Log elliptical radius of input (x,y)
            e1 = np.arctan2(np.abs(y/qmed), np.abs(x))    # Eccentric anomaly of input (x,y)
            mu = bilinear_interpolate(np.log(rad), ang, model.reshape(nang, nrad), r1, e1)

            # Calculation was done in positive quadrant: use symmetries
            match moment:
                case 'xy' | 'xz':
                    mu *= np.sign(x*y)
                case 'y' | 'z':
                    mu *= np.sign(x)
                case 'x':
                    mu *= np.sign(y)

    return mu, psf_convolution, interp, vel, vel2

##############################################################################

class jam_axi_proj:
    """
    jam.axi.proj
    ============

    Purpose
    -------
    This procedure calculates a prediction for all the projected first or second
    velocity moments for an anisotropic (three-integral) axisymmetric galaxy model.

    Any of the three components of the first velocity moment or any of the six
    components of the symmetric velocity dispersion tensor are supported.
    These include the line-of-sight velocities and the components of the proper motion.

    Two assumptions for the orientation of the velocity ellipsoid are supported:

    - The cylindrically-aligned ``(R, z, phi)`` solution was presented in
      `Cappellari (2008) <https://ui.adsabs.harvard.edu/abs/2008MNRAS.390...71C>`_

    - The spherically-aligned ``(r, th, phi)`` solution was presented in
      `Cappellari (2020) <https://ui.adsabs.harvard.edu/abs/2020MNRAS.494.4819C>`_

    Calling Sequence
    ----------------
    .. code-block:: python

        import jampy as jam

        out = jam.axi.proj(
                 surf_lum, sigma_lum, qobs_lum, surf_pot, sigma_pot, qobs_pot,
                 inc, mbh, distance, xbin, ybin, align='cyl', analytic_los=True,
                 beta=None, data=None, epsrel=1e-2, errors=None, flux_obs=None,
                 gamma=None, goodbins=None, interp=True, kappa=None,
                 logistic=False, ml=None, moment='zz', nang=10, nlos=1500,
                 nodots=False, normpsf=1., nrad=20, pixang=0., pixsize=0.,
                 plot=True, quiet=False, rbh=0.01, sigmapsf=0., step=0.,
                 vmax=None, vmin=None)

        vrms = out.model  # with moment='zz' the output is the LOS Vrms

        out.plot()   # Generate data/model comparison when data is given

    See more examples in the ``jampy/examples`` folder inside
    `site-packages <https://stackoverflow.com/a/46071447>`_.

    Parameters
    ----------
    surf_lum: array_like with shape (n,)
        peak surface values of the `Multi-Gaussian Expansion
        <https://pypi.org/project/mgefit/>`_ (MGE) Gaussians describing the
        surface brightness of the tracer population for which the kinematics
        is derived.

        The units are arbitrary as they cancel out in the final results.

        EXAMPLE: when one obtains the kinematics from optical spectroscopy,
        surf_lum contains the galaxy optical surface brightness, which has
        typical units of ``Lsun/pc^2`` (solar luminosities per ``parsec^2``).
    sigma_lum: array_like with shape (n,)
        dispersion (sigma) in arcseconds of the MGE Gaussians describing the
        distribution of the kinematic-tracer population.
    qobs_lum: array_like with shape (n,)
        observed axial ratio (q') of the MGE Gaussians describing the
        distribution of the kinematic-tracer population.
    surf_pot: array_like with shape (m,)
        peak value of the MGE Gaussians describing the galaxy total-mass
        surface density in units of ``Msun/pc^2`` (solar masses per ``parsec^2``).
        This is the MGE model from which the model gravitational potential is
        computed.

        EXAMPLE: with a self-consistent model, one has the same Gaussians
        for both the kinematic-tracer and the gravitational potential.
        This implies ``surf_pot = surf_lum``, ``sigma_pot = sigma_lum`` and
        ``qobs_pot = qobs_lum``. The global M/L of the model is fitted by the
        routine when passing the ``data`` and ``errors`` keywords with the
        observed kinematics.
    sigma_pot: array_like with shape (m,)
        dispersion in arcseconds of the MGE Gaussians describing the galaxy
        total-mass surface density.
    qobs_pot: array_like with shape (m,)
        observed axial ratio of the MGE Gaussians describing the galaxy
        total-mass surface density.
    inc: float
        inclination in degrees between the line-of-sight and the galaxy symmetry
        axis (0 being face-on and 90 edge-on).
    mbh: float
        Mass of a nuclear supermassive black hole in solar masses.

        IMPORTANT: The model predictions are computed assuming ``surf_pot``
        gives the total mass. In the self-consistent case, one has
        ``surf_pot = surf_lum`` and if requested (keyword ``ml``) the program
        can scale the output ``model`` to best fit the data. The scaling is
        equivalent to multiplying *both* ``surf_pot`` and ``mbh`` by a factor M/L.
        To avoid mistakes, the actual ``mbh`` used by the output model is
        printed on the screen.
    distance: float
        the distance of the galaxy in ``Mpc``. When the distance is derived 
        from redshift one should use the angular diameter distance ``D_A`` here.
    xbin: array_like with shape (p,)
        X coordinates in arcseconds of the bins (or pixels) at which one wants
        to compute the model predictions. The X-axis is assumed to coincide with
        the galaxy projected major axis. The galaxy center is at ``(0,0)``.
        
        In general the coordinates ``(xbin, ybin)`` have to be rotated to bring 
        the galaxy major axis on the X-axis, before calling ``jam.axi.proj``.

        When no PSF/pixel convolution is performed (``sigmapsf=0`` or
        ``pixsize=0``) there is a singularity at ``(0,0)`` which must be
        avoided by the user in the input coordinates.
    ybin: array_like with shape (p,)
        Y coordinates in arcseconds of the bins (or pixels) at which one wants
        to compute the model predictions. The Y-axis is assumed to coincide with
        the projected galaxy symmetry axis.

    Other Parameters
    ----------------
    align: {'cyl', 'sph'}, optional.
        Assumed alignment for the velocity ellipsoid during the solution of
        the Jeans equations.

        - ``align='cyl'`` assumes a cylindrically-aligned velocity ellipsoid
          using the solution of `Cappellari (2008)`_

        - ``align='sph'`` assumes a spherically-aligned velocity ellipsoid
          using the solution of `Cappellari (2020)`_

    analytic_los: bool, optional
        This is ``True`` (default) if the line-of-sight integral is performed
        analytically and ``False`` if it is done via numerical quadrature.

        An analytic integral is only possible with ``align='cyl'`` and only for
        the second velocity moments. For this reason, when comparing the two
        second-moment solutions with ``align='cyl'`` and ``align='sph'``, it
        may be preferable to set ``analytic_los=False`` to ensure that
        numerical interpolation error is exactly the same in both cases.

        When ``align='sph'``, or when the user requests a first velocity
        moment, this keyword is automatically set to ``False``.
    beta: array_like with shape (n,) or (4,)
        Radial anisotropy of the individual kinematic-tracer MGE Gaussians
        (Default: ``beta=np.zeros(n)``)::

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
    data: array_like with shape (p,), optional
        observed first or second velocity moment used to fit the model.

        EXAMPLE: In the common case where one has only line-of-sight velocities
        the second moment is given by::

            Vrms = np.sqrt(velBin**2 + sigBin**2)

        at the coordinates positions given by the vectors ``xbin`` and ``ybin``.

        If ``data`` is set and ``ml`` is negative or ``None``, then the model
        is fitted to the data, otherwise, the adopted ``ml`` is used and just
        the ``chi**2`` is returned.
    epsrel: float, optional
        Relative error requested for the numerical computation of the intrinsic
        moments (before line-of-sight quadrature). (Default: ``epsrel=1e-2``)
    errors: array_like with shape (p,), optional
        1sigma uncertainty associated with the ``data`` measurements.

        EXAMPLE: In the case where the data are given by the
        ``Vrms = np.sqrt(velBin**2 + sigBin**2)``, from the error propagation::

            errors = np.sqrt((dVel*velBin)**2 + (dSig*sigBin)**2)/Vrms,

        where ``velBin`` and ``sigBin`` are the velocity and dispersion in each
        bin and ``dVel`` and ``dSig`` are the corresponding 1sigma uncertainties.
        (Default: constant ``errors = 0.05*np.median(data)``)
    flux_obs: array_like with shape (p,), optional
        Optional mean surface brightness of each bin for plotting.
    gamma: array_like with shape (n,)
        tangential anisotropy of the individual kinematic-tracer MGE Gaussians
        (Default: ``gamma=np.zeros(n)``)::

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
    goodbins: array_like with shape (p,)
        Boolean vector with values ``True`` for the bins/spaxels which have to
        be included in the fit (if requested) and in the ``chi**2`` calculation.
        (Default: fit all bins).
    interp: bool, optional
        This keyword is for advanced use only! Set ``interp=False`` to force 
        no-interpolation on the sky plane. In this way ``out.vel`` and 
        ``out.vel2`` contain all the first and second velocity moments at the 
        input coordinates ``(xbin, ybin)``, without PSF convolution.
        By default ``interp=True`` and one should generally not change this.

        IMPORTANT: If ``sigmapsf=0`` or ``pixsize=0`` or ``interp=False`` then
        PSF convolution is not performed.

        This keyword is mainly useful for testing against analytic results or
        to compute all moments, including proper motions,  simultaneously.
    kappa: float, optional
        Scaling factor for the first velocity moments.

        - If ``kappa=None`` (default): The model's first velocity moments are
          scaled so that the projected angular momentum of the model matches
          that of the data (see equation 52 of `Cappellari (2008)`_). The sign
          of ``kappa`` is chosen to best fit the observed velocity field.
        
        - If ``kappa`` is a float (e.g., ``kappa=1``): The model's first
          velocity moments are multiplied by this value. ``kappa=1`` means no
          scaling is applied.
          
    logistic: bool, optional
        When ``logistic=True``, JAM interprets the anisotropy parameters
        ``beta`` and ``gamma`` as defining a 4-parameters logistic function.
        See the documentation of the anisotropy keywords for details.
        (Default ``logistic=False``)
    ml: float, optional
        Mass-to-light ratio (M/L) to multiply the values given by ``surf_pot``.
        Setting this keyword is completely equivalent to multiplying the
        output ``model`` by ``np.sqrt(M/L)`` after the fit. This implies that
        the BH mass is also scaled and becomes ``mbh*ml``.

        If ``ml=None`` (default) the M/L is fitted from the data and the
        best-fitting M/L is returned in output. The BH mass of the model is
        also scaled and becomes ``mbh*ml``.
    moment: {'x', 'y', 'z', 'xx', 'yy', 'zz', 'xy', 'xz', 'yz'}, optional
        String specifying the component of the velocity first or second moments
        requested by the user in output. All values ar in ``km/s``.

        - ``moment='x'`` gives the first moment ``<V_x'>`` of the proper motion
          in the direction orthogonal to the projected symmetry axis.

        - ``moment='y'`` gives the first moment ``<V_y'>`` of the proper motion
          in the direction parallel to the projected symmetry axis.

        - ``moment='z'`` gives the first moment ``Vlos = <V_z'>`` of the
          line-of-sight velocity.

        - ``moment='xx'`` gives ``sqrt<V_x'^2>`` of the component of the proper
          motion dispersion tensor in the direction orthogonal to the projected
          symmetry axis.

        - ``moment='yy'`` gives ``sqrt<V_y'^2>`` of the component of the proper
          motion dispersion tensor in the direction parallel to the projected
          symmetry axis.

        - ``moment='zz'`` (default) gives the usual line-of-sight
          ``Vrms = sqrt<V_z'^2>``.

        - ``moment='xy'`` gives the mixed component ``<V_x'V_y'>`` of the proper
          motion dispersion tensor.

        - ``moment='xz'`` gives the mixed component ``<V_x'V_z'>`` of the proper
          motion dispersion tensor.

        - ``moment='yz'`` gives the mixed component ``<V_y'V_z'>`` of the proper
          motion dispersion tensor.
    nang: int, optional
        The number of linearly-spaced intervals in the eccentric anomaly at
        which the model is evaluated before interpolation and PSF convolution.
        (default: ``nang=10``)
    nlos: int (optional)
        Number of values used for the numerical line-of-sight quadrature.
        (default ``nlos=1500``)
    nodots: bool, optional
        Set to ``True`` to hide the dots indicating the centers of the bins in
        the linearly-interpolated two-dimensional map (default ``False``).
    normpsf: array_like with shape (q,)
        fraction of the total PSF flux contained in the circular Gaussians
        describing the PSF of the kinematic observations.
        The PSF will be used for seeing convolution of the model kinematics.
        It has to be ``np.sum(normpsf) = 1``.
    nrad: int, optional
        The number of logarithmically spaced radial positions at which the
        model is evaluated before interpolation and PSF convolution. One may
        want to increase this value if the model has to be evaluated over many
        orders of magnitude in radius (default: ``nrad=20``).
    pixang: float, optional
        Angle between the observed spaxels and the galaxy major axis X.
        This angle only rotates the spaxels around their centers, *not* the
        whole coordinate system ``(xbin, ybin)``, which must be rotated
        independently by the user before calling ``jam.axi.proj``. 
        Using the keyword is generally unnecessary.
    pixsize: float, optional
        Size in arcseconds of the (square) spatial elements at which the
        kinematics is obtained. This may correspond to the side of the spaxel
        or lenslets of an integral-field spectrograph. This size is used to
        compute the kernel for the seeing and aperture convolution.

        IMPORTANT: If ``sigmapsf=0`` or ``pixsize=0`` or ``interp=False`` then
        PSF convolution is not performed.
    plot: bool
        When ``data is not None`` setting this keyword produces a plot with the
        data/model comparison at the end of the calculation.
    quiet: bool
        Set this keyword to avoid printing values on the console.
    rbh: float, optional
        This keyword is ignored unless ``align='cyl'`` and ``analytic_los=True``.
        In all other cases JAM assume a point-like central black hole.
        This scalar gives the sigma in arcsec of the Gaussian approximating the
        central black hole of mass MBH [See Section 3.1.2 of `Cappellari (2008)`_]
        The gravitational potential is indistinguishable from a point source
        for ``radii > 2*rbh``, so the default ``rbh=0.01`` arcsec is appropriate
        in most current situations.

        When using different units as input, e.g. pc instead of arcsec, one
        should check that ``rbh`` is not too many order of magnitude smaller
        than the spatial resolution of the data.
    sigmapsf: array_like with shape (q,)
        dispersion in arcseconds of the circular Gaussians describing the PSF
        of the kinematic observations.

        IMPORTANT: If ``sigmapsf=0`` or ``pixsize=0`` or ``interp=False`` then
        PSF convolution is not performed.

        IMPORTANT: PSF convolution is done by creating a 2D image, with pixels
        size given by ``step=np.min(sigmapsf)/4``, and convolving it with the
        PSF + aperture. If the input radii are very large compared to ``step``,
        the 2D image may require a too large amount of memory. If this is the
        case one may compute the model predictions at small radii with a first
        call to ``jam.axi.proj`` with PSF convolution, and the model
        predictions at large radii with a second call to ``jam.axi.proj``
        without PSF convolution.
    step: float, optional
        Spatial step for the model calculation and PSF convolution in arcsec.
        This value is automatically computed by default as
        ``step=np.min(sigmapsf)/4``. It is assumed that when ``sigmapsf`` is
        large, high-resolution calculations are not needed. In some cases,
        however, e.g. to accurately estimate the Vrms inside a large aperture,
        comparable with the PSF size, one may want to override the default
        value to force smaller spatial pixels using this keyword.
    vmax: float, optional
        Maximum value of the ``data`` to plot.
    vmin: float, optional
        Minimum value of the ``data`` to plot.

    Returns
    -------
    Stored as attributes of the ``jam.axi.proj`` class.

    .chi2: float
        Reduced ``chi**2``, namely per degree of freedom,  describing the 
        quality of the fit::

            d, m = (data/errors)[goodbins], (model/errors)[goodbins]
            chi2 = ((d - m)**2).sum()/goodbins.sum()

        When no data are given in input, this is returned as ``np.nan``.
    .flux: array_like with shape (p,)
        PSF-convolved MGE surface brightness of each bin in ``Lsun/pc^2``,
        used to plot the isophotes of the kinematic-tracer on the model results.
    .kappa: float
        Ratio by which the model was scaled to fit the observed velocity
        [defined by equation 52 of `Cappellari (2008)`_]
    .ml: float
        Best fitting M/L by which the mass was scaled to fit the observed moments.
    .model: array_like with shape (p,)
        Model predictions for the selected velocity moments for each input bin
        ``(xbin, ybin)``. This attribute is the main output from the program.

        Any of the six components of the symmetric proper motion dispersion
        tensor ``{'xx', 'yy', 'zz', 'xy', 'xz', 'yz'}``, or any of the three 
        first velocity moments ``{'x', 'y', 'z'}`` can be returned in output.
        The desired model output is selected using the ``moment`` keyword.
        See the ``moment`` documentation for details.
    .vel: array_like with shape (3, p)
        This attribute generally contains an intermediate result of the
        calculation and should not be used. Instead, the output kinematic
        model predictions are contained in the ``.model`` attribute.

        However, for advanced use only, when setting ``interp=False`` and
        ``analytic_los=False``, this attribute contains the first velocity
        moments for all the x, y and z components, *not* PSF convolved, at the
        sky coordinates ``(xbin, ybin)``.
    .vel2: array_like with shape (3, 3, p)
        This attribute generally contains an intermediate result of the
        calculation and should not be used. Instead, the output kinematic
        model predictions are contained in the ``.model`` attribute.

        However, for advanced use only, when setting ``interp=False`` and
        ``analytic_los=False``, this attribute contains the full 3x3 second
        velocity moment tensor, *not* PSF convolved, at the sky coordinates
        ``(xbin, ybin)``.

    ###########################################################################
    """
    def __init__(self, surf_lum, sigma_lum, qobs_lum, surf_pot, sigma_pot,
                 qobs_pot, inc, mbh, distance, xbin, ybin, align='cyl',
                 analytic_los=True, beta=None, data=None, epsrel=1e-2,
                 errors=None, flux_obs=None, gamma=None, goodbins=None,
                 interp=True, kappa=None, logistic=False, ml=None, moment='zz',
                 nang=10, nlos=1500, nodots=False, normpsf=1., nrad=20,
                 pixang=0., pixsize=0., plot=True, quiet=False, rbh=0.01,
                 sigmapsf=0., step=0.):

        str1 = ['x', 'y', 'z']
        str2 =  ['xx', 'yy', 'zz', 'xy', 'xz', 'yz']
        assert moment in str1 + str2, f"`moment` must be one of {str1 + str2}"
        assert align in ['sph', 'cyl'], "`align` must be 'sph' or 'cyl'"
        assert (ml is None) or (ml > 0), "The input `ml` must be positive"
        if beta is None:
            beta = np.zeros_like(surf_lum)  # Anisotropy parameter beta = 1 - (sig_th/sig_r)**2
        if gamma is None:  # Anisotropy parameter beta = 1 - (sig_th/sig_r)**2
            if logistic:
                gamma = [1, 0, 0, 1]
            else:
                gamma = np.zeros_like(beta)
        assert (surf_lum.size == sigma_lum.size == qobs_lum.size) \
               and ((len(beta) == 4 and logistic) or (len(beta) == surf_lum.size)) \
               and (len(beta) == len(gamma)), "The luminous MGE components and anisotropies do not match"
        assert surf_pot.size == sigma_pot.size == qobs_pot.size, "The total-mass MGE components do not match"
        assert xbin.size == ybin.size, "`xbin` and `ybin` do not match"
        if (not interp) or (moment in str1) or (align == 'sph') or logistic:
            analytic_los = False
        if data is not None:
            if errors is None:
                if moment in str2:
                    errors = np.full_like(data, np.median(data)*0.05)  # Constant ~5% errors
                else:
                    errors = np.full_like(data, 5.)  # Constant 5 km/s errors
            if goodbins is None:
                goodbins = np.ones_like(data, dtype=bool)
            else:
                assert goodbins.dtype == bool, "goodbins must be a boolean vector"
                assert np.any(goodbins), "goodbins must contain some True values"
            assert xbin.size == data.size == errors.size == goodbins.size, \
                "(rms, erms, goodbins) and (xbin, ybin) do not match"

        sigmapsf = np.atleast_1d(sigmapsf)
        normpsf = np.atleast_1d(normpsf)
        assert sigmapsf.size == normpsf.size, "sigmaPSF and normPSF do not match"
        assert round(np.sum(normpsf), 2) == 1, "PSF not normalized"

        # Convert all distances to pc
        pc = distance*np.pi/0.648  # Factor to convert arcsec --> pc (with distance in Mpc)
        surf_lum_pc = surf_lum
        surf_pot_pc = surf_pot
        sigma_lum_pc = sigma_lum*pc
        sigma_pot_pc = sigma_pot*pc
        xbin_pc = xbin*pc
        ybin_pc = ybin*pc
        pixSize_pc = pixsize*pc
        sigmaPsf_pc = sigmapsf*pc
        step_pc = step*pc

        # Assumes beta = [r_a, beta_0, beta_inf, alpha]
        #        gamma = [r_a, gamma_0, gamma_inf, alpha]
        if logistic:
            beta = beta.copy()
            gamma = gamma.copy()
            beta[0] *= pc
            gamma[0] *= pc

        # Add a Gaussian with small sigma and the same total mass as the BH.
        # The Gaussian provides an excellent representation of the second moments
        # of a point-like mass, to 1% accuracy out to a radius 2*sigmaBH.
        # The error increases to 14% at 1*sigmaBH, independently of the BH mass.
        if mbh > 0 and analytic_los:
            tmp = np.concatenate([sigmapsf, [pixsize], sigma_lum])
            assert rbh > 0.01*np.min(tmp[tmp > 0]), "`rbh` is too small"
            sigmaBH_pc = rbh*pc     # Adopt for the BH just a very small size
            surfBH_pc = mbh/(2*np.pi*sigmaBH_pc**2)
            surf_pot_pc = np.append(surfBH_pc, surf_pot_pc) # Add Gaussian to potential only!
            sigma_pot_pc = np.append(sigmaBH_pc, sigma_pot_pc)
            qobs_pot = np.append(1., qobs_pot)  # Make sure vectors do not have extra dimensions

        t = clock()
        model, psfConvolution, interp, vel, vel2 = psf_conv(
            xbin_pc, ybin_pc, inc,
            surf_lum_pc, sigma_lum_pc, qobs_lum,
            surf_pot_pc, sigma_pot_pc, qobs_pot,
            mbh, beta, gamma, logistic, moment, align, sigmaPsf_pc, normpsf,
            pixSize_pc, pixang, step_pc, nrad, nang, nlos, epsrel,
            interp, analytic_los)

        if moment in str2[:3]:
            model = np.sqrt(model.clip(0))  # sqrt and clip to allow for rounding errors

        # If PSF convolution is applied, it returns the MGE model that has been
        # convolved with the PSF (but ignoring pixel integration). Otherwise,
        # it returns the original MGE model without PSF convolution.
        # Analytic convolution of the MGE model with an MGE circular PSF
        # uses Equations (4,5) of Cappellari (2002, MNRAS, 333, 400).
        # https://ui.adsabs.harvard.edu/abs/2002MNRAS.333..400C
        # Broadcast triple loop over (n_MGE, n_PSF, n_bins)
        if psfConvolution:
            sigmaX2 = sigma_lum**2 + sigmapsf[:, None]**2
            sigmaY2 = (sigma_lum*qobs_lum)**2 + sigmapsf[:, None]**2
            surf_lum_pc = surf_lum_pc*qobs_lum*sigma_lum**2*normpsf[:, None]/np.sqrt(sigmaX2*sigmaY2)
        else:
            sigmaX2 = sigma_lum**2
            sigmaY2 = (sigma_lum*qobs_lum)**2      
                  
        psf = np.exp(-0.5*(xbin**2/sigmaX2[..., None] + ybin**2/sigmaY2[..., None]))
        flux = np.tensordot(surf_lum_pc, psf, surf_lum_pc.ndim)  # PSF-convolved Lsun/pc^2

        if flux_obs is None:
            flux_obs = flux

        if data is None:

            chi2 = np.nan
            if moment in str2[:3]:
                if ml is None:
                    ml = kappa = 1.0
                else:
                    kappa = 1.0
                    model *= np.sqrt(ml)
            else:
                if kappa is None:
                    ml = kappa = 1.0
                else:
                    ml = 1.0
                    model *= kappa

        else:

            d, m = (data/errors)[goodbins], (model/errors)[goodbins]

            if moment in str2[:3]:
                if ml is None:
                    ml = ((d @ m)/(m @ m))**2   # eq. (51) of Cappellari (2008, MNRAS)
                scale, kappa = np.sqrt(ml), 1.0

            else:

                if kappa is None:

                    # Scale by having the same angular momentum in the model and
                    # in the galaxy with eq. (52) of Cappellari (2008, MNRAS)
                    kappa = np.abs(data*xbin)[goodbins].sum()/np.abs(model*xbin)[goodbins].sum()

                    # Measure the scaling one would have from a standard chi^2 fit of the V field.
                    # This value is only used to get proper sense of rotation (sign) for the model.
                    kappa1 = (d @ m)/(m @ m)  # eq. (51) of Cappellari (2008, MNRAS) not squared
                    kappa *= np.sign(kappa1)

                scale, ml = kappa, 1.0

            model *= scale
            m *= scale
            chi2 = ((d - m)**2).sum()/goodbins.sum()

        if not quiet:
            const_anis = not (np.ptp(beta) or np.ptp(gamma))
            print(f"jam.axi.proj(align='{align}', moment='{moment}') -- elapsed time sec: {clock() - t:.2f}\n"
                  f"analytic_los={analytic_los:d} logistic={logistic:d} constant_anisotropy={const_anis:d}")
            if (not psfConvolution) or (not interp):
                txt = "No PSF/pixel convolution because"
                if np.max(sigmapsf) == 0:
                    txt += " sigmapsf=0"
                if pixsize == 0:
                    txt += " pixsize=0"
                if not interp:
                    txt += " interp=0"
                print(txt)
            p = 1 if logistic else 0
            print(f'inc={inc:#.3g}; beta[{p}]={beta[p]:#.2g}; kappa={kappa:#.3g}; '
                  f'M/L={ml:#.3g}; BH={mbh*ml:#.2g}; chi2/DOF={chi2:#.3g}')
            mass = 2*np.pi*surf_pot_pc*qobs_pot*sigma_pot_pc**2
            print(f'Total mass MGE (MSun): {(mass*ml).sum():#.4g}\n')

        self.xbin = xbin
        self.ybin = ybin
        self.goodbins = goodbins
        self.data = data
        self.errors = errors
        self.model = model
        self.ml = ml
        self.chi2 = chi2
        self.flux = flux
        self.flux_obs = flux_obs
        self.kappa = kappa
        self.moment = moment
        self.align = align
        self.vel = vel
        self.vel2 = vel2

        if plot and (data is not None):
            self.plot(nodots)

##############################################################################

    def plot(self, nodots=False, colorbar=False, vmin=None, vmax=None):

        ok = self.goodbins
        str1 = ['x', 'y', 'z']
        sym = 1 if self.moment in str1 else 2
        data1 = self.data.copy()  # Only symmetrize good bins
        data1[ok] = symmetrize_velfield(self.xbin[ok], self.ybin[ok], data1[ok], sym=sym)

        if (vmin is None) or (vmax is None):
            if self.moment in str1 + ['xy', 'xz']:
                vmax1 = np.percentile(np.abs(data1[ok]), 99)
                vmin1 = -vmax1
            else:
                vmin1, vmax1 = np.percentile(data1[ok], [0.5, 99.5])

            if vmin is None: vmin = vmin1
            if vmax is None: vmax = vmax1

        plt.clf()
        plt.subplot(121)
        plot_velfield(self.xbin, self.ybin, data1, vmin=vmin, vmax=vmax, flux=self.flux_obs, nodots=nodots)
        plt.title(f"Input V$_{{{self.moment}}}$ moment")

        plt.subplot(122)
        plot_velfield(self.xbin, self.ybin, self.model, vmin=vmin, vmax=vmax, flux=self.flux, nodots=nodots, colorbar=colorbar)
        plt.plot(self.xbin[~ok], self.ybin[~ok], 'ok', mec='white')
        plt.title(f"JAM$_{{\\rm {self.align}}}$ model")
        plt.tick_params(labelleft=False)
        plt.subplots_adjust(wspace=0.03)

##############################################################################
