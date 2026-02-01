import pytest

from shine2mqtt.growatt.protocol.decoders.header import HeaderDecoder
from tests.utils.loader import CapturedFrameLoader

frames, headers, payloads = CapturedFrameLoader.load("ping_message")


class TestHeaderDecoder:
    @pytest.mark.parametrize(
        "frame,expected_header",
        list(zip(frames[:2], headers[:2], strict=True)),
        ids=[f"case_{i}" for i in range(2)],
    )
    def test_decode(self, frame, expected_header):
        decoder = HeaderDecoder()
        header = decoder.decode(frame)

        assert header == expected_header
