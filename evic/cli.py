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


import sys
import struct
import argparse
from time import sleep

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

    parser_decrypt = subparsers.add_parser('decrypt',
                                           help='Decrypt firmware from INPUT \
                                           to OUTPUT.')
    parser_decrypt.add_argument('input', type=argparse.FileType('rb'))
    parser_decrypt.add_argument('--output', '-o', type=argparse.FileType('wb'),
                                required=True)
    parser_decrypt.set_defaults(which='decrypt')

    parser_decrypt = subparsers.add_parser('dump-dataflash',
                                           help='Dump dataflash to OUTPUT')
    parser_decrypt.add_argument('--output', '-o', type=argparse.FileType('wb'),
                                required=True)
    parser_decrypt.set_defaults(which='dump-dataflash')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()
    args = parser.parse_args()

    dev = evic.VTCMini()
    if args.which in ['upload', 'decrypt']:
        binfile = evic.BinFile(args.input.read())

        if args.which == 'decrypt' or not args.unencrypted:
            aprom = evic.BinFile(binfile.decrypt())
        else:
            aprom = binfile

        if args.which == 'decrypt':
            try:
                args.output.write(aprom.data)
            except IOError:
                print("Error: Can't write decrypted file.")
            sys.exit()

    try:
        dev.attach()

        print("\nFound device:")
        print("\tManufacturer: {0}".format(dev.device.manufacturer))
        print("\tProduct: {0}".format(dev.device.product))
        print("\tSerial No: {0}\n".format(dev.device.serial_number))

        print("Reading data flash...\n")
        if args.dataflash:
            dev.get_sys_data(args.dataflash)
        else:
            dev.get_sys_data(None)

        if dev.device_name in DEVICE_NAMES:
            devicename = DEVICE_NAMES[dev.device_name]
        else:
            devicename = "Unknown device"

        print("\tDevice name: {0}".format(devicename))
        print("\tFirmware version: {0:.2f}".format(dev.fw_version))
        print("\tHardware version: {0:.2f}\n".format(dev.hw_version / 100.0))

        if evic.cal_checksum(dev.data_flash[4:]) == dev.df_checksum and \
                dev.df_checksum | struct.unpack("=I",
                                                dev.data_flash[268:268+4])[0]:
            if dev.hw_version > 1000:
                print("Please set the hardware version.\n")

            if struct.unpack("=I", dev.data_flash[264:264+4]) == 0 \
                    or not dev.fw_version:
                print("Reading data flash...\n")
                if not args.dataflash:
                    dev.get_sys_data(None)

            if args.which == 'dump-dataflash':
                try:
                    args.output.write(dev.data_flash)
                except IOError:
                    print("Error: Can't write data flash file.")
                sys.exit()

            # Bootflag
            # 0 = APROM
            # 1 = LDROM
            dev.data_flash[13] = 1

            # Flashing Presa firmware requires HW version 1.03
            if b'W007' in aprom.data and dev.device_name == b'E052' and \
                    dev.hw_version in [106, 108, 109, 111]:
                print("Changing HW version to 1.03..\n")
                new_hw_version = bytearray(struct.pack("=I", 103))
                for i in range(4):
                    dev.data_flash[8+i] = new_hw_version[i]

            # Calculate new checksum
            checksum = bytearray(struct.pack("=I",
                                             evic.cal_checksum(
                                                 dev.data_flash[4:])))
            for i in range(4):
                dev.data_flash[i] = checksum[i]

            print("Writing data flash...\n")
            sleep(2)
            dev.set_sys_data()
            dev.reset_system()
            sleep(2)
            dev.attach()

            try:
                dev.verify_aprom(aprom)
            except evic.FirmwareException as error:
                print(error)
                sys.exit()

            print("Uploading APROM...\n")
            dev.upload_aprom(aprom)
            print("Firmware upload complete!")

    except AssertionError as error:
        print(error)
        sys.exit()
