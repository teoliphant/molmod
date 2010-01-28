# MolMod is a collection of molecular modelling tools for python.
# Copyright (C) 2007 - 2010 Toon Verstraelen <Toon.Verstraelen@UGent.be>, Center
# for Molecular Modeling (CMM), Ghent University, Ghent, Belgium; all rights
# reserved unless otherwise stated.
#
# This file is part of MolMod.
#
# MolMod is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# MolMod is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --


from molmod.minimizer import *

import unittest, numpy


__all__ = ["MinimizerTestCase"]


def fun(x, do_gradient=False):
    value = 2 + numpy.sin(x[0]) + numpy.cos(x[1]) + x[0]*x[0] + x[1]*x[1] - x[0]*x[1]
    if do_gradient:
        gradient = numpy.array([
            numpy.cos(x[0]) + 2*x[0] - x[1],
            -numpy.sin(x[1]) + 2*x[1] - x[0],
        ])
        return value, gradient
    else:
        return value


class MinimizerTestCase(unittest.TestCase):
    def check_min(self, x_opt, step_rms, grad_rms):
        f_opt = fun(x_opt)
        for i in xrange(100):
            delta = numpy.random.normal(0, 1, 2)
            delta /= numpy.linalg.norm(delta)
            delta *= numpy.sqrt(len(delta))
            delta *= step_rms
            x_dev = x_opt + delta
            f_dev = fun(x_dev)
            self.assert_(f_opt - f_dev <= grad_rms*step_rms)

    def test_golden(self):
        x_init = numpy.zeros(2, float)
        line_search = GoldenLineSearch(qtol=1e-10, qmax=1.0, max_iter=500)
        stop_condition = StopCondition(grad_rms=1e-6, step_rms=1e-6, grad_max=3e-6, step_max=3e-6, max_iter=50)
        minimizer = Minimizer(
            x_init, fun, line_search, stop_condition,
            anagrad=False, verbose=False,
        )
        self.check_min(minimizer.x, 1e-6, 1e-6)

    def test_newton(self):
        x_init = numpy.zeros(2, float)
        line_search = NewtonLineSearch(qtol=1e-10, qmax=1.0, max_iter=500)
        stop_condition = StopCondition(grad_rms=1e-6, step_rms=1e-6, grad_max=3e-6, step_max=3e-6, max_iter=50)
        minimizer = Minimizer(
            x_init, fun, line_search, stop_condition,
            anagrad=True, verbose=False,
        )
        self.check_min(minimizer.x, 1e-6, 1e-6)

    def test_newtong(self):
        x_init = numpy.zeros(2, float)
        line_search = NewtonGLineSearch(qtol=1e-10, qmax=1.0, max_iter=500)
        stop_condition = StopCondition(grad_rms=1e-6, step_rms=1e-6, grad_max=3e-6, step_max=3e-6, max_iter=50)
        minimizer = Minimizer(
            x_init, fun, line_search, stop_condition,
            anagrad=True, verbose=False,
        )
        self.check_min(minimizer.x, 1e-6, 1e-6)


