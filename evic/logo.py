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

import binstruct
from bitarray import bitarray
from PIL import Image


class LogoConversionError(Exception):
    """Logo conversion error."""

    pass


class Logo(binstruct.StructTemplate):
    """Logo class.

    Attributes:
        width: Logo width (integer).
        height: Logo height (integer).
    """

    width = binstruct.Int8Field(0)
    height = binstruct.Int8Field(1)


def fromimage(image, invert=False):
    """Converts an image file to a Logo object.

    Args:
        image: The image that will be converted (file).
        invert: True will invert colors from the source image (boolean).

    Returns:
        An instance of Logo class containing the converted image.
    """

    img = Image.open(image)

    if img.size != (64, 40):
        raise LogoConversionError("Image dimensions must be 64x40.")

    width, height = img.size

    # Convert to b/w
    if img.mode != '1':
        img = img.convert('L')
        img = img.point(lambda x: 0 if x < 32 else 255, '1')

    # 1 bit per pixel
    bits = bitarray(list(img.getdata()))

    # Convert to column-major order, 1 bit per pixel
    img_transposed = img.transpose(Image.TRANSPOSE)
    transposedbits = bitarray(list(img_transposed.getdata()))

    # Invert colors
    if invert:
        bits.invert()
        transposedbits.invert()

    # Convert the bitarrays to bytes
    imgbytes = bits.tobytes() if hasattr(
        bits, 'tobytes') else bits.tostring()
    transposedbytes = transposedbits.tobytes() if hasattr(
        transposedbits, 'tobytes') else transposedbits.tostring()

    # Create a buffer for the logo
    buff = bytearray(1024)
    buff[0], buff[512] = (width,)*2
    buff[1], buff[513] = (height,)*2

    # Copy logo to the buffer
    buff[2:len(imgbytes) + 2] = imgbytes
    buff[514:len(transposedbytes) + 514] = transposedbytes

    return Logo(buff, 0)
