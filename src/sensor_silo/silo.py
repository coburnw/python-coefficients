#
# silo.py - the applications main entrance to the library.
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
import datetime

import tomli

from . import shell
from . import procedure
from . import sensor
from . import deploy

class xDeploy():
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

class Deploy():
    def __init__(self, filename=None):
        self.deployment = deploy.DeployShell()
        self.sensors = None

        if filename is not None:
            self.load(filename)
            
        return

    @property
    def key_name(self):
        return self.deployment.key_name

    @property
    def folder_name(self):
        return self.deployment.folder_name

    @property
    def group_name(self):
        return self.deployment.group_name

    @property
    def stream_period(self):
        return self.deployment.update_interval*60

    @property
    def sample_period(self):
        return self.stream_period / self.over_sample_rate

    @property
    def over_sample_rate(self):
        return self.deployment.over_sample_rate

    @property
    def time_constant(self):
        tc = self.deployment.filter_in_percent / 100
        if tc < 1:
            tc = 1
            
        return tc
    
    def load(self, filename=None):
        config = ConfigFile()
        filename = config.get_filename(filename)
        package = config.load(filename)
        self.unpack(package)

        return
    
    def connect(self, streams):
        for sensor in self.sensors.values():
            stream = streams[sensor.stream_type]() # create a new hardware stream instance
            sensor.connect(stream)

        return

    def unpack(self, package):
        if 'sensors' in package:
            self.sensors = sensor.Sensors(package['sensors'])

        if 'deployment' in package:
            self.deployment.unpack(package['deployment'])

        return


class ConfigFile():
    def __init__(self):
        self.suffix = '.toml'
        self.filename = 'deployment{}'.format(self.suffix)

        return

    def load(self, filename=None):
        if filename is None:
            filename = self.filename
            
        package = ''
        with open(filename, 'rb') as fp:
            package = tomli.load(fp)
            print(' calibration data loaded from {}.'.format(filename))

        return package

    def save(self, package, filename=None):
        if filename is None:
            filename = self.filename

        with open(filename, 'w') as fp:
            fp.write(package)
            print(' calibration data saved to {}.'.format(filename))
            
        self.filename = filename

        return

    def get_filename(self, filename=None):
        new_name = filename
        if new_name is None:
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
    
    
class Shell(shell.Shell):
    intro = 'Welcome to the Sensor Silo. ? for help.'
    prompt = 'silo: '

    def __init__(self, procedures, *kwargs):
        super().__init__(*kwargs)

        self.procedures = procedure.Procedures(procedures)
        self.sensors = sensor.SensorsShell(self.procedures)
        self.deploy = deploy.DeployShell()

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

    def do_deploy(self, arg):
        ''' view/edit project deployment'''
        self.deploy.cmdloop()

        return

    def do_dump(self, arg):
        ''' view sensor configuration'''
        package = self.pack()
        print(package)
        
        return
    
    def do_save(self, arg):
        ''' save sensor configuration file'''
        config = ConfigFile()
        
        filename = config.get_filename()        
        print(' Saving sensor data to {}'.format(filename))
        
        package = self.pack()
        config.save(package, filename)

        return

    def do_load(self, arg):
        ''' load sensor configuration file'''
        config = ConfigFile()
        
        filename = config.get_filename()
        print(' Loading sensor data from {}'.format(filename))
        
        package = config.load(filename)

        self.unpack(package)
        
        return
    
    def do_exit(self, arg):
        ''' Done'''
        print(' exiting')

        return True

    def pack(self):
        package = 'date = {}\n'.format(datetime.datetime.now())        

        prefix = 'procedures'
        package += self.procedures.pack(prefix)
        
        prefix = 'sensors'
        package += self.sensors.pack(prefix)

        prefix = 'deployment'
        package += self.deploy.pack(prefix)

        return package

    def unpack(self, package):
        print(package['date'])

        if 'procedures' in package:
            self.procedures.unpack(package['procedures'])

        if 'sensors' in package:
            self.sensors.unpack(package['sensors'])

        if 'deployment' in package:
            self.deploy.unpack(package['deployment'])

        return
    

if __name__ == '__main__':
    
    with smbus.SMBus(1) as bus:
        shell = CalShell(bus)
        shell.cmdloop()

    exit()
