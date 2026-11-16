"""Adapt Home Automation driver operations."""

import libioplus


def __getattr__(name):
    return getattr(libioplus, name)


def get_one_wire_temperature(stack, channel):
    raw = round(libioplus.owbGetTemp(stack, channel) * 100)
    if raw == 0xFFFF:
        raise OSError("One-Wire temperature is not available")
    if raw & 0x8000:
        raw -= 0x10000
    return raw / 100
