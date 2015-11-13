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

import struct

import usb.core
import usb.util

from .helpers import cal_checksum


class Cmd():
    """Nuvoton HID command class

    Available HID command codes:
        0x35: Read data flash.
        0x53: Write data flash.
        0x83: Reset device.
        0xC3: Write APROM.

    Attributes:
        cmd: A bytes object for HID command code (1 byte)
        length: A bytes object for HID command length (1 byte)
        arg1: A bytes object for the first HID command argument (4 bytes)
        arg2: A bytes object for the second HID command argument (4 bytes)
        signature: A bytes object for HID command signature (4 bytes)
        checksum: A bytes object for the checksum of the HID command (4 bytes)
        fullcmd: A bytes object for the full command (18 bytes)
    """

    signature = struct.pack('=I', 0x43444948)
    length = struct.pack('=B', 14)  # Do not count the last 4 bytes (checksum)

    def __init__(self, cmd, arg1, arg2):
        self.cmd = struct.pack('=B', cmd)
        self.arg1 = struct.pack('=I', arg1)
        self.arg2 = struct.pack('=I', arg2)
        self.fullcmd = self.cmd + self.length + self.arg1 + self.arg2 +\
            self.signature
        self.checksum = struct.pack('=I', cal_checksum(self.fullcmd))
        self.fullcmd += self.checksum


class VTCMini():
    """Evic VTC Mini

    Attributes:
        vid = USB vendor ID as an integer.
        pid = USB product ID as an integer.
        binfile: Encrypted firmware file in a bytearray.
        aprom: Unencrypted firmware file in a bytearray.
        device: PyUSB device for the VTC Mini.
        data_flash: An array of bytes.
        device_name: An array containing device name.
        df_checksum: An integer checksum for data flash.
        hw_version: A float hardware version.
        fw_version: A float firmware version.

    """

    vid = 0x0416
    pid = 0x5020

    def __init__(self):
        self.binfile = None
        self.aprom = None
        self.device = None
        self.data_flash = None
        self.device_name = None
        self.df_checksum = None
        self.hw_version = None
        self.fw_version = None

    def read_binfile(self, binfile):
        """Reads an encrypted binary file to the attribute binfile

        Args:
            binfile: binary file object
        """
        self.binfile = binfile.read()

    def _genfun(self, filesize, index):
        """Generator function for decrypting the binary file

        Args:
            filesize: An integer, filesize of the binary file
            index: An integer, index of the byte that is being decrypted

        """
        return filesize + 408376 + index - filesize // 408376

    def decrypt(self):
        """ Decrypts the binary file into the attribute aprom.
        """
        self.aprom = bytearray(len(self.binfile))
        for i in range(0, len(self.binfile)):
            self.aprom[i] = (self.binfile[i] ^
                             self._genfun(len(self.binfile), i)) & 0xFF

    def attach(self):
        """Detaches kernel drivers from the device and claims it

        Raises:
            AssertionError: If device could not be opened.

        """
        self.device = usb.core.find(idVendor=self.vid, idProduct=self.pid)
        assert self.device, "Device not found"
        if self.device.is_kernel_driver_active(0):
            self.device.detach_kernel_driver(0)
            self.device.set_configuration()
            usb.util.claim_interface(self.device, 0)

    def send_cmd(self, cmd):
        """Sends a HID command

        Writes a HID command to the device.

        Args:
            cmd: A bytes object for the HID command in the form of
             Cmd.fullcommand

        Returns:
            An integer count of bytes written to the device
        """
        return self.device.write(0x2, cmd, 1000)

    def get_sys_data(self):
        """Sends the HID command for reading data flash (0x35)

        Writes the HID command to the device and reads 2048 bytes to the
        data_flash attribute. Sets relevant attributes from data flash.

        Raises:
            AssertionError: Correct amount of bytes was not written to the
             device. (18 bytes)
        """

        start = 0
        end = 2048

        cmd = Cmd(0x35, start, end)
        assert self.send_cmd(cmd.fullcmd) == 18,\
            "Error: Sending read data flash command failed."

        self.data_flash = self.read_data(end)

        self.device_name = self.data_flash[316:316+4]
        self.hw_version = struct.unpack("=I", self.data_flash[8:8+4])[0] / 100
        self.fw_version = struct.unpack("=I",
                                        self.data_flash[260:260+4])[0] / 100
        self.df_checksum = struct.unpack("=I", self.data_flash[0:4])[0]

    def read_data(self, count):
        """Reads data from the device

        Args:
            count: An integer, count of bytes to read.

        Returns:
            An array object of the data read.

        Raises:
            AssertionError: Incorrect amount of bytes was read.
        """
        data = self.device.read(0x81, count)
        assert len(data) == count, 'Error: Read failed'
        return data

    def set_sys_data(self):
        """Sends the HID command for writing data flash (0x53)

        Writes the HID command to the device and writes 2048 bytes from
        data_flash attribute to the device data flash.

        Raises:
            AssertionError: Incorrect amount of bytes was written.

        """

        start = 0
        end = 2048

        cmd = Cmd(0x53, start, end)

        assert self.send_cmd(cmd.fullcmd) == 18,\
            "Error: Sending write data flash command failed."

        assert self.device.write(0x2, self.data_flash, 100000) == 2048,\
            "Error: Writing data flash failed"

    def reset_system(self):
        """Sends the HID command for reseting the system (0xB4)

        """
        cmd = Cmd(0xB4, 0, 0)

        assert self.send_cmd(cmd.fullcmd) == 18,\
            "Error: Sending reset command failed."

    def verify_aprom(self):
        """Verifies that the unencrypted APROM is correct

        Raises:
            AssertionError: Verification failed.

        """
        assert b'Joyetech APROM' in self.aprom,\
            "Firmware manufacturer verification failed"
        assert bytearray(self.device_name) in self.aprom,\
            "Firmware device name verification failed"

    def upload_aprom(self):
        """Writes APROM to the the device.

        Raises:
            AssertionError: Incorrect amount of bytes was written.

        """
        start = 0
        end = len(self.aprom)

        cmd = Cmd(0xC3, start, end)
        assert self.send_cmd(cmd.fullcmd) == 18,\
            "Error: Sending write APROM command failed."

        assert self.device.write(0x2, self.aprom, 1000000) == len(self.aprom),\
            "Error: APROM write failed"
