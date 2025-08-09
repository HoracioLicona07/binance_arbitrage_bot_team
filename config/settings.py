# binance_arbitrage_bot/config/settings.py

import logging

# =============================================================================
# CONFIGURACIÓN PRINCIPAL DEL BOT
# =============================================================================

# 🔴 IMPORTANTE: Configurar en False para SIMULACIÓN
LIVE = False  # ⚠️ True = trades reales, False = simulación

# Configuración de mercado
TOP_N_PAIRS = 50          # Reducido para mejor rendimiento
BOOK_LIMIT = 20           # Reducido para optimización
BASE_ASSET = 'USDT'       # Asset base para arbitraje

# Configuración de rentabilidad
PROFIT_THOLD = 0.001      # 0.1% ganancia mínima
SLIPPAGE_PCT = 0.001      # 0.1% slippage esperado
HOLD_SECONDS = 5          # Tiempo estimado de ejecución

# Configuración de cantidades (USDT)
QUANTUMS_USDT = [10, 25]  # Cantidades pequeñas para pruebas

# Configuración de timing
SLEEP_BETWEEN = 2         # Pausa entre ciclos (segundos)

# Configuración de logging
LOG_LEVEL = logging.INFO

# =============================================================================
# CONFIGURACIÓN AVANZADA (OPCIONAL)
# =============================================================================

# Límites de riesgo
MAX_POSITION_SIZE = 50    # Máximo 50 USDT por posición
MAX_DAILY_RISK = 100      # Máximo 100 USDT de riesgo por día
MIN_LIQUIDITY = 1000      # Liquidez mínima requerida (USDT)

# Configuración de performance
MAX_EXECUTION_TIME = 10   # Máximo 10 segundos por trade
MIN_CONFIDENCE = 0.6      # 60% confianza mínima
MAX_SLIPPAGE = 0.02       # 2% slippage máximo

# Configuración de API
API_TIMEOUT = 10          # Timeout de 10 segundos para API calls
MAX_RETRIES = 3           # Máximo 3 reintentos por API call

# =============================================================================
# CONFIGURACIONES POR MODO
# =============================================================================

if LIVE:
    # Configuración para trading real (MÁS CONSERVADORA)
    PROFIT_THOLD = 0.005    # 0.5% ganancia mínima para trades reales
    QUANTUMS_USDT = [10]    # Solo 10 USDT para trades reales iniciales
    SLEEP_BETWEEN = 3       # Más tiempo entre ciclos
    MAX_POSITION_SIZE = 25  # Posiciones más pequeñas
    
    print("🔴 MODO LIVE ACTIVADO - TRADES REALES")
    print("⚠️  USAR CON PRECAUCIÓN")
    
else:
    # Configuración para simulación (MÁS AGRESIVA PARA TESTING)
    PROFIT_THOLD = 0.001    # 0.1% para encontrar más oportunidades
    QUANTUMS_USDT = [10, 25, 50]  # Varias cantidades para testing
    SLEEP_BETWEEN = 2       # Ciclos más rápidos
    
    print("✅ MODO SIMULACIÓN ACTIVADO")
    print("💡 No se ejecutarán trades reales")

# =============================================================================
# CONFIGURACIÓN DE DEBUGGING
# =============================================================================

# Configuración de logs detallados
DETAILED_LOGGING = True   # Logs más detallados
LOG_OPPORTUNITIES = True  # Loggear todas las oportunidades encontradas
LOG_PERFORMANCE = True    # Loggear métricas de rendimiento

# Configuración de testing
TEST_MODE = not LIVE      # True en simulación
QUICK_TEST = False        # True para testing rápido (menos monedas)

if QUICK_TEST:
    TOP_N_PAIRS = 20
    QUANTUMS_USDT = [10]
    print("🚀 MODO TESTING RÁPIDO ACTIVADO")

# =============================================================================
# VALIDACIONES DE CONFIGURACIÓN
# =============================================================================

# Validar configuración
if LIVE and PROFIT_THOLD < 0.003:
    print("⚠️ ADVERTENCIA: Threshold de ganancia muy bajo para modo LIVE")
    
if LIVE and max(QUANTUMS_USDT) > 100:
    print("⚠️ ADVERTENCIA: Cantidades muy altas para modo LIVE")

if not LIVE and SLEEP_BETWEEN > 5:
    print("💡 INFO: Considera reducir SLEEP_BETWEEN para simulación más rápida")

# Mostrar configuración actual
print(f"📊 Configuración cargada:")
print(f"   Modo: {'🔴 LIVE' if LIVE else '✅ SIMULACIÓN'}")
print(f"   Ganancia mínima: {PROFIT_THOLD*100:.2f}%")
print(f"   Cantidades: {QUANTUMS_USDT} USDT")
print(f"   Pares a evaluar: {TOP_N_PAIRS}")
print(f"   Pausa entre ciclos: {SLEEP_BETWEEN}s")