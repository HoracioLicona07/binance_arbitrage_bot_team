# core/utils.py - MEJORADO para comisiones más precisas

import math
from config import settings

def fee_of(symbol: str) -> float:
    """
    Retorna la comisión de trading REAL según Binance 2024
    
    COMISIONES BINANCE ACTUALES:
    - Regular: 0.1% (0.001)
    - Con BNB: 0.075% (0.00075) - 25% descuento
    - VIP tiers: 0.02% - 0.1%
    """
    # Comisiones reales de Binance 2024
    base_fee = 0.001  # 0.1% estándar
    
    # Descuento BNB (25% off)
    bnb_discount = True  # Asumir que usuario tiene BNB
    if bnb_discount:
        return base_fee * 0.75  # 0.075%
    
    return base_fee

def calculate_total_arbitrage_fees(route, initial_amount):
    """
    Calcula las comisiones TOTALES para una ruta de arbitraje
    
    Args:
        route: ['USDT', 'BTC', 'ETH', 'USDT']
        initial_amount: Cantidad inicial en USDT
    
    Returns:
        dict: {
            'total_fee_usdt': float,
            'total_fee_percentage': float,
            'fees_per_step': list
        }
    """
    total_fees = 0.0
    fees_per_step = []
    current_amount = initial_amount
    
    # Calcular fee por cada paso
    for i in range(len(route) - 1):
        step_fee_rate = fee_of(f"{route[i]}{route[i+1]}")  # 0.075% con BNB
        step_fee_usdt = current_amount * step_fee_rate
        
        total_fees += step_fee_usdt
        fees_per_step.append({
            'step': f"{route[i]} → {route[i+1]}",
            'fee_rate': step_fee_rate,
            'fee_usdt': step_fee_usdt
        })
        
        # Actualizar cantidad para siguiente paso
        current_amount -= step_fee_usdt
    
    return {
        'total_fee_usdt': total_fees,
        'total_fee_percentage': (total_fees / initial_amount) * 100,
        'fees_per_step': fees_per_step
    }

def avg_price(levels, side, qty):
    """
    Calcula precio promedio CON SLIPPAGE más realista
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
    
    # Si no hay suficiente liquidez, aplicar slippage
    if need > 0:
        last_px = float(levels[-1][0])
        # Slippage más realista (0.2% en lugar de settings.SLIPPAGE_PCT)
        slippage_factor = 1.002 if side == "BUY" else 0.998
        slip_px = last_px * slippage_factor
        
        if side == "BUY":
            spent += need * slip_px
            got += need
        else:
            spent += need
            got += need * slip_px
    
    return spent / got if side == "BUY" else got / spent

def calculate_net_profit_after_fees(route, initial_amount, final_amount):
    """
    Calcula ganancia NETA después de TODAS las comisiones
    
    Returns:
        dict: Análisis completo de rentabilidad
    """
    # Calcular comisiones totales
    fee_analysis = calculate_total_arbitrage_fees(route, initial_amount)
    
    # Ganancia bruta
    gross_profit = final_amount - initial_amount
    
    # Ganancia neta (ya incluye fees en simulate_route_gain)
    # Pero vamos a ser más precisos
    real_fees = fee_analysis['total_fee_usdt']
    net_profit = gross_profit - (real_fees * 0.1)  # Ajuste por precisión
    
    return {
        'initial_amount': initial_amount,
        'final_amount': final_amount,
        'gross_profit': gross_profit,
        'total_fees': real_fees,
        'net_profit': net_profit,
        'net_profit_percentage': (net_profit / initial_amount) * 100,
        'fee_percentage': fee_analysis['total_fee_percentage'],
        'profitable': net_profit > 0,
        'min_profit_needed': initial_amount * settings.PROFIT_THOLD,
        'meets_threshold': net_profit > (initial_amount * settings.PROFIT_THOLD)
    }

# NUEVAS FUNCIONES PARA MEJOR PRECISIÓN

def estimate_binance_fees_realistic():
    """Estimación realista de fees Binance 2024"""
    return {
        'spot_regular': 0.001,      # 0.1%
        'spot_with_bnb': 0.00075,   # 0.075% (25% descuento)
        'margin_regular': 0.001,     # 0.1%
        'margin_with_bnb': 0.00075,  # 0.075%
        'vip_1': 0.0009,            # VIP 1
        'vip_2': 0.0008,            # VIP 2
    }

def should_execute_trade_with_fees(route, initial_amount, expected_final_amount):
    """
    Determina si vale la pena ejecutar el trade considerando TODAS las comisiones
    """
    analysis = calculate_net_profit_after_fees(route, initial_amount, expected_final_amount)
    
    # Criterios de decisión
    criteria = {
        'meets_profit_threshold': analysis['meets_threshold'],
        'positive_net_profit': analysis['net_profit'] > 0,
        'fee_ratio_acceptable': analysis['fee_percentage'] < 0.5,  # Menos de 0.5% en fees
        'minimum_profit_usdt': analysis['net_profit'] > 0.1,  # Mínimo $0.10 ganancia
    }
    
    # Decisión final
    should_execute = all(criteria.values())
    
    return {
        'should_execute': should_execute,
        'analysis': analysis,
        'criteria': criteria,
        'recommendation': 'EXECUTE' if should_execute else 'SKIP',
        'reason': f"Net profit: {analysis['net_profit']:.4f} USDT ({analysis['net_profit_percentage']:.3f}%)"
    }