import asyncio
from asyncio import Queue, Server, StreamReader, StreamWriter

from loguru import logger

from shine2mqtt.growatt.protocol.frame.decoder import FrameDecoder
from shine2mqtt.growatt.protocol.processor.processor import ProtocolProcessor
from shine2mqtt.growatt.server.config import GrowattServerConfig
from shine2mqtt.growatt.server.session import GrowattTcpSession


class GrowattServer:
    def __init__(
        self,
        decoder: FrameDecoder,
        incoming_messages: Queue,
        outgoing_frames: Queue,
        protocol_processor: ProtocolProcessor,
        config: GrowattServerConfig,
    ) -> None:
        self._decoder = decoder
        self.host = config.host
        self.port = config.port

        self.server: Server | None = None
        self.session: GrowattTcpSession | None = None
        self.session_task = None
        self._incoming_messages = incoming_messages
        self._outgoing_frames = outgoing_frames
        self._protocol_processor = protocol_processor

    async def start(self):
        logger.info("Creating TCP server")
        self.server = await asyncio.start_server(
            self._handle_client, host=self.host, port=self.port
        )

    async def serve(self):
        if self.server is None:
            raise RuntimeError("Server not started. Call start() first.")

        logger.info(f"Starting TCP server on {self.host}:{self.port}")
        async with self.server:
            await self.server.serve_forever()

    async def stop(self):
        logger.info("Stopping TCP server")

        if self.session_task:
            logger.info("Closing active TCP session")
            self.session_task.cancel()

            try:
                await asyncio.wait_for(self.session_task, timeout=1.0)
            except asyncio.CancelledError:
                logger.debug("TCP session task closed")
                raise
            except TimeoutError:
                logger.warning("TCP session cancellation timed out")

            logger.info("Active TCP session closed")

        if self.server:
            logger.info("Closing TCP server")
            self.server.close()
            await self.server.wait_closed()
            logger.info("TCP server was closed")

    async def _handle_client(self, reader: StreamReader, writer: StreamWriter):
        addr = writer.get_extra_info("peername")

        logger.info(f"Accepted new TCP connection from {addr}")

        # Only allow a single session
        if self.session is not None:
            logger.warning("Existing active session, rejecting new connection")
            writer.close()
            await writer.wait_closed()
            return

        self.session = GrowattTcpSession(
            reader,
            writer,
            self._decoder,
            self._incoming_messages,
            self._outgoing_frames,
        )
        self._protocol_processor.reset()
        self.session_task = asyncio.create_task(self.session.run())

        try:
            logger.info(f"Starting TCP session for {addr}")
            await self.session_task
        except Exception:
            logger.error(f"Error in TCP session from {addr}")
        finally:
            logger.info(f"TCP session closed from {addr}")
            self.session = None
            self.session_task = None
