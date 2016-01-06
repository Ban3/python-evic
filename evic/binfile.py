# -*- coding: utf-8 -*-
"""
Evic is a USB programmer for devices based on the Joyetech Evic VTC Mini.
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


class FirmwareError(Exception):
    """Firmware verification error."""

    pass


class BinFile(object):
    """Firmware binary file class

    Attributes:
        data: A bytearray containing binary data of the firmware.
    """

    def __init__(self, data):
        self.data = bytearray(data)

    @staticmethod
    def _genfun(filesize, index):
        """Generator function for decrypting/encrypting the binary file.

        Args:
            filesize: An integer, filesize of the binary file.
            index: An integer, index of the byte that is being decrypted.
        """

        return filesize + 408376 + index - filesize // 408376

    def convert(self):
        """Decrypts/Encrypts the binary data.

        Returns:
            A Bytearray containing decrypted/encrypted APROM image.
        """

        data = bytearray(len(self.data))
        for i in range(0, len(self.data)):
            data[i] = (self.data[i] ^
                       self._genfun(len(self.data), i)) & 0xFF
        return data

    def verify(self, product_names, hw_version):
        """Verifies the data unencrypted firmware.

        Args:
            product_names: A list of supported product names for the device.
            hw_version: An integer device hardware version.

        Raises:
            FirmwareException: Verification failed.

        """
        if b'Joyetech APROM' not in self.data:
            raise FirmwareError(
                "Firmware manufacturer verification failed.")

        id_ind = 0
        max_hw_version = 0
        for product_name in product_names:
            try:
                id_ind = self.data.index(product_name)
                max_hw_ind = id_ind + len(product_name)
                max_hw_version = (self.data[max_hw_ind] * 100) + \
                    (self.data[max_hw_ind + 1] * 10) + \
                    (self.data[max_hw_ind + 2])
                break
            except ValueError:
                continue
        if id_ind:
            if max_hw_version < hw_version:
                raise FirmwareError(
                    "Firmware hardware version verification failed.")
        else:
            raise FirmwareError("Firmware device name verification failed.")
