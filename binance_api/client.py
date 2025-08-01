# binance_arbitrage_bot/binance_api/client.py

import os
from dotenv import load_dotenv
from binance.client import Client

# Load environment variables from .env
load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

# Initialize Binance Client
client = Client(API_KEY, API_SECRET)
