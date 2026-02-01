import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from loguru import logger

from shine2mqtt.growatt.protocol.command import (
    GetConfigByNameCommand,
    GetConfigByRegistersCommand,
)


class RestApi:
    def __init__(self, protocol_commands: asyncio.Queue):
        self.protocol_commands = protocol_commands
        self.app = FastAPI()

        self._setup_routes()

    def _setup_routes(self):
        @self.app.get("/", include_in_schema=False)
        async def root():
            return RedirectResponse(url="/docs")

        # WARN: order matters, /config/registers must be before /config/{name}
        @self.app.get("/config/registers")
        async def get_config_by_register(register: int):
            future = asyncio.get_running_loop().create_future()

            command = GetConfigByRegistersCommand(
                register=register,
                future=future,
            )

            try:
                logger.debug(f"Enqueuing command: {command}")
                self.protocol_commands.put_nowait(command)
            except asyncio.QueueFull as e:
                raise HTTPException(status_code=503, detail="Server error") from e

            try:
                logger.debug(f"Waiting for command result: {command}")
                return await asyncio.wait_for(future, timeout=10)
            except TimeoutError as e:
                raise HTTPException(status_code=504, detail="Server timeout") from e

        @self.app.get("/config/{name}")
        async def get_config_by_name(name: str):
            future = asyncio.get_running_loop().create_future()

            command = GetConfigByNameCommand(name=name, future=future)

            try:
                logger.debug(f"Enqueuing command: {command}")
                self.protocol_commands.put_nowait(command)
            except asyncio.QueueFull as e:
                raise HTTPException(status_code=503, detail="Server error") from e

            try:
                logger.debug(f"Waiting for command result: {command}")
                return await asyncio.wait_for(future, timeout=10)
            except TimeoutError as e:
                raise HTTPException(status_code=504, detail="Server timeout") from e
