import struct
from abc import ABC, abstractmethod

from shine2mqtt.growatt.protocol.messages.base import BaseMessage


class ByteEncoder:
    def encode_string(self, value: str, length: int) -> bytes:
        return struct.pack(f">{length}s", value.encode("ascii"))

    def encode_uint8(self, value: int) -> bytes:
        return struct.pack(">B", value)

    def encode_uint16(self, value: int) -> bytes:
        return struct.pack(">H", value)

    def encode_uint32(self, value: int) -> bytes:
        return struct.pack(">I", value)


class BaseEncoder[T: BaseMessage](ABC, ByteEncoder):
    def __init__(self, message_type: type[T]):
        self.message_type = message_type

    @abstractmethod
    def encode(self, message: T) -> bytes:
        pass
