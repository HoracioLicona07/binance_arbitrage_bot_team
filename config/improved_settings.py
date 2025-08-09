# config/improved_settings.py
# Configuración optimizada para detectar más oportunidades

import logging

# =============================================================================
# 🔴 CONFIGURACIÓN OPTIMIZADA PARA DETECTAR OPORTUNIDADES
# =============================================================================

# 🟢 ACTIVAR TRADES REALES
LIVE = True  # True = trades reales, False = simulación

# Configuración de mercado AMPLIADA
TOP_N_PAIRS = 50          # Aumentado para más pares
BOOK_LIMIT = 20           # Profundidad de orderbook
BASE_ASSET = 'USDT'       # Asset base para arbitraje

# Configuración de rentabilidad MÁS AGRESIVA
PROFIT_THOLD = 0.004      # 0.4% ganancia mínima (reducido de 0.8%)
SLIPPAGE_PCT = 0.002      # 0.2% slippage esperado
HOLD_SECONDS = 3          # Tiempo estimado de ejecución

# 🔥 CANTIDADES AMPLIADAS PARA MÁS OPORTUNIDADES
QUANTUMS_USDT = [10, 15, 20, 25, 30]  # Más opciones de cantidad

# Configuración de timing OPTIMIZADA
SLEEP_BETWEEN = 2         # Ciclos más rápidos (reducido de 3s)

# Configuración de logging
LOG_LEVEL = logging.INFO

# =============================================================================
# LÍMITES DE SEGURIDAD AJUSTADOS
# =============================================================================

# Límites de riesgo MENOS RESTRICTIVOS
MAX_POSITION_SIZE = 35     # Aumentado de 20 a 35 USDT
MAX_DAILY_RISK = 75        # Aumentado de 50 a 75 USDT  
MIN_LIQUIDITY = 1000       # Reducido de 2000 a 1000 USDT
MAX_DAILY_TRADES = 30      # Aumentado de 20 a 30 trades

# Configuración de performance OPTIMIZADA
MAX_EXECUTION_TIME = 10    # Más tiempo para trades complejos
MIN_CONFIDENCE = 0.6       # Reducido de 0.75 a 0.6 (60%)
MAX_SLIPPAGE = 0.02        # Aumentado de 1.5% a 2%

# Configuración de API
API_TIMEOUT = 10           # Más tiempo para API calls
MAX_RETRIES = 3            # Máximo 3 reintentos

# =============================================================================
# CONFIGURACIÓN MEJORADA PARA DETECCIÓN
# =============================================================================

# Monedas prioritarias para arbitraje
PRIORITY_COINS = [
    'BTC', 'ETH', 'BNB', 'ADA', 'DOT', 'LINK', 'XRP', 'LTC', 
    'MATIC', 'AVAX', 'SOL', 'DOGE', 'ATOM', 'FIL', 'TRX'
]

# Configuración adaptativa
ADAPTIVE_THRESHOLD_ENABLED = True
THRESHOLD_REDUCTION_FACTOR = 0.9    # Reducir 10% si no hay oportunidades
THRESHOLD_INCREASE_FACTOR = 1.1     # Aumentar 10% si hay muchas
MIN_ADAPTIVE_THRESHOLD = 0.002      # Mínimo 0.2%
MAX_ADAPTIVE_THRESHOLD = 0.015      # Máximo 1.5%

# Configuración de calidad
MIN_QUALITY_SCORE = 0.3             # Reducido para más oportunidades
LIQUIDITY_WEIGHT = 0.3              # Peso de liquidez en score
PROFITABILITY_WEIGHT = 0.4          # Peso de rentabilidad
TIMING_WEIGHT = 0.3                 # Peso de timing

# =============================================================================
# CONFIGURACIÓN DE ALERTAS MEJORADA
# =============================================================================

# Alertas menos restrictivas
ENABLE_PROFIT_ALERTS = True
ENABLE_LOSS_ALERTS = True  
ENABLE_ERROR_ALERTS = True
ENABLE_OPPORTUNITY_ALERTS = True    # Nueva: alertas de oportunidades

# Límites para alertas AJUSTADOS
PROFIT_ALERT_THRESHOLD = 2.0        # Reducido de 5.0 a 2.0 USDT
LOSS_ALERT_THRESHOLD = 1.0          # Reducido de 2.0 a 1.0 USDT
OPPORTUNITY_ALERT_MIN = 3           # Alertar si hay +3 oportunidades

# =============================================================================
# CONFIGURACIÓN AVANZADA
# =============================================================================

# Configuración de mercado
MARKET_HOURS_OPTIMIZATION = True    # Optimizar según horas de mercado
WEEKEND_FACTOR = 0.8                # Factor de reducción en fines de semana
NIGHT_FACTOR = 0.9                  # Factor de reducción en horario nocturno

# Configuración de ML (si está disponible)
ML_ENABLED = True                   # Activar ML si está disponible
ML_CONFIDENCE_WEIGHT = 0.3          # Peso del ML en decisiones
ML_LEARNING_RATE = 0.01             # Tasa de aprendizaje

# Configuración de red
WEBSOCKET_ENABLED = True            # Usar WebSocket si está disponible
FALLBACK_TO_REST = True             # Usar REST API como fallback
CONNECTION_TIMEOUT = 5              # Timeout de conexión

# =============================================================================
# VALIDACIONES DE CONFIGURACIÓN MEJORADA
# =============================================================================

print("🚀 CONFIGURACIÓN OPTIMIZADA PARA DETECCIÓN")
print("⚡ PARÁMETROS AJUSTADOS PARA MÁS OPORTUNIDADES")

# Validaciones automáticas mejoradas
if LIVE and PROFIT_THOLD < 0.003:
    print("⚠️ ADVERTENCIA: Threshold muy bajo para modo LIVE")
    print(f"💡 Usando threshold mínimo seguro: 0.3%")
    PROFIT_THOLD = 0.003
    
if LIVE and max(QUANTUMS_USDT) > 50:
    print("⚠️ ADVERTENCIA: Cantidades muy altas")
    QUANTUMS_USDT = [10, 15, 20, 25, 30]

# Mostrar configuración optimizada
print(f"📊 Configuración OPTIMIZADA:")
print(f"   🎯 Ganancia mínima: {PROFIT_THOLD*100:.2f}% (reducida)")
print(f"   💰 Cantidades: {QUANTUMS_USDT} USDT (ampliadas)")
print(f"   🛡️ Posición máxima: {MAX_POSITION_SIZE} USDT (aumentada)")
print(f"   📈 Trades máximos/día: {MAX_DAILY_TRADES} (aumentados)")
print(f"   ⏱️ Pausa entre ciclos: {SLEEP_BETWEEN}s (acelerada)")
print(f"   🎲 Confianza mínima: {MIN_CONFIDENCE*100:.0f}% (reducida)")
print(f"   📈 Pares monitoreados: {TOP_N_PAIRS} (ampliados)")
print(f"   🔄 Threshold adaptativo: {'✅' if ADAPTIVE_THRESHOLD_ENABLED else '❌'}")

# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def get_current_time_factor():
    """Obtiene factor basado en hora actual"""
    import datetime
    hour = datetime.datetime.now().hour
    
    # Horas óptimas de trading (UTC)
    if 6 <= hour <= 22:
        return 1.0  # Horario principal
    elif 0 <= hour <= 6:
        return NIGHT_FACTOR  # Horario nocturno
    else:
        return 0.9  # Otras horas

def get_weekend_factor():
    """Obtiene factor para fines de semana"""
    import datetime
    weekday = datetime.datetime.now().weekday()
    
    if weekday >= 5:  # Sábado (5) o Domingo (6)
        return WEEKEND_FACTOR
    else:
        return 1.0

def calculate_adaptive_sleep():
    """Calcula tiempo de sleep adaptativo"""
    base_sleep = SLEEP_BETWEEN
    time_factor = get_current_time_factor()
    weekend_factor = get_weekend_factor()
    
    return base_sleep * time_factor * weekend_factor

def is_high_activity_period():
    """Determina si es período de alta actividad"""
    import datetime
    hour = datetime.datetime.now().hour
    weekday = datetime.datetime.now().weekday()
    
    # Lunes a Viernes, 8 AM a 6 PM UTC
    return weekday < 5 and 8 <= hour <= 18

# =============================================================================
# CONFIGURACIÓN DINÁMICA
# =============================================================================

class DynamicConfig:
    """Configuración que se ajusta dinámicamente"""
    
    def __init__(self):
        self.current_threshold = PROFIT_THOLD
        self.opportunities_history = []
        
    def update_threshold(self, opportunities_found):
        """Actualiza threshold basado en oportunidades encontradas"""
        self.opportunities_history.append(opportunities_found)
        
        # Mantener solo últimas 20 mediciones
        if len(self.opportunities_history) > 20:
            self.opportunities_history = self.opportunities_history[-20:]
        
        # Calcular promedio de oportunidades
        avg_opportunities = sum(self.opportunities_history) / len(self.opportunities_history)
        
        # Ajustar threshold
        if avg_opportunities < 1:
            # Pocas oportunidades: reducir threshold
            self.current_threshold *= THRESHOLD_REDUCTION_FACTOR
            self.current_threshold = max(MIN_ADAPTIVE_THRESHOLD, self.current_threshold)
        elif avg_opportunities > 4:
            # Muchas oportunidades: aumentar threshold  
            self.current_threshold *= THRESHOLD_INCREASE_FACTOR
            self.current_threshold = min(MAX_ADAPTIVE_THRESHOLD, self.current_threshold)
        
        return self.current_threshold
    
    def get_current_settings(self):
        """Obtiene configuración actual"""
        return {
            'threshold': self.current_threshold,
            'max_position': MAX_POSITION_SIZE,
            'sleep_time': calculate_adaptive_sleep(),
            'high_activity': is_high_activity_period(),
            'opportunities_avg': sum(self.opportunities_history) / max(len(self.opportunities_history), 1)
        }

# Instancia global de configuración dinámica
dynamic_config = DynamicConfig()

print("✅ Configuración optimizada cargada - Lista para detectar más oportunidades")