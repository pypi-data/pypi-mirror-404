import asyncio
from asyncio import StreamReader, StreamWriter

from loguru import logger

from shine2mqtt.growatt.protocol.frame.decoder import FrameDecoder


class GrowattTcpSession:
    def __init__(
        self,
        reader: StreamReader,
        writer: StreamWriter,
        decoder: FrameDecoder,
        incoming_messages: asyncio.Queue,
        outgoing_frames: asyncio.Queue,
    ):
        self.reader = reader
        self.writer = writer
        self.decoder = decoder

        self._incoming_messages = incoming_messages
        self._outgoing_frames = outgoing_frames

    async def run(self):
        try:
            await asyncio.gather(self._reader_loop(), self._writer_loop())
        finally:
            logger.info("Closing TCP session")
            await self._flush_writer_queue()
            self.writer.close()
            await self.writer.wait_closed()
            logger.info("TCP session fully closed")

    async def _reader_loop(self):
        logger.info("Starting TCP Session reader loop, waiting for messages")
        try:
            while True:
                raw_header = await self.reader.readexactly(8)
                header = self.decoder.decode_header(raw_header)

                raw_message_data = await self.reader.readexactly(header.length)

                message = self.decoder.decode(header, raw_header + raw_message_data)

                self._incoming_messages.put_nowait(message)
        except asyncio.IncompleteReadError:
            logger.error("Can't read from client, client disconnected")
            raise

    async def _writer_loop(self):
        logger.info("Starting TCP Session writer loop, waiting to send messages")
        while True:
            frame = await self._outgoing_frames.get()
            try:
                self.writer.write(frame)
                await self.writer.drain()
            except Exception as e:
                logger.warning(f"Error writing to TCP client: {e}")
                raise

    async def _flush_writer_queue(self):
        logger.info("Flushing writer queue")
        while not self._outgoing_frames.empty():
            frame = await self._outgoing_frames.get()
            try:
                self.writer.write(frame)
                await asyncio.wait_for(self.writer.drain(), timeout=0.5)
            except Exception as e:
                logger.warning(f"Error sending frame during flush: {e}")
                break
        logger.info("Writer queue flushed")
