import logging

from digiformatter import logger as digilogger

logger = logging.getLogger("jam2025")

def setup() -> None:
    logging.basicConfig(level=logging.INFO)
    dfhandler = digilogger.DigiFormatterHandler()
    logger.setLevel(logging.DEBUG)
    logger.handlers = []
    logger.propagate = False
    logger.addHandler(dfhandler)
