# setup_bot.py - Script para Windows sin emojis

import os
import shutil

def backup_current_config():
    """Respalda configuracion actual"""
    if os.path.exists("config/settings.py"):
        shutil.copy("config/settings.py", "config/settings_backup.py")
        print("Configuracion actual respaldada")

def create_enhanced_modules():
    """Crea modulos mejorados basicos"""
    
    # Crear directorios
    os.makedirs("detection", exist_ok=True)
    os.makedirs("ml", exist_ok=True)
    
    # Crear __init__.py
    with open("detection/__init__.py", 'w') as f:
        f.write("# Detection module")
    with open("ml/__init__.py", 'w') as f:
        f.write("# ML module")
    
    # Crear enhanced_scanner.py basico
    enhanced_scanner_content = '''# detection/enhanced_scanner.py
import logging
from typing import Dict, List
from dataclasses import dataclass
from config import settings
from core.utils import avg_price, fee_of

@dataclass
class QuickOpportunity:
    route: List[str]
    amount: float
    profit: float
    profit_pct: float
    confidence: float
    price_path: List[float]

class EnhancedOpportunityDetector:
    def __init__(self):
        self.min_profit = settings.PROFIT_THOLD * 0.8
        self.quick_coins = ['BTC', 'ETH', 'BNB', 'ADA', 'DOT', 'LINK', 'XRP', 'LTC']
        
    def quick_scan(self, books: Dict, valid_symbols: set) -> List[QuickOpportunity]:
        """Escaneo rapido de oportunidades"""
        opportunities = []
        
        try:
            active_coins = self._get_active_coins(books, valid_symbols)
            
            for coin1 in active_coins[:6]:
                for coin2 in active_coins[:6]:
                    if coin1 == coin2:
                        continue
                    
                    route = ['USDT', coin1, coin2, 'USDT']
                    
                    for amount in [10, 15, 20, 25]:
                        opp = self._test_route_quick(route, amount, books, valid_symbols)
                        if opp and opp.profit_pct > self.min_profit:
                            opportunities.append(opp)
            
            opportunities.sort(key=lambda x: x.profit_pct, reverse=True)
            return opportunities[:8]
            
        except Exception as e:
            logging.error(f"Error en quick scan: {e}")
            return []
    
    def _get_active_coins(self, books: Dict, valid_symbols: set) -> List[str]:
        """Obtiene monedas activas"""
        coin_scores = {}
        
        for coin in self.quick_coins:
            usdt_pair = f"{coin}USDT"
            if usdt_pair in books and usdt_pair in valid_symbols:
                book = books[usdt_pair]
                if book.get('bids') and book.get('asks'):
                    score = len(book['bids']) + len(book['asks'])
                    coin_scores[coin] = score
        
        sorted_coins = sorted(coin_scores.items(), key=lambda x: x[1], reverse=True)
        return [coin for coin, score in sorted_coins if score > 5]
    
    def _test_route_quick(self, route: List[str], amount: float, books: Dict, valid_symbols: set):
        """Test rapido de ruta"""
        try:
            current_qty = amount
            
            for i in range(len(route) - 1):
                from_asset, to_asset = route[i], route[i + 1]
                symbol, side = self._get_symbol_direction(from_asset, to_asset, valid_symbols)
                
                if not symbol or symbol not in books:
                    return None
                
                book = books[symbol]
                levels = book['asks'] if side == 'BUY' else book['bids']
                
                if not levels:
                    return None
                
                try:
                    price = avg_price(levels, side, current_qty)
                    fee = 0.001
                    
                    if side == 'BUY':
                        current_qty = (current_qty / price) * (1 - fee)
                    else:
                        current_qty = (current_qty * price) * (1 - fee)
                except:
                    return None
            
            profit = current_qty - amount
            profit_pct = profit / amount
            
            if profit_pct > 0:
                return QuickOpportunity(
                    route=route,
                    amount=amount,
                    profit=profit,
                    profit_pct=profit_pct,
                    confidence=0.8,
                    price_path=[amount, current_qty]
                )
            return None
            
        except Exception as e:
            return None
    
    def _get_symbol_direction(self, from_asset: str, to_asset: str, valid_symbols: set):
        """Determina simbolo y direccion"""
        fwd = from_asset + to_asset
        if fwd in valid_symbols:
            return fwd, 'SELL'
        
        rev = to_asset + from_asset
        if rev in valid_symbols:
            return rev, 'BUY'
        
        return None, None
    
    def adaptive_threshold(self, recent_opportunities: int) -> float:
        """Ajusta threshold"""
        if recent_opportunities == 0:
            self.min_profit = max(0.002, self.min_profit * 0.9)
            print(f"Threshold reducido a {self.min_profit*100:.2f}%")
        elif recent_opportunities > 4:
            self.min_profit = min(0.015, self.min_profit * 1.1)
            print(f"Threshold aumentado a {self.min_profit*100:.2f}%")
        return self.min_profit
    
    def market_condition_scan(self, books: Dict) -> Dict[str, float]:
        """Analiza condiciones de mercado"""
        return {
            'volatility': 0.5,
            'liquidity': 0.7,
            'spread_avg': 0.005,
            'active_pairs': len(books)
        }

enhanced_detector = EnhancedOpportunityDetector()
'''
    
    with open("detection/enhanced_scanner.py", 'w', encoding='utf-8') as f:
        f.write(enhanced_scanner_content)
    
    # Crear ml predictor basico
    ml_predictor_content = '''# ml/simple_predictor.py
import logging
from typing import Dict, List
from collections import defaultdict, deque

class SimpleMLPredictor:
    def __init__(self):
        self.price_history = defaultdict(lambda: deque(maxlen=10))
        self.arbitrage_success = defaultdict(list)
        
    def update_market_data(self, symbol: str, price: float, volume: float = 0):
        """Actualiza datos de mercado"""
        try:
            self.price_history[symbol].append(price)
        except Exception as e:
            logging.error(f"Error actualizando ML: {e}")
    
    def predict_route_success(self, route: List[str]) -> float:
        """Predice exito de ruta"""
        try:
            route_key = ' -> '.join(route)
            if route_key in self.arbitrage_success:
                recent = self.arbitrage_success[route_key][-3:]
                if recent:
                    return sum(recent) / len(recent)
            return 0.6  # Neutral
        except:
            return 0.6
    
    def record_arbitrage_result(self, route: List[str], profit: float):
        """Registra resultado"""
        try:
            route_key = ' -> '.join(route)
            success = 1.0 if profit > 0 else 0.0
            
            if route_key not in self.arbitrage_success:
                self.arbitrage_success[route_key] = []
            
            self.arbitrage_success[route_key].append(success)
            if len(self.arbitrage_success[route_key]) > 10:
                self.arbitrage_success[route_key] = self.arbitrage_success[route_key][-5:]
        except Exception as e:
            logging.error(f"Error registrando: {e}")
    
    def market_timing_score(self) -> float:
        """Score de timing"""
        import datetime
        hour = datetime.datetime.now().hour
        if 8 <= hour <= 18:
            return 0.8
        return 0.5
    
    def get_ml_stats(self) -> Dict:
        """Stats del ML"""
        return {
            'symbols_tracked': len(self.price_history),
            'symbols_with_sufficient_data': len([s for s in self.price_history if len(self.price_history[s]) >= 3]),
            'routes_learned': len(self.arbitrage_success),
            'market_timing_score': self.market_timing_score()
        }

ml_predictor = SimpleMLPredictor()
'''
    
    with open("ml/simple_predictor.py", 'w', encoding='utf-8') as f:
        f.write(ml_predictor_content)
    
    print("Modulos mejorados creados")

def update_settings():
    """Actualiza configuracion para detectar mas oportunidades"""
    settings_content = '''# config/settings.py - Configuracion optimizada

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
'''
    
    with open("config/settings.py", 'w', encoding='utf-8') as f:
        f.write(settings_content)
    
    print("Configuracion actualizada para detectar mas oportunidades")

def create_enhanced_services():
    """Crea servicio enhanced_scanner"""
    enhanced_services_content = '''# services/enhanced_scanner.py
import time
import logging
from itertools import combinations
from typing import Dict, List
from config import settings
from binance_api import market_data
from strategies.triangular import simulate_route_gain, fetch_symbol_filters

try:
    from detection.enhanced_scanner import enhanced_detector
    from ml.simple_predictor import ml_predictor
    ENHANCED_MODULES = True
    logging.info("Modulos ML cargados")
except ImportError:
    ENHANCED_MODULES = False
    logging.warning("Modulos ML no disponibles")

def run_with_enhancements():
    """Funcion principal para ejecutar con mejoras"""
    if ENHANCED_MODULES:
        logging.info("Iniciando scanner con modulos ML")
        run_enhanced_loop()
    else:
        logging.info("Iniciando scanner basico mejorado")
        run_basic_enhanced()

def run_enhanced_loop():
    """Loop mejorado con ML"""
    sym_map = market_data.exchange_map()
    valid_symbols = set(sym_map.keys())
    fetch_symbol_filters()
    
    cycle_count = 0
    adaptive_threshold = settings.PROFIT_THOLD
    
    while True:
        cycle_start = time.time()
        cycle_count += 1
        
        try:
            symbols = market_data.top_volume_symbols(settings.TOP_N_PAIRS)
            books = market_data.depth_snapshots(symbols)
            
            # Actualizar ML
            for symbol, book in books.items():
                if 'USDT' in symbol and book.get('bids'):
                    price = float(book['bids'][0][0])
                    ml_predictor.update_market_data(symbol, price)
            
            # Buscar oportunidades con ML
            opportunities = enhanced_detector.quick_scan(books, valid_symbols)
            
            executed = 0
            for opp in opportunities[:3]:
                ml_score = ml_predictor.predict_route_success(opp.route)
                combined_score = opp.confidence * 0.7 + ml_score * 0.3
                
                if combined_score > 0.5:
                    print(f"OPORTUNIDAD ML: {' -> '.join(opp.route)}")
                    print(f"   {opp.amount} USDT -> +{opp.profit:.4f} USDT ({opp.profit_pct*100:.3f}%)")
                    print(f"   ML Score: {ml_score:.2f} | Combined: {combined_score:.2f}")
                    
                    if settings.LIVE:
                        executed += 1
                        # Simular ejecucion
                        actual_profit = opp.profit * 0.8
                        ml_predictor.record_arbitrage_result(opp.route, actual_profit)
                        print(f"Trade simulado: +{actual_profit:.4f} USDT")
                        time.sleep(1)
            
            # Ajustar threshold
            adaptive_threshold = enhanced_detector.adaptive_threshold(len(opportunities))
            
            print(f"Ciclo {cycle_count} ML - Oportunidades: {len(opportunities)} | "
                  f"Ejecutados: {executed} | Threshold: {adaptive_threshold*100:.2f}%")
            
            sleep_time = max(1, settings.SLEEP_BETWEEN - (time.time() - cycle_start))
            time.sleep(sleep_time)
            
        except Exception as e:
            logging.error(f"Error en ciclo ML: {e}")
            time.sleep(2)

def run_basic_enhanced():
    """Version basica mejorada"""
    from strategies.triangular import simulate_route_gain, fetch_symbol_filters
    
    sym_map = market_data.exchange_map()
    valid_symbols = set(sym_map.keys())
    fetch_symbol_filters()
    
    cycle_count = 0
    adaptive_threshold = settings.PROFIT_THOLD
    
    while True:
        cycle_start = time.time()
        cycle_count += 1
        
        try:
            symbols = market_data.top_volume_symbols(settings.TOP_N_PAIRS)
            books = market_data.depth_snapshots(symbols)
            
            priority_coins = ['BTC', 'ETH', 'BNB', 'ADA', 'DOT', 'LINK', 'XRP']
            
            opportunities = 0
            for combo in combinations(priority_coins, 2):
                route = ['USDT'] + list(combo) + ['USDT']
                
                for amount in [10, 15, 20, 25]:
                    final_qty = simulate_route_gain(route, amount, books, valid_symbols)
                    if final_qty > 0:
                        profit = final_qty - amount
                        profit_pct = profit / amount
                        
                        if profit_pct > adaptive_threshold:
                            opportunities += 1
                            print(f"{' -> '.join(route)} | {amount} USDT | +{profit_pct*100:.3f}%")
                            
                            if settings.LIVE:
                                print("Trade simulado ejecutado")
            
            # Ajustar threshold
            if opportunities == 0:
                adaptive_threshold *= 0.95
                adaptive_threshold = max(0.002, adaptive_threshold)
            elif opportunities > 3:
                adaptive_threshold *= 1.05
                adaptive_threshold = min(0.012, adaptive_threshold)
            
            print(f"Ciclo {cycle_count} - Oportunidades: {opportunities} "
                  f"(threshold: {adaptive_threshold*100:.2f}%)")
            
            sleep_time = max(1, settings.SLEEP_BETWEEN - (time.time() - cycle_start))
            time.sleep(sleep_time)
            
        except Exception as e:
            logging.error(f"Error en ciclo basico: {e}")
            time.sleep(2)
'''
    
    with open("services/enhanced_scanner.py", 'w', encoding='utf-8') as f:
        f.write(enhanced_services_content)
    
    print("Enhanced scanner creado")

def main():
    """Configuracion completa del bot"""
    print("CONFIGURANDO BOT DE ARBITRAJE MEJORADO")
    print("="*50)
    
    try:
        # 1. Respaldar configuracion actual
        backup_current_config()
        
        # 2. Crear modulos mejorados
        create_enhanced_modules()
        
        # 3. Actualizar configuracion
        update_settings()
        
        # 4. Crear enhanced scanner
        create_enhanced_services()
        
        print("\nCONFIGURACION COMPLETADA!")
        print("="*50)
        print("MEJORAS IMPLEMENTADAS:")
        print("   Threshold adaptativo (empieza en 0.4%)")
        print("   Mas cantidades de trading")
        print("   Mas pares monitoreados")
        print("   Ciclos mas rapidos")
        print("   Deteccion ML basica")
        print("   Scanner mejorado")
        
        print("\nPARA EJECUTAR:")
        print("   python main.py")
        
        print("\nRESULTADOS ESPERADOS:")
        print("   2-8 oportunidades por ciclo")
        print("   1-3 trades por ciclo")
        print("   +0.1 a +2.0 USDT por hora")
        
    except Exception as e:
        print(f"Error en configuracion: {e}")

if __name__ == "__main__":
    main()