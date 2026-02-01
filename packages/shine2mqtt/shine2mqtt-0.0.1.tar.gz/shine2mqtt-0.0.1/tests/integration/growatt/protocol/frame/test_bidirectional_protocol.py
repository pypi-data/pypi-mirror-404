"""Test bidirectional protocol support with separate server/client decoder registries."""

import pytest

from shine2mqtt.growatt.protocol.constants import FunctionCode
from shine2mqtt.growatt.protocol.decoders.registry import DecoderRegistry
from shine2mqtt.growatt.protocol.frame.factory import FrameFactory


class TestBidirectionalProtocol:
    """Test that server and client can properly decode the same function codes differently."""

    @pytest.fixture
    def server_decoder(self):
        """Server decoder for messages FROM client."""
        return FrameFactory.server_decoder()

    @pytest.fixture
    def client_decoder(self):
        """Client decoder for messages FROM server."""
        return FrameFactory.client_decoder()

    def test_server_registry_has_correct_decoders(self):
        """Server should decode client requests."""
        registry = DecoderRegistry.server()

        # Server receives ANNOUNCE from client (large 573-byte payload)
        announce_decoder = registry.get_decoder(FunctionCode.ANNOUNCE)
        assert announce_decoder.__class__.__name__ == "AnnounceRequestDecoder"

        # Server receives DATA from client
        data_decoder = registry.get_decoder(FunctionCode.DATA)
        assert data_decoder.__class__.__name__ == "DataRequestDecoder"

        # Server receives PING from client
        ping_decoder = registry.get_decoder(FunctionCode.PING)
        assert ping_decoder.__class__.__name__ == "PingRequestDecoder"

        # Server receives GET_CONFIG response from client
        config_decoder = registry.get_decoder(FunctionCode.GET_CONFIG)
        assert config_decoder.__class__.__name__ == "GetConfigResponseDecoder"

    def test_client_registry_has_correct_decoders(self):
        """Client should decode server responses."""
        registry = DecoderRegistry.client()

        # Client receives ACK for ANNOUNCE (1-byte payload)
        announce_decoder = registry.get_decoder(FunctionCode.ANNOUNCE)
        assert announce_decoder.__class__.__name__ == "AckMessageResponseDecoder"

        # Client receives ACK for DATA (1-byte payload)
        data_decoder = registry.get_decoder(FunctionCode.DATA)
        assert data_decoder.__class__.__name__ == "AckMessageResponseDecoder"

        # Client receives PING echo from server
        ping_decoder = registry.get_decoder(FunctionCode.PING)
        assert ping_decoder.__class__.__name__ == "PingRequestDecoder"

        # Client receives GET_CONFIG request from server
        config_decoder = registry.get_decoder(FunctionCode.GET_CONFIG)
        assert config_decoder.__class__.__name__ == "GetConfigRequestDecoder"

    def test_announce_function_code_decodes_differently(self):
        """
        FunctionCode.ANNOUNCE means different things:
        - Server receives: AnnounceMessage (573 bytes) from client
        - Client receives: AckMessage (1 byte) from server
        """
        server_registry = DecoderRegistry.server()
        client_registry = DecoderRegistry.client()

        server_decoder = server_registry.get_decoder(FunctionCode.ANNOUNCE)
        client_decoder = client_registry.get_decoder(FunctionCode.ANNOUNCE)

        # Different decoders for same function code
        assert server_decoder.__class__.__name__ == "AnnounceRequestDecoder"
        assert client_decoder.__class__.__name__ == "AckMessageResponseDecoder"

    def test_get_config_function_code_decodes_differently(self):
        """
        FunctionCode.GET_CONFIG means different things:
        - Server receives: GetConfigResponseMessage (client responding)
        - Client receives: GetConfigRequestMessage (server requesting)
        """
        server_registry = DecoderRegistry.server()
        client_registry = DecoderRegistry.client()

        server_decoder = server_registry.get_decoder(FunctionCode.GET_CONFIG)
        client_decoder = client_registry.get_decoder(FunctionCode.GET_CONFIG)

        # Different decoders for same function code
        assert server_decoder.__class__.__name__ == "GetConfigResponseDecoder"
        assert client_decoder.__class__.__name__ == "GetConfigRequestDecoder"
