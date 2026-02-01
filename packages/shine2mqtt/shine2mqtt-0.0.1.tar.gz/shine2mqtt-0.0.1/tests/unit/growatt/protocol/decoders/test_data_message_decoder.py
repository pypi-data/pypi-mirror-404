from datetime import datetime

import pytest

from shine2mqtt.growatt.protocol.constants import InverterStatus
from shine2mqtt.growatt.protocol.decoders.data import (
    DataRequestDecoder,
)
from shine2mqtt.growatt.protocol.messages.base import MBAPHeader
from shine2mqtt.growatt.protocol.messages.data import GrowattDataMessage
from tests.utils.loader import CapturedFrameLoader

frames, headers, payloads = CapturedFrameLoader.load("data_message")

DATALOGGER_SERIAL = "XGDABCDEFG"
INVERTER_SERIAL = "MLG0A12345"

EXPECTED_MESSAGES = [
    GrowattDataMessage(
        header=headers[0],
        datalogger_serial=DATALOGGER_SERIAL,
        inverter_serial=INVERTER_SERIAL,
        timestamp=datetime(2026, 1, 12, 11, 27),
        inverter_status=InverterStatus.NORMAL,
        power_dc=237.4,
        voltage_dc_1=325.4,
        current_dc_1=0.7,
        power_dc_1=237.4,
        voltage_dc_2=0.0,
        current_dc_2=0.0,
        power_dc_2=0.0,
        power_ac=232.7,
        frequency_ac=49.99,
        voltage_ac_1=232.2,
        current_ac_1=1.2,
        power_ac_1=234.4,
        voltage_ac_l1_l2=232.2,
        voltage_ac_l2_l3=0.0,
        voltage_ac_l3_l1=0.0,
        energy_ac_today=1.0,
        energy_ac_total=7446.5,
        energy_dc_total=7522.8,
        energy_dc_1_today=1.0,
        energy_dc_1_total=7522.8,
        energy_dc_2_today=0.0,
        energy_dc_2_total=0.0,
    ),
    GrowattDataMessage(
        header=headers[1],
        datalogger_serial=DATALOGGER_SERIAL,
        inverter_serial=INVERTER_SERIAL,
        timestamp=datetime(2026, 1, 12, 11, 27),
        inverter_status=InverterStatus.NORMAL,
        power_dc=240.4,
        voltage_dc_1=321.5,
        current_dc_1=0.7,
        power_dc_1=240.4,
        voltage_dc_2=0.0,
        current_dc_2=0.0,
        power_dc_2=0.0,
        power_ac=235.8,
        frequency_ac=49.97,
        voltage_ac_1=231.7,
        current_ac_1=1.2,
        power_ac_1=236.5,
        voltage_ac_l1_l2=231.7,
        voltage_ac_l2_l3=0.0,
        voltage_ac_l3_l1=0.0,
        energy_ac_today=1.0,
        energy_ac_total=7446.5,
        energy_dc_total=7522.8,
        energy_dc_1_today=1.0,
        energy_dc_1_total=7522.8,
        energy_dc_2_today=0.0,
        energy_dc_2_total=0.0,
    ),
]
# Build test cases from captured data
CASES = list(zip(headers[:2], payloads[:2], EXPECTED_MESSAGES, strict=True))


class TestDataRequestDecoder:
    @pytest.fixture
    def decoder(self):
        return DataRequestDecoder()

    @pytest.mark.parametrize("header,payload,expected_message", CASES, ids=list(range(len(CASES))))
    def test_decode_announce_request_valid_header_and_payload_success(
        self,
        decoder: DataRequestDecoder,
        header: MBAPHeader,
        payload: bytes,
        expected_message: GrowattDataMessage,
    ):
        message = decoder.decode(header, payload)

        assert message == expected_message
