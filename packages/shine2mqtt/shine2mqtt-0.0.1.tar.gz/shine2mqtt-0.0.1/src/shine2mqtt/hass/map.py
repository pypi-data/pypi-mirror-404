POWER_DC_ICON = "mdi:solar-power"
CURRENT_DC_ICON = "mdi:current-dc"
VOLTAGE_DC_ICON = "mdi:gauge"

POWER_AC_ICON = "mdi:solar-power"
CURRENT_AC_ICON = "mdi:current-ac"
VOLTAGE_AC_ICON = "mdi:gauge"
FREQUENCY_AC_ICON = "mdi:sine-wave"
VERSION_ICON = "mdi:chip"
IP_ADDRESS_ICON = "mdi:ip-network"
NETWORK_ICON = "mdi:network"

ENERGY_ICON = "mdi:meter-electric-outline"

HASS_CONTROLS_MAP = {}


DATA_MESSAGE_SENSORS = {
    "power_dc": {
        "entity_id": "power_dc",
        "name": "Power DC",
        "device_class": "power",
        "unit_of_measurement": "W",
        "icon": POWER_DC_ICON,
        "device": "inverter",
    },
    "voltage_dc_1": {
        "entity_id": "voltage_dc_1",
        "name": "Voltage DC 1",
        "device_class": "voltage",
        "unit_of_measurement": "V",
        "icon": VOLTAGE_DC_ICON,
    },
    "current_dc_1": {
        "entity_id": "current_dc_1",
        "name": "Current DC 1",
        "device_class": "current",
        "unit_of_measurement": "A",
        "icon": CURRENT_DC_ICON,
    },
    "power_dc_1": {
        "entity_id": "power_dc_1",
        "name": "Power DC 1",
        "device_class": "power",
        "unit_of_measurement": "W",
        "icon": POWER_DC_ICON,
    },
    "voltage_dc_2": {
        "entity_id": "voltage_dc_2",
        "name": "Voltage DC 2",
        "device_class": "voltage",
        "unit_of_measurement": "V",
        "icon": VOLTAGE_DC_ICON,
    },
    "current_dc_2": {
        "entity_id": "current_dc_2",
        "name": "Current DC 2",
        "device_class": "current",
        "unit_of_measurement": "A",
        "icon": CURRENT_DC_ICON,
    },
    "power_dc_2": {
        "entity_id": "power_dc_2",
        "name": "Power DC 2",
        "device_class": "power",
        "unit_of_measurement": "W",
        "icon": POWER_DC_ICON,
    },
    "power_ac": {
        "entity_id": "power_ac",
        "name": "Power AC",
        "device_class": "power",
        "unit_of_measurement": "W",
        "icon": POWER_AC_ICON,
    },
    "frequency_ac": {
        "entity_id": "frequency_ac",
        "name": "Frequency AC",
        "device_class": "frequency",
        "unit_of_measurement": "Hz",
        "icon": FREQUENCY_AC_ICON,
    },
    "voltage_ac_1": {
        "entity_id": "voltage_ac_1",
        "name": "Voltage AC 1",
        "device_class": "voltage",
        "unit_of_measurement": "V",
        "icon": VOLTAGE_AC_ICON,
    },
    "current_ac_1": {
        "entity_id": "current_ac_1",
        "name": "Current AC 1",
        "device_class": "current",
        "unit_of_measurement": "A",
        "icon": CURRENT_AC_ICON,
    },
    "power_ac_1": {
        "entity_id": "power_ac_1",
        "name": "Power AC 1",
        "device_class": "apparent_power",
        "unit_of_measurement": "VA",
        "icon": POWER_AC_ICON,
    },
    "voltage_ac_l1_l2": {
        "entity_id": "voltage_ac_l1_l2",
        "name": "Voltage AC L1-L2",
        "device_class": "voltage",
        "unit_of_measurement": "V",
        "icon": VOLTAGE_AC_ICON,
    },
    "voltage_ac_l2_l3": {
        "entity_id": "voltage_ac_l2_l3",
        "name": "Voltage AC L2-L3",
        "device_class": "voltage",
        "unit_of_measurement": "V",
        "icon": VOLTAGE_AC_ICON,
    },
    "voltage_ac_l3_l1": {
        "entity_id": "voltage_ac_l3_l1",
        "name": "Voltage AC L3-L1",
        "device_class": "voltage",
        "unit_of_measurement": "V",
        "icon": VOLTAGE_AC_ICON,
    },
    "energy_ac_today": {
        "entity_id": "energy_ac_today",
        "name": "Energy AC Today",
        "device_class": "energy",
        "unit_of_measurement": "kWh",
        "icon": ENERGY_ICON,
    },
    "energy_ac_total": {
        "entity_id": "energy_ac_total",
        "name": "Energy AC Total",
        "device_class": "energy",
        "unit_of_measurement": "kWh",
        "icon": ENERGY_ICON,
    },
    "energy_dc_total": {
        "entity_id": "energy_dc_total",
        "name": "Energy DC Total",
        "device_class": "energy",
        "unit_of_measurement": "kWh",
        "icon": ENERGY_ICON,
    },
    "energy_dc_1_today": {
        "entity_id": "energy_dc_1_today",
        "name": "Energy DC 1 Today",
        "device_class": "energy",
        "unit_of_measurement": "kWh",
        "icon": ENERGY_ICON,
    },
    "energy_dc_1_total": {
        "entity_id": "energy_dc_1_total",
        "name": "Energy DC 1 Total",
        "device_class": "energy",
        "unit_of_measurement": "kWh",
        "icon": ENERGY_ICON,
    },
    "energy_dc_2_today": {
        "entity_id": "energy_dc_2_today",
        "name": "Energy DC 2 Today",
        "device_class": "energy",
        "unit_of_measurement": "kWh",
        "icon": ENERGY_ICON,
    },
    "energy_dc_2_total": {
        "entity_id": "energy_dc_2_total",
        "name": "Energy DC 2 Total",
        "device_class": "energy",
        "unit_of_measurement": "kWh",
        "icon": ENERGY_ICON,
    },
}

ANNOUNCE_MESSAGE_SENSORS = {
    # "datalogger_serial": {
    #     "entity_id": "datalogger_serial",
    #     "entity_category": "diagnostic",
    #     "name": "Datalogger serial",
    #     "icon": "mdi:identifier",
    # },
    "inverter_serial": {
        "entity_id": "inverter_serial",
        "entity_category": "diagnostic",
        "name": "Inverter serial",
        "icon": "mdi:identifier",
    },
    "active_power_ac_max": {
        "entity_id": "active_power_ac_max",
        "entity_category": "diagnostic",
        "name": "Active power AC max",
        "unit_of_measurement": "%",
        "icon": POWER_AC_ICON,
    },
    "reactive_power_ac_max": {
        "entity_id": "reactive_power_ac_max",
        "entity_category": "diagnostic",
        "name": "Reactive power AC max",
        "unit_of_measurement": "%",
        "icon": POWER_AC_ICON,
    },
    "power_factor": {
        "entity_id": "power_factor",
        "entity_category": "diagnostic",
        "name": "Power factor",
        "device_class": "power_factor",
        "icon": POWER_AC_ICON,
    },
    "rated_power_ac": {
        "entity_id": "rated_power_ac",
        "entity_category": "diagnostic",
        "name": "Rated power AC",
        "device_class": "apparent_power",
        "unit_of_measurement": "VA",
        "icon": POWER_AC_ICON,
    },
    "rated_voltage_dc": {
        "entity_id": "rated_voltage_dc",
        "entity_category": "diagnostic",
        "name": "Rated voltage DC",
        "device_class": "voltage",
        "unit_of_measurement": "V",
        "icon": VOLTAGE_DC_ICON,
    },
    "inverter_fw_version": {
        "entity_id": "inverter_fw_version",
        "entity_category": "diagnostic",
        "name": "Inverter firmware version",
        "icon": VERSION_ICON,
    },
    "inverter_control_fw_version": {
        "entity_id": "inverter_control_fw_version",
        "entity_category": "diagnostic",
        "name": "Inverter control firmware version",
        "icon": VERSION_ICON,
    },
    # lcd_language
    # device_type
    # timestamp
    "voltage_ac_low_limit": {
        "entity_id": "voltage_ac_low_limit",
        "entity_category": "diagnostic",
        "name": "Voltage AC low limit",
        "device_class": "voltage",
        "unit_of_measurement": "V",
        "icon": VOLTAGE_AC_ICON,
    },
    "voltage_ac_high_limit": {
        "entity_id": "voltage_ac_high_limit",
        "entity_category": "diagnostic",
        "name": "Voltage AC high limit",
        "device_class": "voltage",
        "unit_of_measurement": "V",
        "icon": VOLTAGE_AC_ICON,
    },
    "frequency_ac_low_limit": {
        "entity_id": "frequency_ac_low_limit",
        "entity_category": "diagnostic",
        "name": "Frequency AC low limit",
        "device_class": "frequency",
        "unit_of_measurement": "Hz",
        "icon": FREQUENCY_AC_ICON,
    },
    "frequency_ac_high_limit": {
        "entity_id": "frequency_ac_high_limit",
        "entity_category": "diagnostic",
        "name": "Frequency AC high limit",
        "device_class": "frequency",
        "unit_of_measurement": "Hz",
        "icon": FREQUENCY_AC_ICON,
    },
    "power_factor_control_mode": {
        "entity_id": "power_factor_control_mode",
        "entity_category": "diagnostic",
        "name": "Power factor control mode",
        "icon": "mdi:cog",
    },
}

INVERTER_SENSOR_MAP = {
    **DATA_MESSAGE_SENSORS,
    **ANNOUNCE_MESSAGE_SENSORS,
}

DATALOGGER_SENSOR_MAP = {
    "update_interval": {
        "entity_id": "update_interval",
        "entity_category": "diagnostic",
        "name": "Update interval",
        "device_class": "duration",
        "unit_of_measurement": "min",
        "icon": "mdi:timer-sand",
    },
    "datalogger_serial": {
        "entity_id": "datalogger_serial",
        "entity_category": "diagnostic",
        "name": "Datalogger serial",
        "icon": "mdi:identifier",
    },
    "ip_address": {
        "entity_id": "ip_address",
        "entity_category": "diagnostic",
        "name": "IP Address",
        "icon": IP_ADDRESS_ICON,
    },
    "mac_address": {
        "entity_id": "mac_address",
        "entity_category": "diagnostic",
        "name": "MAC Address",
        "icon": NETWORK_ICON,
    },
    "server_ip_address": {
        "entity_id": "server_ip_address",
        "entity_category": "diagnostic",
        "name": "Server IP Address",
        "icon": IP_ADDRESS_ICON,
    },
    "server_port": {
        "entity_id": "server_port",
        "entity_category": "diagnostic",
        "name": "Server Port",
        "icon": NETWORK_ICON,
    },
    "datalogger_sw_version": {
        "entity_id": "datalogger_sw_version",
        "entity_category": "diagnostic",
        "name": "Datalogger Software Version",
        "icon": VERSION_ICON,
    },
    "datalogger_hw_version": {
        "entity_id": "datalogger_hw_version",
        "entity_category": "diagnostic",
        "name": "Datalogger Hardware Version",
        "icon": VERSION_ICON,
    },
    "netmask": {
        "entity_id": "netmask",
        "entity_category": "diagnostic",
        "name": "Netmask",
        "icon": IP_ADDRESS_ICON,
    },
    "gateway_ip_address": {
        "entity_id": "gateway_ip_address",
        "entity_category": "diagnostic",
        "name": "Gateway IP Address",
        "icon": IP_ADDRESS_ICON,
    },
    "wifi_ssid": {
        "entity_id": "wifi_ssid",
        "entity_category": "diagnostic",
        "name": "WiFi SSID",
        "icon": "mdi:wifi",
    },
}
