# dods/analyze/core/logging_setup.py
import logging
import os
from dotenv import load_dotenv, find_dotenv

# --- load environment automatically once ---
load_dotenv(find_dotenv(), override=False)

def setup_logger(name: str = "dods.analyze", level: str | None = None) -> logging.Logger:
    """
    Create and configure a logger with unified formatting and env-based level.

    - Automatically loads nearest .env (using find_dotenv)
    - Respects LOG_LEVEL (default: INFO)
    - Prevents duplicate handlers
    """
    level_name = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    level_value = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
        handler.setFormatter(logging.Formatter(fmt, "%H:%M:%S"))
        logger.addHandler(handler)
        logger.setLevel(level_value)
        logger.propagate = False
    return logger
