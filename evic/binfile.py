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


class FirmwareException(Exception):
    """Exception for firmware verification"""

    pass


class BinFile(object):
    """Firmware binary file

    Attributes:
        data: binary data of the firmware image

    """
    def __init__(self, data):
        self.data = bytearray(data)

    @staticmethod
    def _genfun(filesize, index):
        """Generator function for decrypting/encrypting the binary file

        Args:
            filesize: An integer, filesize of the binary file
            index: An integer, index of the byte that is being decrypted

        """
        return filesize + 408376 + index - filesize // 408376

    def convert(self):
        """ Decrypts/Encrypts the binary data.

        Returns:
            A Bytearray containing decrypted/encrypted APROM image
        """
        data = bytearray(len(self.data))
        for i in range(0, len(self.data)):
            data[i] = (self.data[i] ^
                       self._genfun(len(self.data), i)) & 0xFF
        return data

    def verify(self, product_names):
        """Verifies that the unencrypted APROM is correct

        Args:
            product_names: A list of supported product names for the device

        Raises:
            FirmwareException: Verification failed.

        """
        if b'Joyetech APROM' not in self.data:
            raise FirmwareException(
                "Firmware manufacturer verification failed")
        for name in product_names:
            if name in self.data:
                return
        raise FirmwareException("Firmware device name verification failed")
