# binance_arbitrage_bot/core/utils.py

import math
from config import settings

def avg_price(levels, side, qty):
    """
    Calcula el precio promedio ponderado dada una cantidad y profundidad de libro.
    """
    need, spent, got = qty, 0.0, 0.0
    for p_str, q_str in levels:
        p, q = float(p_str), float(q_str)
        take = min(q, need)
        if side == "BUY":
            spent += take * p
            got += take
        else:
            spent += take
            got += take * p
        need -= take
        if need <= 0:
            break
    if need > 0:
        last_px = float(levels[-1][0])
        slip_px = last_px * (1 + settings.SLIPPAGE_PCT if side == "BUY" else 1 - settings.SLIPPAGE_PCT)
        spent += need * slip_px if side == "BUY" else need
        got += need if side == "BUY" else need * slip_px
    return spent / got if side == "BUY" else got / spent

def fee_of(symbol: str) -> float:
    """
    Devuelve la comisión de trading del símbolo (por defecto 0.1%).
    """
    return 0.001
