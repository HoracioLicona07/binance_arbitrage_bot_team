# config/settings.py - CONFIGURACIÓN EXTREMA PARA FORZAR OPORTUNIDADES

import logging

# 🔥 CONFIGURACIÓN EXTREMA PARA DETECTAR OPORTUNIDADES GARANTIZADO
LIVE = True

# Configuración de mercado AMPLIADA AL MÁXIMO
TOP_N_PAIRS = 100         # MÁXIMO posible
BOOK_LIMIT = 20           
BASE_ASSET = 'USDT'       

# 🎯 CONFIGURACIÓN DE RENTABILIDAD EXTREMADAMENTE AGRESIVA
PROFIT_THOLD = 0.0005     # 0.05% ganancia mínima (EXTREMO)
SLIPPAGE_PCT = 0.005      # 0.5% slippage
HOLD_SECONDS = 2          

# 💰 CANTIDADES MUY AMPLIAS
QUANTUMS_USDT = [3, 5, 8, 10, 12, 15, 18, 20, 25, 30]  # MÁS opciones

# ⚡ CONFIGURACIÓN DE TIMING ULTRA-RÁPIDA
SLEEP_BETWEEN = 0.5       # SUPER rápido - 0.5 segundos

# Configuración de logging
LOG_LEVEL = logging.INFO

# 🛡️ LÍMITES ULTRA-FLEXIBLES
MAX_POSITION_SIZE = 30     # Aumentado
MAX_DAILY_RISK = 100       # Muy alto
MIN_LIQUIDITY = 100        # MUY bajo para más flexibilidad
MAX_DAILY_TRADES = 100     # Sin límites prácticos

# 🎲 CONFIGURACIÓN ULTRA-RELAJADA
MAX_EXECUTION_TIME = 20    
MIN_CONFIDENCE = 0.1       # Solo 10% mínimo (EXTREMO)
MAX_SLIPPAGE = 0.05        # 5% slippage máximo

# Configuración de API
API_TIMEOUT = 10           
MAX_RETRIES = 5            

# VERIFICACIÓN DE BALANCE MUY FLEXIBLE
MIN_BALANCE_REQUIRED = 3   # Solo 3 USDT
BALANCE_MULTIPLIER = 1.1   # Muy poco restrictivo

# CONFIGURACIÓN DE ALERTAS ULTRA-SENSIBLES
ENABLE_PROFIT_ALERTS = True    
ENABLE_LOSS_ALERTS = True      
ENABLE_ERROR_ALERTS = True     

# Límites para alertas EXTREMADAMENTE SENSIBLES
PROFIT_ALERT_THRESHOLD = 0.1   # Alertar con solo 0.1 USDT
LOSS_ALERT_THRESHOLD = 0.1     

# 🔥 CONFIGURACIÓN EXPERIMENTAL EXTREMA
EXPERIMENTAL_MODE = True
MICRO_ARBITRAGE_ENABLED = True
LOW_PROFIT_DETECTION = True
ULTRA_AGGRESSIVE_MODE = True

# 🚨 NUEVAS CONFIGURACIONES EXTREMAS
FORCE_OPPORTUNITIES = True      # Forzar detección
IGNORE_SMALL_PROFITS = False   # Aceptar cualquier ganancia
RELAXED_VALIDATION = True      # Validación muy relajada
TURBO_MODE = True              # Modo turbo activado

print("🚨 CONFIGURACIÓN EXTREMA CARGADA")
print("🔥 MODO TURBO ULTRA-AGRESIVO ACTIVADO")
print("⚠️ FORZANDO DETECCIÓN DE OPORTUNIDADES")
print(f"Configuración EXTREMA:")
print(f"   🎯 Ganancia mínima: {PROFIT_THOLD*100:.3f}% (EXTREMO)")
print(f"   💰 Cantidades: {QUANTUMS_USDT}")
print(f"   📊 Pares monitoreados: {TOP_N_PAIRS}")
print(f"   ⚡ Ciclos cada: {SLEEP_BETWEEN}s (TURBO)")
print(f"   🎲 Confianza mínima: {MIN_CONFIDENCE*100:.0f}% (EXTREMO)")
print(f"   📈 Balance mínimo: {MIN_BALANCE_REQUIRED} USDT")
print("="*50)