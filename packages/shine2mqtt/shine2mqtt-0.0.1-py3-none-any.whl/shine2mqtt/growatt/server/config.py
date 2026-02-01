from pydantic import BaseModel


class GrowattServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 5279
