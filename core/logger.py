# binance_arbitrage_bot/core/logger.py

import logging
from config import settings

def setup_logger():
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format='[%(asctime)s] %(levelname)-4s %(message)s',
        datefmt='%d/%m/%y %H:%M:%S'
    )
