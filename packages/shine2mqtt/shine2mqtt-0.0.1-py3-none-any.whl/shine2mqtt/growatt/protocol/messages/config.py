from dataclasses import dataclass

from shine2mqtt.growatt.protocol.messages.base import BaseMessage


# Client messages ######################################################################
# requests
# responses
@dataclass
class GrowattGetConfigResponseMessage(BaseMessage):
    datalogger_serial: str
    register: int
    length: int
    data: bytes
    name: str | None = None
    description: str = ""
    value: int | str | None = None


# Server messages ######################################################################
# responses
# request
@dataclass
class GrowattSetConfigRequestMessage(BaseMessage):
    datalogger_serial: str
    register: int
    length: int
    value: int | str


@dataclass
class GrowattGetConfigRequestMessage(BaseMessage):
    datalogger_serial: str
    register_start: int
    register_end: int
