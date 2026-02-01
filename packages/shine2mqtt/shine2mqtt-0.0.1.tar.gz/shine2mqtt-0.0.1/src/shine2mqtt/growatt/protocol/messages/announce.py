from dataclasses import dataclass
from datetime import datetime

from shine2mqtt.growatt.protocol.messages.base import BaseMessage


# Client messages ######################################################################
# requests
@dataclass
class GrowattAnnounceMessage(BaseMessage):
    datalogger_serial: str
    inverter_serial: str
    active_power_ac_max: int
    reactive_power_ac_max: int
    power_factor: float
    rated_power_ac: float
    rated_voltage_dc: float
    inverter_fw_version: str
    inverter_control_fw_version: str
    lcd_language: str
    device_type: str
    timestamp: datetime

    voltage_ac_low_limit: float
    voltage_ac_high_limit: float
    frequency_ac_low_limit: float
    frequency_ac_high_limit: float
    power_factor_control_mode: str
