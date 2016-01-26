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

import struct


class APROMError(Exception):
    """APROM verification error."""

    pass


class APROM(object):
    """APROM file class

    Attributes:
        data: A bytearray containing the binary data of the firmware.
    """

    def __init__(self, data):
        self.data = bytearray(data)

    @staticmethod
    def _genfun(filesize, index):
        """Generator function for decrypting/encrypting the binary file.

        Args:
            filesize: Filesize of the APROM file in bytes.
            index: Index of the byte being converted.
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

    def verify(self, product_ids, hw_version):
        """Verifies the contained data.

        Data needs to be unencrypted.

        Args:
            product_names: A list of supported product names for the device.
            hw_version: An integer device hardware version.

        Raises:
            FirmwareException: Verification failed.

        """

        # Does the APROM contain the string "Joyetech APROM"?
        if b'Joyetech APROM' not in self.data:
            raise APROMError("Firmware manufacturer verification failed.")

        id_ind = 0
        max_hw_version = 0
        # Try to locate supported product IDs
        for product_id in product_ids:
            try:
                product_id = product_id.encode()
                id_ind = self.data.index(product_id)
                # Maximum hardware version follows the product ID
                max_hw_ind = id_ind + len(product_id)
                max_hw_version = struct.unpack("=I", bytes(b'\x00' +
                                                           self.data[max_hw_ind:max_hw_ind+3]))[0]
                break
            # Product ID was not found, try the next one
            except ValueError:
                continue

        # Raise an error if none of the supported product IDs were found
        if not id_ind:
            raise APROMError("Firmware device name verification failed.")

        # Raise an error if the maximum supported hardware version is less than
        # the supplied hardware version
        if max_hw_version < hw_version:
            raise APROMError("Firmware hardware version verification failed.")
