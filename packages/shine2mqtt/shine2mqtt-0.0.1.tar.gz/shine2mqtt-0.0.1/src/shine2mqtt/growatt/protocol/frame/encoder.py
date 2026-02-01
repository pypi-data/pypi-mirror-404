from shine2mqtt.growatt.protocol.encoders.crc import CRCEncoder
from shine2mqtt.growatt.protocol.encoders.header import HeaderEncoder
from shine2mqtt.growatt.protocol.encoders.registry import PayloadEncoderRegistry
from shine2mqtt.growatt.protocol.frame.cipher import PayloadCipher
from shine2mqtt.growatt.protocol.frame.crc import CRC16_LENGTH, CRCCalculator
from shine2mqtt.growatt.protocol.messages.base import BaseMessage


class FrameEncoder:
    def __init__(
        self,
        encryption_key: bytes,
        header_encoder: HeaderEncoder,
        payload_cipher: PayloadCipher,
        encoder_registry: PayloadEncoderRegistry,
        crc_calculator: CRCCalculator,
        crc_encoder: CRCEncoder,
    ):
        self.encryption_key = encryption_key
        self.header_encoder = header_encoder
        self.payload_cipher = payload_cipher
        self.encoder_registry = encoder_registry
        self.crc_calculator = crc_calculator
        self.crc_encoder = crc_encoder

    def encode(self, message: BaseMessage) -> bytes:
        encoder = self.encoder_registry.get_encoder(type(message))

        raw_payload = encoder.encode(message)

        # FIXME maybe not ideal to change message here
        # would be better to have immutability
        message.header.length = len(raw_payload) + CRC16_LENGTH

        raw_header = self.header_encoder.encode(message.header)

        encrypted_payload = self.payload_cipher.encrypt(raw_payload, self.encryption_key)

        crc = self.crc_calculator.calculate_crc16(raw_header + encrypted_payload + b"\x00\x00")

        frame = raw_header + encrypted_payload + self.crc_encoder.encode(crc)

        return frame
