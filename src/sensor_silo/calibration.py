import datetime

from . import factory

class Calibration():
    def __init__(self, package=None):
        self.timestamp = datetime.date(1970, 1, 1)
        self.interval = datetime.timedelta(days=0)

        self.procedure_type = None
        self.equation = None
        self.parameters = dict()
        
        self.scaled_units = ''

        if package:
            self.unpack(package)

        return

    @property
    def due_date(self):
        if self.interval == 0:
            return 'None Required'
        
        return self.timestamp + self.interval

    @property
    def is_valid(self):
        if self.interval == 0:
            return true
        
        return self.due_date > datetime.date.today()

    def show(self):
        self.dump()
        return
    
    def dump(self):
        print(self.pack('xyz'))
        return
    
    # def generate(self):
    #     raise NotImplemented
    
    def pack(self, prefix):
        package = ''
        package += '[{}]\n'.format(prefix)
        package += 'procedure_type = "{}"\n'.format(self.procedure_type)
        package += 'scaled_units = "{}"\n'.format(self.scaled_units)
        package += 'timestamp = "{}"\n'.format(self.timestamp.isoformat())
        package += 'interval = "{}"\n'.format(self.interval.days)

        if self.equation:
            package += '\n'
            package += self.equation.pack(prefix)
            
        return package
    
    def unpack(self, package):
        self.procedure_type = package['procedure_type'] 
        self.scaled_units = package['scaled_units']
        self.timestamp = datetime.date.fromisoformat(package['timestamp'])
        self.interval = datetime.timedelta(days=int(package['interval']))

        if 'equation' in package:
            section = package['equation']

            # self.equation = factory.EquationFactory().new(section)
            f = factory.EquationFactory()
            self.equation = f.new(section)
            
        return
