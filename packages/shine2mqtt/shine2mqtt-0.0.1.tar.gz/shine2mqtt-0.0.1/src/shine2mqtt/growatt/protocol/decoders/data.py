from shine2mqtt.growatt.protocol.constants import InverterStatus
from shine2mqtt.growatt.protocol.decoders.base import MessageDecoder
from shine2mqtt.growatt.protocol.messages.base import MBAPHeader
from shine2mqtt.growatt.protocol.messages.data import GrowattDataMessage


class DataRequestDecoder(MessageDecoder[GrowattDataMessage]):
    def decode(self, header: MBAPHeader, payload: bytes) -> GrowattDataMessage:
        return GrowattDataMessage(
            header=header,
            # Custom  data block #######################################################
            datalogger_serial=self.read_str(payload, 0, 10),
            #
            # 10-30 is \x00
            #
            # Holding registers (read/write) ###########################################
            # See 4.1 Holding Registers in Protocol document v1.20(page 9)
            # 23 Serial NO
            inverter_serial=self.read_str(payload, 30, 10),
            # 40-60 is \x00
            timestamp=self._read_datetime(payload, offset=60, fmt="B"),
            # "year": struct.unpack_from(">B", data, 60)[0],              # 45  Sys Year  System time-year
            # "month": struct.unpack_from(">B", data, 61)[0],             # 46
            # "day": struct.unpack_from(">B", data, 62)[0],               # 47
            # "hour": struct.unpack_from(">B", data, 63)[0],              # 48
            # "min": struct.unpack_from(">B", data, 64)[0],               # 49
            # "sec": struct.unpack_from(">B", data, 65)[0],               # 50
            # "weekly": struct.unpack_from(">B", data, 66)[0],            # 51
            #
            # 67-70 is \x00
            #
            # Input registers (read) ###################################################
            # See 4.2 Input Reg -> Protocol document v1.20 (page 33)
            # 0 Inverter Status
            inverter_status=InverterStatus(self.read_u16(payload, 71)),
            # 1 Ppv
            power_dc=self._read_u32_scaled(payload, 73, 0.1),
            # 3 Vpv1, 4 PV1Curr, 5 Ppv1
            voltage_dc_1=self._read_u16_scaled(payload, 77, 0.1),
            current_dc_1=self._read_u16_scaled(payload, 79, 0.1),
            power_dc_1=self._read_u32_scaled(payload, 81, 0.1),
            # 7 Vpv2, 8 PV2Curr, 9 Ppv2
            voltage_dc_2=self._read_u16_scaled(payload, 85, 0.1),
            current_dc_2=self._read_u16_scaled(payload, 87, 0.1),
            power_dc_2=self._read_u32_scaled(payload, 89, 0.1),
            # # 11 Vpv3, 12 PV3Curr, 13 Ppv3
            # "voltage_dc_3": self._read_u16(payload, 93, 0.1),
            # "current_dc_3": self._read_u16(payload, 95, 0.1),
            # "power_dc_3": self._read_u32(payload, 97, 0.1),
            # # 15 Vpv4, 16 PV4Curr, 17 Ppv4
            # "voltage_dc_4": self._read_u16(payload, 101, 0.1),
            # "current_dc_4": self._read_u16(payload, 103, 0.1),
            # "power_dc_4": self._read_u32(payload, 105, 0.1),
            # # 19 Vpv5, 20 PV5Curr, 21 Ppv5
            # "voltage_dc_5": self._read_u16(payload, 109, 0.1),
            # "current_dc_5": self._read_u16(payload, 111, 0.1),
            # "power_dc_5": self._read_u32(payload, 113, 0.1),
            # 35 Pac, 37 Fac
            power_ac=self._read_u32_scaled(payload, 117, 0.1),
            frequency_ac=self._read_u16_scaled(payload, 121, 0.01),
            # 38 Vac1, 39 Iac1, 40 Pac1
            voltage_ac_1=self._read_u16_scaled(payload, 123, 0.1),
            current_ac_1=self._read_u16_scaled(payload, 125, 0.1),
            power_ac_1=self._read_u32_scaled(payload, 127, 0.1),
            # # 42 Vac2, 43 Iac2, 44 Pac2
            # "voltage_ac_2": self._read_u16(payload, 131, 0.1),
            # "current_ac_2": self._read_u16(payload, 133, 0.1),
            # "power_ac_2": self._read_u32(payload, 135, 0.1),
            # # 46 Vac3, 47 Iac3, 48 Pac3
            # "voltage_ac_3": self._read_u16(payload, 139, 0.1),
            # "current_ac_3": self._read_u16(payload, 141, 0.1),
            # "power_ac_3": self._read_u32(payload, 143, 0.1),
            # 50 Vac_RS, Vac_ST, Vac_TR  Three phase grid voltage, line voltages
            voltage_ac_l1_l2=self._read_u16_scaled(payload, 147, 0.1),
            voltage_ac_l2_l3=self._read_u16_scaled(payload, 149, 0.1),
            voltage_ac_l3_l1=self._read_u16_scaled(payload, 151, 0.1),
            # 53 Eactoday,  Today generate energy (ac)
            energy_ac_today=self._read_u32_scaled(payload, 169, 0.1),
            energy_ac_total=self._read_u32_scaled(payload, 173, 0.1),
            energy_dc_total=self._read_u32_scaled(payload, 177, 0.1),
            energy_dc_1_today=self._read_u32_scaled(payload, 181, 0.1),
            energy_dc_1_total=self._read_u32_scaled(payload, 185, 0.1),
            energy_dc_2_today=self._read_u32_scaled(payload, 189, 0.1),
            energy_dc_2_total=self._read_u32_scaled(payload, 193, 0.1),
        )


class BufferDataRequestDecoder(DataRequestDecoder):
    pass
