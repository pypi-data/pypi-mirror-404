from datetime import datetime

import pytest

from shine2mqtt.growatt.protocol.constants import InverterStatus
from shine2mqtt.growatt.protocol.frame.decoder import FrameDecoder
from shine2mqtt.growatt.protocol.frame.factory import FrameFactory
from shine2mqtt.growatt.protocol.messages import (
    BaseMessage,
    GrowattAnnounceMessage,
    MBAPHeader,
)
from shine2mqtt.growatt.protocol.messages.ack import GrowattAckMessage
from shine2mqtt.growatt.protocol.messages.config import GrowattGetConfigResponseMessage
from shine2mqtt.growatt.protocol.messages.data import GrowattDataMessage
from shine2mqtt.growatt.protocol.messages.ping import GrowattPingMessage
from tests.utils.loader import CapturedFrameLoader

announce_frames, announce_headers, announce_payloads = CapturedFrameLoader.load("announce_message")
buffered_data_frames, buffered_data_headers, buffered_data_payloads = CapturedFrameLoader.load(
    "buffered_data_message"
)
data_frames, data_headers, data_payloads = CapturedFrameLoader.load("data_message")
get_config_frames, get_config_headers, get_config_payloads = CapturedFrameLoader.load(
    "get_config_message"
)
ping_frames, ping_headers, ping_payloads = CapturedFrameLoader.load("ping_message")

ack_frames, ack_headers, ack_payloads = CapturedFrameLoader.load("ack_message")

DECRYPTION_KEY = b"Growatt"
DATALOGGER_SERIAL = "XGDABCDEFG"
INVERTER_SERIAL = "MLG0A12345"


EXPECTED_MESSAGES = [
    GrowattAnnounceMessage(
        header=announce_headers[0],
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
    ),
    GrowattDataMessage(
        header=buffered_data_headers[0],
        datalogger_serial=DATALOGGER_SERIAL,
        inverter_serial=INVERTER_SERIAL,
        timestamp=datetime(2026, 1, 12, 11, 27),
        inverter_status=InverterStatus.NORMAL,
        power_dc=46.50,
        voltage_dc_1=284.9,
        current_dc_1=0.1,
        power_dc_1=46.5,
        voltage_dc_2=0.0,
        current_dc_2=0.0,
        power_dc_2=0.0,
        power_ac=45.6,
        frequency_ac=50.03,
        voltage_ac_1=233.2,
        current_ac_1=1.0,
        power_ac_1=47.9,
        voltage_ac_l1_l2=233.2,
        voltage_ac_l2_l3=0.0,
        voltage_ac_l3_l1=0.0,
        energy_ac_today=0.0,
        energy_ac_total=7430.4,
        energy_dc_total=7506.5,
        energy_dc_1_today=0.0,
        energy_dc_1_total=7506.5,
        energy_dc_2_today=0.0,
        energy_dc_2_total=0.0,
    ),
    GrowattDataMessage(
        header=data_headers[0],
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
    GrowattGetConfigResponseMessage(
        header=get_config_headers[14],
        datalogger_serial=DATALOGGER_SERIAL,
        register=14,
        length=13,
        data=b"192.168.1.100",
        name="ip_address",
        description="Local IP",
        value="192.168.1.100",
    ),
    GrowattAckMessage(
        header=ack_headers[0],
        ack=True,
    ),
    GrowattPingMessage(
        header=ping_headers[0],
        datalogger_serial=DATALOGGER_SERIAL,
    ),
]


CASES = [
    (announce_frames[0], announce_headers[0], EXPECTED_MESSAGES[0]),
    (buffered_data_frames[0], buffered_data_headers[0], EXPECTED_MESSAGES[1]),
    (data_frames[0], data_headers[0], EXPECTED_MESSAGES[2]),
    (get_config_frames[14], get_config_headers[14], EXPECTED_MESSAGES[3]),
    (ack_frames[0], ack_headers[0], EXPECTED_MESSAGES[4]),
    (ping_frames[0], ping_headers[0], EXPECTED_MESSAGES[5]),
]


class TestFrameDecoder:
    @pytest.fixture
    def decoder(self):
        return FrameFactory.server_decoder()

    @pytest.mark.parametrize("frame,header,expected_message", CASES, ids=list(range(len(CASES))))
    def test_decode_valid_frame_success(
        self,
        decoder: FrameDecoder,
        frame: bytes,
        header: MBAPHeader,
        expected_message: BaseMessage,
    ):
        message = decoder.decode(header, frame)

        assert message == expected_message
