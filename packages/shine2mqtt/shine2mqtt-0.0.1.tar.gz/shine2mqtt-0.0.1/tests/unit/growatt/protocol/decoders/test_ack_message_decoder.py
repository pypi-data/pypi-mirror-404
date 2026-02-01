import pytest

from shine2mqtt.growatt.protocol.decoders.ack import AckMessageResponseDecoder
from shine2mqtt.growatt.protocol.messages.ack import GrowattAckMessage
from tests.utils.loader import CapturedFrameLoader

frames, headers, payloads = CapturedFrameLoader.load("ack_message")

EXPECTED_MESSAGES = [
    GrowattAckMessage(header=headers[0], ack=True),
    GrowattAckMessage(header=headers[1], ack=False),
]

CASES = list(zip(headers[:2], payloads[:2], EXPECTED_MESSAGES, strict=True))


class TestAckMessageResponseDecoder:
    @pytest.mark.parametrize(
        "header,payload,expected_message", CASES, ids=[f"case_{i}" for i in range(len(CASES))]
    )
    def test_decode(self, header, payload, expected_message):
        decoder = AckMessageResponseDecoder()
        message = decoder.decode(header, payload)
        assert message == expected_message
