#!/usr/bin/env python
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


def main():
    parser = argparse.ArgumentParser(description='evic')
    subparsers = parser.add_subparsers()

    parser_upload = subparsers.add_parser('upload',
                                          help='Write firmware from INPUT into device.')
    parser_upload.add_argument('input', type=argparse.FileType('rb'))
    parser_upload.set_defaults(which='upload')

    parser_decrypt = subparsers.add_parser('decrypt',
                                           help='Decrypt firmware from INPUT to OUTPUT.')
    parser_decrypt.add_argument('input', type=argparse.FileType('rb'))
    parser_decrypt.add_argument('--output', '-o', type=argparse.FileType('wb'),
                                required=True)
    parser_decrypt.set_defaults(which='decrypt')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()
    args = parser.parse_args()

    dev = evic.VTCMini()
    dev.read_binfile(args.input)
    dev.decrypt()

    if args.which == 'decrypt':
        try:
            args.output.write(dev.aprom)
        except IOError:
            print("Error: Can't write decrypted file.")
        sys.exit()

    try:
        dev.attach()

        print("\nFound device:")
        print("\tManufacturer: %s" % dev.device.manufacturer)
        print("\tProduct: %s" % dev.device.product)
        print("\tSerial No: %s\n" % dev.device.serial_number)

        print("Reading data flash...\n")
        dev.get_sys_data()

        if dev.device_name.tostring() == b'E052':
            devicename = "eVic-VTC Mini"
        else:
            devicename = "Unknown device"

        print("\tDevice name: %s" % devicename)
        print("\tFirmware version: %.2f" % dev.fw_version)
        print("\tHardware version: %.2f\n" % dev.hw_version)

        if evic.cal_checksum(dev.data_flash[4:]) == dev.df_checksum:
            if dev.df_checksum | struct.unpack("=I",
                                               dev.data_flash[268:268+4])[0]:
                if dev.hw_version > 1000:
                    print("Please set the hardware version.\n")

                if struct.unpack("=I", dev.data_flash[264:264+4]) == 0 or not dev.fw_version:
                    print("Reading data flash...\n")
                    dev.get_sys_data()

                dev.data_flash[13] = 1
                # Update checksum
                checksum = struct.pack("=I",
                                       evic.cal_checksum(dev.data_flash[4:]))
                for i in range(4):
                    dev.data_flash[i] = checksum[i]
                print("Writing data flash...\n")
                sleep(2)
                dev.set_sys_data()
                dev.reset_system()
                sleep(2)
                dev.attach()

                dev.verify_aprom()

                print("Uploading APROM...\n")
                dev.upload_aprom()
                print("Firmware upload complete!")

    except AssertionError as e:
        print(e)
        sys.exit()
