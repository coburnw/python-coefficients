#
# deploy.py - a container for a runtime metadata.
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

from . import shell

class DeployShell(shell.Shell):
    intro = 'Sensor Configuration.  x to return to previous menu.'
    # prompt = 'sensor: '

    def __init__(self, *kwargs): # sensors
        super().__init__(*kwargs)

        self.key_name = ''
        self.folder_name = ''
        self.group_name = ''

        self.update_interval = 60 # minutes
        self.over_sample_rate = 10 # samples per interval
        self.filter_in_percent = 10 # %

        # self.silo_sensors = sensors
        # self.sensors = [] # deployed sensors
        return

    @property
    def id(self):
        return self.sensor.id
    
    @property
    def prompt(self):
        prompt = '{}: '.format(self.cyan('deploy'))
            
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

    def do_key(self, arg):
        ''' Enter name of Grovestreams API Key (typically hostname of deployed system)'''
        self.key_name = arg.strip().replace(' ', '_')
        
        return False

    def do_folder(self, arg):
        ''' Enter Grovestreams Folder Name'''

        self.folder_name = arg.strip().replace(' ', '_')
        
        return False

    def do_group(self, arg):
        ''' Enter Group Name'''

        self.group_name = arg.strip().replace(' ', '_')

        return False

    def do_interval(self, arg):
        ''' Grovestreams update Interval in minutes'''
        self.update_interval = int(arg)

        if self.update_interval < 10:
            self.update_interval = 10
            
        return False

    def do_osr(self, arg):
        ''' Over Sample Rate, number of sensor samples to filter per Interval (10 is a good number)'''

        self.over_sample_rate = int(arg)
        
        if self.over_sample_rate > 100:
            self.over_sample_rate = 100
        elif self.over_sample_rate < 1:
            self.over_sample_rate = 1
            
        return False

    def do_filter(self, arg):
        ''' Aproximate Filter Time Constant in percent of Interval'''

        self.filter_in_percent = int(arg)
        
        if self.filter_in_percent < 0:
            self.filter_in_percent = 0
        if self.filter_in_percent > 250:
            self.filter_in_percent = 250
            
        return False
    
    def do_show(self, arg=None):
        ''' print sensors parameters'''
        print(' Group: {}'.format(self.group_name))
        print('  Folder: {}'.format(self.folder_name))
        print('  Key Name: {}'.format(self.key_name))
        print('')
        print('  Interval: {} minutes'.format(self.update_interval))
        print('  OSR:  {} samples per interval'.format(self.over_sample_rate))
        print('  Filter TC: {}% interval'.format(self.filter_in_percent))
        
        return False

    def pack(self, prefix):
        # deploy

        package = ''
        package += '\n'
        package += '[{}]\n'.format(prefix)
        
        package += 'folder_name = "{}"\n'.format(self.folder_name)
        package += 'group_name = "{}"\n'.format(self.group_name)
        package += 'key_name = "{}"\n'.format(self.key_name)
        
        package += 'update_interval = {}\n'.format(self.update_interval)
        package += 'over_sample_rate = {}\n'.format(self.over_sample_rate)
        package += 'filter_in_percent = {}\n'.format(self.filter_in_percent)

        return package

    def unpack(self, package):
        # deploy
        self.folder_name = package.get('folder_name', 'folder')
        self.group_name = package.get('group_name', 'group')
        self.key_name = package.get('key_name', 'key')
        
        self.update_interval = package.get('update_interval', 60)
        self.over_sample_rate = package.get('over_sample_rag', 10)        
        self.filter_in_percent = package.get('filter_in_percent', 0)
                
        return

