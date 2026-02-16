from . import shell

class Quantity():
    def __init__(self, name='name', units='units', value=None, prefix=None):
        self.title = 'empty title'

        self._name = name
        self._units = units
        self._value = value
        self._prefix = prefix
        
        return

    def __str__(self):
        return '{}: {} {}'.format(self.name, self.value, self.units)
    
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        return
    
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        return
    
    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, units):
        self._units = units
        return
        
    @property
    def prefix(self):
        return self._prefix

    @prefix.setter
    def prefix(self, prefix):
        self._prefix = prefix
        return
        
    def clone(self):
        return(Quantity(self._name, self._units, self._value))

    def update(self, source=None): # acquire?
        return
    
    def pack(self, prefix):
        # Constant parameter
        package = ''
        package += '[{}]\n'.format(prefix)
        
        package += 'name = "{}"\n'.format(self._name)
        package += 'value = {}\n'.format(self._value)
        package += 'units = "{}"\n'.format(self._units)
        package += 'prefix = "{}"\n'.format(self._prefix)

        return package

    def unpack(self, package):
        # constant parameter
        self._name = package['name']
        self._value = package['value']
        self._units = package['units']
        self._prefix = package['prefix']

        return

    
class QuantityShell(shell.Shell):
    intro = 'Parameter Configuration'
    prompt = 'quantity: '

    def __init__(self, quantity, *kwargs):
        super().__init__(*kwargs)

        self.quantity = quantity
        self.title = 'empty title'

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
        print('  Name:   {}'.format(self.quantity.name))
        print('  Units:   {}'.format(self.quantity.units))
        print('  Value:   {} {}'.format(self.quantity.value, self.quantity.units))
            
        return False
    
    def do_value(self, arg):
        ''' the first (lowest pH) in a two or three point calibration'''
        self.quantity.value = float(arg)

        self.do_show()
        
        return False

    def dump(self):
        str = '{}'.format(self.quantity)

        return str

