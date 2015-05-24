#!/usr/bin/env python
"""
This module extracts the configuration of an Intel memory controller
out of PCI configuration space by using port I/O.

The configuration space for Intel memory controllers is specified
inside the processors datasheet and is the same for all core CPUs
from 2nd generation (Sandy Bridge) to 5th generation (Broadwell).

On Intel CPUs older than Sandy Bridge the layout is different and
this module will not work.

Information on memory controller PCI configuration can be found in
Volume 2 of the corresponding processor datasheet: http://goo.gl/WpMju1
"""

from __future__ import print_function

__author__ = "Johannes Stuettgen <johannes.stuettgen@gmail.com>"

from os import strerror
from portio import ioperm, inl, outl
from struct import pack, unpack
from sys import exit

DWORD_SIZE = 4
IOPERM_LONG = 4
IOPERM_ENABLE = 1

# Intel memory controllers are located at bus 0, device 0 and function 0
MCH_BDF = (0, 0, 0)
# To make sure we use the correct layout for the config space we throw
# a warning if the memory controller is not known. Insert ids for devices
# here were you know that their config layout is compatible.
VENDOR_IDS = [0x8086]
DEVICE_IDS = [0x0100, 0x0104, 0x0150, 0x0154]

PCI_CONFIG_ADDRESS = 0xcf8
PCI_CONFIG_DATA = 0xcfc
PCI_CONFIG_ENABLE = 0x80000000
PCI_CONFIG_SIZE = 0xff

PCIMCHConfig = [
    ("vendor_id", "<H", 2),
    ("device_id", "<H", 2),
    ("command", "<H", 2),
    ("status", "<H", 2),
    ("revision_id", "<B", 1),
    ("reserved_class_code", "<B", 0x3),
    ("reserved_0", "<H", 2),
    ("header_type", "<B", 1),
    ("reserved_1", "<B", 0x1d),
    ("svid", "<H", 2),
    ("sid", "<H", 2),
    ("reserved_2", "<B", 0x10),
    ("pxpepbar", "<Q", 8),
    ("mchbar", "<Q", 8),
    ("ggc", "<H", 2),
    ("reserved_3", "<B", 0x2),
    ("device_enable", "<I", 4),
    ("pavpc", "<I", 4),
    ("dma_protected_range", "<I", 4),
    ("pxiexbar", "<Q", 8),
    ("dmibar", "<Q", 8),
    ("reserved_4", "<B", 0x10),
    ("pam0", "<B", 1),
    ("pam1", "<B", 1),
    ("pam2", "<B", 1),
    ("pam3", "<B", 1),
    ("pam4", "<B", 1),
    ("pam5", "<B", 1),
    ("pam6", "<B", 1),
    ("lac", "<B", 1),
    ("reserved_5", "<B", 8),
    ("remap_base", "<Q", 8),
    ("remap_limit", "<Q", 8),
    ("tom", "<Q", 8),
    ("touud", "<Q", 8),
    ("bdsm", "<I", 4),
    ("bgsm", "<I", 4),
    ("tsegmb", "<I", 4),
    ("tolud", "<I", 4),
    ("reserved_6", "<B", 0x2c),
]

def unpack_structure(definition, data):
    pos = 0
    structure = {}
    for name, data_type, size in definition:
        if pos + size > len(data):
            raise RuntimeError("Unpacking {} bytes from struct size {}".format(
                pos + size, len(data)))
        if "reserved" not in name:
            structure[name] = unpack(data_type, data[pos:pos+size])[0]
        pos += size
    return structure

def encode_config_address(bus, device, function, register):
    return bus << 16 | device << 11 | function << 8 | register

def pci_config_seek(bus, device, function, register):
    target_address = encode_config_address(bus, device, function, register)
    outl(PCI_CONFIG_ENABLE | target_address, PCI_CONFIG_ADDRESS)

def read_pci_config(bus, device, function):
    buf = []
    register_offsets = range(0, 0xff, 0x4)
    for offset in register_offsets:
        pci_config_seek(bus, device, function, offset)
        buf.append(pack("<I", inl(PCI_CONFIG_DATA)))
    return "".join(buf)

def print_mch_config():
    raw_config = read_pci_config(*MCH_BDF)
    mch_config = unpack_structure(PCIMCHConfig, raw_config)
    if mch_config["vendor_id"] not in VENDOR_IDS:
        print("Unknown vendor id for MCH: {:#04x} ".format(
            mch_config["vendor_id"]))
    if mch_config["device_id"] not in DEVICE_IDS:
        print("Unknown device id for MCH: {:#04x}".format(
            mch_config["device_id"]))
    print("MCH configuration (least significant bit is lock flag)\n"
        "Top Segment Memory Base:   {:#016x}\n".format(mch_config["tsegmb"]) +
        "Base of GFX stolen Memory: {:#016x}\n".format(mch_config["bdsm"]) +
        "Base of GTT stolen Memory: {:#016x}\n".format(mch_config["bgsm"]) +
        "Top of Low Usable DRAM:    {:#016x}\n".format(mch_config["tolud"]) +
        "Remap Base:                {:#016x}\n".format(mch_config["remap_base"]) +
        "Remap Limit:               {:#016x}\n".format(mch_config["remap_limit"]) +
        "Top of Upper Usable DRAM:  {:#016x}\n".format(mch_config["touud"]) +
        "Top of Memory:             {:#016x}\n".format(mch_config["tom"])
    )

if __name__ == "__main__":
    error = ioperm(PCI_CONFIG_DATA, IOPERM_LONG, IOPERM_ENABLE)
    error = ioperm(PCI_CONFIG_ADDRESS, IOPERM_LONG, IOPERM_ENABLE)
    if error:
        print("Failed to acquire I/O priviledges: {}".format(strerror(error)))
        exit(-1)
    print_mch_config()
