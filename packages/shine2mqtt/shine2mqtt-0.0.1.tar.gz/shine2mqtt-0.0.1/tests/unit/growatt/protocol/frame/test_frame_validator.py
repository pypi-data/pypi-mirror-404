import struct

import pytest

from shine2mqtt.growatt.protocol.constants import FunctionCode
from shine2mqtt.growatt.protocol.frame.crc import CRCCalculator
from shine2mqtt.growatt.protocol.frame.validator import FrameValidator
from shine2mqtt.growatt.protocol.messages.base import MBAPHeader
from tests.utils.loader import CapturedFrameLoader

frames, _, _ = CapturedFrameLoader.load("data_message")


class TestFrameValidator:
    @pytest.fixture
    def validator(self):
        crc_calculator = CRCCalculator()
        return FrameValidator(crc_calculator)

    @pytest.fixture
    def valid_header(self):
        return MBAPHeader(
            transaction_id=18,
            protocol_id=6,
            length=199,
            unit_id=1,
            function_code=FunctionCode.DATA,
        )

    @pytest.fixture
    def valid_frame(self):
        return frames[0]

    def test_validate_valid_frame_succeeds(
        self, validator: FrameValidator, valid_frame: bytes, valid_header: MBAPHeader
    ):
        validator.validate(valid_frame, valid_header)

    def test_validate_invalid_payload_length_fails(
        self, validator: FrameValidator, valid_frame: bytes, valid_header: MBAPHeader
    ):
        actual_payload_length = valid_header.length
        valid_header.length = 42

        with pytest.raises(
            ValueError,
            match=f"Invalid payload length: expected {42}, got {actual_payload_length}",
        ):
            validator.validate(valid_frame, valid_header)

    def test_validate_frame_with_invalid_crc_failure(
        self, validator: FrameValidator, valid_frame: bytes, valid_header: MBAPHeader
    ):
        invalid_crc = b"\x00\x00"
        actual_crc = struct.unpack_from("<H", valid_frame, len(valid_frame) - 2)[0]
        frame_with_invalid_crc = valid_frame[:-2] + invalid_crc

        with pytest.raises(
            ValueError,
            match=f"Invalid CRC: expected 0x0000, got 0x{actual_crc:04x}.",
        ):
            validator.validate(frame_with_invalid_crc, valid_header)
