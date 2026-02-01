import asyncio
from dataclasses import dataclass


@dataclass
class BaseCommand:
    future: asyncio.Future


@dataclass
class GetConfigByNameCommand(BaseCommand):
    name: str


@dataclass
class GetConfigByRegistersCommand(BaseCommand):
    register: int
    future: asyncio.Future
