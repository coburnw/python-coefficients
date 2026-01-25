import cmd
import sys
import time
from datetime import datetime

import smbus3 as smbus

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

class Coefficients():
    def __init__(self):
        # self.units = sensor_units
        self.degree = 1
        self.coefficients = dict()

        return

    def __len__(self):
        return len(self.coefficients)
    
    def generate(self, x1,y1, x2,y2):
        try:
            self.coefficients['slope'] = (y1 - y2) / (x1 - x2)
            self.coefficients['offset'] = y2 + self.coefficients['slope'] * x2
        except ZeroDivisionError:
            self.coefficients['slope'] = 1.0
            self.coefficients['offset'] = 0.0
            
        return

    def evaluate(self, raw_value):
        result = (raw_value + self.coefficients['offset']) / self.coefficients['slope']
        
        return result
    
    def dump(self):
        for key, value in self.coefficients.items():
            print(key, value)

        return
    
    def serialize(self, prefix):
        serialized = '[{}]\n'.format(prefix)
        serialized += 'degree = {}\n'.format(self.degree)
        
        for key, value in self.coefficients.items():
            serialized += '{} = {}\n'.format(key, value)

        return serialized

    
class SensorShell(cmd.Cmd):
    intro = 'Sensor Configuration.  Blank line to return to previous menu.'
    # prompt = 'sensor: '

    def __init__(self, i2c_bus, sensor_id, *kwargs):
        super().__init__(*kwargs)
        self.bus = i2c_bus

        self.sensor_type = 'none'
        self.id = sensor_id
        self.phorp_address = 0x68
        self.phorp_channel = 2

        a = phorp.PhorpX4(self.bus, 'a')
        self.stream = fs.PhStream(a[self.phorp_channel], 'ph_cal', filter_constant=1)

        self.coefficients = Coefficients()
        
        return

    @property
    def prompt(self):
        return 'sensor {}: '.format(self.id)

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
        
        return False
    
    def do_dump(self, arg):
        ''' dump sensor's coefficients and stats'''
        self.dump()
        return False

    def update(self):
        self.stream.update()
        
        return

    def dump(self):
        for setpoint in self.setpoints:
            print(setpoint.dump())
            
        self.coefficients.dump()

        return
    
    @property
    def is_calibrated(self):
        is_calibrated = False

        if len(self.coefficients) > 0:
            is_calibrated = True

        return is_calibrated
    
    @property
    def raw_value(self):
        return self.stream.raw_value

    @property
    def value(self):
        return self.stream.value

    def serialize(self, prefix):
        prefix = '{}.{}'.format(prefix, self.id)
        serialized = '[{}]\n'.format(prefix)
        serialized += 'type = {}\n'.format(self.sensor_type)
        serialized += 'chan_addr = {}.{}\n'.format(self.phorp_address, self.phorp_channel)
        serialized += '\n'
        
        if self.is_calibrated:
            my_prefix = '{}.{}'.format(prefix, 'setpoints')
            #serialized += '[{}]\n'.format(my_prefix)
            for setpoint in self.setpoints:
                setpoint_prefix = '{}.{}'.format(my_prefix, setpoint.name)
                serialized += setpoint.serialize(setpoint_prefix)
                serialized += '\n'

            my_prefix = '{}.{}'.format(prefix, 'coefficients')
            serialized += self.coefficients.serialize(my_prefix)

        return serialized

    
class PhSensorShell(SensorShell):
    def __init__(self, i2c_bus, sensor_id, *kwargs):
        super().__init__(i2c_bus, sensor_id, *kwargs)

        self.sensor_type = 'ph'
        self.units = 'pH'
        
        return
    
    @property
    def value(self):
        return self.coefficients.evaluate(self.raw_value) + 7
    
class EhSensorShell(SensorShell):
    def __init__(self, i2c_bus, sensor_id, *kwargs):
        super().__init__(i2c_bus, sensor_id, *kwargs)

        self.sensor_type = 'eh'
        self.units = 'mV'
        
        return
    
    @property
    def value(self):
        return self.coefficients.evaluate(self.raw_value)
    
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

        self.sample_period = 1.0
        self.update_period = 2
        self.number_of_samples = 10
        
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
            return

        while True:
            sys.stdout.write("\x1b[A")  # move cursor up one line
            blankline = ' ' * len(prompt)
            print(blankline, end='\r')

            print('   ({} {}): '.format(self.units, self.value), end='')
            #sensor.calibration.stats[self.name] = rs.RunningStats()
            self.stats.clear()
            
            sample_time = time.time()
            update_time = sample_time
            for i in range(self.number_of_samples):
                sensor.update()
                #sensor.calibration.stats[self.name].push(sensor.raw_value)
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
                            
        return

    def serialize(self, prefix):
        # CalibrationPoint
        serialized = '[{}]\n'.format(prefix)
        
        serialized += 'name = {}\n'.format(self.name)
        serialized += 'units = {}\n'.format(self.units)
        serialized += 'value = {}\n'.format(self.value)

        if self.n > 0:
            serialized += 'n = {}\n'.format(self.n)
            serialized += 'mean = {}\n'.format(self.mean)
            serialized += 'variance = {}\n'.format(self.variance)
            serialized += 'standard_deviation = {}\n'.format(self.standard_deviation)
            
        return serialized

    
class ProcedureShell(cmd.Cmd):
    intro = 'Procedure Configuration'
    prompt = 'procedure: '

    def __init__(self, *kwargs):
        super().__init__(kwargs)
        
        self.possible_units = ['eh', 'ph']

        self.units = 'ph'
        self.point_count = 2
        self.p1 = CalibrationPoint('p1', 'pH', 4.0)
        self.p2 = CalibrationPoint('p2', 'pH', 7.0)
        self.p3 = CalibrationPoint('p3', 'pH', 10.0)

        return
        
    def preloop(self):
        self.do_show()

        return

    def emptyline(self):
        self.do_show()
        
        return False
    
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
            print('invalid value: setpoint unchanged.')

        self.do_show()
        
        return False
        
    def do_p2(self, arg):
        ''' the middle or highest ph in a two or three point calibration'''
        try:
            self.p2.value = float(arg)
        except:
            print('invalid value: setpoint unchanged.')

        self.do_show()
        
        return False
        
    def do_p3(self, arg):
        ''' the highest ph in a three point calibration'''
        if self.point_count < 3:
            print('there is no point 3 in a two point calibration')
        else:
            self.p3.value = float(arg)

        self.do_show()
        
        return False
        
    def do_return(self, arg):
        ''' return to calibration'''
        return True

    def prep(self, sensor):
        sensor.setpoints = []
        sensor.setpoints.append(self.p1.clone())
        sensor.setpoints.append(self.p2.clone())
        if self.point_count == 3:
            sensor.setpoints.append(self.p3.clone())

        return
    
    def run(self, sensor):
        print(' running {} point calibration on sensor {}'.format(self.point_count, sensor.id))

        for setpoint in sensor.setpoints:
            setpoint.run(sensor)
        
        p1 = sensor.setpoints[0]
        p2 = sensor.setpoints[1]

        sensor.coefficients.generate(p1.value-7,p1.mean, p2.value-7,p2.mean)
        sensor.coefficients.dump()

        return

    def serialize(self, prefix):
        # Procedure
        serialized = '[{}]\n'.format(prefix)
        
        serialized += '# Default Calibration Setpoints\n'
        serialized += 'point_count = {}\n'.format(self.point_count)

        point_prefix = '{}.{}'.format(prefix, 'p1')
        serialized += '{}\n'.format(self.p1.serialize(point_prefix))
        
        point_prefix = '{}.{}'.format(prefix, 'p2')
        serialized += '{}\n'.format(self.p2.serialize(point_prefix))
        
        point_prefix = '{}.{}'.format(prefix, 'p3')
        serialized += '{}'.format(self.p3.serialize(point_prefix))

        return serialized
    
class Sensors(cmd.Cmd):
    intro = 'Sensor Database, Blank line to return to previous menu...'

    def __init__(self, i2c_bus, procedure, *kwargs):
        super().__init__(*kwargs)
        
        self.bus = i2c_bus
        self.procedure = procedure

        self.sensors = []
        self.sensor_index = 0

        # known sensor types
        self.types = ['eh', 'ph'] # 'therm'

        return

    @property
    def prompt(self):
        if len(self.sensors) == 0:
            sensor_id = 'empty'
        else:
            sensor_id = self.sensor.id
            
        return '{}[{}]: '.format('db', sensor_id)

    @property
    def sensor(self):
        return self.sensors[self.sensor_index]

    def emptyline(self):
        return True
    
    def do_new(self, sensor_id):
        ''' new <id>. Create a new sensor instance'''
        if len(sensor_id.strip()) == 0:
            print(' missing sensor id.')
            return
        
        sensor_type = input(' Enter sensor type [{}] :'.format(self.types))
        
        if sensor_type.lower() not in self.types:
            print(' known types are {}. sensor not created.'.format(self.types))
            return

        print('creating new {} sensor {}'.format(sensor_type, sensor_id))
        if sensor_type == 'ph':
            sensor = PhSensorShell(self.bus, sensor_id)
        elif sensor_type == 'eh':
            sensor = EhSensorShell(self.bus, sensor_id)
        elif sensor_type == 'therm':
            sensor = None
                                   
        self.procedure.prep(sensor)
        self.sensors.append(sensor)
        self.sensor_index = len(self.sensors) - 1

        sensor.do_show()
        
        return

    def do_edit(self, arg):
        ''' edit selected sensor'''
        self.sensor.cmdloop()

        return
    
    def do_list(self, arg):
        ''' List sensors '''

        if len(self.sensors) == 0:
            print(' No sensors in list.  "new" to add a sensor.')
            return
        
        i = 0
        for sensor in self.sensors:
            carret = ' '
            if i == self.sensor_index:
                carret = '>'
                
            i += 1               
            print(' {}{}'.format(carret, sensor.id))
        
        return

    def do_prev(self, arg):
        ''' retreat to previous sensor in list'''
        self.sensor_index -= 1
        if self.sensor_index < 0:
            self.sensor_index = 0

        self.do_list('')
        
        return
    
    def do_next(self, arg):
        ''' advance to next sensor in list'''
        self.sensor_index += 1
        if self.sensor_index > len(self.sensors):
            self.sensor_index = len(self.sensors)

        self.do_list('')

        return
    
    def do_cal(self, arg):
        ''' Acquire sensor calibration data'''
        self.procedure.run(self.sensor)
            
        return

    def do_measure(self, arg):
        ''' Sensor measurement in engineering units'''
        self.sensor.update()

        if self.sensor.is_calibrated:
            print(' {} {}: {} {}'.format(self.sensor.raw_value, 'mV', self.sensor.value, self.sensor.units))
        else:
            print(' uncalibrated: {} {}'.format(self.sensor.raw_value, 'mV'))
            
        return
    
    def do_dump(self, arg):
        ''' Dump sensor calibration parameters '''
        self.sensor.dump()

        return

    def serialize(self, prefix):
        # Sensors
        serialized = '[{}]\n'.format(prefix)

        for sensor in self.sensors:
            serialized += '{}\n'.format(sensor.serialize(prefix))
            
        return serialized
            
        
class CalShell(cmd.Cmd):
    intro = 'Welcome to the Calibration Shell'
    prompt = 'cal: '

    def __init__(self, i2c_bus, *kwargs):
        super().__init__(*kwargs)

        self.bus = i2c_bus
        self.procedure = ProcedureShell()
        self.sensors = Sensors(self.bus, self.procedure)
              
        return
    
    def emptyline(self):
        self.do_help('') # displays help
        
        return False
    
    def do_procedure(self, arg):
        ''' procedure configuration '''
        self.procedure.cmdloop()
        
        return
    
    def do_sensors(self, arg):
        ''' edit sensors'''
        self.sensors.cmdloop()

        return
    
    def do_save(self, arg):
        ''' Save sensor coefficients'''
        print('saveing sensors')
        serialized = self.serialize()
        
        return

    def do_exit(self, arg):
        ''' Done'''
        print('exiting')
        
        exit()

    def serialize(self):
        serialized = 'date = {}\n'.format(datetime.now())
        
        prefix = 'procedure'
        serialized += '{}\n'.format(self.procedure.serialize(prefix))
        
        prefix = 'sensors'
        serialized += '{}\n'.format(self.sensors.serialize(prefix))

        print(serialized)

        return

    
if __name__ == '__main__':
    
    with smbus.SMBus(1) as bus:
        shell = CalShell(bus)
        shell.cmdloop()
    
