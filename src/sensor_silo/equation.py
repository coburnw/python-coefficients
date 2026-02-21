
class Equation():
    def __init__(self):
        self.package_prefix = ''
        return

    @property
    def type(self):
        return self.__class__.__name__
    
    def dump(self):
        print(self.pack('me'))
        return

    def pack(self, prefix):
        self.package_prefix = '{}.{}'.format(prefix, 'equation')
        
        package = '[{}]\n'.format(self.package_prefix)
        package += 'type = "{}"\n'.format(self.type)

        return package

    def unpack(self, package):
        # nothing for us to unpack?
        return
    
