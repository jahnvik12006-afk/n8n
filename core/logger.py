import logging
import sys

from core.config import config


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("autoanimebot")
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    return logger


logger = setup_logger()
