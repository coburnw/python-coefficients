#
# procedure.py - base class for a procedure that calibrates a sensor.
#                part of the python sensor silo project.
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

import datetime

from . import shell

class ProcedureShell(shell.Shell):
    intro = 'Generic Procedure Configuration'

    def __init__(self, streams, *kwargs):
        super().__init__(*kwargs)

        self.streams = streams
        self.stream_type = None
        self.stream_address = None

        # set by specialized procedure
        self.kind = None
        self.parameters = dict()
        self.property = None
        self.scaled_units = None
        self.unit_id = None
        self.interval = datetime.timedelta(days=180)

        return

    @property
    def type(self):
        return self.__class__.__name__
    
    @property
    def prompt(self):
        text = 'edit procedure ({})'.format(self.kind)
        return '{}: '.format(self.cyan(text))
    
    def preloop(self):
        self.do_show(None)

        return

    def emptyline(self):
        self.do_show(None)
        
        return False
    
    def do_x(self, arg):
        ''' exit to previous menu'''
        return True
    
    def do_show(self, arg=None):
        ''' print present values'''
        
        print('  Stream Type : {}'.format(self.stream_type))
        print('  Stream Address: {}'.format(self.stream_address))
        print()
        print('  Property: {}'.format(self.property))
        self.show()
        
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

        self.do_show(None)
        
        return
    
    def do_interval(self, arg):
        ''' interval <n> Calibration interval in days'''

        try:
            days = int(arg)
        except:
            days = self.interval.days
            print(' argument is not integer. using {}.'.format(days))
            
        self.interval = datetime.timedelta(days=int(days))

        self.do_show(None)
        
        return False

    def prep(self, sensor):
        from . import calibration # circular reference

        if sensor.kind is None:
            # initialize a new sensor
            sensor.kind = self.kind
            sensor.name = '{}.{}'.format(sensor.kind, sensor.id)
            sensor.property = self.property

        if sensor.calibration is None:
            sensor.calibration = calibration.Calibration()
            sensor.calibration.procedure_type = self.type
            sensor.calibration.scaled_units = self.scaled_units
            sensor.calibration.unit_id = self.unit_id
            sensor.calibration.interval = self.interval

        sensor.stream_type = self.stream_type        
        stream = self.streams[sensor.stream_type]() # create a new stream instance
        sensor.connect(stream, self.stream_address) # and override deployed address
        
        return
    
    def run(self, sensor):
        if not self.evaluate(sensor):
            print(' sensor calibration canceled.')
        else:
            sensor.calibration.timestamp = datetime.date(1970, 1, 1)
            if self.save(sensor):
                sensor.calibration.timestamp = datetime.date.today()
            else:
                print(' sensor calibration failed.  calibration invalidated.')
               
            # prompt here to accept...
        
        # sensor.calibration.show()

        return

    def evaluate(self, sensor):
        ''' specialized evaluation of sensor calibration constants'''
        raise NotImplemented
    
    def save(self, sensor):
        ''' specialized save/use of sensor calibration constatns'''
        raise NotImplemented
    
    def pack(self, prefix):
        # Procedure
        package = ''
        package += 'type = "{}"\n'.format(self.type)
        package += 'kind = "{}"\n'.format(self.kind)
        package += 'scaled_units = "{}"\n'.format(self.scaled_units)
        package += 'unit_id = "{}"\n'.format(self.unit_id)
        package += 'stream_type = "{}"\n'.format(self.stream_type)
        package += 'stream_address = "{}"\n'.format(self.stream_address)
        package += 'interval = {}\n'.format(self.interval.days)
        
        return package

    def unpack(self, package):
        # procedure
        ### self.type = package['type'] dont override our own type
        self.kind = package['kind']
        self.scaled_units = package['scaled_units']
        self.unit_id = package['unit_id']
        self.stream_type = package['stream_type']
        self.stream_address = package['stream_address']
        self.interval = datetime.timedelta(days=package['interval'])

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
        self.do_help(None)
        
        return False
    
    def do_x(self, arg):
        ''' exit to previous menu'''
        return True
    
    def do_ph(self, arg):
        ''' ph<cr> edit pH procedure default parameters''' 
        self.procedures['ph'].cmdloop()

        return False

    def do_orp(self, arg):
        ''' ph<cr> edit Eh procedure default parameters''' 
        self.procedures['orp'].cmdloop()

        return False

    def do_ntc(self, arg):
        ''' ph<cr> edit Eh procedure default parameters''' 
        self.procedures['ntc'].cmdloop()

        return False

    def do_do(self, arg):
        ''' ph<cr> edit Eh procedure default parameters''' 
        self.procedures['do'].cmdloop()

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
            #print('unpacking procedure: {}'.format(key))
            
            if key in self.procedures.keys():
                procedure = self.procedures[key]
            else:
                print('unrecognized procedure {}. ignoring'.format(key))
                
            procedure.unpack(template)
            self.procedures[key] = procedure
            
        return

