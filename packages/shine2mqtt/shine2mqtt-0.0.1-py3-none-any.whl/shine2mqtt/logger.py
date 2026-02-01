import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        logger.patch(
            lambda r: r.update(
                name=record.name,
                function=record.funcName,
                line=record.lineno,
            )
        ).log(level, record.getMessage())


def setup_logging(log_level: str, color: bool | None = None) -> None:
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(handlers=[InterceptHandler()], level=logging.NOTSET)

    loggers = (
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
        "asyncio",
        "starlette",
    )

    for logger_name in loggers:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = []
        logging_logger.propagate = True

    log_format = "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{module}</cyan> - <level>{message}</level>"

    if log_level == "DEBUG":
        log_format = "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

    logger.remove()
    logger.add(
        sys.stderr,
        format=log_format,
        level=log_level,
        colorize=color,
        enqueue=True,
        filter=lambda record: "paho.mqtt" not in record["name"],
    )
