import sys
import datetime

#import smbus3 as smbus
import tomli

from . import shell
from . import procedure
from . import sensor

class Deploy():
    def __init__(self, streams, *kwargs):
        super().__init__(*kwargs)

        self.deployment = deployment.Deployment(streams)
        self.sensors = sensor.Sensors(self.deployment)

        self.suffix = '.toml'
        self.filename = 'coefficients{}'.format(self.suffix)

        return

    def load(self):
        ''' load sensor configuration file'''

        filename = self.get_filename()
        package = ''
        print(' Loading sensor data from {}'.format(filename))
        with open(filename, 'rb') as fp:
            package = tomli.load(fp)

        self.unpack(package)
        
        return
    
    
class Shell(shell.Shell):
    intro = 'Welcome to the Calibration Toolcrib. ? for help.'
    prompt = 'crib: '

    def __init__(self, procedures, *kwargs):
        super().__init__(*kwargs)

        self.procedures = procedure.Procedures(procedures)
        self.sensors = sensor.SensorsShell(self.procedures)

        self.suffix = '.toml'
        self.filename = 'coefficients{}'.format(self.suffix)

        self.prompt = '{}'.format(self.cyan(self.prompt))

        return
    
    def emptyline(self):
        self.do_help('')
        
        return False
    
    def do_procedures(self, arg):
        ''' procedure configuration '''
        self.procedures.cmdloop()
        
        return
    
    def do_sensors(self, arg):
        ''' view/edit sensor database'''
        self.sensors.cmdloop()

        return

    def do_dump(self, arg):
        ''' view sensor configuration'''

        package = self.pack()

        print(package)
        
        return
    
    def do_save(self, arg):
        ''' save sensor configuration file'''

        package = self.pack()

        filename = self.get_filename()
        
        print(' Saving sensor data to {}'.format(filename))
        with open(filename, 'w') as fp:
            fp.write(package)

        print(' calibration data saved to {}.'.format(filename))
        self.filename = filename
        
        return

    def do_load(self, arg):
        ''' load sensor configuration file'''

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
        package += self.procedures.pack(prefix)
        
        prefix = 'sensors'
        package += self.sensors.pack(prefix)

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
