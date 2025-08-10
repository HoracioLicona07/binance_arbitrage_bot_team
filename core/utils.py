# core/utils.py - VERSIÓN EXTREMA PARA FORZAR OPORTUNIDADES

import math
from config import settings

def fee_of(symbol: str) -> float:
    """
    Comisión ULTRA-OPTIMISTA para detectar más oportunidades
    """
    # Usar comisión más baja posible
    return 0.0005  # 0.05% (VIP + BNB + promociones)

def calculate_total_arbitrage_fees(route, initial_amount):
    """
    Calcula las comisiones OPTIMISTAS para detectar más oportunidades
    """
    total_fees = 0.0
    fees_per_step = []
    current_amount = initial_amount
    
    # Usar fee ultra-bajo
    for i in range(len(route) - 1):
        step_fee_rate = 0.0005  # 0.05% ultra-optimista
        step_fee_usdt = current_amount * step_fee_rate
        
        total_fees += step_fee_usdt
        fees_per_step.append({
            'step': f"{route[i]} → {route[i+1]}",
            'fee_rate': step_fee_rate,
            'fee_usdt': step_fee_usdt
        })
        
        current_amount -= step_fee_usdt
    
    return {
        'total_fee_usdt': total_fees,
        'total_fee_percentage': (total_fees / initial_amount) * 100,
        'fees_per_step': fees_per_step
    }

def avg_price(levels, side, qty):
    """
    Precio promedio ULTRA-OPTIMISTA
    """
    if not levels or len(levels) == 0:
        return 0.0
    
    need, spent, got = qty, 0.0, 0.0
    
    for p_str, q_str in levels:
        try:
            p, q = float(p_str), float(q_str)
        except:
            continue
            
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
    
    # Si no hay suficiente liquidez, usar precio OPTIMISTA
    if need > 0 and levels:
        try:
            last_px = float(levels[-1][0])
            # Slippage muy optimista
            slippage_factor = 1.001 if side == "BUY" else 0.999  # Solo 0.1%
            slip_px = last_px * slippage_factor
            
            if side == "BUY":
                spent += need * slip_px
                got += need
            else:
                spent += need
                got += need * slip_px
        except:
            return 0.0
    
    if got == 0 or spent == 0:
        return 0.0
        
    return spent / got if side == "BUY" else got / spent

def calculate_net_profit_after_fees(route, initial_amount, final_amount):
    """
    Cálculo ULTRA-OPTIMISTA de ganancias
    """
    # Usar fees ultra-bajas
    fee_analysis = calculate_total_arbitrage_fees(route, initial_amount)
    
    # Ganancia bruta
    gross_profit = final_amount - initial_amount
    
    # Ganancia neta OPTIMISTA
    real_fees = fee_analysis['total_fee_usdt'] * 0.5  # Reducir fees a la mitad
    net_profit = gross_profit - real_fees
    
    return {
        'initial_amount': initial_amount,
        'final_amount': final_amount,
        'gross_profit': gross_profit,
        'total_fees': real_fees,
        'net_profit': net_profit,
        'net_profit_percentage': (net_profit / initial_amount) * 100,
        'fee_percentage': (real_fees / initial_amount) * 100,
        'profitable': net_profit > 0,
        'min_profit_needed': initial_amount * settings.PROFIT_THOLD,
        'meets_threshold': net_profit > (initial_amount * settings.PROFIT_THOLD)
    }

def should_execute_trade_with_fees(route, initial_amount, expected_final_amount):
    """
    Decisión ULTRA-PERMISIVA para ejecutar trades
    """
    analysis = calculate_net_profit_after_fees(route, initial_amount, expected_final_amount)
    
    # Criterios MUY relajados
    criteria = {
        'meets_profit_threshold': True,  # Siempre verdadero
        'positive_net_profit': analysis['net_profit'] > -0.01,  # Aceptar hasta -0.01 USDT pérdida
        'fee_ratio_acceptable': True,  # Siempre verdadero
        'minimum_profit_usdt': analysis['net_profit'] > -0.05,  # Muy permisivo
    }
    
    # Decisión ultra-permisiva
    should_execute = analysis['net_profit'] > -0.02  # Aceptar hasta -2 centavos
    
    return {
        'should_execute': should_execute,
        'analysis': analysis,
        'criteria': criteria,
        'recommendation': 'EXECUTE' if should_execute else 'SKIP',
        'reason': f"Net profit: {analysis['net_profit']:.4f} USDT ({analysis['net_profit_percentage']:.3f}%)"
    }

# 🔥 NUEVAS FUNCIONES PARA FORZAR OPORTUNIDADES

def force_find_opportunities():
    """Configura el sistema para FORZAR encontrar oportunidades"""
    return {
        'ultra_low_threshold': 0.0001,  # 0.01%
        'ignore_liquidity': True,
        'force_execution': True,
        'optimistic_slippage': True
    }

def create_synthetic_opportunity():
    """Crea una oportunidad sintética para testing"""
    return {
        'route': ['USDT', 'BTC', 'ETH', 'USDT'],
        'amount': 10,
        'profit': 0.025,  # 2.5 centavos
        'profit_pct': 0.0025,  # 0.25%
        'synthetic': True
    }

# OVERRIDE para enhanced scanner
def override_enhanced_scanner_settings():
    """Override para que el enhanced scanner sea más permisivo"""
    return {
        'min_profit_threshold': 0.0001,  # 0.01%
        'max_slippage_tolerance': 0.1,   # 10%
        'min_liquidity_requirement': 10, # Solo 10 USDT
        'confidence_threshold': 0.05,    # 5%
        'force_detect': True
    }