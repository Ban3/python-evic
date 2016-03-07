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

from click.testing import CliRunner

from evic import cli


class TestCli:

    def test_cli_convert(self):
        with open('testdata/helloworld.bin', 'rb') as apromfile:
            aprom_data = apromfile.read()

        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('test_aprom.bin', 'wb') as apromfile:
                apromfile.write(aprom_data)

            result = runner.invoke(cli.convert, ['test_aprom.bin',
                                                 '-o',
                                                 'test_aprom_unencrypted.bin'])
            assert result.exit_code == 0

            result = runner.invoke(cli.convert, ['test_aprom_unencrypted.bin',
                                                 '-o',
                                                 'test_aprom2.bin'])
            assert result.exit_code == 0

            with open('test_aprom2.bin', 'rb') as apromfile:
                assert aprom_data == apromfile.read()
