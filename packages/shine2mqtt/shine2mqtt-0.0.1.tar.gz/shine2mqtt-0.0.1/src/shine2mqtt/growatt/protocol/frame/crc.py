# CRC-16-ANSI/CRC-16-IBM polynomial: 0xA001 (reversed 0x8005)
_CRC16_POLYNOMIAL = 0xA001
_CRC16_INITIAL_VALUE = 0xFFFF


def _compute_crc16_lookup_table():
    """Compute a crc16 lookup table

    .. note:: This will only be generated once
    """
    table = []
    for byte_value in range(256):
        crc = 0x0000
        for _ in range(8):
            if (byte_value ^ crc) & 0x0001:
                crc = (crc >> 1) ^ _CRC16_POLYNOMIAL
            else:
                crc >>= 1
            byte_value >>= 1
        table.append(crc)
    return table


_CRC16_LOOKUP_TABLE = _compute_crc16_lookup_table()

CRC16_LENGTH = 2


class CRCCalculator:
    def calculate_crc16(self, frame: bytes) -> int:
        crc = _CRC16_INITIAL_VALUE
        for byte_value in frame[:-CRC16_LENGTH]:
            table_index = (crc ^ byte_value) & 0xFF
            crc = ((crc >> 8) & 0xFF) ^ _CRC16_LOOKUP_TABLE[table_index]
        return ((crc << 8) & 0xFF00) | ((crc >> 8) & 0x00FF)
