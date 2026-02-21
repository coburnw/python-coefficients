#
# equation.py - base class for an equation to scale a sensors raw output.
#               part of the python sensor silo project.
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
    
