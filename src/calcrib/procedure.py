import datetime

from . import shell

class ProcedureShell(shell.Shell):
    intro = 'Generic Procedure Configuration'

    def __init__(self, streams, *kwargs):
        super().__init__(*kwargs)

        self.procedure_type = self.__class__.__name__
        
        self.streams = streams
        self.stream_type = None
        self.stream_address = None
        
        self.scaled_units = None
        self.interval = datetime.timedelta(days=180)


        return

    @property
    def prompt(self):
        text = 'edit procedure ({})'.format(self.type)
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
        #sensor.name = self.name
        sensor.name = '{}1'.format(self.type)
        sensor.property = self.property
        
        sensor.calibration.type = self.__class__.__name__
        sensor.calibration.scaled_units = self.scaled_units
        sensor.calibration.interval = self.interval

        sensor.stream_type = self.stream_type        
        stream = self.streams[self.stream_type]() # create a new stream instance

        sensor.connect(stream, self.stream_address) # and override deployed address
        
        return
    
    def run(self, sensor):
        if self.cal(sensor):
            # prompt here to accept...
            pass
        
        # sensor.calibration.show()

        return

    def pack(self, prefix):
        # Procedure
        package = ''
        package += 'procedure_type = "{}"\n'.format(self.procedure_type)
        package += 'units = "{}"\n'.format(self.scaled_units)
        package += 'stream_type = "{}"\n'.format(self.stream_type)
        package += 'stream_address = "{}"\n'.format(self.stream_address)
        package += 'interval = {}\n'.format(self.interval.days)
        
        return package

    def unpack(self, package):
        # procedure
        ### self.procedure_type = package['procedure_type'] dont override our own type
        self.scaled_units = package['units']
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
            print('unpacking procedure: {}'.format(key))
            
            if key in self.procedures.keys():
                procedure = self.procedures[key]
            else:
                print('unrecognized procedure {}. ignoring'.format(key))
                
            procedure.unpack(template)
            self.procedures[key] = procedure
            
        return

