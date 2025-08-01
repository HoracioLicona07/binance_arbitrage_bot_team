# binance_arbitrage_bot/main.py

from core.logger import setup_logger
from services import scanner

if __name__ == "__main__":
    setup_logger()
    scanner.run()
