# binance_arbitrage_bot/binance_api/market_data.py

from binance_api.client import client
from config import settings

def exchange_map():
    """Devuelve un diccionario de símbolos activos a tuplas (baseAsset, quoteAsset)."""
    info = client.get_exchange_info()
    return {
        s["symbol"]: (s["baseAsset"], s["quoteAsset"])
        for s in info["symbols"]
        if s["status"] == "TRADING"
    }

def top_volume_symbols(n):
    """Devuelve los n símbolos con mayor volumen de cotización."""
    data = client.get_ticker()
    data.sort(key=lambda d: float(d["quoteVolume"]), reverse=True)
    return [d["symbol"] for d in data[:n]]

def depth_snapshots(symbols):
    """Descarga los libros de órdenes para una lista de símbolos."""
    return {
        sym: client.get_order_book(symbol=sym, limit=settings.BOOK_LIMIT)
        for sym in symbols
    }
