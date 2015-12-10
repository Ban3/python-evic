# -*- coding: utf-8 -*-
"""
Evic decrypts/encrypts Joyetech Evic firmware images and uploads them using USB.
Copyright © Jussi Timperi

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__version__ = '0.1.dev0'


from .device import VTCMini
from .helpers import cal_checksum
from .binfile import BinFile, FirmwareException
