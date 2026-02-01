from shine2mqtt.growatt.protocol.decoders.base import MessageDecoder
from shine2mqtt.growatt.protocol.messages import GrowattAnnounceMessage
from shine2mqtt.growatt.protocol.messages.base import MBAPHeader


class AnnounceRequestDecoder(MessageDecoder[GrowattAnnounceMessage]):
    def decode(self, header: MBAPHeader, payload: bytes) -> GrowattAnnounceMessage:
        return GrowattAnnounceMessage(
            # Custom Announce block ####################################################
            header=header,
            datalogger_serial=self.read_str(payload, 0, 10),
            # 10-30 is \x00
            inverter_serial=self.read_str(payload, 30, 10),
            #
            # Holding registers (read/write) ###########################################
            # See 4.1 Holding Registers in Protocol document v1.20(page 9)
            #
            # 03 Active Rate , Inverter Max output active power percent
            active_power_ac_max=self.read_u16(payload, 77),
            reactive_power_ac_max=self.read_u16(payload, 79),
            power_factor=self._read_u16_scaled(payload, 81, 0.0001),
            rated_power_ac=self._read_u32_scaled(payload, 83, 0.1),
            rated_voltage_dc=self._read_u16_scaled(payload, 87, 0.1),
            inverter_fw_version=self._decoder_inverter_fw_version(payload, 89),
            inverter_control_fw_version=self._decoder_inverter_control_fw_version(payload, 95),
            lcd_language=self._decoder_lcd_language(payload, 101),
            #
            device_type=self.read_str(payload, 139, 16).rstrip("\x00"),
            #
            timestamp=self._read_datetime(payload, offset=161, fmt="H"),
            voltage_ac_low_limit=self._read_u16_scaled(payload, 175, 0.1),
            voltage_ac_high_limit=self._read_u16_scaled(payload, 177, 0.1),
            frequency_ac_low_limit=self._read_u16_scaled(payload, 179, 0.01),
            frequency_ac_high_limit=self._read_u16_scaled(payload, 181, 0.01),
            power_factor_control_mode=self._decoder_power_factor_control_mode(payload, 249),
        )

    def _decoder_power_factor_control_mode(self, payload: bytes, offset: int) -> str:
        value = self.read_u16(payload, offset)
        power_factor_modes = {
            0: "Unity PF",
            1: "Default PF curve",
            2: "User PF curve",
            4: "Q under-excited",
            5: "Q over-excited",
            6: "Volt-VAR",
            7: "Direct Q control",
        }

        return power_factor_modes.get(value, "Unknown")

    def _decoder_inverter_fw_version(self, payload: bytes, offset: int) -> str:
        return self.read_str(payload, offset, 6).rstrip("\x00")

    def _decoder_inverter_control_fw_version(self, payload: bytes, offset: int) -> str:
        high = self.read_str(payload, offset, 2)
        mid = self.read_str(payload, offset + 2, 2)
        low = self.read_u16(payload, offset + 4)
        return f"{high}{mid}.{low}"

    def _decoder_lcd_language(self, payload: bytes, offset: int) -> str:
        lang_code = self.read_u16(payload, offset)
        lang_map = {
            0: "Italian",
            1: "English",
            2: "German",
            3: "Spanish",
            4: "French",
            5: "Chinese",
            6: "Polish",
            7: "Portuguese",
            8: "Hungarian",
        }
        return lang_map.get(lang_code, "Unknown")
