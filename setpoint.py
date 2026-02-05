import sys
import time

import shell
import statistics as rs
    
class Setpoint(shell.Shell):
    intro = 'Calibration Setpoint Configuration'
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
        return(Setpoint(self.name, self.units, self.value))

    def dump(self):
        str = '{}{}: n={}, mean={}, var={}, sd={}'.format(self.value, self.units, self.n, self.mean, self.variance, self.standard_deviation)

        return str
    
    def run(self, sensor):
        # setpoint run
        prompt = '  ready {} {} Calibration Solution. press <space> to begin, other to cancel'.format(self.units, self.value)
        print(prompt)
        key = self.get_char()
        
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
            key = self.get_char()
        
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

    
