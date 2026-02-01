from collections.abc import Callable

from loguru import logger

from shine2mqtt.growatt.protocol.decoders.base import MessageDecoder
from shine2mqtt.growatt.protocol.decoders.header import HeaderDecoder
from shine2mqtt.growatt.protocol.decoders.registry import DecoderRegistry
from shine2mqtt.growatt.protocol.frame.cipher import PayloadCipher
from shine2mqtt.growatt.protocol.frame.validator import FrameValidator
from shine2mqtt.growatt.protocol.messages.base import BaseMessage, MBAPHeader

HEADER_LENGTH = 8
CRC_LENGTH = 2


class DecodingError(Exception):
    pass


class FrameDecoder:
    def __init__(
        self,
        decryption_key: bytes,
        header_decoder: HeaderDecoder,
        frame_validator: FrameValidator,
        payload_cipher: PayloadCipher,
        decoder_registry: DecoderRegistry,
        on_decode: Callable[[BaseMessage], None] | None = None,
    ):
        self.decryption_key = decryption_key
        self.header_decoder = header_decoder
        self.validator = frame_validator
        self.payload_cipher = payload_cipher
        self.decoder_registry = decoder_registry
        self.on_decode = on_decode

    def decode_header(self, raw_header: bytes) -> MBAPHeader:
        return self.header_decoder.decode(raw_header)

    def decode(self, header: MBAPHeader, frame: bytes) -> BaseMessage:
        self.validator.validate(frame, header)

        encrypted_payload = frame[HEADER_LENGTH : HEADER_LENGTH + header.length - CRC_LENGTH]

        raw_payload = self.payload_cipher.decrypt(encrypted_payload, self.decryption_key)

        try:
            decoder: MessageDecoder = self.decoder_registry.get_decoder(header.function_code)
        except KeyError as e:
            message = f"Decoder not found for function code {header.function_code.name} ({header.function_code.value:#02x})"
            logger.error(message)
            raise DecodingError(message) from e

        try:
            message = decoder.decode(header, raw_payload)

            # Hook: capture frame after successful decode
            try:
                if self.on_decode:
                    self.on_decode(message)
            except Exception as e:
                logger.error(f"on_decode hook failed: {e}")

            return message
        except Exception as e:
            message = f"Failed to decode message with function code {header.function_code.name} ({header.function_code.value:#02x}) {e}"
            logger.error(message)
            raise DecodingError(message) from e
