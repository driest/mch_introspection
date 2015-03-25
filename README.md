# MCH Introspection

This module extracts the configuration of an Intel memory controller out of PCI configuration space by using port I/O. You need the '''portio''' package for this to work.

The configuration space for Intel memory controllers is specified inside the processors datasheet and is the same for all core CPUs from 2nd generation (Sandy Bridge) to 5th generation (Broadwell).

On Intel CPUs older than Sandy Bridge the layout is different and this module will not work. Information on memory controller PCI configuration can be found in Volume 2 of the corresponding [processor datasheet](http://goo.gl/WpMju1)

