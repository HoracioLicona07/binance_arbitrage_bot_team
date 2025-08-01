# binance_arbitrage_bot/strategies/triangular.py

from binance_api.client import client
from core.utils import avg_price, fee_of
from config import settings
import logging
import math

symbol_filters = {}
margin_enabled_assets = {}

def fetch_symbol_filters():
    info = client.get_exchange_info()
    for s in info['symbols']:
        for f in s['filters']:
            if f['filterType'] == 'LOT_SIZE':
                symbol_filters[s['symbol']] = {
                    'stepSize': float(f['stepSize']),
                    'minQty': float(f['minQty'])
                }

def format_quantity(symbol, qty):
    if symbol not in symbol_filters:
        return qty
    step = symbol_filters[symbol]['stepSize']
    precision = int(round(-math.log10(step)))
    return float(f"{math.floor(qty / step) * step:.{precision}f}")

def simulate_route_gain(route, usdt_amount, books, valid_symbols):
    qty = usdt_amount
    for i in range(len(route) - 1):
        a, b = route[i], route[i + 1]
        fwd, rev = a + b, b + a
        symbol = None
        if fwd in valid_symbols:
            symbol, side = fwd, 'SELL'
        elif rev in valid_symbols:
            symbol, side = rev, 'BUY'
        else:
            return 0.0
        if symbol not in books:
            try:
                books[symbol] = client.get_order_book(symbol=symbol, limit=settings.BOOK_LIMIT)
            except Exception:
                return 0.0
        book = books[symbol]
        levels = book['asks'] if side == 'BUY' else book['bids']
        px = avg_price(levels, side, qty)
        conv = (1 / px) * (1 - fee_of(symbol)) if side == 'BUY' else px * (1 - fee_of(symbol))
        qty *= conv
    return qty

def get_valid_symbol(a, b, valid_symbols):
    if f"{a}{b}" in valid_symbols:
        return f"{a}{b}", 'fwd'
    elif f"{b}{a}" in valid_symbols:
        return f"{b}{a}", 'rev'
    return None, None

def hourly_interest(asset):
    return margin_enabled_assets.get(asset, 0.0)

# 🟢 puedes agregar aquí 'execute_arbitrage_trade' si no lo tienes aún
def execute_arbitrage_trade(route, usdt_amt):
    logging.info(f"(Simulado) Trade ejecutado para ruta: {route} con cantidad: {usdt_amt} USDT")
