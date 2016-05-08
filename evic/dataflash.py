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

import binstruct


class DataFlashError(Exception):
    """Data flash verification error."""

    pass


class DataFlash(binstruct.StructTemplate):
    """Device data flash class.

    Attributes:
        hw_version: An integer hardware version number.
        bootflag: 0 or 1. Controls whether APROM or LDROM is booted
                  when the device is restarted.
                    0 = APROM
                    1 = LDROM
        product_id: Product ID string.
        fw_version: An integer firmware version number.
        unknown1: TODO
        unknown2: TODO
    """

    hw_version = binstruct.Int32Field(4)
    bootflag = binstruct.Int8Field(9)
    product_id = binstruct.StringField(312, 4)
    fw_version = binstruct.Int32Field(256)
    ldrom_version = binstruct.Int32Field(260)

    def verify(self, checksum):
        """Verifies the data flash against given checksum.

        Args:
            checksum: Checksum of the data.

        Raises:
            DataFlashError: Data flash verification failed.
        """

        if sum(self.array) != checksum:
            raise DataFlashError("Data flash verification failed.")
