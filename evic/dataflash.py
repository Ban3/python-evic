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

from .helpers import cal_checksum


class DataFlashError(Exception):
    """Data flash verification error."""

    pass


class DataFlash(object):
    """Device data flash class.

    Attributes:
        data: A bytearray containing binary data of the data flash.
        device_name: A bytestring containing device name.
        hw_version: An integer hardware version.
        fw_version: An integer firmware version.
        bootflag: 0 or 1. Controls whether APROM or LDROM is booted
                when the device is restarted. TODO: Confirm this.
                0 = LDROM
                1 = APROM
        checksum: A bytearray containing checksum for the data flash.
    """

    def __init__(self, data):
        self.data = bytearray(data)
        self._device_name = bytes(self.data[316:320])
        self._hw_version = struct.unpack("=I", self.data[8:12])[0]
        self._fw_version = struct.unpack("=I", self.data[260:264])[0]
        self._bootflag = self.data[13]
        self._checksum = self.data[0:4]

    @property
    def device_name(self):
        return self._device_name

    @device_name.setter
    def device_name(self, device_name):
        self.device_name = device_name
        self.data[316:320] = bytearray(struct.pack("4s", device_name))
        self.update_checksum()

    @property
    def hw_version(self):
        return self._hw_version

    @hw_version.setter
    def hw_version(self, version):
        self._hw_version = version
        self.data[8:12] = bytearray(struct.pack("=I", version))
        self.update_checksum()

    @property
    def fw_version(self):
        return self._fw_version

    @fw_version.setter
    def fw_version(self, version):
        self._fw_version = version
        self.data[260:264] = bytearray(struct.pack("=I", version))
        self.update_checksum()

    @property
    def bootflag(self):
        return self._bootflag

    @bootflag.setter
    def bootflag(self, flag):
        self._bootflag = flag
        self.data[13] = flag
        self.update_checksum()

    @property
    def checksum(self):
        return self._checksum

    @checksum.setter
    def checksum(self, checksum):
        self._checksum = checksum
        self.data[0:4] = checksum

    def update_checksum(self):
        """Updates the checksum for the data flash data."""

        self.checksum = cal_checksum(self.data[4:])

    def verify(self):
        """Verifies the data flash.

        Raises:
            DataFlashError: Data flash verification failed.
        """

        if cal_checksum(self.data[4:]) != self.checksum \
                or not struct.unpack("=I", self.checksum)[0] \
                | struct.unpack("=I", self.data[268:272])[0]:
            raise DataFlashError("Data flash verification failed")
