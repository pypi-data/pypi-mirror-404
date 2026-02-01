import asyncio

from loguru import logger

from shine2mqtt.growatt.client.config import SimulatedClientConfig
from shine2mqtt.growatt.client.generator import DataGenerator
from shine2mqtt.growatt.protocol.constants import FunctionCode
from shine2mqtt.growatt.protocol.frame import FrameDecoder, FrameEncoder
from shine2mqtt.growatt.protocol.messages import BaseMessage
from shine2mqtt.growatt.protocol.messages.ack import GrowattAckMessage


class SimulatedClient:
    def __init__(
        self,
        encoder: FrameEncoder,
        decoder: FrameDecoder,
        config: SimulatedClientConfig,
    ):
        self.config = config
        self.encoder = encoder
        self.decoder = decoder

        self._announce_ack_event = asyncio.Event()
        self._generator = DataGenerator()
        self._transaction_id = 1
        self._is_connected = False

    async def run(self):
        try:
            await self._connect()
            await self._run_protocol()
        except Exception as e:
            logger.error(f"Client error: {e}")
        finally:
            await self._close()

    async def _connect(self):
        logger.info(f"Connecting to {self.config.server_host}:{self.config.server_port}")
        self.reader, self.writer = await asyncio.open_connection(
            self.config.server_host, self.config.server_port
        )
        self._is_connected = True
        logger.info("Connected to server")

    async def _close(self):
        logger.info("Closing connection")
        if hasattr(self, "writer"):
            self.writer.close()
            await self.writer.wait_closed()
        self._is_connected = False
        logger.info("Connection closed")

    async def _run_protocol(self):
        """Run the client protocol with concurrent reader and state machine"""
        reader_loop_task = asyncio.create_task(self._reader_loop())
        protocol_loop_task = asyncio.create_task(self._announce_loop())

        try:
            await asyncio.gather(reader_loop_task, protocol_loop_task)
        except asyncio.CancelledError:
            logger.info("Reader loop and protocol loop cancelled")
            raise
        finally:
            reader_loop_task.cancel()
            protocol_loop_task.cancel()
            try:
                await asyncio.wait_for(
                    asyncio.gather(reader_loop_task, protocol_loop_task, return_exceptions=True),
                    timeout=1.0,
                )
                logger.info("Reader loop and protocol loop tasks cancelled successfully")
            except TimeoutError:
                logger.warning("Reader/protocol task cancellation timed out")

    async def _announce_loop(self):
        """
        High-level protocol state machine:
        1. Send ANNOUNCE
        2. Wait for ACK
        3. If ACK received: enter connected mode
           - Send DATA every data_interval (default 60s)
           - Send PING every ping_interval (default 180s)
        4. If no ACK: retry ANNOUNCE every 30s
        """
        while self._is_connected:
            await self._send_announce()

            try:
                # Wait for ACK with 30s timeout
                await asyncio.wait_for(self._announce_ack_event.wait(), timeout=30)
                logger.info("✓ Announce ACK received, entering connected mode")
                await self._connected_mode()
            except TimeoutError:
                logger.warning("⚠ No ACK received within 30s, retrying announce")
                self._announce_ack_event.clear()

    async def _connected_mode(self):
        """
        Connected mode: send DATA and PING periodically
        State machine:
        - Send DATA every data_interval
        - Send PING every ping_interval
        """
        data_task = asyncio.create_task(self._send_data_loop())
        ping_task = asyncio.create_task(self._send_ping_loop())

        try:
            await asyncio.gather(data_task, ping_task)
        except asyncio.CancelledError:
            logger.info("Connected mode cancelled")
            raise
        finally:
            data_task.cancel()
            ping_task.cancel()
            try:
                await asyncio.wait_for(
                    asyncio.gather(data_task, ping_task, return_exceptions=True), timeout=1.0
                )
                logger.info("Data and ping tasks cancelled successfully")
            except TimeoutError:
                logger.warning("Data/ping task cancellation timed out")

    async def _send_data_loop(self):
        """Periodically send DATA messages"""
        while self._is_connected:
            await self._send_data()
            await asyncio.sleep(self.config.data_interval)

    async def _send_ping_loop(self):
        """Periodically send PING messages"""
        await asyncio.sleep(self.config.ping_interval)  # Initial delay
        while self._is_connected:
            await self._send_ping()
            await asyncio.sleep(self.config.ping_interval)

    # ---------- reader ----------

    async def _reader_loop(self):
        """Read incoming messages from server"""
        try:
            while self._is_connected:
                raw_header = await self.reader.readexactly(8)
                header = self.decoder.decode_header(raw_header)

                logger.debug(
                    f"← Reading message: function_code={header.function_code.name} "
                    f"({header.function_code.value:#02x}), length={header.length} bytes"
                )

                raw_message_data = await self.reader.readexactly(header.length)
                frame = raw_header + raw_message_data

                logger.debug(f"← Full frame ({len(frame)} bytes): {frame.hex()}")
                logger.debug(f"← Payload ({len(raw_message_data)} bytes): {raw_message_data.hex()}")

                message = self.decoder.decode(header, frame)

                await self._handle_server_message(message)
        except asyncio.IncompleteReadError:
            logger.warning("Connection closed by server")
            self._is_connected = False
        except Exception as e:
            logger.error(f"Reader error: {e}")
            self._is_connected = False

    # ---------- message handling ----------

    async def _handle_server_message(self, message: BaseMessage):
        """Handle messages received from server"""
        function_code = message.header.function_code

        logger.debug(f"← Received {function_code.name} message")

        if isinstance(message, GrowattAckMessage):
            # ACK for ANNOUNCE
            if message.header.function_code == FunctionCode.ANNOUNCE:
                logger.info("✓ Received ACK for ANNOUNCE")
                self._announce_ack_event.set()
            else:
                logger.debug(f"Received ACK for {message.header.function_code.name}")

        elif function_code == FunctionCode.GET_CONFIG:
            logger.info("← Received GET_CONFIG request")
            await self._send_get_config_response(message)

        elif function_code == FunctionCode.SET_CONFIG:
            logger.info("← Received SET_CONFIG request")
            await self._send_ack(message)

        elif function_code == FunctionCode.PING:
            logger.info("← Received PING response")

        else:
            logger.warning(f"Unhandled message type: {function_code.name}")

    async def _send_announce(self):
        """Send ANNOUNCE message to server"""
        logger.info("→ Sending ANNOUNCE message")
        message = self._generator.generate_announce_message(
            transaction_id=self._get_transaction_id()
        )
        await self._send_message(message)

    async def _send_data(self):
        """Send DATA or BUFFERED_DATA message"""
        # TODO: Determine if new data is available
        # For now, always send DATA
        logger.info("→ Sending DATA message")
        message = self._generator.generate_data_message(transaction_id=self._get_transaction_id())
        await self._send_message(message)

    async def _send_ping(self):
        """Send PING message to keep connection alive"""
        logger.info("→ Sending PING message")
        message = self._generator.generate_ping_message(transaction_id=self._get_transaction_id())
        await self._send_message(message)

    async def _send_get_config_response(self, request_message: BaseMessage):
        """Send GET_CONFIG response"""
        logger.info("→ Sending GET_CONFIG response")
        message = self._generator.generate_get_config_response(
            transaction_id=request_message.header.transaction_id,
            register=request_message.register_start,  # type: ignore
        )
        await self._send_message(message)

    async def _send_ack(self, message: BaseMessage):
        """Send ACK message"""
        logger.info(f"→ Sending ACK for {message.header.function_code.name}")
        message = self._generator.generate_ack_message(
            transaction_id=message.header.transaction_id,
            function_code=message.header.function_code,
        )
        await self._send_message(message)

    async def _send_message(self, message: BaseMessage):
        """Encode and send a message to the server"""
        frame = self.encoder.encode(message)
        self.writer.write(frame)
        await self.writer.drain()

    def _get_transaction_id(self) -> int:
        """Get next transaction ID"""
        tid = self._transaction_id
        self._transaction_id += 1
        if self._transaction_id > 65535:
            self._transaction_id = 1
        return tid
