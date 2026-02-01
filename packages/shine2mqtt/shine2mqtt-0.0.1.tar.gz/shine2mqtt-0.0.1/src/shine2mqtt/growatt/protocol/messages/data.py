from dataclasses import dataclass
from datetime import datetime

from shine2mqtt.growatt.protocol.constants import InverterStatus
from shine2mqtt.growatt.protocol.messages.base import BaseMessage


# Client messages ######################################################################
# requests
@dataclass
class GrowattDataMessage(BaseMessage):
    datalogger_serial: str
    inverter_serial: str
    timestamp: datetime
    inverter_status: InverterStatus
    # DC
    power_dc: float
    # DC 1
    voltage_dc_1: float
    current_dc_1: float
    power_dc_1: float
    # DC 2
    voltage_dc_2: float
    current_dc_2: float
    power_dc_2: float
    # AC
    power_ac: float
    frequency_ac: float
    # AC 1
    voltage_ac_1: float
    current_ac_1: float
    power_ac_1: float
    # AC line
    voltage_ac_l1_l2: float
    voltage_ac_l2_l3: float
    voltage_ac_l3_l1: float
    # Energy AC
    energy_ac_today: float
    energy_ac_total: float
    energy_dc_total: float
    # Energy DC 1
    energy_dc_1_today: float
    energy_dc_1_total: float
    # Energy DC 2
    energy_dc_2_today: float
    energy_dc_2_total: float


@dataclass
class GrowattBufferedDataMessage(GrowattDataMessage):
    pass
