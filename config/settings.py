# binance_arbitrage_bot/config/settings.py

import logging

TOP_N_PAIRS = 250
BOOK_LIMIT = 100
PROFIT_THOLD = 0.00001
SLIPPAGE_PCT = 0.0005
HOLD_SECONDS = 5
LIVE = True
SLEEP_BETWEEN = 1
QUANTUMS_USDT = [10]
LOG_LEVEL = logging.INFO
BASE_ASSET = 'USDT'
