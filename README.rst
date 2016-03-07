===============================
Evic
===============================

.. image:: https://travis-ci.org/Ban3/python-evic.svg?branch=master
   :target: https://travis-ci.org/Ban3/python-evic

Evic is a USB programmer for devices based on the Joyetech Evic VTC Mini.

Supported devices
---------------------

* Evic VTC Mini
* Cuboid
* Presa TC75W*
* Vaporflask Classic*
* Vaporflask Lite*
* Vaporflask Stout*
* Reuleaux RX200*

\*Untested

Tested firmware versions
-----------------------------

* Evic VTC Mini <=3.0
* Presa TC75W 1.02\*
* Examples from `evic-sdk <https://github.com/ReservedField/evic-sdk>`_

\*Flashing Presa firmware to a VTC Mini requires changing the hardware version
on some devices. Backup your data flash before flashing!

Installation
-------------

Install from source:
^^^^^^^^^^^^^^^^^^^^^^

Building hidapi requires libusb headers and cython. On Arch Linux they can be obtained from the repositories by installing packages ``libusb`` and ``cython``. Debian based distributions will have packages ``libusb-1.0-0-dev`` and ``cython``.

On Windows you will also need the correct compiler for your Python version. See `this <https://wiki.python.org/moin/WindowsCompilers>`_
page for more information on setting up the compiler.

|

Building python-evic:

::

    $ git clone git://github.com/Ban3/python-evic.git
    $ cd python-evic
    $ python setup.py install


Allowing non-root access to the device
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The file ``udev/99-nuvoton-hid.rules`` contains an example set of rules for setting the device permissions to ``0666``.  Copy the file to the directory ``/etc/udev/rules.d/`` to use it.

Usage
-------
See  ``--help`` for more information on a given command.

|
  
Encrypt/decrypt a firmware image:

::

    $ evic convert in.bin -o out.bin

Dump device data flash to a file:

::

    $ evic dump-dataflash -o out.bin

Upload an encrypted firmware image to the device:

::

    $ evic upload firmware.bin

Upload an unencrypted firmware image to the device:

::

    $ evic upload -u firmware.bin

Upload a firmware image using data flash from a file:

::

    $ evic upload -d data.bin firmware.bin

Use  ``--no-verify`` to disable verification for APROM or data flash. To disable both:

::  

    $ evic upload --no-verify aprom --no-verify dataflash firmware.bin

