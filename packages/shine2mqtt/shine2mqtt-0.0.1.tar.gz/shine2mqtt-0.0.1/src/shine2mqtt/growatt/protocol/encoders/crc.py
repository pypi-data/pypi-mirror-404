import struct


class CRCEncoder:
    def encode(self, crc: int) -> bytes:
        # NOTE: CRC is little-endian
        return struct.pack("<H", crc)
