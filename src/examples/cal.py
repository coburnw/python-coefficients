import sys
import time

import smbus3 as smbus
import phorp
import frame_streams as fs

import calcrib

class PhorpStream(calcrib.Stream):
    i2c_bus = None
    
    def __init__(self):
        super().__init__(self.__class__.__name__)
        
        self.bus = self.get_i2c_bus()
        self.channel = None
        self.address = None

        self._raw_value = 0
        
        return

    @classmethod
    def get_i2c_bus(cls):
        return cls.i2c_bus
    
    def connect(self, address):
        self.address = address
        
        board = phorp.PhorpX4(self.bus, self.board_index)
        self.channel = board[self.channel_index]
        
        self.channel.sample_rate = 60
        self.channel.pga_gain = 1
        self.channel.continuous = False

        return

    def update(self):
        self.channel.start_conversion()
        time.sleep(self.channel.conversion_time)
        self._raw_value = self.channel.get_conversion_volts()

        return

    def validate_address(self, address):
        board, chan_idx = self.split_address(address)
        
        if board in 'abcdefg' and chan_idx in '1234':
            self.address = board + chan_idx
        else:
            return' invalid address. board_id is a-g, channel_id is 1-4 as in "b3"'

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
        ''' returns the result of the last update() as a float'''
        return self._raw_value * 1000
    
    @property
    def raw_units(self):
        ''' returns a string'''
        return 'mV'
    
    
class ThermistorProcedure(calcrib.ThermistorProcedure):
    intro = 'Thermistor Configuration'
    prompt = 'edit(Therm): '
    
    def __init__(self, streams, *kwargs):
        super().__init__(streams, *kwargs)

        self.stream_type = 'PhorpStream'
        self.stream_address = 'a1'
        
        self.type = 'therm'
        self.name = 'Thermistor'
        self.scaled_units = 'deg C'

        # the default setpoint settings.
        self.parameters['beta'] = calcrib.Constant('beta', 'K', 3574.6)
        self.parameters['r25'] = calcrib.Constant('r25', 'Ohms', 10000)

        return

    def quality(self, sensor):
        print(' Not implemented ')

        return

    
class EhProcedure(calcrib.PolynomialProcedure):
    intro = 'Eh Procedure Configuration'
    prompt = 'edit(Eh): '
    
    def __init__(self, streams, *kwargs):
        super().__init__(streams, *kwargs)
        
        self.stream_type = 'PhorpStream'
        self.stream_address = 'a2'
        
        self.type = 'eh'
        self.name = 'Eh'
        self.units = 'mV'

        # the default setpoint settings.
        self.parameters['p1'] = calcrib.Setpoint('p1', self.units, 0.0)
        self.parameters['p2'] = calcrib.Setpoint('p2', self.units, 225)

        return

    def quality(self, sensor):
        print(' Not implemented ')

        return

    
class PhProcedure(calcrib.PolynomialProcedure):
    intro = 'pH Procedure Configuration'
    prompt = 'edit(pH): '

    def __init__(self, streams, *kwargs):
        super().__init__(streams, *kwargs)

        self.stream_type = 'PhorpStream'
        self.stream_address = 'a2'
        
        self.type = 'ph'
        self.name = 'pH'
        self.scaled_units = 'pH'

        # the default setpoint settings.
        self.parameters['p1'] = calcrib.Setpoint('p1', self.scaled_units, 4.0)
        self.parameters['p2'] = calcrib.Setpoint('p2', self.scaled_units, 7.0)
        self.parameters['p3'] = calcrib.Setpoint('p3', self.scaled_units, 10.0)

        return

    def quality(self, sensor):
        if not  sensor.calibration.is_valid:
            print(' Sensor out of calibration: ')
            return
        
        slope = sensor.calibration.coefficients['slope']
        offset = sensor.calibration.evaluate_x(7.0)

        print(' slope = {} {}/unit '.format(round(slope,3), 'mV'))
        print(' offset = {} {}'.format(round(offset,3), 'mV'))

        return

    
if __name__ == '__main__':

    config = False
    if len(sys.argv) > 1:
        config = True

    with smbus.SMBus(1) as bus:
        streams = dict()
        PhorpStream.i2c_bus = bus
        streams[PhorpStream.__name__] = PhorpStream
    
        if config == True:
            procedures = dict()
            procedures['ph'] = PhProcedure(streams)
            procedures['eh'] = EhProcedure(streams)
            procedures['therm'] = ThermistorProcedure(streams)

            shell = calcrib.Shell(procedures)
            shell.cmdloop()
        else:
            # load toml file, initialize sensors, and run
            project = calcrib.Deploy()
            project.load()
            project.connect(streams)
            while True:
                for sensor in project.sensors.values():
                    sensor.update()
                    val = round(sensor.scaled_value, 1)
                    parm = '{} {} {}, '.format(sensor.name, val, sensor.scaled_units)
                    print(parm, end='')
                    # sys.stdout.flush()
                    time.sleep(0.5)

                print('')
            

    exit()
