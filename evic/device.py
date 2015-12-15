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

import hid

from .dataflash import DataFlash
from .helpers import cal_checksum

DEVICE_NAMES = {b'E052': "eVic-VTC Mini", b'W007': "Presa TC75W"}


class HIDCmd(object):
    """Nuvoton HID command class.

    Available HID command codes:
        0x35: Read data flash.
        0x53: Write data flash.
        0xB4: Reset device.
        0xC3: Write APROM.

    Attributes:
        cmdcode: A list containing  HID command code (1 byte).
        length: A list containing HID command length,
                not including the checksum  (1 byte).
        arg1: A list containing the first HID command argument (4 bytes).
        arg2: A list containing the second HID command argument (4 bytes).
        signature: A list containing the HID command signature (4 bytes).
        checksum: A list containing the checksum of the HID command.
                  (4 bytes).
        cmd: A list containing the full command (18 bytes).
    """

    signature = [byte for byte in bytearray(struct.pack('=I', 0x43444948))]
    # Do not count the last 4 bytes (checksum)
    length = [14]

    def __init__(self, cmdcode, arg1, arg2):
        self.cmdcode = [byte for byte in bytearray(struct.pack('=B', cmdcode))]
        self.arg1 = [byte for byte in bytearray(struct.pack('=I', arg1))]
        self.arg2 = [byte for byte in bytearray(struct.pack('=I', arg2))]

    @property
    def cmd(self):
        """HID Command

        Returns:
            A list containing the full HID command
        """

        cmd = self.cmdcode + self.length + self.arg1 + self.arg2 + \
            self.signature
        return cmd + [byte for byte in cal_checksum(cmd)]


class VTCMini(object):
    """Evic VTC Mini

    Attributes:
        vid = USB vendor ID as an integer.
        pid = USB product ID as an integer.
        supported_device_names: A list of bytestrings containing the name of
                                the product with compatible firmware
        device: A HIDAPI device for the VTC Mini.
        manufacturer: A string containing the device manufacturer.
        product: A string containing the product name.
        serial: A string conraining the product serial number.
        data_flash: An instance of DataFlash containing the device data flash.
        ldrom: A Boolean value set to True if the device is booted to LDROM.
    """

    vid = 0x0416
    pid = 0x5020
    supported_device_names = [b'E052', b'W007']

    def __init__(self):
        self.device = hid.device()
        self.manufacturer = None
        self.product = None
        self.serial = None
        self.data_flash = None
        self.ldrom = False

    def attach(self):
        """Opens the USB device.

        Opens the device and retrieves the device attributes.
        """

        self.device.open(self.vid, self.pid)
        self.manufacturer = self.device.get_manufacturer_string()
        self.product = self.device.get_product_string()
        self.serial = self.device.get_serial_number_string()

    def get_sys_data(self):
        """Reads the device data flash

        Writes the HID command for reading the data flash
        and retrieves the data flash to the data_flash attribute as an instance
        of DataFlash.
        Sets the ldrom attribute to True if the device is booted to LDROM.
        """

        start = 0
        end = 2048

        read_df = HIDCmd(0x35, start, end)
        self.write(read_df.cmd)

        self.data_flash = DataFlash(self.read(end))

        self.ldrom = self.data_flash.fw_version == 0

    def write(self, data):
        """Writes data to the device.

        Args:
            data: A list containing binary data.

        Raises:
            IOError: Incorrect amount of bytes was written.
        """

        bytes_written = 0
        chunks = [data[i:i+64] for i in range(0, len(data), 64)]
        for chunk in chunks:
            buf = [0] + chunk
            bytes_written += self.device.write(buf) - 1

        if bytes_written != len(data):
            raise IOError("HID Write failed.")

    def read(self, length):
        """Reads data from the device.

        Args:
            length: Amount of bytes bytes to read.

        Returns:
            A list containing binary data.

        Raises:
            IOError: Incorrect amount of bytes was read.
        """

        data = []
        pages, rem = divmod(length, 64)
        for _ in range(0, pages):
            data += self.device.read(64)
        if rem:
            data += self.device.read(rem)

        if len(data) != length:
            raise IOError("HID read failed")

        return data

    def set_sys_data(self, data_flash):
        """Writes the device data flash.

        Writes the HID command for writing the data flash
        and writes the first 2048 bytes from the data_flash argument
        to the device data flash.

        Args:
            data_flash: A DataFlash object.
        """

        start = 0
        end = 2048

        write_df = HIDCmd(0x53, start, end)
        self.write(write_df.cmd)

        self.write(list(data_flash.data))

    def reset_system(self):
        """Sends the HID command for resetting the system (0xB4)

        """
        reset = HIDCmd(0xB4, 0, 0)
        self.write(reset.cmd)

    def upload_aprom(self, aprom):
        """Writes APROM to the the device.

        Args:
            aprom: A BinFile object containing unencrypted APROM image.
        """

        start = 0
        end = len(aprom.data)

        write_aprom = HIDCmd(0xC3, start, end)
        self.write(write_aprom.cmd)

        self.write(list(aprom.data))
