# binance_arbitrage_bot/binance_api/margin.py

import logging
import os
import requests
from dotenv import load_dotenv
from binance.client import Client
from strategies.triangular import format_quantity

# Cargar variables de entorno desde el archivo .env
load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

# Inicializar cliente de Binance
client = Client(API_KEY, API_SECRET)

def get_valid_margin_pairs():
    try:
        url = "https://api.binance.com/sapi/v1/margin/allPairs"
        headers = {"X-MBX-APIKEY": API_KEY}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return {pair['symbol'] for pair in data if pair.get('isMarginTrade')}
    except Exception as e:
        logging.warning(f"❌ Could not fetch margin symbols: {e}")
        return set()

def execute_arbitrage_trade(route, usdt_amt):
    try:
        asset1, asset2, asset3 = route[1], route[2], route[3]
        symbol1 = f"{asset1}{asset2}" if client.get_symbol_info(f"{asset1}{asset2}") else f"{asset2}{asset1}"
        symbol2 = f"{asset2}{asset3}" if client.get_symbol_info(f"{asset2}{asset3}") else f"{asset3}{asset2}"

        borrow_qty = client.get_margin_price_index(symbol=f"{asset1}USDT")
        price = float(borrow_qty['price'])
        amount_to_borrow = format_quantity(f"{asset1}USDT", usdt_amt / price)

        logging.info(f"🔄 Borrowing {amount_to_borrow:.8f} {asset1}...")
        client.create_margin_loan(asset=asset1, amount=amount_to_borrow)

        logging.info(f"🛒 Step 1: {asset1} → {asset2}")
        order1 = client.create_margin_order(
            symbol=symbol1,
            side='SELL',
            type='MARKET',
            quantity=amount_to_borrow
        )
        qty2 = format_quantity(f"{asset2}USDT", float(order1['executedQty']))

        logging.info(f"🛒 Step 2: {asset2} → USDT")
        order2 = client.create_margin_order(
            symbol=f"{asset2}USDT",
            side='SELL',
            type='MARKET',
            quantity=qty2
        )
        usdt_return = float(order2['cummulativeQuoteQty'])

        repay_amt = format_quantity(f"{asset1}USDT", amount_to_borrow)
        client.repay_margin_loan(asset=asset1, amount=repay_amt)

        net_profit = usdt_return - usdt_amt
        logging.info(f"✅ Arbitrage completed: +{net_profit:.4f} USDT")
    except Exception as e:
        logging.error(f"❌ Trade execution failed: {e}")
