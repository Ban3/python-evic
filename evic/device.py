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
from collections import namedtuple

try:
    import hid
    HIDAPI_AVAILABLE = True
except ImportError:
    HIDAPI_AVAILABLE = False

from .dataflash import DataFlash

DeviceInfo = namedtuple('DeviceInfo',
                        'name supported_product_ids logo_dimensions')

class HIDTransfer(object):
    """Generic Nuvoton HID Transfer device class.

    Attributes:
        vid: USB vendor ID.
        pid: USB product ID.
        devices: A dictionary mapping product IDs to DeviceInfo tuples.
        hid_signature: A bytearray containing the HID command signature
                       (4 bytes).
        device: A HIDAPI device.
        manufacturer: A string containing the device manufacturer.
        product: A string containing the product name.
        serial: A string conraining the product serial number.
        ldrom: A Boolean value set to True if the device is booted to LDROM.
    """

    vid = 0x0416
    pid = 0x5020
    devices = {'E043': DeviceInfo("eVic VTwo", None, (64, 40)),
               'E052': DeviceInfo("eVic-VTC Mini", ['W007'], (64, 40)),
               'E056': DeviceInfo("CUBOID MINI", None, (64, 40)),
               'E060': DeviceInfo("Cuboid", None, (64, 40)),
               'E083': DeviceInfo("eGrip II", None, (64, 40)),
               'E092': DeviceInfo("eVic AIO", None, (64, 40)),
               'E115': DeviceInfo("eVic VTwo mini", None, (64, 40)),
               'E150': DeviceInfo("eVic Basic", None, (64, 40)),
               'M011': DeviceInfo("iStick TC100W", None, None),
               'M037': DeviceInfo("ASTER", None, (96, 16)),
               'M041': DeviceInfo("iStick Pico", None, (96, 16)),
               'M045': DeviceInfo("iStick Pico Mega", None, (96, 16)),
               'M046': DeviceInfo("iPower", None, (96, 16)),
               'W007': DeviceInfo("Presa TC75W", ['E052'], None),
               'W010': DeviceInfo("Classic", None, None),
               'W011': DeviceInfo("Lite", None, None),
               'W013': DeviceInfo("Stout", None, None),
               'W014': DeviceInfo("Reuleaux RX200", None, None),
               'W016': DeviceInfo("CENTURION", None, None),
               'W018': DeviceInfo("Reuleaux RX2/3", None, (64, 48)),
               'W026': DeviceInfo("Reuleaux RX75", None, (64, 48)),
               'W033': DeviceInfo("Reuleaux RX200S", None, None)
              }

    # 0x43444948
    hid_signature = bytearray(b'HIDC')

    def __init__(self):
        if HIDAPI_AVAILABLE:
            self.device = hid.device()
        else:
            self.device = None
        self.manufacturer = None
        self.product = None
        self.serial = None
        self.ldrom = False

    @classmethod
    def hidcmd(cls, cmdcode, arg1, arg2):
        """Generates a Nuvoton HID command.

        Args:
            cmdcode: A byte long HID command.
            arg1: First HID command argument.
            arg2: Second HID command argument.

        Returns:
            A bytearray containing the full HID command.
        """

        # Do not count the last 4 bytes (checksum)
        length = bytearray([14])

        # Construct the command
        cmdcode = bytearray(struct.pack('=B', cmdcode))
        arg1 = bytearray(struct.pack('=I', arg1))
        arg2 = bytearray(struct.pack('=I', arg2))
        cmd = cmdcode + length + arg1 + arg2 + cls.hid_signature

        # Return the command with checksum tacked at the end
        return cmd + bytearray(struct.pack('=I', sum(cmd)))

    def connect(self):
        """Connects the USB device.

        Connects the device and saves the USB device info attributes.
        """

        self.device.open(self.vid, self.pid)
        if not self.manufacturer:
            self.manufacturer = self.device.get_manufacturer_string()
            self.product = self.device.get_product_string()
            self.serial = self.device.get_serial_number_string()

    def send_command(self, cmd, arg1, arg2):
        """Sends a HID command to the device.

        Args:
            cmd: Byte long HID command
            arg1: First argument to the command (integer)
            arg2: Second argument to the command (integer)
        """

        command = self.hidcmd(cmd, arg1, arg2)
        self.write(command)

    def read_dataflash(self):
        """Reads the device data flash.

        ldrom attribute will be set to to True if the device is in LDROM.

        Returns:
            A tuple containing the data flash and its checksum.
        """

        start = 0
        end = 2048

        # Send the command for reading the data flash
        self.send_command(0x35, start, end)

        # Read the dataflash
        buf = self.read(end)
        dataflash = DataFlash(buf[4:], 0)

        # Get the checksum from the beginning of the data flash transfer
        checksum = struct.unpack('=I', bytes(buf[0:4]))[0]

        # Are we booted to LDROM?
        self.ldrom = dataflash.ldrom_version or not dataflash.fw_version

        return (dataflash, checksum)

    def write(self, data):
        """Writes data to the device.

        Args:
            data: An iterable containing the binary data.

        Raises:
            IOError: Incorrect amount of bytes was written.
        """

        bytes_written = 0

        # Split the data into 64 byte long chunks
        chunks = [bytearray(data[i:i+64]) for i in range(0, len(data), 64)]

        # Write the chunks to the device
        for chunk in chunks:
            buf = bytearray([0]) + chunk  # First byte is the report number
            bytes_written += self.device.write(buf) - 1

        # Windows always writes full pages
        if bytes_written > len(data):
            bytes_written -= 64 - (len(data) % 64)

        # Raise IOerror if the amount sent doesn't match what we wanted
        if bytes_written != len(data):
            raise IOError("HID Write failed.")

    def read(self, length):
        """Reads data from the device.

        Args:
            length: Amount of bytes to read.

        Returns:
            A bytearray containing the binary data.

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

        # Raise IOerror if the amount read doesn't match what we wanted
        if len(data) != length:
            raise IOError("HID read failed")

        return bytearray(data)

    def write_dataflash(self, dataflash):
        """Writes the data flash to the device.

        Args:
            dataflash: A DataFlash object.
        """

        # We want 2048 bytes
        start = 0
        end = 2048

        # Send the command for writing the data flash
        self.send_command(0x53, start, end)

        # Add checksum of the data in front of it
        buf = bytearray(struct.pack("=I", sum(dataflash.array))) + \
            dataflash.array

        self.write(buf)

    def reset_dataflash(self):
        """Resets the device data flash.

        Sends a data flash reset request to the firmware.
        """

        self.send_command(0x7C, 0, 0)

    def reset(self):
        """Sends the HID command for resetting the system (0xB4)"""

        self.send_command(0xB4, 0, 0)

    def write_flash(self, data, start):
        """Writes data to the flash memory.

        Args:
            start: Start address.
        """

        end = len(data)

        # Send the command for writing the data
        self.send_command(0xC3, start, end)

        self.write(data)

    def write_aprom(self, aprom):
        """Writes the APROM to the device.

        Args:
            aprom: A BinFile object containing an unencrypted APROM image.
        """

        self.write_flash(aprom.data, 0)

    def write_logo(self, logo):
        """Writes the logo to the the device.

        Args:
            logo: A Logo object.
        """

        self.write_flash(logo.array, 102400)
