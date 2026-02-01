import struct

from shine2mqtt.growatt.protocol.frame.crc import CRC16_LENGTH, CRCCalculator
from shine2mqtt.growatt.protocol.messages.base import MBAPHeader


class FrameValidator:
    def __init__(self, crc_calculator: CRCCalculator):
        self.crc_calculator = crc_calculator

    def validate(self, frame: bytes, header: MBAPHeader) -> None:
        self._validate_payload_length(frame, header.length)

        self._validate_crc(frame)

    def _validate_payload_length(self, frame: bytes, expected_payload_length: int) -> None:
        header_length = 8
        payload_length = len(frame) - header_length
        if payload_length != expected_payload_length:
            raise ValueError(
                f"Invalid payload length: expected {expected_payload_length}, got {payload_length}."
            )

    def _validate_crc(self, frame: bytes) -> None:
        offset = len(frame) - CRC16_LENGTH
        crc = struct.unpack_from("<H", frame, offset)[0]
        computed_crc = self.crc_calculator.calculate_crc16(frame)

        if crc != computed_crc:
            raise ValueError(f"Invalid CRC: expected 0x{crc:04x}, got 0x{computed_crc:04x}.")
