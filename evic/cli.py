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

import click

import evic


class Context(object):
    """Click context.

    Attributes:
        device_names: A dictionary mapping of device names.
        dev: An instance of evic.VTCMini.
    """

    def __init__(self):
        self.dev = evic.VTCMini()

pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group()
def main():
    """A USB programmer for devices based on the Joyetech Evic VTC Mini."""

    pass


def attach(dev):
    """Attaches the USB device.

    Attaches the device and prints the device information to the screen.

    Args:
        dev: An instance of the device.
    """

    try:
        dev.attach()
        click.echo("\nFound device:")
        click.echo("\tManufacturer: ", nl=False)
        click.secho(dev.manufacturer, bold=True)
        click.echo("\tProduct: ", nl=False)
        click.secho(dev.product, bold=True)
        click.echo("\tSerial No: ", nl=False)
        click.secho(dev.serial, bold=True)
        click.echo("")
    except IOError as error:
        click.echo("Device not found: " + str(error))
        sys.exit(1)


def read_data_flash(dev):
    """Reads the data flash from the device.

    Reads the data flash from the device and verifies it.

    Args:
        dev: An instance of the attached device.
    """

    try:
        click.echo("Reading data flash...", nl=False)
        dev.get_sys_data()
        if struct.unpack("=I", dev.data_flash.data[264:268])[0] \
                or not dev.data_flash.fw_version:
            dev.get_sys_data()
        click.secho("OK", fg='green', bold=True)
        click.echo("Verifying data flash...", nl=False)
        dev.data_flash.verify()
        click.secho("OK", fg='green', bold=True)

        if dev.data_flash.device_name in evic.DEVICE_NAMES:
            devicename = evic.DEVICE_NAMES[dev.data_flash.device_name]
        else:
            devicename = "Unknown device"

        click.echo("\n\tDevice name: ", nl=False)
        click.secho(devicename, bold=True)
        click.echo("\tFirmware version: ", nl=False)
        click.secho("{0:.2f}".format(
            dev.data_flash.fw_version / 100.0), bold=True)
        click.echo("\tHardware version: ", nl=False)
        click.secho("{0:.2f}\n".format(
            dev.data_flash.hw_version / 100.0), bold=True)

        if dev.data_flash.hw_version > 1000:
            click.echo("Please set the hardware version.")

    except (IOError, evic.DataFlashError) as error:
        click.secho("FAIL", fg='red', bold=True)
        click.echo(error)
        sys.exit(1)


@main.command()
@click.argument('input', type=click.File('rb'))
@click.option('--unencrypted/--encrypted', '-u/-e', default=False,
              help='Use unencrypted/encrypted image. Defaults to encrypted.')
@click.option('--dataflash', '-d', type=click.File('rb'),
              help='Use data flash from a file.')
@pass_context
def upload(ctx, input, unencrypted, dataflash):
    """Upload an APROM image to the device."""

    attach(ctx.dev)
    read_data_flash(ctx.dev)

    binfile = evic.BinFile(input.read())
    if unencrypted:
        aprom = binfile
    else:
        aprom = evic.BinFile(binfile.convert())

    try:
        click.echo("Verifying APROM...", nl=False)
        aprom.verify(ctx.dev.supported_device_names)
        click.secho("OK", fg='green', bold=True)
    except evic.FirmwareError as error:
        click.secho("FAIL", fg='red', bold=True)
        click.echo(error)
        sys.exit(1)

    if dataflash:
        data_flash_file = evic.DataFlash(dataflash.read())
        try:
            click.echo("Verifying data flash file...", nl=False)
            data_flash_file.verify()
            click.secho("OK", fg='green', bold=True)
            data_flash = data_flash_file
        except evic.DataFlashError as error:
            click.secho("FAIL", fg='red', bold=True)
            click.echo(error)
            sys.exit(1)
    else:
        data_flash = ctx.dev.data_flash

    data_flash.bootflag = 1

    # Flashing Presa firmware requires HW version <=1.03 on type A devices
    if b'W007' in aprom.data and data_flash.device_name == b'E052' \
            and data_flash.hw_version in [106, 108, 109, 111]:
        click.echo("Changing HW version to 1.03...", nl=False)
        data_flash.hw_version = 103
        click.secho("OK", fg='green', bold=True)

    click.echo("Writing data flash...", nl=False)
    ctx.dev.set_sys_data(data_flash)
    click.secho("OK", fg='green', bold=True)
    if not ctx.dev.ldrom:
        click.echo("Restarting the device...", nl=False)
        ctx.dev.reset_system()
        sleep(2)
        click.secho("OK", fg='green', bold=True)
        click.echo("Reconnecting the device...", nl=False)
        ctx.dev.attach()
        click.secho("OK", fg='green', bold=True)

    click.echo("Writing APROM...", nl=False)
    ctx.dev.upload_aprom(aprom)
    click.secho("OK", fg='green', bold=True)


@main.command('dump-dataflash')
@click.option('--output', '-o', type=click.File('wb'))
@pass_context
def dumpdataflash(ctx, output):
    """Write device data flash to a file."""

    attach(ctx.dev)
    read_data_flash(ctx.dev)

    try:
        click.echo("Writing data flash to the file...", nl=False)
        output.write(ctx.dev.data_flash.data)
        click.secho("OK", fg='green', bold=True)
    except IOError as error:
        click.secho("FAIL", fg='red', bold=True)
        click.echo("Error: Can't write data flash file: " + str(error))
        sys.exit(1)


@main.command()
@click.argument('input', type=click.File('rb'))
@click.option('--output', '-o', type=click.File('wb'))
def convert(input, output):
    """Decrypt/encrypt an APROM image."""

    infile = evic.BinFile(input.read())
    outfile = evic.BinFile(infile.convert())

    try:
        output.write(outfile.data)
    except IOError:
        click.echo("Error: Can't write converted file.")
        sys.exit(1)
