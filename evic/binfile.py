# -*- coding: utf-8 -*-
"""
Evic decrypts Joyetech Evic firmware images and uploads them using USB.
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


class BinFile():
    """Firmware binary file

    Attributes:
        data: binary data of the firmware image

    """
    def __init__(self, data):
        self.data = bytearray(data)

    @staticmethod
    def _genfun(filesize, index):
        """Generator function for decrypting the binary file

        Args:
            filesize: An integer, filesize of the binary file
            index: An integer, index of the byte that is being decrypted

        """
        return filesize + 408376 + index - filesize // 408376

    def decrypt(self):
        """ Decrypts the binary data.

        Returns:
            A Bytearray containing unencrypted APROM image
        """
        data = bytearray(len(self.data))
        for i in range(0, len(self.data)):
            data[i] = (self.data[i] ^
                       self._genfun(len(self.data), i)) & 0xFF
        return data
