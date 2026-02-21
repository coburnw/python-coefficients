#
# polynomial.py - a specialized equation to scale a sensors raw value.
#                 part of the python sensor silo project.
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

import datetime

from . import procedure
from . import setpoint as sp
from . import equation
from . import quantity


class PolynomialProcedure(procedure.ProcedureShell):
    def __init__(self, streams, *kwargs):
        super().__init__(streams, *kwargs)

        self.point_count = 2 # spread_count?
        
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
        super().prep(sensor)

        if sensor.calibration.equation is None:
            sensor.calibration.equation = PolynomialEquation()
        
        # copy parameters of interest
        sensor.calibration.parameters = dict()
        sensor.calibration.parameters[self.sp1.name] = self.sp1.clone()
        sensor.calibration.parameters[self.sp2.name] = self.sp2.clone()
        if self.point_count == 3:
            sensor.calibration.parameters[self.sp3.name] = self.sp3.clone()

        return
        
    def evaluate(self, sensor):
        print(' running {} point calibration on sensor {}'.format(self.point_count, sensor.id))
        ok = True

        # assume all our parameters are setpoints...
        for setpoint in sensor.calibration.parameters.values():
            if not setpoint.run(sensor):
                ok = False
                break

        return ok

    def save(self, sensor):
        p1 = sensor.calibration.parameters['sp1']
        p2 = sensor.calibration.parameters['sp2']
        
        ok = sensor.calibration.equation.generate(p1, p2)            

        return ok

    def pack(self, prefix):
        package = super().pack(prefix)
        package += 'point_count = {}\n'.format(self.point_count)

        my_prefix = '{}.{}'.format(prefix, 'parameters')
        for name, parameter in self.parameters.items():
            parameter_prefix = '{}.{}'.format(my_prefix, name)
            package += '\n'
            package += parameter.pack(parameter_prefix)
        
        return package

    def unpack(self, package):
        super().unpack(package)
        self.point_count = package['point_count']

        # need a parameter factory and move to Procedure
        if 'parameters' in package:
            for name, section in package['parameters'].items():
                setpoint = sp.StreamSetpoint(quantity.Quantity())
                setpoint.unpack(section)
                self.parameters[setpoint.name] = setpoint
            
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

