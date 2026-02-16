import datetime

from . import procedure
from . import setpoint as sp
from . import equation
from . import quantity


class PolynomialProcedure(procedure.ProcedureShell):
    def __init__(self, streams, *kwargs):
        super().__init__(streams, *kwargs)

        self.parameters = dict()
        self.point_count = 2
        
        return

    @property
    def sp1(self):
        return self.parameters['sp1']

    @property
    def sp2(self):
        return self.parameters['sp2']

    @property
    def sp3(self):
        return self.parameters['sp3']
        
    # def do_spread(self, arg):
    #     ''' spread <n> Calibration point count, 2 or 3'''
        
    #     try:
    #         if int(arg) > len(self.parameters): # not in [2,3]:
    #             print(' possible point count is {}'.format([2,3]))
    #         else:
    #             self.point_count = int(arg)
    #     except:
    #         print(' possible choices are 2 or 3')
            
    #     self.do_show()
        
    #     return False

    def do_sp1(self, arg):
        ''' sp1 <n> The first (lowest value) in a two or three point calibration'''
        
        try:
            self.sp1.target_quantity.value = float(arg)
        except:
            print(' invalid value: setpoint unchanged.')

        self.do_show()
        
        return False
        
    def do_sp2(self, arg):
        ''' sp2 <n> The middle or highest value in a two or three point calibration'''
        
        try:
            self.sp2.target_quantity.value = float(arg)
        except:
            print(' invalid value: setpoint unchanged.')

        self.do_show()
        
        return False
        
    def do_sp3(self, arg):
        ''' sp3 <n> The highest value in a three point calibration'''
        
        if self.point_count < 3:
            print(' there is no point 3 in a two point calibration')
        else:
            self.sp3.target_quantity.value = float(arg)

        self.do_show()
        
        return False
        
    def show(self):
        print('  Units:  {}'.format(self.scaled_units))
        print('  Spread: {} point'.format(self.point_count))
        print('   {}'.format(self.sp1.target_quantity))
        print('   {}'.format(self.sp2.target_quantity))
        if self.point_count == 3:
            print('   SP3:   {} {}'.format(self.sp3.target_quantity))

        return

    def prep(self, sensor):
        if sensor.calibration.equation is None:
            sensor.calibration.equation = PolynomialEquation()
        
        # give sensor its own copy of paramters
        sensor.parameters = dict()
        sensor.parameters[self.sp1.name] = self.sp1.clone()
        sensor.parameters[self.sp2.name] = self.sp2.clone()
        if self.point_count == 3:
            sensor.parameters[self.sp3.name] = self.sp3.clone()

        super().prep(sensor)

        return
        
    def cal(self, sensor):
        print(' running {} point calibration on sensor {}'.format(self.point_count, sensor.id))
        ok = True

        # run thru the setpoints
        for parameter in sensor.parameters.values():
            if parameter.name in ['sp1', 'sp2', 'sp3']:
                if not parameter.run(sensor):
                    ok = False
                    break

        if ok:
            sensor.calibration.timestamp = datetime.date(1970, 1, 1)
            
            p1 = sensor.parameters['sp1']
            p2 = sensor.parameters['sp2']
            ok = sensor.calibration.equation.generate(p1, p2)
            
            if ok:
                sensor.calibration.timestamp = datetime.date.today()
    
        return ok

    def pack(self, prefix):
        package = super().pack(prefix)
        package += 'point_count = {}\n'.format(self.point_count)

        my_prefix = '{}.{}'.format(prefix, 'parameters')
        for parameter in self.parameters.values():
            parameter_prefix = '{}.{}'.format(my_prefix, parameter.name)
            package += '\n'
            package += parameter.pack(parameter_prefix)
        
        return package

    def unpack(self, package):
        super().unpack(package)
        self.point_count = package['point_count']

        if 'parameters' in package:        
            for template in package['parameters'].values():
                parameter = sp.StreamSetpoint(quantity.Quantity())
                parameter.unpack(template)
                self.parameters[parameter.name] = parameter
            
        return
    
class PolynomialEquation(equation.Equation):
    def __init__(self, package=None):
        super().__init__()
        
        self.degree = 1
        self.coefficients = dict()
        self.coefficients[0] = 0.0
        self.coefficients[1] = 1.0

        if package:
            self.unpack(package)

        return

    def __len__(self):
        return len(self.coefficients)

    def generate(self, p1, p2):
        #print(p1.target_quantity, p1.measured_quantity)
        #print(p2.target_quantity, p2.measured_quantity)
        
        is_valid = False
        try:
            dx = p2.target_quantity.value - p1.target_quantity.value
            dy = p2.measured_quantity.value - p1.measured_quantity.value
            self.coefficients[1] = dy / dx
            self.coefficients[0] = p1.measured_quantity.value - self.coefficients[1] * p1.target_quantity.value
            
            is_valid = True
        except ZeroDivisionError:
            self.coefficients[1] = 0.00001
            self.coefficients[0] = 0.0

        return is_valid
    
    def evaluate_x(self, x_value):
        y = self.coefficients[1] * x_value + self.coefficients[0]
        
        return y

    def evaluate_y(self, y_value):
        slope = self.coefficients[1]
        if slope == 0:
            slope = 0.00001

        x = (y_value - self.coefficients[0]) / slope
        
        return x
    
    # def dump(self):
    #     for key, value in self.coefficients.items():
    #         print(key, round(value, 3))

    #     return
    
    def pack(self, prefix):
        package = super().pack(prefix)

        package += 'degree = {}\n'.format(self.degree)

        package += '[{}.{}]\n'.format(self.package_prefix, 'coefficients')
        for key, value in self.coefficients.items():
            package += '{} = {}\n'.format(key, value)

        return package

    def unpack(self, package):
        super().unpack(package)
        
        self.degree = package['degree']
        
        for name, value in package['coefficients'].items():
            self.coefficients[int(name)] = value
        
        return

