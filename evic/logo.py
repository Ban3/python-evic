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

    width, height = img.size

    if width % 8 != 0 or height % 8 != 0:
        raise LogoConversionError("Image dimensions must be multiples of 8.")
    if width * height > 4080:
        raise LogoConversionError("Image is too big.")

    # Convert to b/w
    if img.mode != '1':
        img = img.convert('L')
        img = img.point(lambda x: 0 if x < 32 else 255, '1')

    # 1 bit per pixel
    bits = bitarray(list(img.getdata()))

    # Convert to paged column-major order
    # 1 bit per pixel, 8 rows per page, LSB topmost
    imgpixels = img.load()
    pagedbits = bitarray(endian='little')
    for page in range(0, height / 8):
        for x in range(0, width):
            for y in range(0, 8):
                pagedbits.append(imgpixels[x, page*8 + y])

    # Invert colors
    if invert:
        bits.invert()
        pagedbits.invert()

    # Convert the bitarrays to bytes
    imgbytes = bits.tobytes() if hasattr(
        bits, 'tobytes') else bits.tostring()
    pagedbytes = pagedbits.tobytes() if hasattr(
        pagedbits, 'tobytes') else pagedbits.tostring()

    # Create a buffer for the logo
    buff = bytearray(1024)
    buff[0], buff[512] = (width,)*2
    buff[1], buff[513] = (height,)*2

    # Copy logo to the buffer
    buff[2:len(imgbytes) + 2] = imgbytes
    buff[514:len(pagedbytes) + 514] = pagedbytes

    return Logo(buff, 0)
