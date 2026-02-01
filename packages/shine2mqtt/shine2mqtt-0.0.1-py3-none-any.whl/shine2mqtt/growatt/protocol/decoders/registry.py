from loguru import logger

from shine2mqtt.growatt.protocol.constants import FunctionCode
from shine2mqtt.growatt.protocol.decoders.ack import AckMessageResponseDecoder
from shine2mqtt.growatt.protocol.decoders.announce import AnnounceRequestDecoder
from shine2mqtt.growatt.protocol.decoders.base import MessageDecoder
from shine2mqtt.growatt.protocol.decoders.config import (
    GetConfigRequestDecoder,
    GetConfigResponseDecoder,
    SetConfigRequestDecoder,
)
from shine2mqtt.growatt.protocol.decoders.data import (
    BufferDataRequestDecoder,
    DataRequestDecoder,
)
from shine2mqtt.growatt.protocol.decoders.ping import PingRequestDecoder


class DecoderRegistry:
    def __init__(self):
        self._decoders = {}

    def register_decoder(self, function_code: FunctionCode, decoder: MessageDecoder):
        self._decoders[function_code] = decoder

    def get_decoder(self, function_code: FunctionCode) -> MessageDecoder:
        decoder = self._decoders.get(function_code, None)

        if decoder is None:
            message = f"No decoder registered for this function code {function_code.name} ({function_code.value:#02x})"
            logger.error(message)
            raise KeyError(message)

        return decoder

    @classmethod
    def server(cls) -> "DecoderRegistry":
        """
        Create a registry for the server (decodes messages FROM client/datalogger).

        Server receives:
        - ANNOUNCE → AnnounceRequestDecoder (client announces itself)
        - DATA → DataRequestDecoder (client sends real-time data)
        - BUFFERED_DATA → BufferDataRequestDecoder (client sends buffered data)
        - PING → PingRequestDecoder (client pings)
        - GET_CONFIG → GetConfigResponseDecoder (client responds with config)
        """

        registry = cls()

        # Client → Server messages
        registry.register_decoder(FunctionCode.ANNOUNCE, AnnounceRequestDecoder())
        registry.register_decoder(FunctionCode.DATA, DataRequestDecoder())
        registry.register_decoder(FunctionCode.BUFFERED_DATA, BufferDataRequestDecoder())
        registry.register_decoder(FunctionCode.PING, PingRequestDecoder())
        registry.register_decoder(FunctionCode.GET_CONFIG, GetConfigResponseDecoder())
        registry.register_decoder(FunctionCode.SET_CONFIG, AckMessageResponseDecoder())

        return registry

    @classmethod
    def client(cls) -> "DecoderRegistry":
        """
        Create a registry for the client/datalogger (decodes messages FROM server).

        Client receives:
        - ANNOUNCE → AckMessageResponseDecoder (server ACKs announce)
        - DATA → AckMessageResponseDecoder (server ACKs data)
        - BUFFERED_DATA → AckMessageResponseDecoder (server ACKs buffered data)
        - PING → PingRequestDecoder (server echoes ping back)
        - GET_CONFIG → GetConfigRequestDecoder (server requests config)
        - SET_CONFIG → SetConfigRequestDecoder (server sets config)
        """

        registry = cls()

        # Server → Client messages (ACKs)
        ack_decoder = AckMessageResponseDecoder()
        registry.register_decoder(FunctionCode.ANNOUNCE, ack_decoder)
        registry.register_decoder(FunctionCode.DATA, ack_decoder)
        registry.register_decoder(FunctionCode.BUFFERED_DATA, ack_decoder)

        # Server → Client messages (requests/responses)
        # PING is echoed back with same structure
        registry.register_decoder(FunctionCode.PING, PingRequestDecoder())
        registry.register_decoder(FunctionCode.GET_CONFIG, GetConfigRequestDecoder())
        registry.register_decoder(FunctionCode.SET_CONFIG, SetConfigRequestDecoder())

        return registry
