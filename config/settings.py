# binance_arbitrage_bot/config/settings.py

import logging

# =============================================================================
# 🔴 CONFIGURACIÓN PARA TRADES REALES
# =============================================================================

# 🟢 ACTIVAR TRADES REALES
LIVE = True  # ✅ True = trades reales, False = simulación

# Configuración de mercado
TOP_N_PAIRS = 30          # Reducido para mejor rendimiento
BOOK_LIMIT = 20           # Profundidad de orderbook
BASE_ASSET = 'USDT'       # Asset base para arbitraje

# Configuración de rentabilidad CONSERVADORA para trades reales
PROFIT_THOLD = 0.008      # 0.8% ganancia mínima (más conservador)
SLIPPAGE_PCT = 0.002      # 0.2% slippage esperado
HOLD_SECONDS = 3          # Tiempo estimado de ejecución

# 🔥 CANTIDADES PARA TRADES REALES (EMPEZAR PEQUEÑO)
QUANTUMS_USDT = [10, 15]  # Solo cantidades pequeñas al inicio

# Configuración de timing
SLEEP_BETWEEN = 3         # Pausa más larga entre ciclos para trades reales

# Configuración de logging
LOG_LEVEL = logging.INFO

# =============================================================================
# LÍMITES DE SEGURIDAD PARA TRADES REALES
# =============================================================================

# Límites de riesgo ESTRICTOS
MAX_POSITION_SIZE = 20     # Máximo 20 USDT por posición (conservador)
MAX_DAILY_RISK = 50        # Máximo 50 USDT de riesgo por día
MIN_LIQUIDITY = 2000       # Liquidez mínima requerida (USDT)
MAX_DAILY_TRADES = 20      # Máximo 20 trades por día

# Configuración de performance
MAX_EXECUTION_TIME = 8     # Máximo 8 segundos por trade
MIN_CONFIDENCE = 0.75      # 75% confianza mínima para trades reales
MAX_SLIPPAGE = 0.015       # 1.5% slippage máximo

# Configuración de API
API_TIMEOUT = 8            # Timeout de 8 segundos para API calls
MAX_RETRIES = 3            # Máximo 3 reintentos por API call

# =============================================================================
# CONFIGURACIÓN DE ALERTAS Y MONITOREO
# =============================================================================

# Alertas críticas
ENABLE_PROFIT_ALERTS = True    # Alertas de ganancias
ENABLE_LOSS_ALERTS = True      # Alertas de pérdidas
ENABLE_ERROR_ALERTS = True     # Alertas de errores

# Límites para alertas
PROFIT_ALERT_THRESHOLD = 5.0   # Alertar si ganancia > 5 USDT
LOSS_ALERT_THRESHOLD = 2.0     # Alertar si pérdida > 2 USDT

# =============================================================================
# VALIDACIONES DE SEGURIDAD
# =============================================================================

print("🔴 MODO LIVE ACTIVADO - TRADES REALES")
print("⚠️  CONFIGURACIÓN CONSERVADORA APLICADA")
print("💡 Empezando con cantidades pequeñas para pruebas")

# Validaciones automáticas
if LIVE and PROFIT_THOLD < 0.005:
    print("⚠️ ADVERTENCIA: Threshold de ganancia muy bajo para modo LIVE")
    PROFIT_THOLD = 0.008  # Forzar mínimo 0.8%
    
if LIVE and max(QUANTUMS_USDT) > 50:
    print("⚠️ ADVERTENCIA: Cantidades muy altas para modo LIVE")
    QUANTUMS_USDT = [10, 15]  # Forzar cantidades conservadoras

# Mostrar configuración actual
print(f"📊 Configuración para TRADES REALES:")
print(f"   🎯 Ganancia mínima: {PROFIT_THOLD*100:.2f}%")
print(f"   💰 Cantidades: {QUANTUMS_USDT} USDT")
print(f"   🛡️ Posición máxima: {MAX_POSITION_SIZE} USDT")
print(f"   📈 Trades máximos/día: {MAX_DAILY_TRADES}")
print(f"   ⏱️ Pausa entre ciclos: {SLEEP_BETWEEN}s")
print(f"   🎲 Confianza mínima: {MIN_CONFIDENCE*100:.0f}%")