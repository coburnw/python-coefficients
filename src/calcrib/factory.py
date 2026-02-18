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
