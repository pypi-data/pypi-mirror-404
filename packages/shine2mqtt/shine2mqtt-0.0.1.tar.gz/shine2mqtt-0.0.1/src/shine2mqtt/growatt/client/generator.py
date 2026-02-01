from datetime import datetime

from shine2mqtt.growatt.protocol.constants import FunctionCode, InverterStatus
from shine2mqtt.growatt.protocol.messages import (
    GrowattAnnounceMessage,
    GrowattDataMessage,
    GrowattGetConfigResponseMessage,
    GrowattPingMessage,
    MBAPHeader,
)
from shine2mqtt.growatt.protocol.messages.ack import GrowattAckMessage

DATALOGGER_SERIAL = "XGD1234567"
INVERTER_SERIAL = "MLABC12345"


class DataGenerator:
    def generate_announce_message(self, transaction_id: int) -> GrowattAnnounceMessage:
        return GrowattAnnounceMessage(
            header=MBAPHeader(
                transaction_id=transaction_id,
                protocol_id=6,
                length=0,  # Will be calculated by encoder
                unit_id=1,
                function_code=FunctionCode.ANNOUNCE,
            ),
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
            timestamp=datetime.now(),
            voltage_ac_low_limit=184.0,
            voltage_ac_high_limit=264.5,
            frequency_ac_low_limit=47.5,
            frequency_ac_high_limit=51.5,
            power_factor_control_mode="Unity PF",
        )

    def generate_data_message(self, transaction_id: int) -> GrowattDataMessage:
        """Generate a DATA message with simulated inverter data"""
        return GrowattDataMessage(
            header=MBAPHeader(
                transaction_id=transaction_id,
                protocol_id=6,
                length=0,
                unit_id=1,
                function_code=FunctionCode.DATA,
            ),
            datalogger_serial=DATALOGGER_SERIAL,
            inverter_serial=INVERTER_SERIAL,
            timestamp=datetime.now(),
            inverter_status=InverterStatus.NORMAL,
            # DC values
            power_dc=160.0,
            voltage_dc_1=288.8,
            current_dc_1=0.5,
            power_dc_1=160.0,
            voltage_dc_2=0.0,
            current_dc_2=0.0,
            power_dc_2=0.0,
            # AC values
            power_ac=156.8,
            frequency_ac=50.04,
            voltage_ac_1=232.4,
            current_ac_1=0.9,
            power_ac_1=158.1,
            voltage_ac_l1_l2=232.4,
            voltage_ac_l2_l3=0.0,
            voltage_ac_l3_l1=0.0,
            # Energy values
            energy_ac_today=1.5,
            energy_ac_total=7428.8,
            energy_dc_total=7504.9,
            energy_dc_1_today=1.5,
            energy_dc_1_total=7504.9,
            energy_dc_2_today=0.0,
            energy_dc_2_total=0.0,
        )

    def generate_ping_message(self, transaction_id: int) -> GrowattPingMessage:
        """Generate a PING message"""
        return GrowattPingMessage(
            header=MBAPHeader(
                transaction_id=transaction_id,
                protocol_id=6,
                length=0,
                unit_id=1,
                function_code=FunctionCode.PING,
            ),
            datalogger_serial=DATALOGGER_SERIAL,
        )

    def generate_get_config_response(
        self, transaction_id: int, register: int
    ) -> GrowattGetConfigResponseMessage:
        """Generate a GET_CONFIG response message"""
        return GrowattGetConfigResponseMessage(
            header=MBAPHeader(
                transaction_id=transaction_id,
                protocol_id=6,
                length=0,
                unit_id=1,
                function_code=FunctionCode.GET_CONFIG,
            ),
            datalogger_serial=DATALOGGER_SERIAL,
            register=register,
            length=1,
            data=b"X",  # Dummy data
            name="",
            description="",
            value=None,
        )

    def generate_ack_message(
        self, transaction_id: int, function_code: FunctionCode
    ) -> GrowattAckMessage:
        """Generate an ACK message"""
        return GrowattAckMessage(
            header=MBAPHeader(
                transaction_id=transaction_id,
                protocol_id=6,
                length=0,
                unit_id=1,
                function_code=function_code,
            ),
            ack=True,
        )
