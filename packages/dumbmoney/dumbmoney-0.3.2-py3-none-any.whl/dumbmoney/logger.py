import logging
import os

logger = logging.getLogger("dumbmoney")
logger.setLevel(
    logging.DEBUG if os.getenv("ENV", "").lower() == "debug" else logging.INFO
)
