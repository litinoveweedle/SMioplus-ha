FULL_NAME="Home Automation"
LINK="https://sequentmicrosystems.com/products/raspberry-pi-home-automation-card"

from . import driver_adapter

API = driver_adapter
DOMAIN = "smioplus"
NAME_PREFIX = "smio"

SM_MAP = {
    "button": {
        "opto_cnt_rst": {
            "chan_no": 8,
            "com": {
                "set": "rstOptoCount",
            },
            "icon": {
                "off": "mdi:backup-restore",
            },
        },
        "owb_scan": {
            "chan_no": 1,
            "optional": True,
            "com": {"set": "owbScan"},
        },
    },
    "binary_sensor": {
        "opto": {
            "chan_no": 8,
            "uom": "",
            "com": {
                "get": "getOptoCh",
            },
            "icon": {
                "on": "mdi:numeric-1",
            },
        },
    },
    "sensor":  {
        "owb_count": {
            "chan_no": 1,
            "optional": True,
            "com": {"get": "owbGetSnsNo"},
        },
        "owb_temp": {
            "chan_no": 16,
            "optional": True,
            "uom": "°C",
            "com": {"get": "get_one_wire_temperature"},
        },
        "opto_cnt": {
            "chan_no": 8,
            "uom": "",
            "com": {
                "get": "getOptoCount",
            },
            "icon": {
                "on": "mdi:counter",
                "off": "mdi:counter",
            },
        },
        "adc": {
            "chan_no": 8,
            "uom": "V",
            "com": {
                "get": "getAdcV",
            },
            "icon": {
                "on": "mdi:flash",
                "off": "mdi:flash"
            },
        },
    },
    "switch": {
        "relay": {
            "chan_no": 8,
            "com": {
                "get": "getRelayCh",
                "set": "setRelayCh"
            },
        },
    },
    "number": {
        "dac": {
            "chan_no": 4,
            "uom": "V",
            "min_value": 0.0,
            "max_value": 10.0,
            "step": 0.01,
            "com": {
                "get": "getDacV",
                "set": "setDacV"
            },
            "icon": {
                "on": "mdi:flash",
                "off": "mdi:flash"
            },
        },
        "od": {
            "chan_no": 4,
            "uom": "%",
            "min_value": 0.0,
            "max_value": 100.0,
            "step": 0.01,
            "com": {
                "get": "_fixed_getOdPwm",
                "set": "_fixed_setOdPwm"
            },
            "icon": {
                "on": "mdi:percent",
                "off": "mdi:percent"
            },
        },
    },
}
