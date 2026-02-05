import datetime

import shell
import coefficients
import setpoint as sp

class Procedure(shell.Shell):
    intro = 'Generic Procedure Configuration'
    prompt = 'procedure(?): '

    def __init__(self, *kwargs):
        super().__init__(*kwargs)

        self.units = ''
        self.point_count = 2
        self.setpoints = dict()

        self.phorp_address = 'a2'
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
        print('  Units:  {}'.format(self.units))
        print('  Spread: {} point'.format(self.point_count))
        print('   P1:    {} {}'.format(self.p1.value, self.p1.units))
        print('   P2:    {} {}'.format(self.p2.value, self.p2.units))
        if self.point_count == 3:
            print('   P3:   {} {}'.format(self.p3.value, self.p2.units))

        print('  Interval: {} days'.format(self.interval.days))
        print('  Address:  {}'.format(self.phorp_address))
        
        return False
    
    def do_address(self, arg=None):
        ''' address <addr> change address of phorp channel used by procedure'''

        address = arg[0]
        channel = arg[1]
        
        if address in 'abcdefg' and channel in '1234':
            self.phorp_address = address + channel
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
            self.p1.value = float(arg)
        except:
            print(' invalid value: setpoint unchanged.')

        self.do_show()
        
        return False
        
    def do_p2(self, arg):
        ''' p2 <n> The middle or highest value in a two or three point calibration'''
        
        try:
            self.p2.value = float(arg)
        except:
            print(' invalid value: setpoint unchanged.')

        self.do_show()
        
        return False
        
    def do_p3(self, arg):
        ''' p3 <n> The highest value in a three point calibration'''
        
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

        sensor.sensor.name = self.name
        sensor.sensor.raw_units = self.raw_units
        sensor.sensor.units = self.units
        sensor.sensor.coefficients.interval = self.interval
        
        sensor.sensor.connect(self.phorp_address)
        
        return
    
    def run(self, sensor):
        print(' running {} point calibration on sensor {}'.format(self.point_count, sensor.sensor.id))

        ok = True
        for setpoint in sensor.setpoints.values():
            if not setpoint.run(sensor):
                ok = False
                break

        if ok:
            p1 = sensor.setpoints[self.p1.name]
            p2 = sensor.setpoints[self.p2.name]

            if sensor.sensor.coefficients.generate(p1.value,p1.mean, p2.value,p2.mean):
                # prompt here to accept...
                sensor.sensor.coefficients.timestamp = datetime.date.today() #+ duration
            
            #sensor.sensor.coefficients.generate(4.0,0.180, 8.0,-0.061)
            
        sensor.coefficients.dump()

        return

    def pack(self, prefix):
        # Procedure
        package = ''
        package += 'units = "{}"\n'.format(self.units)
        package += 'phorp_address = "{}"\n'.format(self.phorp_address)
        package += 'interval = {}\n'.format(self.interval.days)
        package += 'point_count = {}\n'.format(self.point_count)
        
        my_prefix = '{}.{}'.format(prefix, 'setpoints')
        for setpoint in self.setpoints.values():
            setpoint_prefix = '{}.{}'.format(my_prefix, setpoint.name)
            package += '{}\n'.format(setpoint.pack(setpoint_prefix))
        
        return package

    def unpack(self, package):
        # procedure
        self.units = package['units']
        self.phorp_addr = package['phorp_address']
        self.interval = datetime.timedelta(days=package['interval'])
        self.point_count = package['point_count']

        if 'setpoints' in package:        
            for template in package['setpoints'].values():
                setpoint = sp.Setpoint('','','')
                setpoint.unpack(template)
                self.setpoints[setpoint.name] = setpoint
            
        return
    

class EhProcedure(Procedure):
    intro = 'Eh Procedure Configuration'
    prompt = 'procedure(Eh): '

    def __init__(self, *kwargs):
        super().__init__(*kwargs)

        self.type = 'eh'
        self.name = 'Eh'
        self.raw_units = 'mV'
        self.units = 'mV'

        # the default setpoint settings.
        self.setpoints['p1'] = sp.Setpoint('p1', self.units, 0.0)
        self.setpoints['p2'] = sp.Setpoint('p2', self.units, 225)

        return

    def quality(self, sensor):
        print(' Not implemented ')
            
        return

class PhProcedure(Procedure):
    intro = 'pH Procedure Configuration'
    prompt = 'procedure(pH): '

    def __init__(self, *kwargs):
        super().__init__(*kwargs)

        self.type = 'ph'
        self.name = 'pH'
        self.raw_units = 'mV'
        self.units = 'pH'

        # the default setpoint settings.
        self.setpoints['p1'] = sp.Setpoint('p1', self.units, 4.0)
        self.setpoints['p2'] = sp.Setpoint('p2', self.units, 7.0)
        self.setpoints['p3'] = sp.Setpoint('p3', self.units, 10.0)

        return

    def quality(self, sensor):
        if not  sensor.config.coefficients.is_valid:
            print(' Sensor out of calibration: ')
            
        slope = sensor.config.coefficients.coefficients['slope']
        offset = sensor.config.coefficients.evaluate_x(7.0)
        
        print(' slope = {} mV/unit '.format(round(slope*1000,3)))
        print(' offset = {} mV'.format(round(offset*1000,3)))

        return
    
    
class Procedures(shell.Shell):
    intro = 'Sensor calibration procedures. ? for help.'
    prompt = 'procedures: '

    def __init__(self, *kwargs):
        super().__init__(*kwargs)

        self.procedures = dict()
        self.procedures['ph'] = PhProcedure()
        self.procedures['eh'] = EhProcedure()
        # self.procedures['therm'] = ThermProcedure()

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
            package += '[{}]\n'.format(my_prefix)
            package += '{}\n'.format(procedure.pack(my_prefix))
            
        return package

    def unpack(self, package):
        for key, template in package.items():
            if key == 'ph':
                procedure = PhProcedure()
            elif key == 'eh':
                procedure = EhProcedure()
            else:
                print('unrecognized procedure {}. ignoring'.format(key))
                
            procedure.unpack(template)
            self.procedures[key] = procedure
            
        return

