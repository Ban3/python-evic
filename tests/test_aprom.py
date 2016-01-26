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

import pytest

import evic


class TestAPROM:

    def test_aprom_convert(self):
        with open("testdata/helloworld.bin", "rb") as apromfile:
            aprom_data = bytearray(apromfile.read())
            aprom = evic.APROM(aprom_data)
            aprom_unencrypted = evic.APROM(aprom.convert())

            assert aprom_data == aprom_unencrypted.convert()

    def test_aprom_verify(self):
        with open("testdata/helloworld.bin", "rb") as apromfile:
            aprom = evic.APROM(apromfile.read())
            aprom_unencrypted = evic.APROM(aprom.convert())

            aprom_unencrypted.verify(['E052'], 106)

            with pytest.raises(evic.APROMError):
                aprom_unencrypted.verify(['W007'], 106)
                aprom_unencrypted.verify(['E052'], 999)
