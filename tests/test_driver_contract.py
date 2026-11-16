"""Check the real driver against the integration's channel API mappings."""

import inspect

import pytest

import libioplus
from custom_components.smioplus import CARD
from custom_components.smioplus.data import API, SM_MAP
from SMcommonHA.button import Button
from SMcommonHA.const import COM_NOGET


def test_one_wire_scan_is_an_optional_button():
    assert SM_MAP["button"]["owb_scan"]["optional"]
    assert SM_MAP["button"]["owb_scan"]["com"]["set"] == "owbScan"


def test_one_wire_scan_uses_stack_not_channel(monkeypatch):
    calls = []

    def scan(stack):
        calls.append(stack)

    monkeypatch.setattr(libioplus, "owbScan", scan)
    button = Button("scan", 2, "owb_scan", 1, CARD)
    button.press()
    assert calls == [2]


@pytest.mark.parametrize(("raw", "expected"), [(2500, 25.0), (0xFB2E, -12.34)])
def test_one_wire_temperature_signed_decoding(monkeypatch, raw, expected):
    class Bus:
        def read_byte_data(self, *_):
            return 1

        def read_word_data(self, *_):
            return raw

        def close(self):
            pass

    monkeypatch.setattr(libioplus.smbus2, "SMBus", lambda _: Bus())
    assert API.get_one_wire_temperature(0, 1) == expected


def test_one_wire_temperature_invalid_value(monkeypatch):
    monkeypatch.setattr(libioplus, "owbGetTemp", lambda *_: 655.35)
    with pytest.raises(OSError, match="not available"):
        API.get_one_wire_temperature(0, 1)


@pytest.mark.parametrize(
    ("platform", "kind", "operation", "method"),
    [
        (platform, kind, operation, method)
        for platform, types in SM_MAP.items()
        for kind, metadata in types.items()
        for operation, method in metadata["com"].items()
        if method != COM_NOGET
    ],
)
def test_driver_method_accepts_expected_arguments(platform, kind, operation, method):
    function = getattr(API, method)
    assert callable(function), f"{platform}.{kind}: {method} is not callable"
    args = [0, 1]
    if kind in {"owb_scan", "owb_count"}:
        args.pop()
    if operation == "set" and platform != "button":
        args.append(1)
    inspect.signature(function).bind(*args)
