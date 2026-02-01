import asyncio
from asyncio import Queue
from dataclasses import asdict

import aiomqtt
from aiomqtt import Client
from loguru import logger

from shine2mqtt.growatt.protocol.messages.base import BaseMessage
from shine2mqtt.mqtt.client import MqttClient
from shine2mqtt.mqtt.processor import MqttDataloggerMessageProcessor


class MqttBridge:
    _RECONNECT_INTERVAL = 5

    def __init__(
        self,
        protocol_events: Queue[BaseMessage],
        event_processor: MqttDataloggerMessageProcessor,
        client: MqttClient,
    ):
        self._protocol_events = protocol_events
        self._client = client
        self._event_processor = event_processor

    async def run(self):
        while True:
            try:
                async with self._client.connect() as client:
                    logger.info("Connected to MQTT broker")
                    try:
                        await self._publish_availability_status(client, online=True)
                        await asyncio.gather(
                            self._subscriber(client),
                            self._publisher(client),
                        )
                    except asyncio.CancelledError:
                        await self._handle_shutdown(client)
                        raise
            except aiomqtt.MqttError as error:
                logger.error(
                    f"MQTT connection error: {error}. "
                    f"Reconnecting in {self._RECONNECT_INTERVAL} seconds..."
                )
                await asyncio.sleep(self._RECONNECT_INTERVAL)

    async def _publish_availability_status(self, client: Client, online: bool) -> None:
        mqtt_message = self._event_processor.build_availability_message(online)
        await client.publish(**asdict(mqtt_message))

    async def _handle_shutdown(self, client: Client) -> None:
        logger.info("MQTT bridge shutting down, flushing Event → MQTT queue")
        await self._flush_protocol_events(client)
        await self._publish_availability_status(client, online=False)

    async def _publisher(self, client: Client) -> None:
        while True:
            message = await self._protocol_events.get()

            logger.debug(
                f"Processing incoming {message.header.function_code.name} ({message.header.function_code.value:#02x}) message."
            )

            for mqtt_message in self._event_processor.process(message):
                logger.info(
                    f"Publishing MQTT message '{mqtt_message.topic}': {mqtt_message.payload}"
                )
                await client.publish(**asdict(mqtt_message))

    async def _subscriber(self, client: Client) -> None:
        async for msg in client.messages:
            logger.debug(f"Received MQTT message '{msg.topic}': {msg.payload}")

    async def _flush_protocol_events(self, client: Client) -> None:
        while not self._protocol_events.empty():
            message = self._protocol_events.get_nowait()
            try:
                for mqtt_message in self._event_processor.process(message):
                    await client.publish(**asdict(mqtt_message), timeout=0.5)
            except Exception as e:
                logger.warning(f"Failed to publish message during flush: {e}")
