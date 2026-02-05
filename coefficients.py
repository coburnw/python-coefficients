import datetime

#import tomli

class Coefficients():
    def __init__(self):

        self.degree = 1
        self.coefficients = dict()
        self.coefficients['slope'] = 1.0
        self.coefficients['offset'] = 0.0
 
        self.timestamp = datetime.date(1970, 1, 1)
        self.interval = datetime.timedelta(days=0)

        return

    def __len__(self):
        return len(self.coefficients)

    @property
    def due_date(self):
        return self.timestamp + self.interval

    @property
    def is_valid(self):
        return self.due_date > datetime.date.today()
    
    def generate(self, x1,y1, x2,y2):
        self.timestamp = datetime.date(1970, 1, 1)

        is_valid = False
        try:
            self.coefficients['slope'] = (y2 - y1) / (x2 - x1)
            self.coefficients['offset'] = y1 - self.coefficients['slope'] * x1
            
            is_valid = True
        except ZeroDivisionError:
            self.coefficients['slope'] = 0.00001
            self.coefficients['offset'] = 0.0
            
        return is_valid

    def evaluate_x(self, x_value):
        y = self.coefficients['slope'] * x_value + self.coefficients['offset']
        
        return y

    def evaluate_y(self, y_value):
        slope = self.coefficients['slope']
        if slope == 0:
            slope = 0.00001
            
        x = (y_value - self.coefficients['offset']) / slope
        
        return x
    
    def dump(self):
        for key, value in self.coefficients.items():
            print(key, value)

        return
    
    def pack(self, prefix):
        package = '[{}]\n'.format(prefix)
        package += 'degree = {}\n'.format(self.degree)
        package += 'timestamp = "{}"\n'.format(self.timestamp.isoformat())
        package += 'interval = "{}"\n'.format(self.interval.days)
        
        package += '[{}.{}]\n'.format(prefix, 'coefficients')
        for key, value in self.coefficients.items():
            package += '{} = {}\n'.format(key, value)

        return package

    def unpack(self, package):
        print('  loading coefficients')
        self.degree = package['degree']
        self.timestamp = datetime.date.fromisoformat(package['timestamp'])
        self.interval = datetime.timedelta(days=int(package['interval']))
        
        for name, value in  package['coefficients'].items():
            self.coefficients[name] = value
        
        return
    
