#
# cal.py -  an app using the sensor_silo library that serves as both example and test.
#           part of the python sensor silo project.
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

import smbus3 as smbus
import phorp

import sensor_silo as silo
import gs_feedput as gs

class PhorpSource(silo.Stream):
    i2c_bus = None
    
    def __init__(self):
        super().__init__(self.__class__.__name__)
        
        self.bus = self.get_i2c_bus()
        self.channel = None
        self.address = None

        self._raw_value = 0
        self.measured_quantity = silo.Quantity('Measured', 'V')
        
        return

    @classmethod
    def get_i2c_bus(cls):
        return cls.i2c_bus
    
    def connect(self, address):
        self.address = address
        
        board = phorp.PhorpX4(self.bus, self.board_index)
        self.channel = board[self.channel_index]
        
        self.channel.sample_rate = 60
        self.channel.pga_gain = 1
        self.channel.continuous = False

        return

    def update(self):
        self.channel.start_conversion()
        time.sleep(self.channel.conversion_time)
        self._raw_value = self.channel.get_conversion_volts()
        
        self.measured_quantity.value = self._raw_value

        return

    def validate_address(self, address):
        board, chan_idx = self.split_address(address)
        
        if board in 'abcdefg' and chan_idx in '1234':
            #self.address = board + chan_idx
            pass
        elif address.strip().lower() == 'nd':
            #self.address = address.strip().upper()
            pass
        else:
            return 'invalid address. board_id is a-g, channel_id is 1-4 as in "b3"'

        return
        
    def split_address(self, address):
        board_index = address[0].lower()
        channel_index = address[1]

        return (board_index, channel_index)

    @property
    def board_index(self):
        board, channel = self.split_address(self.address)

        return board

    @property
    def channel_index(self):
        board, channel = self.split_address(self.address)

        return int(channel)

    @property
    def raw_value(self):
        ''' returns the result of the last update() as a float'''
        return self._raw_value * 1000
    
    @property
    def raw_units(self):
        ''' returns a string'''
        return 'mV'
    
    
class ThermistorProcedure(silo.PhorpNtcBetaProcedure):
    intro = 'Beta Thermistor Configuration'
    
    def __init__(self, streams, *kwargs):
        super().__init__(streams, *kwargs)

        self.stream_type = 'PhorpSource'
        self.stream_address = 'a1'
        
        self.kind = 'ntc'

        self.property = 'Temperature'
        self.scaled_units = 'Celsius'
        self.unit_id = 'celsius'
        
        # the default setpoint settings.
        self.parameters['beta'] = silo.Quantity('Beta', 'K', 3574.6)
        self.parameters['r25'] = silo.Quantity('R25', 'Ohms', 10000)

        return

    def quality(self, sensor):
        print(' Not implemented ')

        return

    
class DoProcedure(silo.PolynomialProcedure):
    intro = 'Dissolved Oxygen Procedure Configuration'
    
    def __init__(self, streams, *kwargs):
        super().__init__(streams, *kwargs)
        
        self.stream_type = 'PhorpSource'
        self.stream_address = 'a2'
        
        self.kind = 'do'
        
        self.property = 'Dissolved Oxygen'
        self.scaled_units = 'mg/L'
        self.unit_id = 'mg_l'

        # the default setpoint settings.
        sp1 = silo.Quantity('SP1', self.scaled_units, 0.0)
        sp2 = silo.Quantity('SP2', self.scaled_units, 9.09)

        self.parameters['sp1'] = silo.ConstantSetpoint(sp1, sp1.clone())
        self.parameters['sp2'] = silo.StreamSetpoint(sp2)

        return

    def quality(self, sensor):
        print(' Not implemented ')

        return

    
class OrpProcedure(silo.PolynomialProcedure):
    intro = 'ORP Procedure Configuration'
    
    def __init__(self, streams, *kwargs):
        super().__init__(streams, *kwargs)
        
        self.stream_type = 'PhorpSource'
        self.stream_address = 'a2'
        
        self.kind = 'orp'

        self.property = 'Eh'
        self.scaled_units = 'mV'
        self.unit_id = 'milli_volts'

        # the default setpoint settings.
        sp1 = silo.Quantity('SP1', self.scaled_units, 0.0)
        sp2 = silo.Quantity('SP2', self.scaled_units, 225)

        self.parameters['sp1'] = silo.StreamSetpoint(sp1)
        self.parameters['sp2'] = silo.StreamSetpoint(sp2)

        return

    def quality(self, sensor):
        print(' Not implemented ')

        return

    
class PhProcedure(silo.PolynomialProcedure):
    intro = 'pH Procedure Configuration'

    def __init__(self, streams, *kwargs):
        super().__init__(streams, *kwargs)

        self.stream_type = 'PhorpSource'
        self.stream_address = 'a2'
        
        self.kind = 'ph'

        self.property = 'pH'
        self.scaled_units = 'pH'
        self.unit_id = 'ph'

        # the default setpoint settings.
        sp1 = silo.Quantity('SP1', self.scaled_units, 4.0)
        sp2 = silo.Quantity('SP2', self.scaled_units, 7.0)
        sp3 = silo.Quantity('SP3', self.scaled_units, 10.0)
        
        self.parameters['sp1'] = silo.StreamSetpoint(sp1)
        self.parameters['sp2'] = silo.StreamSetpoint(sp2)
        self.parameters['sp3'] = silo.StreamSetpoint(sp3)

        return

    def quality(self, sensor):
        if not  sensor.calibration.is_valid:
            print(' Sensor out of calibration: ')
            return

        if sensor.calibration.equation.degree == 1:
            slope = sensor.calibration.equation.coefficients[1]
            offset = sensor.calibration.equation.evaluate_x(7.0)

            print(' slope = {} {}/unit '.format(round(slope,3), 'mV'))
            print(' offset = {} {}'.format(round(offset,3), 'mV'))
        else:
            print(' calibration equation is in an unsupported degree for quality evaluation')

        return


class RollingAverage():
    def __init__(self, filter_constant, initial_value=0):
        if filter_constant < 1.0:
            filter_constant = 1.0
            
        self.n = filter_constant
        self.value= initial_value

        return

    def update(self, new_sample):
        result = self.value
        
        result -= self.value / self.n
        result += new_sample / self.n

        self.value = result
        
        return result

    
class GroveStream(gs.RandomStream):
    def __init__(self, sensor, filter_constant):
        super().__init__(sensor.id, 'FLOAT')

        self.sensor = sensor
        
        name = '{}.{}'.format(sensor.location, sensor.name)
        self.set_name(name)
        self.set_description('fix me')
        self.set_units(sensor.unit_id)

        self.filter = RollingAverage(filter_constant)
        
        return

    def update(self):
        self.sensor.update()
        value = self.filter.update(self.sensor.scaled_value)
        
        self.values.clear()
        self.values.append(round(value, 3))
        
        return

    
if __name__ == '__main__':

    config = False
    if len(sys.argv) > 1:
        config = True

    with smbus.SMBus(1) as bus:
        sources = dict()
        PhorpSource.i2c_bus = bus
        print(PhorpSource.__name__)
        sources[PhorpSource.__name__] = PhorpSource
    
        if config == True:
            procedures = dict()
            procedures['do'] = DoProcedure(sources)
            procedures['ph'] = PhProcedure(sources)
            procedures['orp'] = OrpProcedure(sources)
            procedures['ntc'] = ThermistorProcedure(sources)

            shell = silo.Shell(procedures)
            # shell.procedures.append(proc)
            shell.cmdloop()

        else:
            
            # load toml file, initialize sensors, and run
            project = silo.Deploy('deployment.toml')
            print('Streaming to Components/{}/{}'.format(project.folder_name, project.group_name))
            project.connect(sources)
            print('{}s {}s'.format(project.stream_period, project.sample_period))

            feed = gs.Feed(project.key_name, compress=True)
            comps = gs.Components(project.key_name)
            
            components = gs.Components(project.folder_name)
            component = gs.Component(project.group_name)
            for sensor in project.sensors.values():
                if sensor.is_deployed:
                    component.streams.append(GroveStream(sensor, project.time_constant))

            components.append(component)

            last_update = time.time()
            while True:
                timestamp = time.time()
                print('{}: '.format(timestamp), end='')
                # for stream in component.streams:
                #     stream.update()
                #     #val = round(sensor.scaled_value, 1)
                #     #parm = '{} {} {}, '.format(sensor.name, val, sensor.scaled_units)
                #     #print(parm, end='')
                #     time.sleep(0.1)

                components.update()
                
                if last_update + project.stream_period > timestamp:
                    feed.put(components)
                    last_update = timestamp
                
                print('')
                time.sleep(project.sample_period)

    exit()
