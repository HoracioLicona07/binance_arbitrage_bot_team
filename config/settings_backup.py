# binance_arbitrage_bot/config/settings.py
# Python 3.10

import logging

# =============================================================================
# 🔴 CONFIGURACIÓN PARA TRADES REALES
# =============================================================================

# 🟢 ACTIVAR TRADES REALES
LIVE = True  # ✅ True = trades reales, False = simulación

# Configuración de mercado
TOP_N_PAIRS = 40          # AMPLIADO de 30 -> 40
BOOK_LIMIT = 20           # Profundidad de orderbook
BASE_ASSET = 'USDT'       # Asset base para arbitraje

# Configuración de rentabilidad (más agresiva)
PROFIT_THOLD = 0.004      # 0.4% ganancia mínima (antes 0.008)
SLIPPAGE_PCT = 0.002      # 0.2% slippage esperado
HOLD_SECONDS = 3          # Tiempo estimado de ejecución

# 🔥 CANTIDADES PARA TRADES REALES
QUANTUMS_USDT = [10, 15, 20, 25]  # Ampliado de [10, 15] -> [10, 15, 20, 25]

# Configuración de timing
SLEEP_BETWEEN = 2         # Más rápido: 3 -> 2 s entre ciclos

# Configuración de logging
LOG_LEVEL = logging.INFO

# =============================================================================
# LÍMITES DE SEGURIDAD PARA TRADES REALES
# =============================================================================

# Límites de riesgo y operación
MAX_POSITION_SIZE = 30     # Subido de 20 -> 30 USDT por posición
MAX_DAILY_RISK = 50        # Máximo 50 USDT de riesgo por día (sin cambio)
MIN_LIQUIDITY = 2000       # Liquidez mínima requerida (USDT) (sin cambio)
MAX_DAILY_TRADES = 25      # Subido de 20 -> 25 trades por día

# Configuración de performance
MAX_EXECUTION_TIME = 8     # Máximo 8 s por trade (sin cambio)
MIN_CONFIDENCE = 0.60      # Bajado de 0.75 -> 0.60
MAX_SLIPPAGE = 0.015       # 1.5% slippage máximo (sin cambio)

# Configuración de API
API_TIMEOUT = 8            # Timeout de 8 s para API calls (sin cambio)
MAX_RETRIES = 3            # Máximo 3 reintentos por API call (sin cambio)

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
print("⚙️  PERFIL: Configuración más agresiva aplicada con guardas")
print("💡 Revisa riesgos y límites diarios antes de operar")

# Validaciones automáticas
# Permitimos 0.004 en LIVE, pero prevenimos valores aún más bajos.
if LIVE and PROFIT_THOLD < 0.004:
    print("⚠️ ADVERTENCIA: PROFIT_THOLD por debajo de 0.4% no permitido en LIVE. Ajustando a 0.4%.")
    PROFIT_THOLD = 0.004

# Mantén el guard-rail de cantidades demasiado altas (no aplica con 25, pero se conserva)
if LIVE and max(QUANTUMS_USDT) > 50:
    print("⚠️ ADVERTENCIA: Cantidades muy altas para modo LIVE. Ajustando a perfil conservador.")
    QUANTUMS_USDT = [10, 15]

# Mostrar configuración actual
print(f"📊 Configuración TRADES REALES:")
print(f"   🎯 Ganancia mínima: {PROFIT_THOLD*100:.2f}%")
print(f"   💰 Cantidades: {QUANTUMS_USDT} USDT")
print(f"   🛡️ Posición máxima: {MAX_POSITION_SIZE} USDT")
print(f"   📈 Trades máximos/día: {MAX_DAILY_TRADES}")
print(f"   ⏱️ Pausa entre ciclos: {SLEEP_BETWEEN}s")
print(f"   🎲 Confianza mínima: {MIN_CONFIDENCE*100:.0f}%")
print(f"   🔍 Top N pares: {TOP_N_PAIRS}")
