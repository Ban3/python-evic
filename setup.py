#!/usr/bin/env python
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
along
"""

try:
    from setuptools import setup
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

REQUIREMENTS = [
    'binstruct',
    'bitarray',
    'click',
    'pillow'
]

setup(
    name="evic",
    version="0.1",
    author="Jussi Timperi",
    author_email="jussi.timperi@iki.fi",
    description=("Evic is a USB programmer for devices based on the Joyetech Evic VTC Mini."),
    license="GPL",
    keywords="ecig electronic cigarette evic joyetech presa wismec",
    url="https://github.com/Ban3/python-evic",
    packages=['evic'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    install_requires=REQUIREMENTS,
    data_files=[('udev', ['udev/99-nuvoton-hid.rules'])],
    long_description=readme,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    extras_require={
        'USB':  ['hidapi>=0.7.99'],
    },
    entry_points={
        'console_scripts': [
            'evic-convert=evic.cli:convert',
            'evic=evic.cli:main',
            'evic-usb=evic.cli:usb [USB]'],
    },
)
