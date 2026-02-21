#
# factory.py - Class factories for the various objects stored in configuration files.
#              part of the python sensor silo project.
#
# Copyright (c) 2026 Coburn Wightman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#

from . import thermistor
from . import polynomial

class EquationFactory():
    def __init__(self):
        return

    def new(self, package):
        # print('creating new {}'.format(package['type']))
        if package['type'] == 'NtcBetaEquation':
            equation = thermistor.NtcBetaEquation(package)
        elif package['type'] == 'PhorpNtcBetaEquation':
            equation = thermistor.PhorpNtcBetaEquation(package)
        elif package['type'] == 'PolynomialEquation':
            equation = polynomial.PolynomialEquation(package)

        return equation
