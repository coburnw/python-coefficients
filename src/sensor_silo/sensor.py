#
# sensor.py - a container for a sensors metadata and calibration constants.
#             part of the python sensor silo project.
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

import collections

from . import shell
from . import calibration

# lets move to a source/sink nomenclature
class Stream():
    def __init__(self, type):
        self.type = type

        return

    def connect(self, address):
        ''' initialize an input'''
        raise NotImplemented
    
    def update(self):
        ''' complete a conversion'''
        raise NotImplemented
    
    @property
    def raw_value(self):
        ''' returns a float'''
        raise NotImplemented

    @property
    def raw_units(self):
        ''' returns a string'''
        raise NotImplemented
    
    
class Sensor():
    def __init__(self, sensor_id):
        self.id = sensor_id.strip().lower()
        
        # configured by procedure/deploy.prep()
        self.kind = None
        self.stream_type = None
        self.stream = None
        self.calibration = None # calibration.Calibration()
        
        # deployed sensor values
        self.name = ''
        self.location = ''
        self.address = 'ND'

        return

    # @property
    # def type(self):
    #     return self.__class__.__name__
    
    def connect(self, stream, address=None):
        self.stream = stream
        
        if address is None:
            address = self.address

        if address.lower() == 'nd':
            print(' Sensor.connect(): NO DEPLOYED ADDRESS')
        else:
            self.stream.connect(address)
        
        return

    @property
    def is_deployed(self):
        return self.address.lower() != 'nd'
    
    @property
    def raw_value(self):
        return self.stream.raw_value

    @property
    def raw_units(self):
        return self.stream.raw_units
    
    @property
    def scaled_value(self):
        return self.evaluate(self.raw_value)

    @property
    def scaled_units(self):
        return self.calibration.scaled_units

    @property
    def unit_id(self):
        return self.calibration.unit_id

    def evaluate(self, raw_value):
        return self.calibration.equation.evaluate_y(raw_value)

    def update(self):
        self.stream.update()

        return
    
    def pack(self, prefix):
        # sensor
        package = ''
        package += 'id = "{}"\n'.format(self.id)
        package += 'kind = "{}"\n'.format(self.kind)

        package += 'name = "{}"\n'.format(self.name)
        package += 'location = "{}"\n'.format(self.location)
        package += 'property = "{}"\n'.format(self.property)

        package += 'stream_type = "{}"\n'.format(self.stream_type)
        package += 'address = "{}"\n'.format(self.address)
        
        if self.calibration.is_valid:
            my_prefix = '{}.{}'.format(prefix, 'calibration')
            package += '\n'
            package += self.calibration.pack(my_prefix)

        return package

    def unpack(self, package):
        # sensor
        self.id = package['id']
        self.kind = package['kind']

        self.name = package.get('name', '')
        self.location = package.get('location', '')
        self.property = package.get('property', '')
        
        self.stream_type = package.get('stream_type')
        self.address = package.get('address', 'ND')

        if 'calibration' in package:
            self.calibration = calibration.Calibration(package['calibration'])
                
        return


class SensorShell(shell.Shell):
    intro = 'Sensor Configuration.  x to return to previous menu.'
    # prompt = 'sensor: '

    def __init__(self, sensor, procedure, *kwargs):
        super().__init__(*kwargs)

        self.sensor = sensor
        self.procedure = procedure
        
        return

    @property
    def kind(self):
        return self.sensor.kind
    
    @property
    def id(self):
        return self.sensor.id
    
    @property
    def prompt(self):
        item =  self.red(self.id)
        
        if self.sensor.calibration.is_valid:
            item = self.green(self.id)
            
        prompt = '{} ({}): '.format(self.cyan('edit sensor'), item)
            
        return prompt

    def preloop(self):
        self.do_show()

        return False
    
    def emptyline(self):
        self.do_show()
        
        return False
    
    def do_x(self, arg):
        ''' exit to previous menu'''
        return True
    
    def do_show(self, arg=None):
        ''' print sensors parameters'''
        print(' ID:   {}'.format(self.id))
        print('  Kind: {}'.format(self.sensor.kind))
        print('  Property: {}'.format(self.sensor.property))
        print('  Name: {}'.format(self.sensor.name))
        print('  Location: {}'.format(self.sensor.location))

        print('  Stream Type:  {}'.format(self.sensor.stream.type))
        print('  Deployed Address: {}'.format(self.sensor.address))
        print('  calibration due:  {}'.format(self.sensor.calibration.due_date))
        
        return False

    def do_address(self, arg=None):
        ''' address <addr> enter deployed pHorp address of sensor, or ND for Not Deployed'''

        err_str = self.sensor.stream.validate_address(arg)
        if err_str:
            print(self.red(err_str))
        else:
            self.sensor.address = arg.strip().upper() #self.sensor.stream.address
            
        self.do_show()
        
        return False

    def do_name(self, arg):
        ''' name <name> enter deployed name of sensor'''
        self.sensor.name = arg.strip()

        return False

    def do_location(self, arg):
        ''' location <location> enter deployed location of sensor'''
        self.sensor.location = arg.strip()

        return False
    
    def do_dump(self, arg):
        ''' dump sensor's coefficients and stats'''
        self.dump()
        
        return False

    def do_cal(self, arg):
        ''' acquire sensor calibration data'''
        self.procedure.run(self.sensor)
            
        return

    def do_meas(self, arg):
        ''' meas <mV> Evaluates mV in engineering units, sensor value if blank.'''
        if len(arg.strip()) == 0:
            self.meas(arg)
        else:
            self.eval(arg)
        
        return False

    def do_qual(self, arg):
        ''' evaluate sensor quality '''
        self.procedure.quality(self.sensor)
        
        return False
    
    def dump(self):
        print(self.sensor.pack(self.sensor.id))

        return

    def meas(self, arg):
        ''' sensor measurement in engineering units'''
        self.sensor.update()

        addr = self.sensor.stream.address
        raw = '{} {}'.format(round(self.sensor.raw_value, 3), self.sensor.raw_units)
        if self.sensor.calibration.is_valid:
            scaled = '{} {}'.format(round(self.sensor.scaled_value, 3), self.sensor.scaled_units)
            print('{}: {}, {}'.format(addr, raw, scaled))
        else:
            print('uncalibrated {}: {}'.format(addr, raw))
            
        return
    
    def eval(self, arg):
        ''' evaluate a simulated sensor measurement'''
        if not arg:
            print( 'enter a value in {}.'.format(self.sensor.raw_units))
            return

        try:
            raw_value = float(arg)
        except:
            raw_value = 0

        raw = '{} {}'.format(round(raw_value, 3), self.sensor.raw_units)
        if self.sensor.calibration.is_valid:
            scaled = '{} {}'.format(round(self.sensor.evaluate(raw_value), 3), self.sensor.scaled_units)
            print(' {}: {}'.format(raw, scaled))
        else:
            print(' uncalibrated: {}'.format(raw))

        return False        
    

class Sensors(collections.UserDict):
    def __init__(self, package=None):
        super().__init__()
        ### self.data contains our dict()

        if package is not None:
            self.unpack(package)
            
        return

    def pack(self, prefix):
        # Sensors
        package = ''

        for key, sensor in self.data.items():
            sensor_prefix = '{}.{}'.format(prefix, key)
            package += '\n'
            package += '[{}]\n'.format(sensor_prefix)
            package += sensor.pack(sensor_prefix)
            
        return package

    def unpack(self, package):
        for sensor_key, template in package.items():
            if sensor_key in self.keys():
                print(' Error: sensor already exists. ignoring.')
            else:
                sensor = Sensor(template['id'])
                sensor.unpack(template)
                self.data[sensor_key] = sensor
                
        return

    
class SensorsShell(shell.Shell):
    intro = 'Sensor Database, x to return to previous menu...'

    def __init__(self, procedures, *kwargs):
        super().__init__(*kwargs)
        
        self.procedures = procedures
        
        self.sensors = Sensors()
        self.sensor_index = 0

        return

    @property
    def first_index(self):
        return 0
    
    @property
    def last_index(self):
        return len(self.sensors) - 1
    
    @property
    def sensor(self):
        if self.sensor_index > self.last_index:
            self.sensor_index = self.last_index

        # create a list of sensor keys then select key by index
        key = list(self.sensors)[self.sensor_index]
        
        return self.sensors[key]

    @property
    def procedure(self):
        procedure = self.procedures[self.sensor.kind]

        return procedure

    @property
    def kinds(self):
        # return a list of known sensor kinds
        return list(self.procedures.keys())
    
    @property
    def prompt(self):
        if len(self.sensors) == 0:
            sensor_id = 'empty'
        else:
            sensor_id = self.red(self.sensor.id)
            if self.sensor.calibration.is_valid:
                sensor_id = self.green(self.sensor.id)

        return '{}[{}]: '.format(self.cyan('db'), sensor_id)

    def to_key(self, id):
        id = id.strip().lower().replace(' ', '_')
        
        return id

    def emptyline(self):
        self.do_list(None)
        
        return False
    
    def do_x(self, arg):
        ''' exit to previous menu'''
        return True

    def do_new(self, sensor_id=''):
        ''' new <id>. Create a new sensor instance'''
        sensor_id = sensor_id.strip()
        
        if len(sensor_id) == 0:
            print(' missing sensor id.')
            return

        sensor_key = self.to_key(sensor_id)
        if sensor_key in self.sensors.keys():
            print(' sensor already exists.')
            return
               
        sensor_kind = input(' Enter sensor kind {}: '.format(self.kinds)).strip()
        if len(sensor_kind) == 0:
            print(' missing sensor kind.  known kinds are {}.'.format(self.kinds))
            return
        
        if sensor_kind.lower() not in self.kinds:
            print(' known kinds are {}. sensor not created.'.format(self.kinds))
            return

        sensor = self.new_sensor(sensor_kind, sensor_key)

        self.do_edit('')
        
        return

    def new_sensor(self, sensor_kind, sensor_id):
        print(' creating new {} sensor {}'.format(sensor_kind, sensor_id))

        sensor = Sensor(sensor_id)
        
        self.sensors[sensor_id] = sensor
        self.sensor_index = self.last_index

        self.procedures[sensor_kind].prep(sensor)

        return sensor
        
    def do_edit(self, arg):
        ''' edit selected sensor'''
        SensorShell(self.sensor, self.procedure).cmdloop()

        return
    
    def do_del(self, arg=None):
        ''' delete sensor. del<ret> selected sensor, del <sensor_id> '''
        if arg:
            sensor_key = self.to_key(arg)
        else:
            sensor_key = self.to_key(self.sensor.id)

        if sensor_key not in self.sensors.keys():
            print( ' sensor not found.')
            return
        
        yn = input(' delete sensor {} (y/n)? '.format(self.sensors[sensor_key].id))
        if yn == 'y':
            del self.sensors[sensor_key]
            print( ' sensor deleted.')
        else:
            print( ' delete canceled.')

        return
            
    def do_list(self, arg):
        ''' list available sensors '''

        if len(self.sensors) == 0:
            print(' No sensors in list.  "new" to add a sensor.')
            return
        
        print('   ID\tKind\tAddr\t  Expires\tName\tLocation')
        i = 0
        
        for sensor in self.sensors.values():
            carret = ' '
            if i == self.sensor_index:
                carret = '*'

            i += 1               

            id = self.red(sensor.id)
            if sensor.calibration.is_valid:
                id = self.green(sensor.id)

            kind = sensor.kind
            name = sensor.name
            addr = sensor.address
            location = sensor.location
            due_date = sensor.calibration.due_date
            
            print(' {} {}\t{}\t{}\t{}\t{}\t{}'.format(carret, id, kind, addr, due_date, name, location ))
        
        return

    def do_prev(self, arg):
        ''' move to previous sensor in list'''
        self.sensor_index -= 1
        if self.sensor_index < self.first_index:
            self.sensor_index = self.first_index

        return
    
    def do_next(self, arg):
        ''' move to next sensor in list'''
        self.sensor_index += 1
        if self.sensor_index > self.last_index:
            self.sensor_index = self.last_index

        return
    
    def pack(self, prefix):
        package = self.sensors.pack(prefix)
        
        return package
    
    def unpack(self, package):
        self.sensors.unpack(package)

        for sensor in self.sensors.values():
            # deploy.prep(sensor)
            proc = self.procedures[sensor.kind]
            proc.prep(sensor)

        return
