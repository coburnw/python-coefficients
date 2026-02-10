import datetime

from . import shell
from . import coefficients
from . import setpoint as sp

class Procedure(shell.Shell):
    intro = 'Generic Procedure Configuration'
    prompt = 'edit(?): '

    def __init__(self, streams, *kwargs):
        super().__init__(*kwargs)

        self.streams = streams
        
        self.stream_type = None
        self.stream_address = None
        
        self.scaled_units = None
        self.point_count = 2
        self.setpoints = dict()

        self.interval = datetime.timedelta(days=180)

        self.prompt = '{}'.format(self.cyan(self.prompt))

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
        print('  Stream Type :  {}'.format(self.stream_type))
        print('  Stream Address:  {}'.format(self.stream_address))
        print()
        print('  Units:  {}'.format(self.scaled_units))
        print('  Spread: {} point'.format(self.point_count))
        print('   P1:    {} {}'.format(self.p1.scaled_value, self.p1.scaled_units))
        print('   P2:    {} {}'.format(self.p2.scaled_value, self.p2.scaled_units))
        if self.point_count == 3:
            print('   P3:   {} {}'.format(self.p3.scaled_value, self.p3.scaled_units))

        print('  Interval: {} days'.format(self.interval.days))
        
        return False
    
    def do_address(self, arg=None):
        ''' address <addr> change address of phorp channel used by procedure'''

        address = arg[0]
        channel = arg[1]
        
        if address in 'abcdefg' and channel in '1234':
            self.stream_address = address + channel
        else:
            print(' invalid address. board_id is a-g, channel_id is 1-4')

        self.do_show()
        
        return
    
    def do_spread(self, arg):
        ''' spread <n> Calibration point count, 2 or 3'''
        
        try:
            if int(arg) not in [2,3]:
                print(' possible point count is {}'.format([2,3]))
            else:
                self.point_count = int(arg)
        except:
            print(' possible choices are 2 or 3')
            
        self.do_show()
        
        return False

    def do_interval(self, arg):
        ''' interval <n> Calibration interval in days'''

        try:
            days = int(arg)
        except:
            days = self.interval.days
            print(' argument is not integer. using {}.'.format(days))
            
        self.interval = datetime.timedelta(days=int(days))

        self.do_show()
        
        return False

    def do_p1(self, arg):
        ''' p1 <n> The first (lowest value) in a two or three point calibration'''
        
        try:
            self.p1.scaled_value = float(arg)
        except:
            print(' invalid value: setpoint unchanged.')

        self.do_show()
        
        return False
        
    def do_p2(self, arg):
        ''' p2 <n> The middle or highest value in a two or three point calibration'''
        
        try:
            self.p2.scaled_value = float(arg)
        except:
            print(' invalid value: setpoint unchanged.')

        self.do_show()
        
        return False
        
    def do_p3(self, arg):
        ''' p3 <n> The highest value in a three point calibration'''
        
        if self.point_count < 3:
            print(' there is no point 3 in a two point calibration')
        else:
            self.p3.scaled_value = float(arg)

        self.do_show()
        
        return False
        
    def prep(self, sensor):
        sensor.setpoints = dict()
        sensor.setpoints[self.p1.name] = self.p1.clone()
        sensor.setpoints[self.p2.name] = self.p2.clone()
        if self.point_count == 3:
            sensor.setpoints[self.p2.name] = self.p3.clone()

        sensor.name = self.name
        sensor.calibration.scaled_units = self.scaled_units
        sensor.calibration.interval = self.interval

        stream = self.streams[self.stream_type]() # create a new stream instance
        sensor.connect(stream, self.stream_address) # and override deployed address
        
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

            if sensor.calibration.generate(p1.scaled_value,p1.mean, p2.scaled_value,p2.mean):
                # prompt here to accept...
                sensor.calibration.timestamp = datetime.date.today()
            
        sensor.calibration.dump()

        return

    def pack(self, prefix):
        # Procedure
        package = ''
        package += 'units = "{}"\n'.format(self.scaled_units)
        package += 'stream_type = "{}"\n'.format(self.stream_type)
        package += 'stream_address = "{}"\n'.format(self.stream_address)
        package += 'interval = {}\n'.format(self.interval.days)
        package += 'point_count = {}\n'.format(self.point_count)
        
        my_prefix = '{}.{}'.format(prefix, 'setpoints')
        for setpoint in self.setpoints.values():
            setpoint_prefix = '{}.{}'.format(my_prefix, setpoint.name)
            package += '\n'
            package += setpoint.pack(setpoint_prefix)
        
        return package

    def unpack(self, package):
        # procedure
        self.scaled_units = package['units']
        self.stream_type = package['stream_type']
        self.stream_address = package['stream_address']
        self.interval = datetime.timedelta(days=package['interval'])
        self.point_count = package['point_count']

        if 'setpoints' in package:        
            for template in package['setpoints'].values():
                setpoint = sp.Setpoint('','','')
                setpoint.unpack(template)
                self.setpoints[setpoint.name] = setpoint
            
        return
        
    
class Procedures(shell.Shell):
    intro = 'Sensor calibration procedures. ? for help.'
    prompt = 'procedures: '

    def __init__(self, procedures, *kwargs):
        super().__init__(*kwargs)

        self.procedures = procedures
        
        self.prompt = '{}'.format(self.cyan(self.prompt))
        
        return

    def __getitem__(self, key):
        return self.procedures[key]

    def keys(self):
        return self.procedures.keys()
    
    def preloop(self):
        self.do_help(None)

        return

    def emptyline(self):
        return True
    
    def do_ph(self, arg):
        ''' ph<cr> edit pH procedure default parameters''' 
        self.procedures['ph'].cmdloop()

        return False

    def do_eh(self, arg):
        ''' ph<cr> edit Eh procedure default parameters''' 
        self.procedures['eh'].cmdloop()

        return False

    def pack(self, prefix):
        package = ''
        
        for key, procedure in self.procedures.items():
            my_prefix = '{}.{}'.format(prefix, key)
            package += '\n'
            package += '[{}]\n'.format(my_prefix)
            package += procedure.pack(my_prefix)
            
        return package

    def unpack(self, package):
        for key, template in package.items():
            if key == 'ph':
                procedure = self.procedures[key] #PhProcedure()
            elif key == 'eh':
                procedure = self.procedures[key] #EhProcedure()
            else:
                print('unrecognized procedure {}. ignoring'.format(key))
                
            procedure.unpack(template)
            self.procedures[key] = procedure
            
        return

