#
# setpoint.py - base class for a calibration setpoint.
#               part of the python sensor silo project.
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

import sys
import time

from . import shell
from . import statistics as rs
from . import quantity

class SetpointFactory():
    def __init__(self, package):
        return
        
class Setpoint(shell.Shell):
    def __init__(self, target_quantity=None, measured_quantity=None):
        self.title = 'Calibration Setpoint'

        # make this required 
        if target_quantity is None:
            target_quantity = quantity.Quantity()
            
        if measured_quantity is None:
            measured_quantity = quantity.Quantity()
            
        self.target_quantity = target_quantity
        self.measured_quantity = measured_quantity
        
        return

    @property
    def type(self):
        return self.__class__.__name__
    
    @property
    def name(self):
        return self.target_quantity.name.lower()
    
    def pack(self, prefix):
        # Calibration SetPoint

        package = ''
        package += '[{}]\n'.format(prefix)        
        package += 'type = "{}"\n'.format(self.type)
        
        my_prefix= '{}.{}'.format(prefix, 'target_quantity')
        package += '{}'.format(self.target_quantity.pack(my_prefix))

        return package

    def unpack(self, package):
        # calibration setpoint
        self.target_quantity.unpack(package['target_quantity'])
        
        return

class ConstantSetpoint(Setpoint):
    def __init__(self, target_quantity=None, measured_quantity=None):
        super().__init__(target_quantity, measured_quantity)

        return

    @property
    def mean(self):
        return self.measured_quantity.value

    def clone(self):
        scaled = self.target_quantity.clone()
        
        raw = None
        if self.measured_quantity:
            raw = self.measured_quantity.clone()
            
        return(ConstantSetpoint(scaled, raw))

    def run(self, sensor):
        # Its a constant. Nothing to do...
        
        return True
    
# class PromptSetpoint(Setpoint):
#     def __init__(self, scaled_parameter):
#         self.scaled_parameter = scaled_parameter

#         return

class StreamSetpoint(Setpoint):
    def __init__(self, target_quantity=None, measured_quantity=None):
        super().__init__(target_quantity, measured_quantity)
        
        self.title = 'Calibration Setpoint'
        
        self.sample_period = 0.1
        self.update_period = 1
        self.number_of_samples = 50
        
        self.stats = rs.RunningStats()
        
        return

    @property
    def n(self):
        return self.stats.n

    @property
    def mean(self):
        return round(self.stats.mean(), 3)

    @property
    def variance(self):
        return round(self.stats.variance(), 3)

    @property
    def standard_deviation(self):
        return round(self.stats.standard_deviation(), 3)

    def clone(self):
        scaled = self.target_quantity.clone()
        
        raw = None
        if self.measured_quantity:
            raw = self.measured_quantity.clone()
            
        return(StreamSetpoint(scaled, raw))

    def dump(self):
        str = '{}: n={}, mean={}, var={}, sd={}'.format(self.target_quantity, self.n, self.mean, self.variance, self.standard_deviation)

        return str

    # evaluate?
    def run(self, sensor):
        # setpoint run
        self.measured_quantity = sensor.stream.measured_quantity.clone()
        
        prompt = '  ready {} Calibration Solution. press <space> to begin, <x> to cancel'.format(self.target_quantity)
        print(prompt)
        key = self.get_char()
        
        if key != ' ':
            print('run canceled')
            return False

        while True:
            print('   ({}): '.format(self.target_quantity), end='')
            self.stats.clear()
            
            sample_time = time.time()
            update_time = sample_time
            for i in range(self.number_of_samples):
                sensor.update()
                self.stats.push(sensor.stream.measured_quantity.value * 1000) #fix sensor
            
                now = time.time()
                if now > update_time:
                    print(round(sensor.raw_value, 3), end=', ')
                    sys.stdout.flush()
                    update_time += self.update_period

                sample_time += self.sample_period
                pause_time = sample_time - now
                if pause_time < 0:
                    pause_time = 0
                    sample_time = now
                
                time.sleep(pause_time)

            print()
            print('     {}'.format(self.stats.synopsis))

            prompt = '  {} Calibration Buffer. <space> to repeat, <enter> to advance'.format(self.target_quantity)
            print(prompt) #, end=''
            # sys.stdout.flush()
            key = self.get_char()
        
            if key != ' ':
                self.measured_quantity.value = self.stats.mean()
                break
            
        return True

    
