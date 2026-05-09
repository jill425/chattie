from __future__ import annotations

import logging
import os


def get_logger(name: str = "chattie_py") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
        logger.addHandler(handler)
    logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
    return logger


logger = get_logger()

