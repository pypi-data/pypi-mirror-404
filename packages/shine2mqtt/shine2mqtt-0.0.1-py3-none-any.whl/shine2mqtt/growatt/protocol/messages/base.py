from dataclasses import dataclass

from shine2mqtt.growatt.protocol.messages.header import MBAPHeader


@dataclass
class BaseMessage:
    header: MBAPHeader
