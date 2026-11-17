"""Config-flow tests with simulated card APIs."""

import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers import device_registry, entity_registry
from homeassistant.helpers.entity_component import DATA_INSTANCES
from homeassistant.setup import async_setup_component

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "smioplus"
OPTO = "opto_1" if DOMAIN == "smioplus" else "opto_in_1"


@pytest.fixture
def hass_config_dir(tmp_path):
    custom = tmp_path / "custom_components"
    custom.mkdir()
    (custom / DOMAIN).symlink_to(ROOT / "custom_components" / DOMAIN)
    return str(tmp_path)


@pytest.fixture
def hardware(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT))
    integration = importlib.import_module(f"custom_components.{DOMAIN}")

    def getter(_stack, _channel):
        return 0

    def setter(_stack, _channel, _value=0):
        return None

    class FakeCard:
        def __init__(self, _stack):
            pass

        def __getattr__(self, name):
            if name == "get_rtc":
                return lambda: (2026, 1, 1, 0, 0, 0)
            if name.startswith("get_"):
                return lambda channel: 0
            return lambda *args: None

    if DOMAIN == "smioplus":
        fake = SimpleNamespace()
        for types in integration.SM_MAP.values():
            for info in types.values():
                for operation, method in info["com"].items():
                    if method != integration.COM_NOGET:
                        setattr(fake, method, getter if operation == "get" else setter)
    else:
        fake = FakeCard
    monkeypatch.setattr(integration, "SM_API", fake)
    monkeypatch.setattr(integration.CARD, "api", fake)
    for platform in integration.SM_MAP:
        module = importlib.import_module(f"custom_components.{DOMAIN}.{platform}")
        if hasattr(module, "SM_API"):
            monkeypatch.setattr(module, "SM_API", fake)
    return fake


async def test_yaml_import_preserves_registry_and_options(hass, hardware):
    registry = entity_registry.async_get(hass)
    unique_id = f"binary_sensor.{DOMAIN}0_{OPTO}"
    legacy = registry.async_get_or_create(
        "binary_sensor", DOMAIN, unique_id, suggested_object_id="custom_opto"
    )
    registry.async_update_entity(legacy.entity_id, name="Custom input")

    assert await async_setup_component(
        hass, DOMAIN, {DOMAIN: [{"stack": "0", OPTO: {"update_interval": 0.1}}]}
    )
    await hass.async_block_till_done()
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.state is config_entries.ConfigEntryState.LOADED
    migrated = registry.async_get(legacy.entity_id)
    assert migrated.config_entry_id == entry.entry_id
    assert migrated.name == "Custom input"
    assert migrated.device_id is not None
    assert (
        len(
            device_registry.async_entries_for_config_entry(
                device_registry.async_get(hass), entry.entry_id
            )
        )
        == 1
    )
    assert entry.data["entities"][OPTO]["update_interval"] == 0.1
    assert hass.states.get(legacy.entity_id) is not None

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"entities": [OPTO]}
    )
    assert result["step_id"] == "intervals"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {OPTO: 2.5}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["intervals"][OPTO] == 2.5
    assert registry.async_get(legacy.entity_id).config_entry_id == entry.entry_id
    entity = hass.data[DATA_INSTANCES]["binary_sensor"].get_entity(legacy.entity_id)
    assert entity is not None
    assert getattr(entity, "_update_interval") == 2.5
    integration = importlib.import_module(f"custom_components.{DOMAIN}")
    await integration.async_setup(hass, {DOMAIN: [{"stack": "0", "relay_1": None}]})
    await hass.async_block_till_done()
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert entry.options["entities"] == [OPTO]


async def test_ui_setup_duplicate_and_unload(hass, hardware, monkeypatch):
    import requests

    def no_network(*args, **kwargs):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(requests, "get", no_network)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"stack": 1}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.state is config_entries.ConfigEntryState.LOADED
    registry = entity_registry.async_get(hass)
    entity_id = registry.async_get_entity_id(
        "binary_sensor", DOMAIN, f"binary_sensor.{DOMAIN}1_{OPTO}"
    )
    assert entity_id is not None
    assert registry.async_get(entity_id).device_id is not None
    duplicate = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    duplicate = await hass.config_entries.flow.async_configure(
        duplicate["flow_id"], {"stack": 1}
    )
    assert duplicate["type"] is FlowResultType.ABORT
    assert duplicate["reason"] == "already_configured"
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert (
        registry.async_get_entity_id(
            "binary_sensor", DOMAIN, f"binary_sensor.{DOMAIN}1_{OPTO}"
        )
        == entity_id
    )


async def test_import_of_suffixed_legacy_unique_id(hass, hardware):
    registry = entity_registry.async_get(hass)
    prefix = "smio" if DOMAIN == "smioplus" else "mio"
    old_unique_id = f"binary_sensor.{DOMAIN}0_{OPTO}_2"
    legacy = registry.async_get_or_create(
        "binary_sensor", DOMAIN, old_unique_id, original_name=f"{prefix}0_{OPTO}"
    )
    registry.async_update_entity(
        legacy.entity_id, disabled_by=entity_registry.RegistryEntryDisabler.USER
    )
    assert await async_setup_component(
        hass, DOMAIN, {DOMAIN: [{"stack": "0", OPTO: None}]}
    )
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    restored = registry.async_get(legacy.entity_id)
    assert restored.unique_id == old_unique_id
    assert restored.config_entry_id == entry.entry_id
    assert restored.disabled_by is entity_registry.RegistryEntryDisabler.USER
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert (
        registry.async_get_entity_id("binary_sensor", DOMAIN, old_unique_id)
        == legacy.entity_id
    )
    assert (
        registry.async_get_entity_id("binary_sensor", DOMAIN, old_unique_id[:-2])
        is None
    )


async def test_button_import_preserves_registry_and_resets_selected_channel(
    hass, hardware
):
    calls = []

    def reset(stack, channel):
        calls.append((stack, channel))

    hardware.rstOptoCount = reset
    registry = entity_registry.async_get(hass)
    unique_id = "button.smioplus0_opto_cnt_rst_2_2"
    legacy = registry.async_get_or_create(
        "button", DOMAIN, unique_id, original_name="smio0_opto_cnt_rst_2"
    )
    assert await async_setup_component(
        hass, DOMAIN, {DOMAIN: [{"stack": "0", "opto_cnt_rst_2": None}]}
    )
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    restored = registry.async_get(legacy.entity_id)
    assert restored.unique_id == unique_id
    assert restored.config_entry_id == entry.entry_id
    assert restored.device_id is not None
    assert hass.states.get(legacy.entity_id).attributes["icon"] == "mdi:backup-restore"
    await hass.services.async_call(
        "button", "press", {"entity_id": legacy.entity_id}, blocking=True
    )
    assert calls == [(0, 2)]


async def test_empty_yaml_and_optional_entity_selection(hass, hardware, monkeypatch):
    import requests

    def no_network(*args, **kwargs):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(requests, "get", no_network)
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: None})
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.data["stack"] == 0
    assert OPTO in entry.data["entities"]
    options = await hass.config_entries.options.async_init(entry.entry_id)
    selected = [OPTO, "relay_1"]
    if DOMAIN == "smmultiio":
        assert "rtd_res_1" not in entry.data["entities"]
        selected.append("rtd_res_1")
    options = await hass.config_entries.options.async_configure(
        options["flow_id"], {"entities": selected}
    )
    intervals = {OPTO: 5.0}
    if DOMAIN == "smmultiio":
        intervals["rtd_res_1"] = 6.0
    options = await hass.config_entries.options.async_configure(
        options["flow_id"], intervals
    )
    assert options["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    registry = entity_registry.async_get(hass)
    assert registry.async_get_entity_id("switch", DOMAIN, f"switch.{DOMAIN}0_relay_1")
    if DOMAIN == "smmultiio":
        assert registry.async_get_entity_id(
            "sensor", DOMAIN, "sensor.smmultiio0_rtd_res_1"
        )


def test_yaml_ranges_and_invalid_intervals(hardware):
    support = importlib.import_module("SMcommonHA.config_support")
    card = importlib.import_module(f"custom_components.{DOMAIN}").CARD
    kind = OPTO.rsplit("_", 1)[0]
    imported = support.import_yaml_card(
        card,
        {
            "stack": "2",
            kind: {"channels": "1,3", "update_interval": 0.1},
            "relay": {"chan_range": "1..2"},
        },
    )
    assert set(imported["entities"]) == {f"{kind}_1", f"{kind}_3", "relay_1", "relay_2"}
    assert imported["entities"][f"{kind}_3"]["update_interval"] == 0.1
    assert not support.import_yaml_card(
        card, {f"{kind}_1": {"update_interval": float("nan")}}
    )["entities"]


async def test_import_multiple_cards(hass, hardware):
    assert await async_setup_component(
        hass, DOMAIN, {DOMAIN: [{"stack": "0", OPTO: None}, {"stack": "1", OPTO: None}]}
    )
    await hass.async_block_till_done()
    entries = hass.config_entries.async_entries(DOMAIN)
    assert {entry.data["stack"] for entry in entries} == {0, 1}
    registry = entity_registry.async_get(hass)
    for stack in (0, 1):
        assert registry.async_get_entity_id(
            "binary_sensor", DOMAIN, f"binary_sensor.{DOMAIN}{stack}_{OPTO}"
        )


async def test_hardware_setup_error_retries_platform(hass, hardware):
    support = importlib.import_module("SMcommonHA.config_support")
    card = importlib.import_module(f"custom_components.{DOMAIN}").CARD
    config = support.available_entities(card, 0)[OPTO]
    entry = SimpleNamespace(runtime_data=[config], domain=DOMAIN, entry_id="test")

    def fail(_config):
        raise OSError("I2C unavailable")

    with pytest.raises(PlatformNotReady, match="I2C unavailable"):
        await support.async_setup_entities(
            hass, entry, lambda _entities: None, "binary_sensor", fail, card
        )
