# binance_arbitrage_bot/services/scanner.py

import time
import logging
from itertools import combinations
from config import settings
from binance_api import market_data
from binance_api.margin import get_valid_margin_pairs
from strategies.triangular import (
    simulate_route_gain,
    execute_arbitrage_trade,
    fetch_symbol_filters,
    hourly_interest
)

def run():
    sym_map = market_data.exchange_map()
    valid_symbols = set(sym_map.keys())
    valid_margin_symbols = get_valid_margin_pairs()

    fetch_symbol_filters()

    while True:
        cycle_start = time.time()
        symbols = market_data.top_volume_symbols(settings.TOP_N_PAIRS)
        coins = {c for s in symbols if s in sym_map for c in sym_map[s]}
        coins.discard(settings.BASE_ASSET)

        books = market_data.depth_snapshots(symbols)
        logging.info("▶️  Monedas candidatas: %d", len(coins))

        checked = 0
        profitable = 0

        for hops in (3, 4):
            for combo in combinations(coins, hops - 1):
                route = [settings.BASE_ASSET] + list(combo) + [settings.BASE_ASSET]
                for usdt_amt in settings.QUANTUMS_USDT:
                    final_qty = simulate_route_gain(route, usdt_amt, books, valid_symbols)
                    if final_qty == 0:
                        continue
                    factor = final_qty / usdt_amt
                    hours = max(1, round(settings.HOLD_SECONDS / 3600))
                    factor_eff = factor * (1 - hourly_interest(settings.BASE_ASSET) * hours)
                    net_gain = factor_eff - 1
                    if net_gain > settings.PROFIT_THOLD:
                        profitable += 1
                        logging.info("💰 Ruta %s | size≈%.2f USDT | +%.3f%%",
                                     " → ".join(route), usdt_amt, net_gain * 100)
                        if settings.LIVE:
                            logging.info(f"🟢 Ejecutando arbitraje real para {route}")
                            execute_arbitrage_trade(route, usdt_amt)
                    checked += 1

        logging.info("🔎 Rutas evaluadas: %d – rentables: %d", checked, profitable)
        time.sleep(max(0, settings.SLEEP_BETWEEN - (time.time() - cycle_start)))
