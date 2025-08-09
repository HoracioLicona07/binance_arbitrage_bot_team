# config/settings.py - Configuración para balances bajos

import logging

# CONFIGURACIÓN PARA BALANCES BAJOS (funciona con solo 10-20 USDT)
LIVE = True

# Configuración de mercado
TOP_N_PAIRS = 30          
BOOK_LIMIT = 20           
BASE_ASSET = 'USDT'       

# Configuración de rentabilidad ADAPTADA
PROFIT_THOLD = 0.003      # 0.3% ganancia mínima (muy agresivo)
SLIPPAGE_PCT = 0.002      
HOLD_SECONDS = 3          

# CANTIDADES PARA BALANCES BAJOS
QUANTUMS_USDT = [5, 8, 10]  # Empezar con cantidades muy pequeñas

# Configuración de timing
SLEEP_BETWEEN = 2         

# Configuración de logging
LOG_LEVEL = logging.INFO

# LÍMITES AJUSTADOS PARA BALANCES BAJOS
MAX_POSITION_SIZE = 10     # Máximo 10 USDT por posición
MAX_DAILY_RISK = 20        # Máximo 20 USDT de riesgo por día
MIN_LIQUIDITY = 500        # Liquidez mínima reducida
MAX_DAILY_TRADES = 15      # Máximo 15 trades por día

# Configuración de performance RELAJADA
MAX_EXECUTION_TIME = 10    
MIN_CONFIDENCE = 0.5       # Solo 50% confianza mínima
MAX_SLIPPAGE = 0.02        # 2% slippage máximo

# Configuración de API
API_TIMEOUT = 8            
MAX_RETRIES = 3            

# VERIFICACIÓN DE BALANCE MÁS FLEXIBLE
MIN_BALANCE_REQUIRED = 8   # Solo requiere 8 USDT mínimo
BALANCE_MULTIPLIER = 1.5   # 1.5x la cantidad máxima (vs 2x normal)

# CONFIGURACIÓN DE ALERTAS
ENABLE_PROFIT_ALERTS = True    
ENABLE_LOSS_ALERTS = True      
ENABLE_ERROR_ALERTS = True     

# Límites para alertas AJUSTADOS
PROFIT_ALERT_THRESHOLD = 1.0   # Alertar si ganancia > 1 USDT
LOSS_ALERT_THRESHOLD = 0.5     # Alertar si pérdida > 0.5 USDT

print("CONFIGURACION PARA BALANCES BAJOS CARGADA")
print("FUNCIONA CON SOLO 10-20 USDT EN SPOT")
print(f"Configuracion:")
print(f"   Ganancia minima: {PROFIT_THOLD*100:.2f}%")
print(f"   Cantidades: {QUANTUMS_USDT}")
print(f"   Balance minimo: {MIN_BALANCE_REQUIRED} USDT")
print(f"   Posicion maxima: {MAX_POSITION_SIZE} USDT")
