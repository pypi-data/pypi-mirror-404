from dataclasses import dataclass

from shine2mqtt.growatt.protocol.messages.base import BaseMessage


@dataclass
class GrowattPingMessage(BaseMessage):
    datalogger_serial: str
