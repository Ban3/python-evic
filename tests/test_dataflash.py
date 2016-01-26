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
import pytest

import evic


class TestDataFlash:

    def test_dataflash_from_file(self):
        with open("testdata/test_dataflash.bin", "rb") as dataflashfile:
            dataflash = evic.DataFlash(bytearray(dataflashfile.read()), 0)
            assert dataflash.hw_version == 103
            assert dataflash.bootflag == 0
            assert dataflash.product_id == "E052"
            assert dataflash.fw_version == 300

    def test_set_dataflash_attributes(self):
        with open("testdata/test_dataflash.bin", "rb") as dataflashfile:
            dataflash = evic.DataFlash(bytearray(dataflashfile.read()), 0)
            dataflash.bootflag = 1
            dataflash.hw_version = 106

            assert dataflash.bootflag == 1
            assert dataflash.array[9] == 1
            assert dataflash.hw_version == 106
            assert struct.unpack("=I", dataflash.array[4:8])[0] == 106

    def test_dataflash_verify(self):
        with open("testdata/test_dataflash.bin", "rb") as dataflashfile:
            dataflash = evic.DataFlash(bytearray(dataflashfile.read()), 0)
            checksum = sum(dataflash.array)

            dataflash.verify(checksum)

            with pytest.raises(evic.DataFlashError):
                dataflash.verify(0)
