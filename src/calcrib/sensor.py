import collections

from . import shell
from . import coefficients
from . import setpoint as sp

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
    
    # @property
    # def address(self):
    #     ''' returns the current address '''
    #     raise NotImplemented
    
    @property
    def raw_value(self):
        ''' returns a float'''
        raise NotImplemented

    @property
    def raw_units(self):
        ''' returns a string'''
        raise NotImplemented
    
    
class Sensor():
    def __init__(self, sensor_type, sensor_id):
        self.type = sensor_type
        self.id = sensor_id.strip()

        self.stream = None  # configured by procedure
        
        # deployed sensor values
        self.name = ''
        self.location = ''
        self.address = 'ND'

        self.calibration = coefficients.Coefficients()
        self.setpoints = dict()

        return

    def connect(self, stream, address=None):
        self.stream = stream
        
        if address is None:
            address = self.address

        if address == 'ND':
            print(' Sensor.connect(): NO DEPLOYED ADDRESS')
        else:
            self.stream.connect(address)
        
        return
    
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

    def evaluate(self, raw_value):
        return self.calibration.evaluate_y(raw_value)

    def update(self):
        self.stream.update()

        return
    
    def pack(self, prefix):
        # sensor
        package = ''
        package += 'id = "{}"\n'.format(self.id)
        package += 'type = "{}"\n'.format(self.type)

        package += 'name = "{}"\n'.format(self.name)
        package += 'location = "{}"\n'.format(self.location)
        package += 'address = "{}"\n'.format(self.address)
        
        if self.calibration.is_valid:
            my_prefix = '{}.{}'.format(prefix, 'calibration')
            package += '\n'
            package += self.calibration.pack(my_prefix)

            my_prefix = '{}.{}'.format(prefix, 'setpoints')
            for setpoint in self.setpoints.values():
                setpoint_prefix = '{}.{}'.format(my_prefix, setpoint.name)
                package += '\n'
                package += setpoint.pack(setpoint_prefix)

        return package

    def unpack(self, package):
        # sensor
        self.id = package['id']
        self.type = package['type']
        
        self.name = package.get('name', '')
        self.location = package.get('location', '')
        self.address = package.get('address', 'ND')

        if 'calibration' in package:
            self.calibration = coefficients.Coefficients()
            self.calibration.unpack(package['calibration'])
            
        if 'setpoints' in package:
            for values in package['setpoints'].values():
                setpoint = sp.Setpoint('','','')
                setpoint.unpack(values)
                self.setpoints[setpoint.name] = setpoint
            
        return


class SensorShell(shell.Shell):
    intro = 'Sensor Configuration.  Blank line to return to previous menu.'
    # prompt = 'sensor: '

    def __init__(self, sensor, *kwargs):
        super().__init__(*kwargs)

        self.sensor = sensor
        
        #self.setpoints = None  # a dict() configured by Procedure.prep()
        
        return

    @property
    def type(self):
        return self.sensor.type
    
    @property
    def id(self):
        return self.sensor.id
    
    @property
    def prompt(self):
        if self.sensor.calibration.is_valid:
            prompt = '{} {}: '.format(self.cyan('edit'), self.green(self.id))
        else:
            prompt = '{} {}: '.format(self.cyan('edit'), self.red(self.id))
            
        return prompt

    def preloop(self):
        self.do_show()

        return False
    
    def emptyline(self):
        return True
    
    def do_show(self, arg=None):
        ''' print sensors parameters'''
        print(' ID:   {}'.format(self.id))
        print('  Type: {}'.format(self.sensor.type))
        print('  Name: {}'.format(self.sensor.name))
        print('  Location: {}'.format(self.sensor.location))

        print('  Stream Type:  {}'.format(self.sensor.stream.type))
        print('  Deployed Address: {}'.format(self.sensor.address)) # deployed address
        print('  calibration due:  {}'.format(self.sensor.calibration.due_date))
        
        return False

    def do_address(self, arg=None):
        ''' address <addr> enter deployed pHorp address of sensor'''

        err_str = self.sensor.stream.validate_address(arg)
        if err_str:
            print(self.red(err_str))
        else:
            self.sensor.address = self.sensor.stream.address
            
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

    def dump(self):
        for setpoint in self.sensor.setpoints.values():
            print(setpoint.dump())
            
        self.sensor.calibration.dump()

        return

    def meas(self, arg):
        ''' sensor measurement in engineering units'''
        self.sensor.update()
        
        if self.sensor.calibration.is_valid:
            print(' {} {}: {} {}'.format(round(self.sensor.raw_value, 3), self.sensor.raw_units, round(self.sensor.scaled_value, 3), self.sensor.scaled_units))
        else:
            print(' uncalibrated: {} {}'.format(round(self.sensor.raw_value, 3), self.sensor.raw_units))
            
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

        if self.sensor.calibration.is_valid:
            print(' {} {}: {} {}'.format(round(raw_value,3), self.sensor.raw_units, round(self.sensor.evaluate(raw_value), 3), self.sensor.scaled_units))
        else:
            print(' uncalibrated: {} {}'.format(round(raw_value,3), self.sensor.raw_units))

        return False        
    

class Sensors(collections.UserDict):
    def __init__(self, package=None):
        super().__init__()
        # self.data contains our dict()

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
                sensor = Sensor(template['type'], template['id'])
                sensor.unpack(template)
                self.data[sensor_key] = sensor
                
        return

    
class SensorsShell(shell.Shell):
    intro = 'Sensor Database, blank line to return to previous menu...'

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
        procedure = self.procedures[self.sensor.type]

        return procedure

    @property
    def types(self):
        # return a list of known sensor types
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
               
        sensor_type = input(' Enter sensor type [{}] :'.format(self.types)).strip()
        if len(sensor_type) == 0:
            print(' missing sensor type.  known types are {}.'.format(self.types))
            return
        
        if sensor_type.lower() not in self.types:
            print(' known types are {}. sensor not created.'.format(self.types))
            return

        sensor = self.new_sensor(sensor_type, sensor_key)
        sensor_shell = SensorShell(sensor)
        
        sensor_shell.do_show()
        
        return

    def new_sensor(self, sensor_type, sensor_id):
        print(' creating new {} sensor {}'.format(sensor_type, sensor_id))

        sensor = Sensor(sensor_type, sensor_id)
        
        self.sensors[sensor_id] = sensor
        self.sensor_index = self.last_index

        self.procedure.prep(sensor)

        return sensor
        
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
            
    def do_edit(self, arg):
        ''' edit selected sensor'''
        SensorShell(self.sensor).cmdloop()

        return
    
    def do_list(self, arg):
        ''' list available sensors '''

        if len(self.sensors) == 0:
            print(' No sensors in list.  "new" to add a sensor.')
            return
        
        i = 0
        for sensor in self.sensors.values():
            carret = ' '
            if i == self.sensor_index:
                carret = '*'

            id = self.red(sensor.id)
            if sensor.calibration.is_valid:
                id = self.green(sensor.id)

            type = sensor.type
            address = sensor.address
            due_date = sensor.calibration.due_date
            
            i += 1               
            print(' {} {} {} {} {}'.format(carret, id, type, address, due_date))
        
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
    
    def do_cal(self, arg):
        ''' acquire sensor calibration data'''
        self.procedure.run(self.sensor)
            
        return

    def do_meas(self, arg):
        ''' meas <mV> Evaluates mV in engineering units, sensor value if blank.'''
        if len(arg.strip()) == 0:
            SensorShell(self.sensor).meas(arg)
        else:
            SensorShell(self.sensor).eval(arg)
        
        return False

    def do_quality(self, arg):
        ''' evaluate sensor quality '''
        self.procedure.quality(self.sensor)
        
        return False
    
    def pack(self, prefix):
        package = self.sensors.pack(prefix)
        
        return package
    
    def unpack(self, package):
        self.sensors.unpack(package)

        for sensor in self.sensors.values():
            # deploy.prep(sensor)
            proc = self.procedures[sensor.type]
            proc.prep(sensor)

        return
