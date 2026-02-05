import shell
import coefficients
import phorp
import setpoint as sp

import frame_streams as fs

class Sensor():
    def __init__(self, i2c_bus, sensor_type, sensor_id):
        self.bus = i2c_bus
        self.type = sensor_type
        self.id = sensor_id.strip()

        self.stream = None
        
        # deployed sensor values
        self.name = ''
        self.location = ''
        self.address = 'a1'

        self.coefficients = coefficients.Coefficients()

        return

    def connect(self, address=None):
        if address is None:
            address = self.address

        board_index, channel_index = self.split_address(address)
        
        a = phorp.PhorpX4(self.bus, board_index)
        self.stream = fs.PhStream(a[int(channel_index)], 'ph_cal', filter_constant=1)

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
        return self.stream.raw_value

    @property
    def scaled_value(self):
        return self.stream.value

    @property
    def value(self):
        return self.evaluate(self.raw_value)

    def evaluate(self, raw_value):
        return self.coefficients.evaluate_y(raw_value)

    def update(self):
        self.stream.update()

        return
    
class SensorShell(shell.Shell):
    intro = 'Sensor Configuration.  Blank line to return to previous menu.'
    # prompt = 'sensor: '

    def __init__(self, i2c_bus, sensor_type, sensor_id, *kwargs):
        super().__init__(*kwargs)
        self.bus = i2c_bus
        self.sensor = Sensor(i2c_bus, sensor_type, sensor_id)
        
        self.setpoints = None  # a dict() configured by Procedure.prep()
        
        return

    @property
    def type(self):
        return self.sensor.type
    
    @property
    def id(self):
        return self.sensor.id
    
    @property
    def config(self):
        return self.sensor
    
    @property
    def prompt(self):
        if self.sensor.coefficients.is_valid:
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
        print('  Address:  {}'.format(self.sensor.address))
        print('  calibration due: {}'.format(self.sensor.coefficients.due_date))
        
        return False

    def do_address(self, arg=None):
        ''' address <addr> enter deployed pHorp address of sensor'''

        board, channel = self.sensor.split_address(arg)
        
        if board in 'abcdefg' and channel in '1234':
            self.sensor.address = board + channel
        else:
            print(' invalid address. board_id is a-g, channel_id is 1-4 as in "b3"')

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

    def qual(self, arg):
        ''' evaluate the quality of the sensor from its calibration constants '''
        if not self.is_calibrated:
            print(' Sensor must be calibrated to evaluate its quality.')
            return
        
        self.quality()
        
        return False
    
    def dump(self):
        for setpoint in self.setpoints.values():
            print(setpoint.dump())
            
        self.sensor.coefficients.dump()

        return

    def meas(self, arg):
        ''' sensor measurement in engineering units'''
        self.sensor.update()
        
        if self.is_calibrated:
            print(' {} {}: {} {}'.format(self.sensor.raw_value, 'mV', self.sensor.value, self.sensor.units))
        else:
            print(' uncalibrated: {} {}'.format(self.sensor.raw_value, 'mV'))
            
        return
    
    def eval(self, arg):
        ''' evaluate a simulated sensor measurement'''
        if not arg:
            print( 'enter a value in volts.')
            return

        try:
            raw_value = float(arg)
        except:
            raw_value = 0

        if self.is_calibrated:
            print(' {} {}: {} {}'.format(raw_value, 'mV', self.sensor.evaluate(raw_value), self.sensor.units))
        else:
            print(' uncalibrated: {} {}'.format(raw_value, 'mV'))

        return False
        
    @property
    def type(self):
        return self.sensor.type
    
    @property
    def is_calibrated(self):
        return self.sensor.coefficients.is_valid
    
    def pack(self, prefix):
        # sensor
        package = ''
        package += 'id = "{}"\n'.format(self.id)
        package += 'type = "{}"\n'.format(self.sensor.type)
        package += 'address = "{}"\n'.format(self.sensor.address)
        package += '\n'
        
        if self.is_calibrated:
            my_prefix = '{}.{}'.format(prefix, 'coefficients')
            package += self.sensor.coefficients.pack(my_prefix)

            my_prefix = '{}.{}'.format(prefix, 'setpoints')
            for setpoint in self.setpoints.values():
                setpoint_prefix = '{}.{}'.format(my_prefix, setpoint.name)
                package += '{}\n'.format(setpoint.pack(setpoint_prefix))

        return package

    def unpack(self, package):
        # sensor
        self.id = package['id']
        self.sensor.type = package['type']
        self.sensor.address = package['address']

        if 'coefficients' in package:
            self.sensor.coefficients = coefficients.Coefficients()
            self.sensor.coefficients.unpack(package['coefficients'])
            
        if 'setpoints' in package:
            for values in package['setpoints'].values():
                print('  loading setpoint {}'.format(values['name']))
                setpoint = sp.Setpoint('','','')
                setpoint.unpack(values)
                self.setpoints[setpoint.name] = setpoint
            
        return

    
class Sensors(shell.Shell):
    intro = 'Sensor Database, blank line to return to previous menu...'

    def __init__(self, i2c_bus, procedures, *kwargs):
        super().__init__(*kwargs)
        
        self.bus = i2c_bus
        self.procedures = procedures
        
        self.sensors = dict()
        self.sensor_index = 0

        # known sensor types
        # self.types = ['eh', 'ph'] # 'therm'

        return

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
            if self.sensor.is_calibrated:
                sensor_id = self.green(self.sensor.id)

        return '{}[{}]: '.format(self.cyan('db'), sensor_id)

    @property
    def first_index(self):
        return 0
    
    @property
    def last_index(self):
        return len(self.sensors) - 1
    
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
        
        sensor.do_show()
        
        return

    def new_sensor(self, sensor_type, sensor_id):
        print(' creating new {} sensor {}'.format(sensor_type, sensor_id))

        sensor = SensorShell(self.bus, sensor_type, sensor_id)
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
        self.sensor.cmdloop()

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
            if sensor.is_calibrated:
                id = self.green(sensor.id)

            type = sensor.type
            address = sensor.config.address
            due_date = sensor.config.coefficients.due_date
            
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
            self.sensor.meas(arg)
        else:
            self.sensor.eval(arg)
        
        return False

    def do_quality(self, arg):
        ''' evaluate sensor quality '''
        self.procedure.quality(self.sensor)
        
        return False
    
    def pack(self, prefix):
        # Sensors
        package = '[{}]\n'.format(prefix)

        for key, sensor in self.sensors.items():
            sensor_prefix = '{}.{}'.format(prefix, key)
            package += '[{}]\n'.format(sensor_prefix)
            package += '{}\n'.format(sensor.pack(sensor_prefix))
            
        return package

    def unpack(self, package):
        #print(package)
        for sensor_key, template in package.items():
            if sensor_key in self.sensors.keys():
                print(' sensor already exists. ignoring.')
            else:
                sensor = self.new_sensor(template['type'], template['id'])
                sensor.unpack(template)
                self.sensors[sensor_key] = sensor
                #print(sensor)
            
        return

