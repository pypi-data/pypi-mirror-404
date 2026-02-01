import pytest

from shine2mqtt.growatt.protocol.config import ConfigRegistry
from shine2mqtt.growatt.protocol.decoders.config import (
    GetConfigResponseDecoder,
)
from shine2mqtt.growatt.protocol.messages.config import (
    GrowattGetConfigResponseMessage,
)
from shine2mqtt.growatt.protocol.messages.header import MBAPHeader
from tests.utils.loader import CapturedFrameLoader

frames, headers, payloads = CapturedFrameLoader.load("get_config_message")

DATALOGGER_SERIAL = "XGDABCDEFG"


EXPECTED_MESSAGES = [
    GrowattGetConfigResponseMessage(
        header=headers[14],
        datalogger_serial=DATALOGGER_SERIAL,
        register=14,
        length=13,
        data=b"192.168.1.100",
        name="ip_address",
        description="Local IP",
        value="192.168.1.100",
    ),
]

CASES = [(headers[14], payloads[14], EXPECTED_MESSAGES[0])]


class TestGetConfigResponseDecoder:
    @pytest.fixture
    def decoder(self):
        return GetConfigResponseDecoder(ConfigRegistry())

    @pytest.mark.parametrize(
        "header,payload,expected_message", CASES, ids=[f"{i}" for i in range(len(CASES))]
    )
    def test_decode_get_config_response_valid_header_and_payload_success(
        self,
        decoder: GetConfigResponseDecoder,
        header: MBAPHeader,
        payload: bytes,
        expected_message: GrowattGetConfigResponseMessage,
    ):
        message = decoder.decode(header, payload)

        assert message == expected_message
