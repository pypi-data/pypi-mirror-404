#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import pytest

from turbx import gradient


@pytest.mark.parametrize( "acc, edge, tol", [
    (2, "half", 1e-2),
    (4, "half", 1e-3),
    (6, "half", 1e-6),
    (8, "half", 1e-7),
    (2, "full", 1e-2),
    (4, "full", 1e-3),
    (6, "full", 1e-6),
    (8, "full", 1e-7),
    ],
)
def test_deriv_1d_o1(acc, edge, tol):
    '''
    Test first derivative against analytic sin -> cos.
    '''
    nx = 500
    x = np.linspace(0, 4*np.pi, nx, dtype=np.float64)
    u = np.sin(x)
    exact = np.cos(x)
    num = gradient(
        u=u,
        x=x,
        d=1,
        axis=0,
        acc=acc,
        edge_stencil=edge,
    )
    np.testing.assert_allclose(exact, num, rtol=tol, atol=tol)
