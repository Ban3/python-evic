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

import evic


class TestDevice:

    def test_hidtransfer_hidcmd(self):
        read_df_cmd = bytearray(b'5\x0e\x00\x00\x00\x00\x00\x08\x00\x00HIDCc\x01\x00\x00')
        write_df_cmd = bytearray(b'S\x0e\x00\x00\x00\x00\x00\x08\x00\x00HIDC\x81\x01\x00\x00')
        reset_cmd = bytearray(b'\xb4\x0e\x00\x00\x00\x00\x00\x00\x00\x00HIDC\xda\x01\x00\x00')
        write_aprom_cmd = bytearray(b'\xc3\x0e\x00\x00\x00\x00\x00\x00\x00\x00HIDC\xe9\x01\x00\x00')

        assert evic.HIDTransfer.hidcmd(0xC3, 0, 0) == write_aprom_cmd
        assert evic.HIDTransfer.hidcmd(0xB4, 0, 0) == reset_cmd
        assert evic.HIDTransfer.hidcmd(0x35, 0, 2048) == read_df_cmd
        assert evic.HIDTransfer.hidcmd(0x53, 0, 2048) == write_df_cmd
