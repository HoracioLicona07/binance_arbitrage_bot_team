# config/settings.py - Configuración optimizada para detectar MÁS oportunidades

import logging

# 🔥 CONFIGURACIÓN ULTRA-AGRESIVA PARA DETECTAR OPORTUNIDADES
LIVE = True

# Configuración de mercado AMPLIADA
TOP_N_PAIRS = 50          # Aumentado de 30 a 50 pares
BOOK_LIMIT = 20           
BASE_ASSET = 'USDT'       

# 🎯 CONFIGURACIÓN DE RENTABILIDAD MUY AGRESIVA
PROFIT_THOLD = 0.002      # 0.2% ganancia mínima (reducido de 0.3% a 0.2%)
SLIPPAGE_PCT = 0.002      
HOLD_SECONDS = 3          

# 💰 CANTIDADES AMPLIADAS PARA MÁS OPORTUNIDADES
QUANTUMS_USDT = [5, 8, 10, 15, 20]  # Más opciones de cantidad

# ⚡ CONFIGURACIÓN DE TIMING SUPER RÁPIDA
SLEEP_BETWEEN = 1         # Reducido de 2s a 1s (ciclos más rápidos)

# Configuración de logging
LOG_LEVEL = logging.INFO

# 🛡️ LÍMITES AJUSTADOS PARA MÁS FLEXIBILIDAD
MAX_POSITION_SIZE = 20     # Aumentado de 10 a 20 USDT
MAX_DAILY_RISK = 40        # Aumentado de 20 a 40 USDT
MIN_LIQUIDITY = 500        # Mantenido bajo para más flexibilidad
MAX_DAILY_TRADES = 30      # Aumentado de 15 a 30 trades

# 🎲 CONFIGURACIÓN DE PERFORMANCE MUY RELAJADA
MAX_EXECUTION_TIME = 15    
MIN_CONFIDENCE = 0.3       # Reducido de 0.5 a 0.3 (30% mínimo)
MAX_SLIPPAGE = 0.03        # Aumentado a 3% slippage máximo

# Configuración de API
API_TIMEOUT = 8            
MAX_RETRIES = 3            

# VERIFICACIÓN DE BALANCE MÁS FLEXIBLE
MIN_BALANCE_REQUIRED = 5   # Reducido de 8 a 5 USDT
BALANCE_MULTIPLIER = 1.2   # Reducido para ser menos restrictivo

# CONFIGURACIÓN DE ALERTAS
ENABLE_PROFIT_ALERTS = True    
ENABLE_LOSS_ALERTS = True      
ENABLE_ERROR_ALERTS = True     

# Límites para alertas MUY SENSIBLES
PROFIT_ALERT_THRESHOLD = 0.5   # Alertar con solo 0.5 USDT ganancia
LOSS_ALERT_THRESHOLD = 0.3     # Alertar con 0.3 USDT pérdida

# 🔥 CONFIGURACIÓN EXPERIMENTAL PARA DETECTAR MÁS OPORTUNIDADES
EXPERIMENTAL_MODE = True
MICRO_ARBITRAGE_ENABLED = True
LOW_PROFIT_DETECTION = True

print("🔥 CONFIGURACIÓN ULTRA-AGRESIVA CARGADA")
print("🎯 OPTIMIZADA PARA DETECTAR MÁXIMO DE OPORTUNIDADES")
print("⚠️ MODO EXPERIMENTAL ACTIVADO")
print(f"Configuración:")
print(f"   🎯 Ganancia mínima: {PROFIT_THOLD*100:.2f}% (MUY AGRESIVO)")
print(f"   💰 Cantidades: {QUANTUMS_USDT}")
print(f"   📊 Pares monitoreados: {TOP_N_PAIRS}")
print(f"   ⚡ Ciclos cada: {SLEEP_BETWEEN}s")
print(f"   🎲 Confianza mínima: {MIN_CONFIDENCE*100:.0f}%")
print(f"   📈 Balance mínimo: {MIN_BALANCE_REQUIRED} USDT")
print("="*50)