import cmd
import sys
import time
# from datetime import date, datetime, timedelta
import datetime

import smbus3 as smbus
import tomli

import phorp
import frame_streams as fs
import statistics as rs

def getChar():
    # https://stackoverflow.com/a/36974338
    try:
        # for Windows-based systems
        import msvcrt # If successful, we are on Windows
        return msvcrt.getch()

    except ImportError:
        # for POSIX-based systems (with termios & tty support)
        import tty, sys, termios  # raises ImportError if unsupported

        fd = sys.stdin.fileno()
        oldSettings = termios.tcgetattr(fd)

        try:
            tty.setcbreak(fd)
            answer = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)

        return answer

class Ansi():
    # https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html
    
    def __init__(self):

        self.Black = '\u001b[30m'
        self.Red = '\u001b[31m'
        self.Green = '\u001b[32m'
        self.Yellow = '\u001b[33m'
        self.Blue = '\u001b[34m'
        self.Magenta= '\u001b[35m'
        self.Cyan = '\u001b[36m'
        self.White = '\u001b[37m'
        
        self.Reset = '\u001b[0m'

        return

    def red(self, text):
        return '{}{}{}'.format(self.Red, text, self.Reset)
    
    def green(self, text):
        return '{}{}{}'.format(self.Green, text, self.Reset)

    def blue(self, text):
        return '{}{}{}'.format(self.Blue, text, self.Reset)

    
class Coefficients():
    def __init__(self):

        self.degree = 1
        self.coefficients = dict()

        # self.expires = date.today() - timedelta(days=1)
        self.timestamp = datetime.date(1970, 1, 1)
        self.interval = datetime.timedelta(days=0)

        return

    def __len__(self):
        return len(self.coefficients)

    @property
    def due_date(self):
        return self.timestamp + self.interval

    @property
    def is_valid(self):
        return self.due_date > datetime.date.today()
    
    def generate(self, x1,y1, x2,y2):
        self.timestamp = datetime.date(1970, 1, 1)

        is_valid = False
        try:
            self.coefficients['slope'] = (y2 - y1) / (x2 - x1)
            self.coefficients['offset'] = y1 - self.coefficients['slope'] * x1
            
            is_valid = True
        except ZeroDivisionError:
            self.coefficients['slope'] = 0.00001
            self.coefficients['offset'] = 0.0
            
        return is_valid

    def evaluate_x(self, x_value):
        y = self.coefficients['slope'] * x_value + self.coefficients['offset']
        
        return y

    def evaluate_y(self, y_value):
        slope = self.coefficients['slope']
        if slope == 0:
            slope = 0.00001
            
        x = (y_value - self.coefficients['offset']) / slope
        
        return x
    
    def dump(self):
        for key, value in self.coefficients.items():
            print(key, value)

        return
    
    def pack(self, prefix):
        package = '[{}]\n'.format(prefix)
        package += 'degree = {}\n'.format(self.degree)
        package += 'timestamp = "{}"\n'.format(self.timestamp.isoformat())
        package += 'interval = "{}"\n'.format(self.interval.days)
        
        package += '[{}.{}]\n'.format(prefix, 'coefficients')
        for key, value in self.coefficients.items():
            package += '{} = {}\n'.format(key, value)

        return package

    def unpack(self, package):
        print('  loading coefficients')
        self.degree = package['degree']
        self.timestamp = datetime.date.fromisoformat(package['timestamp'])
        self.interval = datetime.timedelta(days=int(package['interval']))
        
        for name, value in  package['coefficients'].items():
            self.coefficients[name] = value
        
        return
    
class SensorShell(cmd.Cmd):
    intro = 'Sensor Configuration.  Blank line to return to previous menu.'
    # prompt = 'sensor: '

    def __init__(self, i2c_bus, sensor_id, *kwargs):
        super().__init__(*kwargs)
        self.bus = i2c_bus

        self.sensor_type = 'none'
        self.id = sensor_id.strip()
        
        self.phorp_address = 0x68 # deployed
        self.phorp_channel = 2

        a = phorp.PhorpX4(self.bus, 'a')
        self.stream = fs.PhStream(a[self.phorp_channel], 'ph_cal', filter_constant=1)

        self.coefficients = Coefficients()

        self.ansi = Ansi()

        return

    @property
    def prompt(self):
        if self.coefficients.is_valid:
            prompt = 'sensor {}: '.format(self.ansi.green(self.id))
        else:
            prompt = 'sensor {}: '.format(self.ansi.red(self.id))
            
        return prompt

    def preloop(self):
        self.do_show()

        return False
    
    def emptyline(self):
        return True
    
    def do_show(self, arg=None):
        ''' print sensors parameters'''
        print(' ID:   {}'.format(self.id))
        print('  Type: {}'.format(self.sensor_type))
        print('  pHorp address: 0x{:0x}'.format(self.phorp_address))
        print('  pHorp channel: {}'.format(self.phorp_channel))
        print('  calibration due: {}'.format(self.coefficients.due_date))
        
        return False
    
    def do_eval(self, arg):
        ''' evaluate a simulated sensor measurement'''
        if not arg:
            print( 'enter a value in volts.')
            return

        try:
            raw_value = float(arg)
        except:
            raw_value = 0

        if self.is_calibrated:
            print(' {} {}: {} {}'.format(raw_value, 'mV', self.evaluate(raw_value), self.units))
        else:
            print(' uncalibrated: {} {}'.format(raw_value, 'mV'))

        return
        
    def do_meas(self, arg):
        ''' sensor measurement in engineering units'''
        self.update()
        
        if self.is_calibrated:
            print(' {} {}: {} {}'.format(self.raw_value, 'mV', self.value, self.units))
        else:
            print(' uncalibrated: {} {}'.format(self.raw_value, 'mV'))
            
        return
    
    def do_qual(self, arg):
        ''' evaluate the quality of the sensor from its calibration constants '''
        if not self.is_calibrated:
            print(' Sensor must be calibrated to evaluate its quality.')
            return
        
        self.quality()
        
        return
    
    def do_dump(self, arg):
        ''' dump sensor's coefficients and stats'''
        self.dump()
        return False

    def update(self):
        self.stream.update()
        
        return

    def dump(self):
        for setpoint in self.setpoints.values():
            print(setpoint.dump())
            
        self.coefficients.dump()

        return

    @property
    def type(self):
        return self.sensor_type
    
    @property
    def address(self):
        return 'a1'
    
    @property
    def is_calibrated(self):
        return self.coefficients.is_valid
    
    @property
    def raw_value(self):
        return self.stream.raw_value

    @property
    def value(self):
        return self.stream.value

    def pack(self, prefix):
        # sensor
        package = ''
        package += 'id = "{}"\n'.format(self.id)
        package += 'type = "{}"\n'.format(self.sensor_type)
        package += 'chan_addr = "{}.{}"\n'.format(self.phorp_address, self.phorp_channel)
        package += '\n'
        
        if self.is_calibrated:
            my_prefix = '{}.{}'.format(prefix, 'coefficients')
            package += self.coefficients.pack(my_prefix)

            my_prefix = '{}.{}'.format(prefix, 'setpoints')
            for setpoint in self.setpoints.values():
                setpoint_prefix = '{}.{}'.format(my_prefix, setpoint.name)
                package += '{}\n'.format(setpoint.pack(setpoint_prefix))

        return package

    def unpack(self, package):
        # sensor
        self.id = package['id']
        self.sensor_type = package['type']
        self.chan_addr = package['chan_addr']

        if 'coefficients' in package:
            self.coefficients = Coefficients()
            self.coefficients.unpack(package['coefficients'])
            
        if 'setpoints' in package:
            for sp in package['setpoints'].values():
                print('  loading setpoint {}'.format(sp['name']))
                setpoint = CalibrationPoint('','','')
                setpoint.unpack(sp)
                self.setpoints[setpoint.name] = setpoint
            
        return

    
class PhSensorShell(SensorShell):
    def __init__(self, i2c_bus, sensor_id, *kwargs):
        super().__init__(i2c_bus, sensor_id, *kwargs)

        self.sensor_type = 'ph'
        self.units = 'pH'
        
        return
    
    @property
    def value(self):
        return self.evaluate(self.raw_value)

    def evaluate(self, raw_value):
        return self.coefficients.evaluate_y(raw_value)

    def quality(self):
        slope = self.coefficients.coefficients['slope']
        offset = self.coefficients.evaluate_x(7.0)
        
        print(' slope = {} mV/unit '.format(round(slope*1000,3)))
        print(' offset = {} mV'.format(round(offset*1000,3)))

        return

    
class EhSensorShell(SensorShell):
    def __init__(self, i2c_bus, sensor_id, *kwargs):
        super().__init__(i2c_bus, sensor_id, *kwargs)

        self.sensor_type = 'eh'
        self.units = 'mV'
        
        return
    
    @property
    def value(self):
        return self.coefficients.evaluate_y(self.raw_value)

    
class Sensors(cmd.Cmd):
    intro = 'Sensor Database, blank line to return to previous menu...'

    def __init__(self, i2c_bus, procedures, *kwargs):
        super().__init__(*kwargs)
        
        self.bus = i2c_bus
        self.procedures = procedures
        self.procedure = None # fix this
        
        self.sensors = dict()
        self.sensor_index = 0

        # known sensor types
        self.types = ['eh', 'ph'] # 'therm'

        self.ansi = Ansi()

        return

    @property
    def prompt(self):
        if len(self.sensors) == 0:
            sensor_id = 'empty'
        else:
            sensor_id = self.ansi.red(self.sensor.id)
            if self.sensor.is_calibrated:
                sensor_id = self.ansi.green(self.sensor.id)

        return '{}[{}]: '.format('db', sensor_id)

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

    def to_key(self, id):
        id = id.strip().lower().replace(' ', '_')
        
        return id
    
    def emptyline(self):
        return True

    def do_new(self, sensor_id):
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
        
        sensor = self.new_sensor(sensor_type, sensor_id)
        
        self.sensors[sensor_key] = sensor        
        self.sensor_index = self.last_index

        #sensor.do_show()
        sensor.cmdloop()
        
        return

    def new_sensor(self, sensor_type, sensor_id):
        if sensor_type.lower() not in self.types:
            print(' known types are {}. sensor not created.'.format(self.types))
            return

        print(' creating new {} sensor {}'.format(sensor_type, sensor_id))
        if sensor_type == 'ph':
            sensor = PhSensorShell(self.bus, sensor_id)
            self.procedure = self.procedures['ph']
        elif sensor_type == 'eh':
            sensor = EhSensorShell(self.bus, sensor_id)
            self.procedure = self.procedures['ph']
        elif sensor_type == 'therm':
            sensor = None

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

            id = self.ansi.red(sensor.id)
            if sensor.is_calibrated:
                id = self.ansi.green(sensor.id)

            type = sensor.type
            address = sensor.address
            due_date = sensor.coefficients.due_date
            
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

    
class CalibrationPoint(cmd.Cmd):
    intro = 'Calibration Point Configuration'
    prompt = 'point: '

    def __init__(self, name, units, value, *kwargs):
        super().__init__(*kwargs)

        self.name = name
        self.possible_units = ['eh', 'ph']

        if units.lower() not in self.possible_units:
            pass
        
        self.units = units
        self.value = value

        self.sample_period = 0.2
        self.update_period = 1
        self.number_of_samples = 30
        
        self.stats = rs.RunningStats()
        
        return

    def do_show(self, arg=None):
        ''' print present values'''
        print(' Calibration Point')
        print('  Units:   {}'.format(self.units))
        print('  Value:   {} {}'.format(self.value, self.units))
            
        return False
    
    def do_value(self, arg):
        ''' the first (lowest pH) in a two or three point calibration'''
        self.value = float(arg)

        self.do_show()
        return False

    @property
    def n(self):
        return self.stats.n

    @property
    def mean(self):
        return self.stats.mean()

    @property
    def variance(self):
        return self.stats.variance()

    @property
    def standard_deviation(self):
        return self.stats.standard_deviation()

    def clone(self):
        return(CalibrationPoint(self.name, self.units, self.value))

    def dump(self):
        str = '{}{}: n={}, mean={}, var={}, sd={}'.format(self.value, self.units, self.n, self.mean, self.variance, self.standard_deviation)

        return str
    
    def run(self, sensor):
        # setpoint run
        prompt = '  ready {} {} Calibration Solution. press <space> to begin, other to cancel'.format(self.units, self.value)
        print(prompt)
        key = getChar()
        
        if key != ' ':
            print('run canceled')
            return False

        while True:
            # sys.stdout.write("\x1b[A")  # move cursor up one line
            # blankline = ' ' * len(prompt)
            # print(blankline, end='\r')

            print('   ({} {}): '.format(self.units, self.value), end='')
            self.stats.clear()
            
            sample_time = time.time()
            update_time = sample_time
            for i in range(self.number_of_samples):
                sensor.update()
                self.stats.push(sensor.raw_value)
            
                now = time.time()
                if now > update_time:
                    print(sensor.raw_value, end=', ')
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

            prompt = '  {} {} Calibration Buffer. press <space> to repeat, other to advance'.format(self.units, self.value)
            print(prompt) #, end=''
            # sys.stdout.flush()
            key = getChar()
        
            if key != ' ':
                break
                            
        return True

    def pack(self, prefix):
        # Calibration SetPoint
        package = '[{}]\n'.format(prefix)
        
        package += 'name = "{}"\n'.format(self.name)
        package += 'units = "{}"\n'.format(self.units)
        package += 'value = {}\n'.format(self.value)

        # if self.n > 0:
        #     package += 'n = {}\n'.format(self.n)
        #     package += 'mean = {}\n'.format(self.mean)
        #     package += 'variance = {}\n'.format(self.variance)
        #     package += 'standard_deviation = {}\n'.format(self.standard_deviation)
            
        return package

    def unpack(self, package):
        # calibration setpoint
        self.name = package['name']
        self.units = package['units']
        self.value = package['value']

        return
    

class ProcedureShell(cmd.Cmd):
    intro = 'Procedure Configuration'
    prompt = 'pH: '

    def __init__(self, *kwargs):
        super().__init__(kwargs)
        
        self.possible_units = ['eh', 'ph']

        self.units = 'ph'
        self.point_count = 2

        # the default setpoint settings.
        self.setpoints = dict()
        self.setpoints['p1'] = CalibrationPoint('p1', 'pH', 4.0)
        self.setpoints['p2'] = CalibrationPoint('p2', 'pH', 7.0)
        self.setpoints['p3'] = CalibrationPoint('p3', 'pH', 10.0)

        return

    @property
    def p1(self):
        return self.setpoints['p1']

    @property
    def p2(self):
        return self.setpoints['p2']

    @property
    def p3(self):
        return self.setpoints['p3']
    
    def preloop(self):
        self.do_show()

        return

    def emptyline(self):
        return True
    
    def do_show(self, arg=None):
        ''' print present values'''
        print(' Configuration')
        print('  Units:  {}'.format(self.units))
        print('  Spread: {} point'.format(self.point_count))
        print('   P1:    {} {}'.format(self.p1.value, self.p1.units))
        print('   P2:    {} {}'.format(self.p2.value, self.p2.units))
        if self.point_count == 3:
            print('   P3:   {} {}'.format(self.p3.value, self.p2.units))
            
        return False
    
    def do_units(self, arg):
        ''' units of measurement ph or eh'''
        if arg.lower() not in self.possible_units:
            print(' known types are {}'.format(self.possible_units))
        else:
            self.units = arg.lower()
            self.p1.units = self.units
            self.p2.units = self.units
            self.p3.units = self.units

        self.do_show()
        
        return False

    def do_spread(self, arg):
        ''' calibration point count, 2 or 3'''
        try:
            if int(arg) not in [2,3]:
                print(' possible point count is {}'.format([2,3]))
            else:
                self.point_count = int(arg)
        except:
            print(' possible choices are 2 or 3')
            
        self.do_show()
        
        return False

    def do_p1(self, arg):
        ''' the first (lowest pH) in a two or three point calibration'''
        try:
            self.p1.value = float(arg)
        except:
            print(' invalid value: setpoint unchanged.')

        self.do_show()
        
        return False
        
    def do_p2(self, arg):
        ''' the middle or highest ph in a two or three point calibration'''
        try:
            self.p2.value = float(arg)
        except:
            print(' invalid value: setpoint unchanged.')

        self.do_show()
        
        return False
        
    def do_p3(self, arg):
        ''' the highest ph in a three point calibration'''
        if self.point_count < 3:
            print(' there is no point 3 in a two point calibration')
        else:
            self.p3.value = float(arg)

        self.do_show()
        
        return False
        
    def prep(self, sensor):
        sensor.setpoints = dict()
        sensor.setpoints[self.p1.name] = self.p1.clone()
        sensor.setpoints[self.p2.name] = self.p2.clone()
        if self.point_count == 3:
            sensor.setpoints[self.p2.name] = self.p3.clone()

        sensor.coefficients.interval = datetime.timedelta(days=180)
        
        return
    
    def run(self, sensor):
        print(' running {} point calibration on sensor {}'.format(self.point_count, sensor.id))

        ok = True
        for setpoint in sensor.setpoints.values():
            if not setpoint.run(sensor):
                ok = False
                break

        if ok:
            p1 = sensor.setpoints[self.p1.name]
            p2 = sensor.setpoints[self.p2.name]

            if sensor.coefficients.generate(p1.value,p1.mean, p2.value,p2.mean):
                # prompt here to accept...
                sensor.coefficients.timestamp = datetime.date.today() #+ duration
            
            #sensor.coefficients.generate(4.0,0.180, 8.0,-0.061)
            
        sensor.coefficients.dump()

        return

    def pack(self, prefix):
        # Procedure
        package = ''
        package += 'point_count = {}\n'.format(self.point_count)
        
        my_prefix = '{}.{}'.format(prefix, 'setpoints')
        for setpoint in self.setpoints.values():
            setpoint_prefix = '{}.{}'.format(my_prefix, setpoint.name)
            package += '{}\n'.format(setpoint.pack(setpoint_prefix))
            
        return package

    def unpack(self, package):
        # procedure
        self.point_count = package['point_count']

        if 'setpoints' in package:        
            for sp in package['setpoints'].values():
                setpoint = CalibrationPoint('','','')
                setpoint.unpack(sp)
                self.setpoints[setpoint.name] = setpoint
            
        return

    
class Procedures(cmd.Cmd):
    intro = 'Sensor calibration procedures. ? for help.'
    prompt = 'procedures: '

    def __init__(self, *kwargs):
        super().__init__(*kwargs)

        self.procedures = dict()
        self.procedures['ph'] = ProcedureShell()
        
        return

    def __getitem__(self, key):
        return self.procedures[key]
    
    def emptyline(self):
        return True
    
    def do_ph(self, arg):
        ''' ph<cr> edit pH procedure default parameters''' 
        self.procedures['ph'].cmdloop()

        return False

    def pack(self, prefix):
        package = ''
        
        for key, procedure in self.procedures.items():
            my_prefix = '{}.{}'.format(prefix, key)
            package += '[{}]\n'.format(my_prefix)
            package += '{}\n'.format(procedure.pack(my_prefix))
            
        return package

    def unpack(self, package):
        for key, template in package.items():
            procedure = ProcedureShell()
            procedure.unpack(template)
            self.procedures[key] = procedure
            
        return

    
class CalShell(cmd.Cmd):
    intro = 'Welcome to the Calibration Shell. ? for help.'
    prompt = 'shell: '

    def __init__(self, i2c_bus, *kwargs):
        super().__init__(*kwargs)

        self.bus = i2c_bus
        #self.procedure = ProcedureShell()
        self.procedures = Procedures()
        self.sensors = Sensors(self.bus, self.procedures)

        self.suffix = '.toml'
        self.filename = 'coefficients{}'.format(self.suffix)

        return
    
    def emptyline(self):
        self.do_help('') # displays help
        
        return False
    
    def do_procedures(self, arg):
        ''' procedure configuration '''
        self.procedures.cmdloop()
        
        return
    
    def do_sensors(self, arg):
        ''' edit sensors'''
        self.sensors.cmdloop()

        return

    def do_view(self, arg):
        ''' view sensor coefficients'''

        package = 'date = {}\n'.format(datetime.datetime.now())        
        package += self.pack()

        print(package)
        
        return
    
    def do_save(self, arg):
        ''' save sensor coefficients'''

        package = self.pack()

        filename = self.get_filename()
        
        print(' Saving sensor data to {}'.format(filename))
        with open(filename, 'w') as fp:
            fp.write(package)

        print(' calibration data saved to {}.'.format(filename))
        self.filename = filename
        
        return

    def do_load(self, arg):
        ''' load sensor coefficients file'''

        filename = self.get_filename()
        package = ''
        print(' Loading sensor data from {}'.format(filename))
        with open(filename, 'rb') as fp:
            package = tomli.load(fp)

        self.unpack(package)
        
        return
    
    def do_exit(self, arg):
        ''' Done'''
        print(' exiting')

        return True

    def get_filename(self):
        new_name = input('enter filename without suffix ({}): '.format(self.filename))

        # https://stackoverflow.com/a/7406369
        keepcharacters = ('.','_')
        new_name = ''.join(c for c in new_name if c.isalnum() or c in keepcharacters).rstrip()

        filename = self.filename
        if len(new_name) > 0:
            filename = new_name

        if not filename.endswith(self.suffix):
            filename = filename + self.suffix

        return filename
    
    def pack(self):
        package = 'date = {}\n'.format(datetime.datetime.now())        

        prefix = 'procedures'
        package += '{}\n'.format(self.procedures.pack(prefix))
        
        prefix = 'sensors'
        package += '{}\n'.format(self.sensors.pack(prefix))

        return package

    def unpack(self, package):
        print(package['date'])

        if 'procedures' in package:
            self.procedures.unpack(package['procedures'])

        if 'sensors' in package:
            self.sensors.unpack(package['sensors'])

        return
    
    
if __name__ == '__main__':
    
    with smbus.SMBus(1) as bus:
        shell = CalShell(bus)
        shell.cmdloop()

    exit()
