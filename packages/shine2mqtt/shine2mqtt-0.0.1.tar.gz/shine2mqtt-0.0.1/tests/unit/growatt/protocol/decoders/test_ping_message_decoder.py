import pytest

from shine2mqtt.growatt.protocol.decoders.ping import PingRequestDecoder
from shine2mqtt.growatt.protocol.messages.base import MBAPHeader
from shine2mqtt.growatt.protocol.messages.ping import GrowattPingMessage
from tests.utils.loader import CapturedFrameLoader

frames, headers, payloads = CapturedFrameLoader.load("ping_message")

DATALOGGER_SERIAL = "XGDABCDEFG"

EXPECTED_MESSAGES = [
    GrowattPingMessage(
        header=headers[0],
        datalogger_serial=DATALOGGER_SERIAL,
    ),
    GrowattPingMessage(
        header=headers[1],
        datalogger_serial=DATALOGGER_SERIAL,
    ),
]

CASES = list(zip(headers[:2], payloads[:2], EXPECTED_MESSAGES, strict=True))


class TestPingRequestDecoder:
    @pytest.fixture
    def decoder(self):
        return PingRequestDecoder()

    @pytest.mark.parametrize("header,payload,expected_message", CASES, ids=list(range(len(CASES))))
    def test_decode_ping_request_valid_header_and_payload_success(
        self,
        decoder: PingRequestDecoder,
        header: MBAPHeader,
        payload: bytes,
        expected_message: GrowattPingMessage,
    ):
        message = decoder.decode(header, payload)

        assert message == expected_message
