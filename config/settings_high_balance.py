# config/settings.py - Configuracion optimizada

import logging

# CONFIGURACION OPTIMIZADA PARA DETECTAR OPORTUNIDADES
LIVE = True

# Configuracion de mercado AMPLIADA
TOP_N_PAIRS = 40          # Mas pares monitoreados
BOOK_LIMIT = 20           
BASE_ASSET = 'USDT'       

# Configuracion de rentabilidad MAS AGRESIVA
PROFIT_THOLD = 0.004      # 0.4% ganancia minima (reducido de 0.8%)
SLIPPAGE_PCT = 0.002      
HOLD_SECONDS = 3          

# CANTIDADES AMPLIADAS
QUANTUMS_USDT = [10, 15, 20, 25]  # Mas opciones

# Configuracion de timing OPTIMIZADA
SLEEP_BETWEEN = 2         # Ciclos mas rapidos

# Configuracion de logging
LOG_LEVEL = logging.INFO

# LIMITES AJUSTADOS PARA MAS OPORTUNIDADES
MAX_POSITION_SIZE = 30     # Aumentado de 20 a 30 USDT
MAX_DAILY_RISK = 60        # Aumentado 
MIN_LIQUIDITY = 1000       # Reducido para mas flexibilidad
MAX_DAILY_TRADES = 25      # Aumentado

# Configuracion de performance OPTIMIZADA
MAX_EXECUTION_TIME = 8     
MIN_CONFIDENCE = 0.6       # Reducido de 0.75 a 0.6 (60%)
MAX_SLIPPAGE = 0.015       

# Configuracion de API
API_TIMEOUT = 8            
MAX_RETRIES = 3            

# CONFIGURACION DE ALERTAS
ENABLE_PROFIT_ALERTS = True    
ENABLE_LOSS_ALERTS = True      
ENABLE_ERROR_ALERTS = True     

# Limites para alertas
PROFIT_ALERT_THRESHOLD = 3.0   
LOSS_ALERT_THRESHOLD = 1.5     

print("CONFIGURACION OPTIMIZADA CARGADA")
print("PARAMETROS AJUSTADOS PARA MAS OPORTUNIDADES")
print(f"Configuracion:")
print(f"   Ganancia minima: {PROFIT_THOLD*100:.2f}%")
print(f"   Cantidades: {QUANTUMS_USDT}")
print(f"   Pares: {TOP_N_PAIRS}")
print(f"   Ciclos: {SLEEP_BETWEEN}s")
