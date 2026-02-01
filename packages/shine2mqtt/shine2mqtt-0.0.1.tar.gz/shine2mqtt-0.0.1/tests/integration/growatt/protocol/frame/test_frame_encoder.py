import json
from pathlib import Path

import pytest

from shine2mqtt.growatt.protocol.constants import FunctionCode
from shine2mqtt.growatt.protocol.frame.encoder import FrameEncoder
from shine2mqtt.growatt.protocol.messages import (
    BaseMessage,
    GrowattGetConfigRequestMessage,
    GrowattPingMessage,
    GrowattSetConfigRequestMessage,
    MBAPHeader,
)
from shine2mqtt.growatt.protocol.messages.ack import GrowattAckMessage

ENCRYPTION_KEY = b"Growatt"

MESSAGES = [
    GrowattPingMessage(
        header=MBAPHeader(
            transaction_id=2,
            protocol_id=6,
            length=0,
            unit_id=1,
            function_code=FunctionCode.PING,
        ),
        datalogger_serial="XGD4A49AGC",
    ),
    GrowattGetConfigRequestMessage(
        header=MBAPHeader(
            transaction_id=2,
            protocol_id=6,
            length=0,
            unit_id=1,
            function_code=FunctionCode.GET_CONFIG,
        ),
        datalogger_serial="XGD4A49AGC",
        register_start=0,
        register_end=10,
    ),
    GrowattSetConfigRequestMessage(
        header=MBAPHeader(
            transaction_id=2,
            protocol_id=6,
            length=0,
            unit_id=1,
            function_code=FunctionCode.SET_CONFIG,
        ),
        datalogger_serial="XGD4A49AGC",
        register=5,
        length=2,
        value=42,
    ),
    GrowattAckMessage(
        header=MBAPHeader(
            transaction_id=2,
            protocol_id=6,
            length=0,
            unit_id=1,
            function_code=FunctionCode.DATA,
        ),
        ack=True,
    ),
]

FRAMES = [
    b"\x00\x02\x00\x06\x00\x0c\x01\x16\x1f5+C @M\x065,\x15|",
    b"\x00\x02\x00\x06\x00\x10\x01\x19\x1f5+C @M\x065,wat~\xdcb",
    b"\x00\x02\x00\x06\x00\x12\x01\x18\x1f5+C @M\x065,wdtvGX\x19\x7f",
    b"\x00\x02\x00\x06\x00\x03\x01\x04G9\x98",
]

CASES = [
    (MESSAGES[0], FRAMES[0]),
    (MESSAGES[1], FRAMES[1]),
    (MESSAGES[2], FRAMES[2]),
    (MESSAGES[3], FRAMES[3]),
]


def load_captured_frames(message_type: str):
    """Load captured frames from JSON for a specific message type"""
    # Path from test file: tests/integration/protocol/frame/test_*.py
    # Target: tests/data/captured/...
    base_path = Path(__file__).parent.parent.parent.parent / "data" / "captured"
    json_file = base_path / "shine_wifi_x" / "mic_3000tl_x" / f"{message_type}.json"

    if not json_file.exists():
        return []

    with open(json_file) as f:
        data = json.load(f)

    frames = [bytes.fromhex(f) for f in data["frames"]]
    headers = [MBAPHeader.fromdict(header) for header in data["headers"]]
    payloads = [bytes.fromhex(p) for p in data["payloads"]]

    return frames, headers, payloads


class TestFrameEncoder:
    @pytest.fixture
    def encoder(self):
        from shine2mqtt.growatt.protocol.frame import FrameFactory

        return FrameFactory.encoder()

    @pytest.mark.parametrize("message,expected_frame", CASES, ids=list(range(len(CASES))))
    def test_encode_valid_message_success(
        self,
        encoder: FrameEncoder,
        message: BaseMessage,
        expected_frame: bytes,
    ):
        frame = encoder.encode(message)

        assert frame == expected_frame
