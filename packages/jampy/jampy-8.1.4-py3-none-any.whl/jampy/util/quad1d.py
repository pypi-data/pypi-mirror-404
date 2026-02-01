"""
    Copyright (C) 2007-2023, Michele Cappellari

    E-mail: michele.cappellari_at_physics.ox.ac.uk

    Updated versions of the software are available from PyPi
    https://pypi.org/project/jampy

    If you have found this software useful for your research,
    I would appreciate an acknowledgement and a link to the website.

    This software is provided as is without any warranty whatsoever.
    Permission to use, for non-commercial purposes is granted.
    Permission to modify for personal or internal use is granted,
    provided this copyright and disclaimer are included unchanged
    at the beginning of the file. All other rights are reserved.
    In particular, redistribution of the code is not allowed.

############################################################################


CHANGELOG
---------

    V1.0.0: Written and tested against the corresponding MATLAB version,
        Michele Cappellari, Oxford, 22 October, 2007

    V1.1.0: Allow function parameters to be passed via the FUNCTARGS keyword.
        MC, Oxford, 23 October 2007

    V1.1.1: Added STATUS keyword. Provide more informative error messages on failure.
        MC, Windoek, 5 October 2008

    V1.1.2: Renamed CAP_QUADVA to avoid potential naming conflicts.
        MC, Paranal, 8 November 2013

    V2.0.0: Translated from IDL into Python. MC, Paranal, 14 November 2013

    V2.0.1: Fixed possible program stop. MC, Oxford, 27 January 2014

    V2.0.2: Support both legacy Python 2.7 and Python 3. MC, Oxford, 25 May 2014

    V2.0.3: Dropped Python 2.7 support. MC, Oxford, 12 May 2018

    V2.1.0: Included optional plotting of sampled points. MC, Oxford, 25 June 2019

    V3.0.0:
        - Changed interface as a class and renamed quadva --> quad1d
        - Print number of function evaluation if ``verbose=1``.
        - New ``singular`` keyword: set ``singular=False`` to prevent
          transforming the coordinates of the integrand. This is useful
          when one wants to transform the coordinates outside ``quad1d``.
        MC, Oxford, 4 February 2022

    V3.1.0: Change defaults to `singular=False` and `epsabs=0` like `quad2d`.
        MC, Oxford, 3 January 2023

    V4.0.0: Allow for quadrature of vector functions. Uses the same set of
        evaluation points for all components of the function and ensures that
        the convergence criterion is satisfied for all.
        MC, Oxford, 11 June 2023

"""
import numpy as np
import matplotlib.pyplot as plt

EPS = 100*np.finfo(float).eps

################################################################################

def _qva_split(interval):
    """
    If breakpoints are specified, split sub-intervals in
    half as needed to get a minimum of 10 sub-intervals.
    """
    v = interval
    while True:
        npts = interval.size
        if npts > 10:
            break
        v = np.zeros(npts*2 - 1)
        v[0::2] = interval
        v[1::2] = interval[:-1] + 0.5*np.diff(interval)
        interval = v

    return v

################################################################################

def _qva_check_spacing(x):
    ax = np.abs(x)
    too_close = np.any(np.diff(x) <= EPS*np.maximum(ax[:-1], ax[1:]))

    return too_close

################################################################################

def _qva_f1(fun, t, a, b, args):
    """
    Transform to weaken singularities at both ends: [a, b] -> [-1, 1]
    """
    x = 0.25*(b - a)*t*(3. - t**2) + 0.5*(b + a)
    too_close = _qva_check_spacing(x)
    if too_close:
        y = []
    else:
        y = fun(x, *args)
        y *= 0.75*(b - a)*(1. - t**2)

    return y, too_close

################################################################################

def _qva_f2(fun, t, a, b, args):
    """
    Transform to weaken singularity at left end: [a, np.inf) -> [0, Inf).
    Then transform to finite interval: [0, Inf) -> [0, 1].
    """
    Tt = t/(1. - t)
    x = a + Tt**2
    too_close = _qva_check_spacing(x)
    if too_close:
        y = []
    else:
        y = fun(x, *args)
        y *= 2.*Tt/(1. - t)**2

    return y, too_close

################################################################################

def _qva_f3(fun, t, a, b, args):
    """
    Transform to weaken singularity at right end: (-Inf, b] -> (-Inf, 0].
    Then transform to finite interval: (-Inf, 0] -> (-1, 0].
    """
    Tt = t/(1. + t)
    x = b - Tt**2
    too_close = _qva_check_spacing(x)
    if too_close:
        y = []
    else:
        y = fun(x, *args)
        y *= -2.*Tt/(1. + t)**2

    return y, too_close

################################################################################

def _qva_f4(fun, t, a, b, args):
    """
    Transform to finite interval: (-Inf, Inf) -> (-1, 1)
    """
    x = t/(1. - t**2)
    too_close = _qva_check_spacing(x)
    if too_close:
        y = []
    else:
        y = fun(x, *args)
        y *= (1. + t**2)/(1. - t**2)**2

    return y, too_close

################################################################################

def _qva_f5(fun, t, a, b, args):
    """
    Simple linear transformation: [a, b] -> [-1, 1]
    """
    x = 0.5*((b + a) + (b - a)*t)
    too_close = _qva_check_spacing(x)
    if too_close:
        y = []
    else:
        y = fun(x, *args)
        y *= 0.5*(b - a)

    return y, too_close

################################################################################

def _qva_Vadapt(f, tinterval, rtol, atol, samples, nodes, wt, ewt, fun, a, b, args, plot):
    """ Main loop of the quadrature """

    tbma = np.abs(tinterval[-1] - tinterval[0])  # length of transformed interval

    # Initialize array of subintervals of [a,b].
    subs = np.column_stack([tinterval[:-1], tinterval[1:]])  # Two columns array[n, 2]

    # Initialize partial sums.
    IfxOK = errOK = 0

    # Initialize main loop
    OK = first = converged = True
    Ifx = errbnd = fcall = vfcall = 0

    while True:
        # SUBS contains subintervals of [a,b] where the integral is not
        # sufficiently accurate.  The first row of SUBS holds the left end
        # points and the second row, the corresponding right end points.
        midpt = subs.sum(1)/2      # midpoints of the subintervals
        halfh = np.diff(subs, axis=1)/2     # half the lengths of the subintervals
        x = nodes*halfh + midpt[:, None]    # broadcasting midpt
        halfh = halfh.ravel()
        x = x.ravel()

        fx, too_close = f(fun, x, a, b, args)
        fcall += x.size
        vfcall += 1

        # Quit if mesh points are too close or too close to a
        # singular point or got into trouble on first evaluation.
        not_finite = np.any(np.isinf(fx))
        if too_close or not_finite:
            break

        if plot:
            if first:
                plt.figure('quad1d')
                plt.clf()
                plt.xlabel('x')
                plt.ylabel('y')
                xall, yall = x, fx
            else:
                yall = np.column_stack([yall, fx])
                xall = np.append(xall, x)
            plt.figure('quad1d')
            plt.plot(x, fx.T, '+')

        if fx.ndim == 1:
            fx = fx[None, :]

        fx = fx.reshape(len(fx), -1, samples)

        # Quantities for subintervals.
        Ifxsubs = fx @ wt * halfh
        errsubs = fx @ ewt * halfh

        # Quantities for all of [a, b].
        Ifx = Ifxsubs.sum(1) + IfxOK
        errbnd = abs(errsubs.sum(1) + errOK)

        # Test for convergence:
        tol = np.maximum(atol, rtol*np.abs(Ifx))
        if np.all(errbnd <= tol):
            converged = True
            break

        # Locate subintervals where the approximate integrals are
        # sufficiently accurate and use them to update partial sums.
        good = np.all(np.abs(errsubs) <= (2/tbma)*halfh*tol[:, None], 0)
        errOK += np.sum(errsubs[:, good])
        IfxOK += np.sum(Ifxsubs[:, good])
        # Only keep subintervals which are not yet sufficiently accurate
        subs = subs[~good, :]
        if subs.size == 0:  # all intervals are accurate
            converged = True
            break

        # Split the remaining subintervals in half. Quit if splitting
        # results in too many subintervals.
        many_subint = 2*subs.size > 650  # multiplied limit by 10x MC 26/FEB/2008
        if many_subint:
            break
        midpt = subs.sum(1)/2
        tmp = np.column_stack([subs[:, 0], midpt, midpt, subs[:, 1]])
        subs = tmp.reshape(-1, 2)  # ---> subs[n, 2]
        first = False

    if first and not converged:
        if too_close:
            print('***Sub intervals too close.')
        elif not_finite:
            print('***Infinite values in integrand.')
        elif many_subint:
            print('***Too many sub intervals.')
        OK = False

    if plot:
        plt.figure('quad1d')
        w = np.argsort(xall)
        plt.plot(xall[w], yall.T[w])

    return Ifx, errbnd, OK, fcall, vfcall

################################################################################

class quad1d:
    """
    Compute the definite integral of a continuous function over a given interval.

    The function can handle infinite intervals and functions with certain types
    of singularities.

    Parameters
    ----------
    fun : callable
        Function to integrate. Accepts a row vector `x` and returns a vector
        `y` where `y[m] = f(x[m])` for `m = 1, ..., len(x)`.
        For vector-valued functions `fun = [f₁, f₂, ..., fₙ]`, `fun` should
        return a matrix with rows `y[j, :] = fⱼ(x)`.

    interval : array_like
        Interval of integration, specified as `[a, b]` where `a < b`. Endpoints
        `a` and/or `b` can be `-np.inf` or `np.inf` for infinite intervals.
        If necessary, subdivide the interval by specifying breakpoints within
        `interval`, especially if `f(x)` has discontinuities or rapid changes.

    epsrel : float, optional
        Relative error tolerance (default: `1e-5`).

    epsabs : float, optional
        Absolute error tolerance (default: `0`).

    Returns
    -------
    q : object
        An object with attributes:

        * integ : float or ndarray
            Approximation of the integral over the specified interval.

        * errbnd : float or ndarray
            Estimated bound on the absolute error `|integral - q.integ|`.

        * status : int
            Exit status of the algorithm:
            - `0`: Success
            - `1`: Failure

    Notes
    -----
    The goal is to compute `q.integ` such that:

        |q.integ - integral| < max(epsabs, epsrel*|q.integ|)

    If `quad1d` cannot meet the desired tolerance, it still provides meaningful
    values for `q.integ` and `q.errbnd`, along with a warning that includes
    `q.errbnd`.

    **Special Considerations**:

    - **Infinite Intervals**: When integrating over infinite intervals (e.g.,
      `[a, np.inf)`), ensure that `f(x)` decays rapidly as `x → ∞`. Functions
      that decay slowly or oscillate infinitely may require specialized
      algorithms.

    - **Singularities at Endpoints**: If `f(x)` has singularities at the
      endpoints (behaving like `log|x - c|` or `|x - c|^p` with `p ≥ -1/2` at
      `c = a` or `c = b`), `quad1d` can still compute the integral effectively.

    - **Internal Singularities**: For singularities within the interval `(a,
      b)`, split the integral at the points of singularity and integrate each
      segment separately using `quad1d`. Sum the results to obtain the total
      integral.

    - **Function Behavior**: `quad1d` starts by sampling `f(x)` at 150 points
      within the interval. It's crucial that these samples capture the
      essential behavior of `f(x)`. If your function oscillates rapidly or has
      sharp peaks, consider subdividing the interval using breakpoints to guide
      the algorithm.

    References
    ----------
    .. [1] Shampine, L. F. (2008). "Vectorized Adaptive Quadrature in Matlab."
    *Journal of Computational and Applied Mathematics*, 211(1), 131-140. doi:
    [10.1016/j.cam.2006.11.021](http://dx.doi.org/10.1016/j.cam.2006.11.021)

    Examples
    --------
    Compute the integral of `exp(-x^2)` from 0 to infinity:

    >>> import numpy as np
    >>> def integrand(x):
    ...     return np.exp(-x**2)
    >>> q = quad1d(integrand, [0, np.inf])
    >>> print("Integral:", q.integ)
    >>> print("Estimated error bound:", q.errbnd)

    Handling a function with a singularity at an endpoint:

    >>> def singular_integrand(x):
    ...     return np.log(x)
    >>> q = quad1d(singular_integrand, [0, 1], singular=True)
    >>> print("Integral:", q.integ)
    >>> print("Estimated error bound:", q.errbnd)

    Integrating a vector-valued function:

    >>> def vector_integrand(x):
    ...     return np.array([np.sin(x), np.cos(x)])
    >>> q = quad1d(vector_integrand, [0, np.pi])
    >>> print("Integral:", q.integ)
    >>> print("Estimated error bound:", q.errbnd)
    """

    def __init__(self, fun, interval, epsrel=1e-5, epsabs=0, plot=False,
                 verbose=False, singular=False, args=()):

        interval = np.asarray(interval)
        nint = interval.size
        assert nint >= 2, "INTERVAL must be a real vector of at least two entries."
        assert np.all(np.diff(interval) > 0), "Entries of INTERVAL must strictly increase."
        assert epsrel > 0 or epsabs > 0, "Either `epsrel` or `epsabs` must be positive"

        a = interval[0]
        b = interval[-1]

        # Generally the error test is a mixed one, but pure absolute error
        # and pure relative error are allowed.  If a pure relative error
        # test is specified, the tolerance must be at least 100*EPS. 
        #
        rtol = max(epsrel, EPS)
        atol = epsabs

        # Gauss-Kronrod (7,15) pair. Use symmetry in defining nodes and weights.
        #
        samples = 15
        pnodes = np.array(
            [0.2077849550078985, 0.4058451513773972, 0.5860872354676911,
             0.7415311855993944, 0.8648644233597691, 0.9491079123427585,
             0.9914553711208126])
        nodes = np.hstack([-pnodes[::-1], 0, pnodes])
        pwt = np.array(
            [0.2044329400752989, 0.1903505780647854, 0.1690047266392679,
             0.1406532597155259, 0.1047900103222502, 0.06309209262997855,
             0.02293532201052922])
        wt = np.hstack([pwt[::-1], 0.2094821410847278, pwt])
        pwt7 = np.array([0, 0.3818300505051189, 0, 0.2797053914892767,
                         0, 0.1294849661688697, 0])
        ewt = wt - np.hstack([pwt7[::-1], 0.4179591836734694, pwt7])

        # Identify the task. If breakpoints are specified, work out
        # how they map into the standard interval.
        #
        if singular or np.inf in [a, b]:

            if a != -np.inf and b != np.inf:
                if nint > 2:
                    # Analytical transformation suggested by K.L. Metlov:
                    alpha = 2.*np.sin(np.arcsin((a + b - 2.*interval[1:-1])/(a - b))/3.)
                    tinterval = np.hstack([-1., alpha, 1.])
                    tinterval = _qva_split(tinterval)
                else:
                    tinterval = np.linspace(-1, 1, 11)

                Ifx, errbnd, OK, fcall, vfcall = _qva_Vadapt(
                    _qva_f1, tinterval, rtol, atol, samples, nodes, wt, ewt,
                    fun, a, b, args, plot)

            elif a != -np.inf and b == np.inf:
                if nint > 2:
                    alpha = np.sqrt(interval[1:-1] - a)
                    tinterval = np.hstack([0., alpha/(1. + alpha), 1.])
                    tinterval = _qva_split(tinterval)
                else:
                    tinterval = np.linspace(0, 1, 11)

                Ifx, errbnd, OK, fcall, vfcall = _qva_Vadapt(
                    _qva_f2, tinterval, rtol, atol, samples, nodes, wt, ewt,
                    fun, a, b, args, plot)

            elif a == -np.inf and b != np.inf:
                if nint > 2:
                    alpha = np.sqrt(b - interval[1:-1])
                    tinterval = np.hstack([-1., -alpha/(1. + alpha), 0.])
                    tinterval = _qva_split(tinterval)
                else:
                    tinterval = np.linspace(-1, 0, 11)

                Ifx, errbnd, OK, fcall, vfcall = _qva_Vadapt(
                    _qva_f3, tinterval, rtol, atol, samples, nodes, wt, ewt,
                    fun, a, b, args, plot)

            elif a == -np.inf and b == np.inf:
                if nint > 2:
                    # Analytical transformation suggested by K.L. Metlov:
                    alpha = np.tanh(np.arcsinh(2.*interval[1:-1])/2.)
                    tinterval = np.hstack([-1., alpha, 1.])
                    tinterval = _qva_split(tinterval)
                else:
                    tinterval = np.linspace(-1, 1, 11)

                Ifx, errbnd, OK, fcall, vfcall = _qva_Vadapt(
                    _qva_f4, tinterval, rtol, atol, samples, nodes, wt, ewt,
                    fun, a, b, args, plot)

        else:

            tinterval = np.linspace(-1, 1, 11)
            Ifx, errbnd, OK, fcall, vfcall = _qva_Vadapt(
                _qva_f5, tinterval, rtol, atol, samples, nodes, wt, ewt,
                fun, a, b, args, plot)

        if len(Ifx) == 1:
            Ifx = Ifx[0]
            errbnd = errbnd[0]

        if OK:
            status = 0  # success   
        else:
            print('***Integral does not satisfy error test.')
            print('***Approximate bound on error is', errbnd)
            status = 1

        if verbose:
            print(f"Integral: {Ifx} +/- {errbnd}")
            print(f"Function calls: {vfcall}, Function evaluations: {fcall}")

        self.integ = Ifx
        self.errbnd = errbnd
        self.status = status

################################################################################

def quad1d_test1(x, a=3, b=5):
    """
    Gladwell's problem no1. limits x=[0,8]
    Precise result: 0.33333333332074955152

    """
    return np.exp(-a*x)-np.cos(b*np.pi*x)

################################################################################

def quad1d_test2(x):
    """
    Gladwell's problem no2. limits x=[-1,2]
    Precise result: 5.9630898453302550932

    """
    return np.abs(x - 1/np.sqrt(3)) + np.abs(x + 1/np.sqrt(2))

################################################################################

def quad1d_test3(x, a=2.0/3):
    """
    Gladwell's problem no3. limits x=[0,1]
    Precise result: 3 with x^(-2d/3d)

    """
    return x**a

################################################################################

def quad1d_test4(x):
    """
    Gladwell's problem no3. limits x=[0,1]
    Precise result: 2.5066282746310005024

    """
    return np.exp(-x**2/2)

################################################################################

def quad1d_examples():

    print('\ntest 1 ###############################\n')
    ifx = quad1d(quad1d_test1, [0, 8], args=(3, 5), epsrel=0, epsabs=1e-12, singular=1, verbose=1).integ
    print('actual error:', ifx - 0.33333333332074955152)
    print('\ntest 2 ###############################\n')
    ifx = quad1d(quad1d_test2, [-1, 2], epsrel=0, epsabs=1e-12, singular=1, verbose=1).integ
    print('actual error:', ifx - 5.9630898453302550932)
    print('\ntest 2 with breakpoints ##############\n')
    ifx = quad1d(quad1d_test2, [-1, -1/np.sqrt(2), 1/np.sqrt(3), 2], epsrel=0, singular=1, epsabs=1e-12, verbose=1).integ
    print('actual error:', ifx - 5.9630898453302550932)
    print('\ntest 3 ###############################\n')
    ifx = quad1d(quad1d_test3, [0, 1], args=(-2.0/3,), epsrel=0, epsabs=1e-12, singular=1, verbose=1).integ
    print('actual error:', ifx - 3)
    print('\ntest 4 ###############################\n')
    ifx = quad1d(quad1d_test4, [-np.inf, np.inf], epsrel=1e-8, epsabs=0, singular=1, verbose=1).integ
    print('actual error:', ifx - 2.5066282746310005024, "\n")
    ifx = quad1d(quad1d_test4, [-8, 8], epsrel=1e-8, epsabs=0, singular=0, verbose=1, plot=1).integ
    print('actual error:', ifx - 2.5066282746310005024)

################################################################################

if __name__ == '__main__':
    quad1d_examples()
