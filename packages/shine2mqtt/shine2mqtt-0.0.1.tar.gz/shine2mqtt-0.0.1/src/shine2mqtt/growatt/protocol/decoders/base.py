import struct
from abc import ABC, abstractmethod
from datetime import datetime

from loguru import logger

from shine2mqtt.growatt.protocol.messages import BaseMessage, MBAPHeader


class ByteDecoder:
    @staticmethod
    def read_u8(frame: bytes, offset: int) -> int:
        return struct.unpack_from(">B", frame, offset)[0]

    @staticmethod
    def read_u16(frame: bytes, offset: int) -> int:
        return struct.unpack_from(">H", frame, offset)[0]

    @staticmethod
    def read_u32(frame: bytes, offset: int) -> int:
        return struct.unpack_from(">I", frame, offset)[0]

    @staticmethod
    def read_str(frame: bytes, offset: int, length: int) -> str:
        return struct.unpack_from(f">{length}s", frame, offset)[0].decode("ascii").strip()


class MessageDecoder[T: BaseMessage](ABC, ByteDecoder):
    DEFAULT_DATETIME = datetime(2000, 1, 1, 0, 0, 0)

    FLOAT_DIGITS = 6

    @abstractmethod
    def decode(self, header: MBAPHeader, payload: bytes) -> T:
        pass

    def _read_u8_scaled(self, frame: bytes, offset: int, scale: float) -> float:
        value = self.read_u8(frame, offset)
        return round(value * scale, self.FLOAT_DIGITS)

    def _read_u16_scaled(self, frame: bytes, offset: int, scale: float) -> float:
        value = self.read_u16(frame, offset)
        return round(value * scale, self.FLOAT_DIGITS)

    def _read_u32_scaled(self, frame: bytes, offset: int, scale: float) -> float:
        value = self.read_u32(frame, offset)
        return round(value * scale, self.FLOAT_DIGITS)

    def _read_datetime(self, frame: bytes, offset: int, fmt: str) -> datetime:
        step = 2 if fmt == "H" else 1
        year_offset = 0 if fmt == "H" else 2000

        year = struct.unpack_from(f">{fmt}", frame, offset + 0)[0] + year_offset
        month = struct.unpack_from(f">{fmt}", frame, offset + 1 * step)[0]
        day = struct.unpack_from(f">{fmt}", frame, offset + 2 * step)[0]
        hour = struct.unpack_from(f">{fmt}", frame, offset + 3 * step)[0]
        minute = struct.unpack_from(f">{fmt}", frame, offset + 4 * step)[0]
        second = struct.unpack_from(f">{fmt}", frame, offset + 5 * step)[0]

        try:
            return datetime(
                year=year, month=month, day=day, hour=hour, minute=minute, second=second
            )
        except ValueError:
            logger.warning(
                f"Invalid datetime values: {year}-{month}-{day} {hour}:{minute}:{second}, return default datetime {self.DEFAULT_DATETIME}"
            )
            return self.DEFAULT_DATETIME
