# Sequent Microsystems Home Automation Home Assistant Integration

Integrate [Home Automation](https://sequentmicrosystems.com/products/raspberry-pi-home-automation-card)
seamlessly with Home Assistant, bringing all your custom functionality into the Home Assistant ecosystem for enhanced control, automation, and ease of use.



## Installation

> This development version requires `sequent-ha-common==0.1.0`. That package
> must be published to PyPI before Home Assistant can install the integration
> normally. The shared-package version pins in both Sequent integrations
> should be updated and tested together.

For local development, install the shared package into the test Python
environment with `python -m pip install -e /path/to/sequent-ha-common`.
This does not replace publication for a normal Home Assistant installation.

> If you already have HACS, I2C and File editor configured, you can skip to [The actual installation](#the-actual-installation)


#### Video tutorials

- [Install HACS video](https://youtu.be/Fl3lATWhQVM) for step 1.
- [Enable I2C and Install file editor video](https://youtu.be/53Zj8NofS7k) for steps 2. and 3.
- [Install and config card drivers video](https://youtu.be/yH2HKjm7j24) for steps 4. and 5.

#### Prerequirements

1. Install HACS
    - Follow the official [instructions](https://www.hacs.xyz/docs/use/download/download/)

2. Install and run HassOS I2C Configurator add-on
    - Install [HassOS I2C Configurator](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fadamoutler%2FHassOSConfigurator)
    - Select your profile from the buttom left corner and enable `Advanced mode` in User settings
    - In Settings, Add-ons, Add-on Store, search and install `HassOS I2C Configurator`
    - Disable `Protection mode`
    - Start the add-on

3. Install File editor add-on
    - In Settings, Add-ons, Add-on Store, search and install `File editor`
    - Enable `Show in sidebar`
(see multiple config options bellow)


### The actual installation

4. Install SMioplus-ha from HACS
    - Open HACS (from the sidebar)
    - Click on the 3 dots in the top right corner and select `Custom repositories`
    - Repository is `SequentMicrosystems/SMioplus-ha` and type is `Integration`
    - Once added, you can now search it in HACS menu and download it

5. Restart Home Assistant, then open **Settings > Devices & services**.
6. Select **Add integration**, choose **Sequent Microsystems Home Automation
   Integration**, and enter the card's stack address. Repeat for each card.
7. Use **Configure** on each integration entry to choose entities and their
   update intervals. Entity names and enablement can also be changed on their
   Home Assistant entity pages.

### Upgrading from the `SMioplus` domain

The integration domain is now lowercase, as required by Home Assistant and
Marketplace. Back up Home Assistant before upgrading.

1. Uninstall the old `SMioplus` integration from HACS or Marketplace, then
   install the updated version. Marketplace may require uninstalling and
   re-adding the repository when its domain changes.
2. Ensure the old `custom_components/SMioplus` directory is gone and the new
   integration is installed in `custom_components/smioplus`. Do not keep both.
3. Change the top-level `SMioplus:` key in `configuration.yaml` to `smioplus:`,
   keeping the existing settings, and restart Home Assistant.

On startup, existing entity registry entries are migrated to the new domain,
preserving their entity IDs and settings. If conflicting entries already exist
under `smioplus`, setup fails rather than overwriting them; resolve the
conflicting entities before restarting.

### Opto input entities

Opto inputs are now binary sensors rather than numeric sensors. After upgrading,
update automations and dashboards to use the new `binary_sensor` entity IDs and
`on`/`off` states instead of the old `sensor` IDs and `1`/`0` states. Existing
sensor registry entries, customizations, and history are not automatically
transferred. Opto counters remain numeric sensors.

If an opto input returns an invalid reading, its binary sensor reports `unknown`
and an error is logged until a valid reading is received.



## Migrating from YAML

Back up Home Assistant before upgrading. Existing `smioplus` YAML configuration
is imported once, preserving selected channels and their update intervals.
After the entries appear in **Settings > Devices & services**, remove the
`smioplus:` section from `configuration.yaml` and restart Home Assistant.
Further YAML edits are not imported; make changes using the integration UI.
If an entry for the same stack already exists, YAML does not overwrite it.

The following legacy examples are retained for reference:

`configuration.yaml` example:
```yaml
# Loads default set of integrations. Do not remove.
default_config:

# Load frontend themes from the themes folder
frontend:
  themes: !include_dir_merge_named themes

automation: !include automations.yaml
script: !include scripts.yaml
scene: !include scenes.yaml

smioplus:
    # + optional configs
```

- Simple stack 0 config:

```yaml
smioplus:
```

- Specific stack config:

```yaml
smioplus:
    - stack: 2
```

- Multiple cards on different stack levels:

```yaml
smioplus:
    - stack: 0
    - stack: 2
    - stack: 3
```

- Only specific entities for different stack levels:

> !The following example is provided for illustrative purposes only and does NOT necessarily represent real entities!

```yaml
smioplus:
    - stack: 0
      relay_1:
      relay_3:
      opto_1:
        update_interval: 0.1
    - stack: 2
      relay:
        chan_range: "1..8"
      opto_cnt:
        chan_range: "2..6"
        update_interval: 1
```

[//]: # (__CUSTOM_README__ START)
[//]: # (__CUSTOM_README__ END)

### `configuration.yaml` entities

Possible entities:
```yaml
opto_cnt_rst_1: -> opto_cnt_rst_8:  (type: button)
dac_1: -> dac_4:  (type: number)
od_1: -> od_4:  (type: number)
adc_1: -> adc_8:  (type: sensor)
opto_1: -> opto_8:  (type: binary_sensor)
opto_cnt_1: -> opto_cnt_8:  (type: sensor)
relay_1: -> relay_8:  (type: switch)
```

Default icons indicate each entity's function; opto inputs and relays use
different icons for on and off states.

Entity options:
- `channels: "1,3,5"` (specify a comma-separated list of unique channels; takes precedence over `chan_range`)
- `chan_range: "start..end"` (specify inclusive channel range)
- `update_interval: seconds` (specify the update interval for `sensor` and `binary_sensor`, default 30s)

Invalid channel lists and ranges are logged and skipped without loading any
channels for that entity. Individually configured entities now use names such
as `smio0_relay_1` instead of `smio0_relay_1_1`; their unique IDs are unchanged.

## Testing

With Python 3.14, install `pytest-homeassistant==2026.11.1` and `SMioplus` in a
virtual environment, then run:

```shell
pytest -p no:respx --asyncio-mode=auto -o asyncio_default_fixture_loop_scope=function tests
```

The tests simulate the hardware; they do not require a card.
