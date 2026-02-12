from . import calibration
from . import thermistor
from . import polynomial

class EquationFactory():
    def __init__(self):
        return

    def new(self, package):
        # print('creating new {}'.format(package['type']))
        if package['type'] == 'BetaThermistorEquation':
            equation = thermistor.BetaThermistorEquation(package)
        elif package['type'] == 'PhorpThermistorEquation':
            equation = thermistor.PhorpThermistorEquation(package)
        elif package['type'] == 'PolynomialEquation':
            equation = polynomial.PolynomialEquation(package)

        return equation
