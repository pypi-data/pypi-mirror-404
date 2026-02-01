from shine2mqtt.growatt.protocol.constants import DECRYPTION_KEY, ENCRYPTION_KEY
from shine2mqtt.growatt.protocol.decoders import DecoderRegistry, HeaderDecoder
from shine2mqtt.growatt.protocol.encoders import (
    CRCEncoder,
    HeaderEncoder,
    PayloadEncoderRegistry,
)
from shine2mqtt.growatt.protocol.frame.cipher import PayloadCipher
from shine2mqtt.growatt.protocol.frame.crc import CRCCalculator
from shine2mqtt.growatt.protocol.frame.decoder import FrameDecoder
from shine2mqtt.growatt.protocol.frame.encoder import FrameEncoder
from shine2mqtt.growatt.protocol.frame.validator import FrameValidator


class FrameFactory:
    """Factory for creating frame encoder and decoder with all dependencies."""

    @staticmethod
    def encoder() -> FrameEncoder:
        """Create a FrameEncoder with all default encoders registered."""
        return FrameEncoder(
            encryption_key=ENCRYPTION_KEY,
            header_encoder=HeaderEncoder(),
            payload_cipher=PayloadCipher(),
            encoder_registry=PayloadEncoderRegistry.default(),
            crc_calculator=CRCCalculator(),
            crc_encoder=CRCEncoder(),
        )

    @staticmethod
    def decoder(on_decode=None, decoder_registry: DecoderRegistry | None = None) -> FrameDecoder:
        """Create a FrameDecoder with specified or default decoders registered.

        Args:
            on_decode: Optional callback(frame: bytes, message: BaseMessage) called after decoding
            decoder_registry: Optional decoder registry. Defaults to server registry if not specified.
        """
        crc_calculator = CRCCalculator()

        return FrameDecoder(
            decryption_key=DECRYPTION_KEY,
            header_decoder=HeaderDecoder(),
            frame_validator=FrameValidator(crc_calculator),
            payload_cipher=PayloadCipher(),
            decoder_registry=decoder_registry or DecoderRegistry.server(),
            on_decode=on_decode,
        )

    @staticmethod
    def server_decoder(on_decode=None) -> FrameDecoder:
        """Create a FrameDecoder for server (decodes messages FROM client).

        Args:
            on_decode: Optional callback(frame: bytes, message: BaseMessage) called after decoding
        """
        return FrameFactory.decoder(on_decode=on_decode, decoder_registry=DecoderRegistry.server())

    @staticmethod
    def client_decoder(on_decode=None) -> FrameDecoder:
        """Create a FrameDecoder for client (decodes messages FROM server).

        Args:
            on_decode: Optional callback(frame: bytes, message: BaseMessage) called after decoding
        """
        return FrameFactory.decoder(on_decode=on_decode, decoder_registry=DecoderRegistry.client())
