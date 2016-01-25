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


import sys
import struct
from time import sleep
from contextlib import contextmanager

import click

import evic


@contextmanager
def handle_exceptions(*exceptions):
    """Context for handling exceptions."""

    try:
        yield
        click.secho("OK", fg='green', bold=True)
    except exceptions as error:
        click.secho("FAIL", fg='red', bold=True)
        click.echo(str(error), err=True)
        sys.exit(1)


@click.group()
def main():
    """A USB programmer for devices based on the Joyetech Evic VTC Mini."""

    pass


def connect(dev):
    """Connects the USB device.

    Args:
        dev: evic.HIDTransfer object.

    Raises:
        IOerror: The device was not found
    """

    # Connect the device
    with handle_exceptions(IOError):
        click.echo("\nFinding device...", nl=False)
        dev.connect()
        if not dev.manufacturer:
            raise IOError("Device not found.")


def print_usb_info(dev):
    """Prints the USB information attributes of the device

    Args:
        dev: evic.HIDTransfer object
    """

    click.echo("\tManufacturer: ", nl=False)
    click.secho(dev.manufacturer, bold=True)
    click.echo("\tProduct: ", nl=False)
    click.secho(dev.product, bold=True)
    click.echo("\tSerial No: ", nl=False)
    click.secho(dev.serial, bold=True)
    click.echo("")


def read_dataflash(dev, verify):
    """Reads the device data flash.

    Args:
        dev: evic.HIDTransfer object.
        verify: A Boolean set to True to verify the data flash.

    Returns:
        evic.DataFlash object containing the device data flash.
    """

    # Read the data flash
    with handle_exceptions(IOError):
        click.echo("Reading data flash...", nl=False)
        dataflash, checksum = dev.read_dataflash()

    # Verify the data flash
    if verify:
        verify_dataflash(dataflash, checksum)

    return dataflash


def print_device_info(dev, dataflash):
    """Prints the device information found from data flash.

    Args:
        dev: evic.HIDTransfer object.
        dataflash: evic.DataFlash object.
    """

    # Find the product name
    product_name = dev.product_names.get(dataflash.product_id,
                                         "Unknown device")

    # Print out the information
    click.echo("\tDevice name: ", nl=False)
    click.secho(product_name, bold=True)
    click.echo("\tFirmware version: ", nl=False)
    click.secho("{0:.2f}".format(dataflash.fw_version / 100.0), bold=True)
    click.echo("\tHardware version: ", nl=False)
    click.secho("{0:.2f}\n".format(dataflash.hw_version / 100.0), bold=True)

    # Issue a warning about unset hardware version number
    if dataflash.hw_version > 1000:
        click.echo("Please set the hardware version.")


def verify_dataflash(dataflash, checksum):
    """Verifies that the data flash is correct.

    Args:
        data_flash: evic.DataFlash object.
        checksum: Checksum used for the verification.
    """

    with handle_exceptions(evic.DataFlashError):
        click.echo("Verifying data flash...", nl=False)
        dataflash.verify(checksum)


@main.command()
@click.argument('inputfile', type=click.File('rb'))
@click.option('--encrypted/--unencrypted', '-e/-u', default=True,
              help='Use encrypted/unencrypted image. Defaults to encrypted.')
@click.option('--dataflash', 'dataflashfile', '-d', type=click.File('rb'),
              help='Use data flash from a file.')
@click.option('--no-verify', 'noverify',
              type=click.Choice(['aprom', 'dataflash']), multiple=True,
              help='Disable verification for APROM or data flash.')
def upload(inputfile, encrypted, dataflashfile, noverify):
    """Upload an APROM image to the device."""

    dev = evic.HIDTransfer()

    # Connect the device
    connect(dev)

    # Print the USB info of the device
    print_usb_info(dev)

    # Read the data flash
    verify = 'dataflash' not in noverify
    dataflash = read_dataflash(dev, verify)

    # Print the device information
    print_device_info(dev, dataflash)

    # Read the APROM image
    aprom = evic.APROM(inputfile.read())
    if encrypted:
        aprom = evic.APROM(aprom.convert())

    # Verify the APROM image
    if 'aprom' not in noverify:
        with handle_exceptions(evic.APROMError):
            click.echo("Verifying APROM...", nl=False)
            aprom.verify(
                dev.supported_product_ids[dataflash.product_id],
                dataflash.hw_version)

    # Are we using a data flash file?
    if dataflashfile:
        buf = bytearray(dataflashfile.read())
        # We used to store the checksum inside the file
        if len(buf) == 2048:
            checksum = struct.unpack("=I", buf[0:4])[0]
            dataflash = evic.DataFlash(buf[4:], 0)
        else:
            checksum = sum(buf)
            dataflash = evic.DataFlash(buf, 0)
        if 'dataflash' not in noverify:
            verify_dataflash(dataflash, checksum)

    # We want to boot to LDROM on restart
    dataflash.bootflag = 1

    # Flashing Presa firmware requires HW version <=1.03 on type A devices
    if b'W007' in aprom.data and dataflash.product_id == 'E052' \
            and dataflash.hw_version in [106, 108, 109, 111]:
        click.echo("Changing HW version to 1.03...", nl=False)
        dataflash.hw_version = 103
        click.secho("OK", fg='green', bold=True)

    # Write data flash to the device
    with handle_exceptions(IOError):
        click.echo("Writing data flash...", nl=False)
        dev.write_dataflash(dataflash)
        click.secho("OK", fg='green', bold=True)

        # We should only restart if we're not in LDROM
        if not dev.ldrom:
            # Restart
            click.echo("Restarting the device...", nl=False)
            dev.reset()
            sleep(2)
            click.secho("OK", fg='green', nl=False, bold=True)
            # Reconnect
            connect(dev)

        # Write APROM to the device
        click.echo("Writing APROM...", nl=False)
        dev.write_aprom(aprom)


@main.command('dump-dataflash')
@click.option('--output', '-o', type=click.File('wb'))
@click.option('--no-verify', 'noverify', is_flag=True,
              help='Disable verification.')
def dumpdataflash(output, noverify):
    """Write device data flash to a file."""

    dev = evic.HIDTransfer()

    # Connect the device
    connect(dev)

    # Print the USB info of the device
    print_usb_info(dev)

    # Read the data flash
    dataflash = read_dataflash(dev, noverify)

    # Print the device information
    print_device_info(dev, dataflash)

    # Write the data flash to the file
    with handle_exceptions(IOError):
        click.echo("Writing data flash to the file...", nl=False)
        output.write(dataflash.array)


@main.command()
@click.argument('inputfile', type=click.File('rb'))
@click.option('--output', '-o', type=click.File('wb'))
def convert(inputfile, output):
    """Decrypt/encrypt an APROM image."""

    binfile = evic.APROM(inputfile.read())

    with handle_exceptions(IOError):
        click.echo("Writing APROM image...", nl=False)
        output.write(binfile.convert())
