from . import shell

class Parameter():
    def __init__(self):
        pass

    @property
    def type(self):
        return self.__class__.__name__
    
class ParameterShell(shell.Shell):
    intro = 'Parameter Configuration'
    prompt = 'parameter: '

    def __init__(self, name, units, value, *kwargs):
        super().__init__(*kwargs)

        self.title = 'empty title'
        self.name = name
        
        self.scaled_units = units
        self.scaled_value = value

        return

    @property
    def intro(self):
        return self.title

    @property
    def prompt(self):
        return self.prompt
    
    def do_show(self, arg=None):
        ''' print present values'''
        print(' Calibration Point')
        print('  Units:   {}'.format(self.scaled_units))
        print('  Value:   {} {}'.format(self.scaled_value, self.scaled_units))
            
        return False
    
    def do_value(self, arg):
        ''' the first (lowest pH) in a two or three point calibration'''
        self.scaled_value = float(arg)

        self.do_show()
        
        return False

    def clone(self):
        return(ParameterShell(self.name, self.scaled_units, self.scaled_value))

    def dump(self):
        str = '{}: {}{}'.format(self.name, self.scaled_value, self.scaled_units)

        return str
    
    def run(self, sensor):
        print('parameter.run(): nothing to run')
        return

    def pack(self, prefix):
        # Constant parameter
        package = ''
        package += '[{}]\n'.format(prefix)
        
        package += 'name = "{}"\n'.format(self.name)
        package += 'scaled_units = "{}"\n'.format(self.scaled_units)
        package += 'scaled_value = {}\n'.format(self.scaled_value)

        return package

    def unpack(self, package):
        # constant parameter
        self.name = package['name']
        self.scaled_units = package['scaled_units']
        self.scaled_value = package['scaled_value']

        return


class xConstantQuantity(ParameterShell):
    def __init__(self, name, units, value, *kwargs):
        super().__init__(name, units, value, *kwargs)

        self.title = 'Constant Parameter'
        
        return
    
    def clone(self):
        return(Constant(self.name, self.scaled_units, self.scaled_value))

    
