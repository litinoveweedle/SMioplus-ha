"""Check the real driver against the integration's channel API mappings."""

import inspect

import pytest

from custom_components.smioplus.data import API, SM_MAP
from sequent_ha_common.const import COM_NOGET


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
    if operation == "set" and platform != "button":
        args.append(1)
    inspect.signature(function).bind(*args)
