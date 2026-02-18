import math
import datetime

from . import procedure
from . import quantity
from . import equation


class NtcBetaProcedure(procedure.ProcedureShell):
    def __init__(self, streams, *kwargs):
        super().__init__(streams, *kwargs)

        self.parameters = dict()
        
        return

    @property
    def r25(self):
        return self.parameters['r25'] # returns a quantity

    @property
    def beta(self):
        return self.parameters['beta'] # returns a quantity

    def do_beta(self, arg):
        ''' beta <n> The thermistors defined beta value'''
        
        try:
            self.beta.value = float(arg)
        except:
            print(' invalid value: beta unchanged.')

        self.do_show()
        
        return False
        
    def do_r25(self, arg):
        ''' r25 <n> The thermistors defined resistance in ohms at 25 Celsius'''
        
        try:
            self.r25.value = float(arg)
        except:
            print(' invalid value: r25 unchanged.')

        self.do_show()
        
        return False
        
    def show(self):
        print('  Units:  {}'.format(self.scaled_units))
        print('   {}'.format(self.r25))
        print('   {}'.format(self.beta))

        return

    def prep(self, sensor):
        super().prep(sensor)

        if sensor.calibration.equation is None:
            sensor.calibration.equation = NtcBetaEquation()
            
        return
        
    def evaluate(self, sensor):
        # our calibration is based on constants. nothing to do.
        ok = True
        return ok

    def save(self, sensor):
        sensor.calibration.equation.beta = self.parameters['beta'].value
        sensor.calibration.equation.r25 = self.parameters['r25'].value
        
        ok = True
        return ok
    
    def pack(self, prefix):
        package = super().pack(prefix)
    
        my_prefix = '{}.{}'.format(prefix, 'parameters')
        for name, parameter in self.parameters.items():
            parameter_prefix = '{}.{}'.format(my_prefix, name)
            package += '\n'
            package += parameter.pack(parameter_prefix)

        return package

    def unpack(self, package):
        super().unpack(package)

        if 'parameters' in package:        
            for name, section in package['parameters'].items():
                quant = quantity.Quantity.from_package(section)
                self.parameters[name] = quant
                
        return

    
class PhorpNtcBetaProcedure(NtcBetaProcedure):
    def __init__(self, streams, *kwargs):
        super().__init__(streams, *kwargs)

        self.parameters = dict()
        
        return

    def prep(self, sensor):
        # bypass supers prep()
        procedure.ProcedureShell.prep(self, sensor) # xx danger

        if sensor.calibration.equation is None:
            sensor.calibration.equation = PhorpNtcBetaEquation() 
            
        return
        
    
class NtcBetaEquation(equation.Equation):
    def __init__(self, package=None):
        super().__init__()

        self.beta = 3499
        self.r25 = 9999
        self.t0 = 273.15 # freezing point of water in degrees Kelvin
        
        if package:
            self.unpack(package)

        return

    def to_kelvin(self, ntc_ohms):
        t25 = self.t0 + 25.0
        try:
            kelvin = 1.0 / ( 1.0/t25 + (1.0/self.beta) * math.log(ntc_ohms/self.r25) )
        except ValueError:
            kelvin = 0

        return kelvin
    def to_celcius(self, ntc_ohms):
        kelvin = self.to_kelvin(ntc_ohms)
        celcius = kelvin - self.t0

        return celcius

    def to_fahrenheit(self, ntc_ohms):
        celcius = self.to_celcius(ntc_ohms)
        fahrenheit = 9.0/5.0 * celcius + 32

        return fahrenheit

    def pack(self, prefix):
        package = super().pack(prefix)
        
        package += 'beta = {}\n'.format(self.beta)
        package += 'r25 = {}\n'.format(self.r25)

        return package

    def unpack(self, package):
        super().unpack(package)
        
        self.beta = package['beta']
        self.r25 = package['r25']
        
        return
    
class PhorpNtcBetaEquation(NtcBetaEquation):
    # perhaps integrate with ntcbeta and evaluate a quantity with source units.
    def __init__(self, package=None):
        super().__init__()

        self.bias_volts = 1.5
        self.bias_ohms = 10000

        if package:
            self.unpack(package)
        
        return

    def evaluate_y(self, ntc_millivolts):  # target_units
        ntc_volts = ntc_millivolts / 1000  # xx convert back to volts...
        
        ntc_amps = (self.bias_volts - ntc_volts) / self.bias_ohms
        ntc_ohms = ntc_volts / ntc_amps

        #if 'c' in self.scaled_units.lower(): # xx
        return self.to_celcius(ntc_ohms)

        #return self.to_fahrenheit(ntc_ohms)

    def pack(self, prefix):
        package = super().pack(prefix)
        
        package += 'bias_volts = {}\n'.format(self.bias_volts)
        package += 'bias_ohms = {}\n'.format(self.bias_ohms)

        return package

    def unpack(self, package):
        super().unpack(package)
        
        self.bias_volts = package.get('bias_volts', 1.5)
        self.bias_ohms = package.get('bias_ohms', 10000)
        
        return
