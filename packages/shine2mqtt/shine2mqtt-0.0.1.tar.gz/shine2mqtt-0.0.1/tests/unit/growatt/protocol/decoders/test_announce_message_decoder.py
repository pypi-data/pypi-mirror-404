from datetime import datetime

import pytest

from shine2mqtt.growatt.protocol.decoders.announce import (
    AnnounceRequestDecoder,
)
from shine2mqtt.growatt.protocol.messages.announce import GrowattAnnounceMessage
from shine2mqtt.growatt.protocol.messages.base import MBAPHeader
from tests.utils.loader import CapturedFrameLoader

frames, headers, payloads = CapturedFrameLoader.load("announce_message")

DATALOGGER_SERIAL = "XGDABCDEFG"
INVERTER_SERIAL = "MLG0A12345"

EXPECTED_MESSAGES = [
    GrowattAnnounceMessage(
        header=headers[0],
        datalogger_serial=DATALOGGER_SERIAL,
        inverter_serial=INVERTER_SERIAL,
        active_power_ac_max=100,
        reactive_power_ac_max=0,
        power_factor=1.0,
        rated_power_ac=3000.0,
        rated_voltage_dc=100.0,
        inverter_fw_version="GH1.0",
        inverter_control_fw_version="ZAAA.8",
        lcd_language="English",
        device_type="PV Inverter",
        timestamp=datetime(2026, 1, 25, 13, 57, 8),
        voltage_ac_low_limit=184.0,
        voltage_ac_high_limit=264.5,
        frequency_ac_low_limit=47.5,
        frequency_ac_high_limit=51.5,
        power_factor_control_mode="Unity PF",
    )
]

# Build test cases from captured data
CASES = list(zip(headers, payloads, EXPECTED_MESSAGES, strict=True))


class TestAnnounceRequestDecoder:
    @pytest.fixture
    def decoder(self):
        return AnnounceRequestDecoder()

    @pytest.mark.parametrize(
        "header,payload,expected_message", CASES, ids=[f"{i}" for i in range(len(CASES))]
    )
    def test_decode_announce_request_valid_header_and_payload_success(
        self,
        decoder: AnnounceRequestDecoder,
        header: MBAPHeader,
        payload: bytes,
        expected_message: GrowattAnnounceMessage,
    ):
        message = decoder.decode(header, payload)

        assert message == expected_message
