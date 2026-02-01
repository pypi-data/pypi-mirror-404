"""
##############################################################################

Copyright (C) 2026, Michele Cappellari
E-mail: michele.cappellari_at_physics.ox.ac.uk

Updated versions of the software are available from my web page
http://purl.org/cappellari/software

This software is provided as is without any warranty whatsoever.
Permission to use, for non-commercial purposes is granted.
Permission to modify for personal or internal use is granted,
provided this copyright and disclaimer are included unchanged
at the beginning of the file. All other rights are reserved.
In particular, redistribution of the code is not allowed.

##############################################################################

MODIFICATION HISTORY:
    V1.0.0: Written and tested.
        Michele Cappellari, Oxford, 31 January 2026
    Vx.x.x: Additional changes are documented in the CHANGELOG of the JamPy package.

"""

from scipy import special
import numpy as np

##############################################################################

def betax(a, b, x):
    """
    Fully vectorized Incomplete Beta function B_x(a, b).

    Incomplete beta function defined as the Mathematica Beta[x, a, b]:

        Beta[x, a, b] = Integral[t^(a - 1) * (1 - t)^(b - 1), {t, 0, x}]

    Supports scalar/vector a, b and array-like x with standard broadcasting.

    This implementation uses recurrence relations to shift a and b to the
    positive regime, where scipy.special.betainc is well-defined.
    It uses Pochhammer ratios to handle cases where a + b is a non-positive.
    """
    a, b, x = np.asarray(a), np.asarray(b), np.asarray(x)

    na = int(-a.min()) + 1 if a.min() <= 0 else 0
    nb = int(-b.min()) + 1 if b.min() <= 0 else 0
    
    ap, bp = a + na, b + nb
    res = special.betainc(ap, bp, x) * special.beta(ap, bp)

    # 1. Shift a back: I_x(a, bp) via DLMF 8.17.20 https://dlmf.nist.gov/8.17#E20
    if na > 0:
        j = np.arange(na)
        aj, bpj = a[..., None], bp[..., None]
        w = special.poch(aj + bpj, j) / special.poch(aj, j + 1)
        w0 = special.poch(a + bp, na) / special.poch(a, na)        
        term = (x[..., None]**(aj + j) * w).sum(-1)
        res = term * (1 - x)**bp + w0 * res

    # 2. Shift b back: I_x(a, b) via DLMF 8.17.21 https://dlmf.nist.gov/8.17#E21
    if nb > 0:
        j = np.arange(nb)
        aj, bj = a[..., None], b[..., None]
        w = special.poch(aj + bj, j) / special.poch(bj, j + 1)
        w0 = special.poch(a + b, nb) / special.poch(b, nb)        
        term = ((1 - x)[..., None]**(bj + j) * w).sum(-1)
        res = -term * x**a + w0 * res 

    return res

##############################################################################
