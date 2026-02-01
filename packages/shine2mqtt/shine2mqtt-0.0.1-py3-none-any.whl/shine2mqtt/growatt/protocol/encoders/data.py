import struct

from shine2mqtt.growatt.protocol.encoders.base import BaseEncoder
from shine2mqtt.growatt.protocol.messages.data import (
    GrowattBufferedDataMessage,
    GrowattDataMessage,
)


class DataPayloadEncoder(BaseEncoder[GrowattDataMessage]):
    def __init__(self):
        super().__init__(GrowattDataMessage)

    def encode(self, message: GrowattDataMessage) -> bytes:
        payload = bytearray(197)

        # Datalogger serial (0-10)
        payload[0:10] = self.encode_string(message.datalogger_serial, 10)
        # 10-30 is \x00 (padding)
        # Inverter serial (30-40)
        payload[30:40] = self.encode_string(message.inverter_serial, 10)
        # 40-60 is \x00 (padding)

        # System datetime (60-67) - format as bytes (B)
        payload[60] = struct.pack(">B", message.timestamp.year % 100)[0]
        payload[61] = struct.pack(">B", message.timestamp.month)[0]
        payload[62] = struct.pack(">B", message.timestamp.day)[0]
        payload[63] = struct.pack(">B", message.timestamp.hour)[0]
        payload[64] = struct.pack(">B", message.timestamp.minute)[0]
        payload[65] = struct.pack(">B", message.timestamp.second)[0]
        payload[66] = struct.pack(">B", message.timestamp.weekday())[0]
        # 67-71 is \x00 (padding)

        # Inverter status (71-73)
        payload[71:73] = self.encode_uint16(message.inverter_status.value)

        # DC Power (73-77)
        payload[73:77] = self.encode_uint32(int(message.power_dc * 10))

        # DC 1 (77-85)
        payload[77:79] = self.encode_uint16(int(message.voltage_dc_1 * 10))
        payload[79:81] = self.encode_uint16(int(message.current_dc_1 * 10))
        payload[81:85] = self.encode_uint32(int(message.power_dc_1 * 10))

        # DC 2 (85-93)
        payload[85:87] = self.encode_uint16(int(message.voltage_dc_2 * 10))
        payload[87:89] = self.encode_uint16(int(message.current_dc_2 * 10))
        payload[89:93] = self.encode_uint32(int(message.power_dc_2 * 10))

        # AC Power and frequency (117-123)
        payload[117:121] = self.encode_uint32(int(message.power_ac * 10))
        payload[121:123] = self.encode_uint16(int(message.frequency_ac * 100))

        # AC 1 (123-131)
        payload[123:125] = self.encode_uint16(int(message.voltage_ac_1 * 10))
        payload[125:127] = self.encode_uint16(int(message.current_ac_1 * 10))
        payload[127:131] = self.encode_uint32(int(message.power_ac_1 * 10))

        # AC line voltages (147-153)
        payload[147:149] = self.encode_uint16(int(message.voltage_ac_l1_l2 * 10))
        payload[149:151] = self.encode_uint16(int(message.voltage_ac_l2_l3 * 10))
        payload[151:153] = self.encode_uint16(int(message.voltage_ac_l3_l1 * 10))

        # Energy AC (169-178)
        payload[169:173] = self.encode_uint32(int(message.energy_ac_today * 10))
        payload[173:177] = self.encode_uint32(int(message.energy_ac_total * 10))

        # Energy DC (177-194)
        payload[177:181] = self.encode_uint32(int(message.energy_dc_total * 10))
        payload[181:185] = self.encode_uint32(int(message.energy_dc_1_today * 10))
        payload[185:189] = self.encode_uint32(int(message.energy_dc_1_total * 10))
        payload[189:193] = self.encode_uint32(int(message.energy_dc_2_today * 10))
        payload[193:197] = self.encode_uint32(int(message.energy_dc_2_total * 10))

        return bytes(payload)


class BufferedDataPayloadEncoder(DataPayloadEncoder):
    def __init__(self):
        BaseEncoder.__init__(self, GrowattBufferedDataMessage)
