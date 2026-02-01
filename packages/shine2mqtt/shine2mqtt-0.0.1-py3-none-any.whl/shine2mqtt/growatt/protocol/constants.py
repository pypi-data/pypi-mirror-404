from enum import Enum

ACK = b"\x00"
NACK = b"\x03"

ENCRYPTION_KEY = b"Growatt"
DECRYPTION_KEY = ENCRYPTION_KEY


class FunctionCode(Enum):
    PING = 0x16  # 22
    ANNOUNCE = 0x03  # 3 (holding_registers, config, read/write)
    DATA = 0x04  # 4 (input_registers, state, read)
    BUFFERED_DATA = 0x50  # 80
    SET_CONFIG = 0x18  # 24
    GET_CONFIG = 0x19  # 25
    # REBOOT = 020 ?


class InverterStatus(Enum):
    WAITING = 0
    NORMAL = 1
    FAULT = 3


UPDATE_INTERVAL_REGISTER = 4
DATALOGGER_SW_VERSION_REGISTER = 21
DATALOGGER_WIFI_PASSWORD_REGISTER = 57

CONFIG_REGISTERS = {
    4: {
        "name": "update_interval",
        "description": "Update Interval min",  # 0x04
        "fmt": "s",
    },
    5: {
        "name": "modbus_range_low",
        "description": "Modbus Range low",  # 0x05
        "fmt": "s",
    },
    6: {
        "name": "modbus_range_high",
        "description": "Modbus Range high",  # 0x06
        "fmt": "s",
    },
    # 7 is unknown
    8: {
        "name": "datalogger_serial",
        "description": "Datalogger Serial Number",  # 0x08
        "fmt": "s",
    },
    # 9-13 are unknown
    14: {"name": "ip_address", "description": "Local IP", "fmt": "s"},  # 0x0E
    15: {"name": "port", "description": "Local Port", "fmt": "s"},  # 0x0F
    16: {"name": "mac_address", "description": "Mac Address", "fmt": "s"},  # 0x10
    17: {"name": "server_ip_address", "description": "Server IP", "fmt": "s"},  # 0x11
    18: {"name": "server_port", "description": "Server Port", "fmt": "s"},  # 0x12
    19: {"name": "server", "description": "Server", "fmt": "s"},  # 0x13
    20: {"name": "device_type", "description": "Device Type", "fmt": "s"},  # 0x14
    DATALOGGER_SW_VERSION_REGISTER: {
        "name": "datalogger_sw_version",
        "description": "Datalogger software Version",  # 0x15
        "fmt": "s",
    },
    22: {
        "name": "datalogger_hw_version",
        "description": "Datalogger Hardware Version",  # 0x16
        "fmt": "s",
    },
    25: {"name": "netmask", "description": "Netmask", "fmt": "s"},  # 0x19
    26: {"name": "gateway_ip_address", "description": "Gateway IP", "fmt": "s"},  # 0x1A
    # 27-30 are unknown
    31: {"name": "date", "description": "Date", "fmt": "s"},  # 0x1F
    32: {"name": "reboot", "description": "Reboot", "fmt": "s"},  # ?,  # ??? # 0x20
    56: {"name": "wifi_ssid", "description": "WiFi SSID", "fmt": "s"},  # 0x38
    DATALOGGER_WIFI_PASSWORD_REGISTER: {
        "name": "wifi_password",
        "description": "WiFi password",
        "fmt": "s",
    },
}

# TODO
ANNOUNCE_REGISTER = {}
# TODO
DATA_REGISTER = {}
