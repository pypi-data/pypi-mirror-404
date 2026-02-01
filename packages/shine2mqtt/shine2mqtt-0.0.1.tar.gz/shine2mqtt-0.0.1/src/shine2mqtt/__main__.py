import asyncio

from loguru import logger

from shine2mqtt.app import Application
from shine2mqtt.cli import ArgParser
from shine2mqtt.config import ApplicationConfig, ConfigLoader
from shine2mqtt.growatt.client.simulate import SimulatedClient
from shine2mqtt.growatt.protocol.frame.factory import FrameFactory
from shine2mqtt.logger import setup_logging


async def main():
    try:
        args = ArgParser().parse()

        config: ApplicationConfig = ConfigLoader().load(args)
        setup_logging(log_level=config.log_level, color=config.log_color)
        logger.info(f"Loaded configuration: {config}")

        if args.simulated_client__enabled:
            decoder = FrameFactory.client_decoder()
            logger.info(f"Client decoder registry: {decoder.decoder_registry._decoders}")
            client = SimulatedClient(FrameFactory.encoder(), decoder, config.simulated_client)
            await client.run()
        else:
            app = Application(config=config)
            await app.run()
    except asyncio.CancelledError:
        logger.info("Shutting down gracefully")
        raise


def run():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by CTRL+C (Interrupted by user)")


if __name__ == "__main__":
    run()
