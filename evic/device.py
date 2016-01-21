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


class HIDTransfer(object):
    """Generic Nuvoton HID Transfer device

    Attributes:
        vid: USB vendor ID as an integer.
        pid: USB product ID as an integer.
        device_names: A dictionary mapping product IDs to device name bytestrings.
        supported_device_names: A dictionary mapping device name to a list of
                                bytestrings containing the names of
                                the products with compatible firmware
        hid_signature: A list containing the HID command signature (4 bytes).
        device: A HIDAPI device for the VTC Mini.
        manufacturer: A string containing the device manufacturer.
        product: A string containing the product name.
        serial: A string conraining the product serial number.
        data_flash: An instance of DataFlash containing the device data flash.
        ldrom: A Boolean value set to True if the device is booted to LDROM.
    """

    vid = 0x0416
    pid = 0x5020
    device_names = {b'E052': "eVic-VTC Mini",
                    b'E060': "Cuboid",
                    b'W007': "Presa TC75W",
                    b'W010': "Classic",
                    b'W011': "Lite",
                    b'W013': "Stout",
                    b'W014': "Reuleaux RX200"}
    supported_device_names = {b'E052': [b'E052', b'W007'],
                              b'E060': [b'E060'],
                              b'W007': [b'W007'],
                              b'W010': [b'W010'],
                              b'W011': [b'W011'],
                              b'W013': [b'W013'],
                              b'W014': [b'W014']}
    # 0x43444948
    hid_signature = [0x48, 0x49, 0x44, 0x43]

    def __init__(self):
        self.device = hid.device()
        self.manufacturer = None
        self.product = None
        self.serial = None
        self.data_flash = None
        self.ldrom = False

    @classmethod
    def hidcmd(cls, cmdcode, arg1, arg2):
        """Generates a Nuvoton HID command.

        Args:
            cmdcode: The hid command as a single byte.
            arg1:    First HID command argument.
            arg2:    Second HID command argument.

        Returns:
            A list containing the full HID command.
        """

        # Do not count the last 4 bytes (checksum)
        length = [14]

        cmdcode = [byte for byte in bytearray(struct.pack('=B', cmdcode))]
        arg1 = [byte for byte in bytearray(struct.pack('=I', arg1))]
        arg2 = [byte for byte in bytearray(struct.pack('=I', arg2))]
        cmd = cmdcode + length + arg1 + arg2 + cls.hid_signature
        return cmd + [byte for byte in cal_checksum(cmd)]

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

        read_df = self.hidcmd(0x35, start, end)
        self.write(read_df)

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

        # Windows always writes full pages
        if bytes_written > len(data):
            bytes_written -= 64 - (len(data) % 64)

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

        # Windows always reads full pages
        if len(data) > length:
            data = data[:length]

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

        write_df = self.hidcmd(0x53, start, end)
        self.write(write_df)

        self.write(list(data_flash.data))

    def reset_system(self):
        """Sends the HID command for resetting the system (0xB4)

        """
        reset = self.hidcmd(0xB4, 0, 0)
        self.write(reset)

    def upload_aprom(self, aprom):
        """Writes APROM to the the device.

        Args:
            aprom: A BinFile object containing unencrypted APROM image.
        """

        start = 0
        end = len(aprom.data)

        write_aprom = self.hidcmd(0xC3, start, end)
        self.write(write_aprom)

        self.write(list(aprom.data))
