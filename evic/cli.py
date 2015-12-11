# -*- coding: utf-8 -*-
"""
Evic decrypts/encryps Joyetech Evic firmware images and uploads them using USB.
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


import sys
import struct
import argparse
from time import sleep
from array import array

import usb.core

import evic

DEVICE_NAMES = {b'E052': "eVic-VTC Mini", b'W007': "Presa TC75W"}


def main():
    """Console application's main entry point"""

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_upload = subparsers.add_parser('upload',
                                          help='Write firmware from INPUT \
                                          into device.')
    parser_upload.add_argument('input', type=argparse.FileType('rb'))
    parser_upload.add_argument('--unencrypted', '-u', action='store_true',
                               help='Use unencrypted firmware image.')
    parser_upload.add_argument('--dataflash', '-d',
                               type=argparse.FileType('rb'),
                               help='Use data flash file insted the one on \
                               the device')
    parser_upload.set_defaults(which='upload')

    parser_convert = subparsers.add_parser('convert',
                                           help='Decrypt/Encrypt firmware \
                                           from INPUT to OUTPUT.')
    parser_convert.add_argument('input', type=argparse.FileType('rb'))
    parser_convert.add_argument('--output', '-o', type=argparse.FileType('wb'),
                                required=True)
    parser_convert.set_defaults(which='convert')

    parser_dumpdataflash = subparsers.add_parser('dump-dataflash',
                                                 help='Dump dataflash \
                                                 to OUTPUT')
    parser_dumpdataflash.add_argument('--output', '-o',
                                      type=argparse.FileType('wb'),
                                      required=True)
    parser_dumpdataflash.set_defaults(which='dump-dataflash')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()
    args = parser.parse_args()

    dev = evic.VTCMini()
    if args.which in ['upload', 'convert']:
        binfile = evic.BinFile(args.input.read())

        if args.which == 'convert' or not args.unencrypted:
            aprom = evic.BinFile(binfile.convert())
        else:
            aprom = binfile

        if args.which == 'convert':
            try:
                args.output.write(aprom.data)
            except IOError:
                print("Error: Can't write converted file.")
            sys.exit()

    try:
        dev.attach()

        print("\nFound device:")
        print("\tManufacturer: {0}".format(dev.device.manufacturer))
        print("\tProduct: {0}".format(dev.device.product))
        print("\tSerial No: {0}\n".format(dev.device.serial_number))

        if args.which == 'upload':
            try:
                aprom.verify(dev.supported_device_names)
            except evic.FirmwareException as error:
                print(error)
                sys.exit()

        print("Reading data flash...\n")
        data_flash = evic.DataFlash(dev.get_sys_data())
        ldrom = data_flash.fw_version == 0

        if args.which == 'upload' and args.dataflash:
            df_file = array('B')
            df_file.fromfile(args.dataflash, 2048)
            data_flash = evic.DataFlash(df_file)

        if data_flash.device_name in DEVICE_NAMES:
            devicename = DEVICE_NAMES[data_flash.device_name]
        else:
            devicename = "Unknown device"

        print("\tDevice name: {0}".format(devicename))
        print("\tFirmware version: {0:.2f}".format(data_flash.fw_version))
        print("\tHardware version: {0:.2f}\n".format(
            data_flash.hw_version / 100.0))

        if evic.cal_checksum(data_flash.data[4:]) == data_flash.checksum \
                and data_flash.checksum \
                | struct.unpack("=I", data_flash.data[268:268+4])[0]:
            if data_flash.hw_version > 1000:
                print("Please set the hardware version.\n")

            if struct.unpack("=I", data_flash.data[264:264+4]) == 0 \
                    or not data_flash.fw_version:
                if args.which == 'upload' and not args.dataflash:
                    print("Reading data flash...\n")
                    data_flash = evic.DataFlash(dev.get_sys_data())

            if args.which == 'dump-dataflash':
                try:
                    print("Writing data flash to the file...\n")
                    args.output.write(data_flash.data)
                except IOError:
                    print("Error: Can't write data flash file.")
                sys.exit()

            new_df = data_flash.data
            # Bootflag?
            # 0 = APROM
            # 1 = LDROm
            new_df[13] = 1

            # Flashing Presa firmware requires HW version 1.03
            if b'W007' in aprom.data and data_flash.device_name == b'E052' \
                    and data_flash.hw_version in [106, 108, 109, 111]:
                print("Changing HW version to 1.03...\n")
                new_hw_version = bytearray(struct.pack("=I", 103))
                for i in range(4):
                    new_df[8+i] = new_hw_version[i]

            # Calculate new checksum
            checksum = bytearray(struct.pack("=I",
                                             evic.cal_checksum(new_df[4:])))
            for i in range(4):
                new_df[i] = checksum[i]

            data_flash = evic.DataFlash(new_df)

            print("Writing data flash...\n")
            sleep(2)
            dev.set_sys_data(data_flash)
            if not ldrom:
                print("Restarting the device...\n")
                try:
                    dev.reset_system()
                except usb.core.USBError:
                    print("Restart failed. Assuming the device is already \
                          restarted to LDROM\n")
                sleep(2)
                print("Reconnecting the device...\n")
                dev.attach()

            print("Uploading APROM...\n")
            dev.upload_aprom(aprom)
            print("Firmware upload complete!")

    except AssertionError as error:
        print(error)
        sys.exit()
