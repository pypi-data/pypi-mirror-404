import struct

from shine2mqtt.growatt.protocol.encoders.base import BaseEncoder
from shine2mqtt.growatt.protocol.messages.announce import GrowattAnnounceMessage


class AnnouncePayloadEncoder(BaseEncoder[GrowattAnnounceMessage]):
    def __init__(self):
        super().__init__(GrowattAnnounceMessage)

    def encode(self, message: GrowattAnnounceMessage) -> bytes:
        payload = bytearray(252)  # Total payload size from decoder

        # Datalogger serial (0-10)
        payload[0:10] = self.encode_string(message.datalogger_serial, 10)
        # 10-30 is \x00 (padding)
        # Inverter serial (30-40)
        payload[30:40] = self.encode_string(message.inverter_serial, 10)

        # Active/reactive power and power factor
        payload[77:79] = self.encode_uint16(message.active_power_ac_max)
        payload[79:81] = self.encode_uint16(message.reactive_power_ac_max)
        payload[81:83] = self.encode_uint16(int(message.power_factor / 0.0001))
        payload[83:87] = self.encode_uint32(int(message.rated_power_ac / 0.1))
        payload[87:89] = self.encode_uint16(int(message.rated_voltage_dc / 0.1))

        # Inverter firmware version (89-95)
        payload[89:95] = self.encode_string(message.inverter_fw_version, 6)

        # Inverter control firmware version (95-101)
        # Format: "ZAAA.8" -> high=ZA, mid=AA, low=8
        version_parts = message.inverter_control_fw_version.split(".")
        if len(version_parts) == 2:
            payload[95:97] = self.encode_string(version_parts[0][:2], 2)
            payload[97:99] = self.encode_string(version_parts[0][2:4], 2)
            payload[99:101] = self.encode_uint16(int(version_parts[1]))

        # LCD language (101-103)
        lang_map = {
            "Italian": 0,
            "English": 1,
            "German": 2,
            "Spanish": 3,
            "French": 4,
            "Chinese": 5,
            "Polish": 6,
            "Portuguese": 7,
            "Hungarian": 8,
        }
        payload[101:103] = self.encode_uint16(lang_map.get(message.lcd_language, 1))

        # Device type (139-155)
        payload[139:155] = self.encode_string(message.device_type, 16)

        # System datetime (161-175)
        payload[161:163] = struct.pack(">H", message.timestamp.year)
        payload[163:165] = struct.pack(">H", message.timestamp.month)
        payload[165:167] = struct.pack(">H", message.timestamp.day)
        payload[167:169] = struct.pack(">H", message.timestamp.hour)
        payload[169:171] = struct.pack(">H", message.timestamp.minute)
        payload[171:173] = struct.pack(">H", message.timestamp.second)
        payload[173:175] = struct.pack(">H", message.timestamp.weekday())

        # Voltage and frequency limits
        payload[175:177] = self.encode_uint16(int(message.voltage_ac_low_limit / 0.1))
        payload[177:179] = self.encode_uint16(int(message.voltage_ac_high_limit / 0.1))
        payload[179:181] = self.encode_uint16(int(message.frequency_ac_low_limit / 0.01))
        payload[181:183] = self.encode_uint16(int(message.frequency_ac_high_limit / 0.01))

        # Power factor control mode (249-251)
        pf_mode_map = {
            "Unity PF": 0,
            "Default PF curve": 1,
            "User PF curve": 2,
            "Q under-excited": 4,
            "Q over-excited": 5,
            "Volt-VAR": 6,
            "Direct Q control": 7,
        }
        payload[249:251] = self.encode_uint16(pf_mode_map.get(message.power_factor_control_mode, 0))

        return bytes(payload)
