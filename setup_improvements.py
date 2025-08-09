# setup_improvements.py
# Script para configurar las mejoras rápidamente

import os
import logging

def create_file_if_not_exists(filepath, content):
    """Crea archivo si no existe"""
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Creado: {filepath}")
        else:
            print(f"⚠️ Ya existe: {filepath}")
            
    except Exception as e:
        print(f"❌ Error creando {filepath}: {e}")

def setup_enhanced_detector():
    """Configura enhanced detector"""
    content = '''# binance_arbitrage_bot/detection/enhanced_scanner.py

import logging
import time
from typing import Dict, List, Tuple, Optional
from itertools import combinations
from dataclasses import dataclass
from config import settings
from core.utils import avg_price, fee_of

@dataclass
class QuickOpportunity:
    """Oportunidad rápida detectada"""
    route: List[str]
    amount: float
    profit: float
    profit_pct: float
    confidence: float
    price_path: List[float]

class EnhancedOpportunityDetector:
    def __init__(self):
        self.min_profit = settings.PROFIT_THOLD * 0.7  # Reducir threshold para detectar más
        self.quick_coins = ['BTC', 'ETH', 'BNB', 'ADA', 'DOT', 'LINK', 'XRP', 'LTC']
        
    def quick_scan(self, books: Dict, valid_symbols: set) -> List[QuickOpportunity]:
        """Escaneo rápido de oportunidades más probables"""
        opportunities = []
        
        try:
            # Usar solo monedas con alta liquidez
            active_coins = self._get_active_coins(books, valid_symbols)
            
            # Triangular arbitrage: USDT -> Coin1 -> Coin2 -> USDT
            for coin1 in active_coins[:8]:  # Top 8 monedas
                for coin2 in active_coins[:8]:
                    if coin1 == coin2:
                        continue
                    
                    route = ['USDT', coin1, coin2, 'USDT']
                    
                    for amount in [10, 15, 20]:  # Probar diferentes cantidades
                        opp = self._test_route_quick(route, amount, books, valid_symbols)
                        if opp and opp.profit_pct > self.min_profit:
                            opportunities.append(opp)
            
            # Ordenar por rentabilidad
            opportunities.sort(key=lambda x: x.profit_pct, reverse=True)
            return opportunities[:10]  # Top 10
            
        except Exception as e:
            logging.error(f"❌ Error en quick scan: {e}")
            return []
    
    def _get_active_coins(self, books: Dict, valid_symbols: set) -> List[str]:
        """Obtiene monedas activas con buena liquidez"""
        coin_scores = {}
        
        for coin in self.quick_coins:
            usdt_pair = f"{coin}USDT"
            if usdt_pair in books and usdt_pair in valid_symbols:
                book = books[usdt_pair]
                
                # Evaluar liquidez
                if book.get('bids') and book.get('asks'):
                    bid_depth = sum(float(level[1]) for level in book['bids'][:5])
                    ask_depth = sum(float(level[1]) for level in book['asks'][:5])
                    
                    score = bid_depth + ask_depth
                    coin_scores[coin] = score
        
        # Retornar ordenadas por score
        sorted_coins = sorted(coin_scores.items(), key=lambda x: x[1], reverse=True)
        return [coin for coin, score in sorted_coins if score > 100]
    
    def _test_route_quick(self, route: List[str], amount: float, 
                         books: Dict, valid_symbols: set) -> Optional[QuickOpportunity]:
        """Test rápido de una ruta específica"""
        try:
            current_qty = amount
            confidence = 1.0
            
            for i in range(len(route) - 1):
                from_asset, to_asset = route[i], route[i + 1]
                
                # Determinar símbolo
                symbol, side = self._get_symbol_direction(from_asset, to_asset, valid_symbols)
                if not symbol or symbol not in books:
                    return None
                
                book = books[symbol]
                levels = book['asks'] if side == 'BUY' else book['bids']
                
                if not levels or len(levels) < 2:
                    return None
                
                # Calcular precio y nueva cantidad
                try:
                    price = avg_price(levels, side, current_qty)
                    if price <= 0:
                        return None
                    
                    # Aplicar fees y conversión
                    fee = 0.001  # 0.1% fee
                    
                    if side == 'BUY':
                        current_qty = (current_qty / price) * (1 - fee)
                    else:
                        current_qty = (current_qty * price) * (1 - fee)
                        
                except Exception:
                    return None
            
            # Calcular rentabilidad
            profit = current_qty - amount
            profit_pct = profit / amount
            
            if profit_pct > 0:
                return QuickOpportunity(
                    route=route,
                    amount=amount,
                    profit=profit,
                    profit_pct=profit_pct,
                    confidence=confidence,
                    price_path=[amount, current_qty]
                )
            
            return None
            
        except Exception as e:
            logging.debug(f"❌ Error testing route {route}: {e}")
            return None
    
    def _get_symbol_direction(self, from_asset: str, to_asset: str, 
                            valid_symbols: set) -> Tuple[Optional[str], Optional[str]]:
        """Determina símbolo y dirección de trading"""
        # Intentar forward
        fwd = from_asset + to_asset
        if fwd in valid_symbols:
            return fwd, 'SELL'
        
        # Intentar reverse
        rev = to_asset + from_asset
        if rev in valid_symbols:
            return rev, 'BUY'
        
        return None, None
    
    def adaptive_threshold(self, recent_opportunities: int) -> float:
        """Ajusta el threshold basado en oportunidades encontradas"""
        if recent_opportunities == 0:
            # Reducir threshold si no hay oportunidades
            new_threshold = max(0.003, self.min_profit * 0.8)  # Mínimo 0.3%
            logging.info(f"🎯 Reduciendo threshold a {new_threshold*100:.2f}%")
            self.min_profit = new_threshold
            return new_threshold
        elif recent_opportunities > 5:
            # Aumentar threshold si hay muchas oportunidades
            new_threshold = min(0.015, self.min_profit * 1.2)  # Máximo 1.5%
            logging.info(f"🎯 Aumentando threshold a {new_threshold*100:.2f}%")
            self.min_profit = new_threshold
            return new_threshold
        
        return self.min_profit
    
    def market_condition_scan(self, books: Dict) -> Dict[str, float]:
        """Analiza condiciones de mercado"""
        conditions = {
            'volatility': 0.0,
            'liquidity': 0.0,
            'spread_avg': 0.0,
            'active_pairs': 0
        }
        
        try:
            spreads = []
            
            for symbol, book in books.items():
                if 'USDT' not in symbol:
                    continue
                
                if book.get('bids') and book.get('asks'):
                    conditions['active_pairs'] += 1
                    
                    # Calcular spread
                    best_bid = float(book['bids'][0][0])
                    best_ask = float(book['asks'][0][0])
                    spread = (best_ask - best_bid) / best_bid
                    spreads.append(spread)
            
            if spreads:
                conditions['spread_avg'] = sum(spreads) / len(spreads)
            
            return conditions
            
        except Exception as e:
            logging.error(f"❌ Error analizando condiciones: {e}")
            return conditions

# Instancia global
enhanced_detector = EnhancedOpportunityDetector()
'''
    create_file_if_not_exists("detection/enhanced_scanner.py", content)

def setup_ml_predictor():
    """Configura ML predictor básico"""
    content = '''# binance_arbitrage_bot/ml/simple_predictor.py

import logging
import statistics
from typing import Dict, List
from collections import defaultdict, deque

class SimpleMLPredictor:
    def __init__(self):
        self.price_history = defaultdict(lambda: deque(maxlen=20))
        self.arbitrage_success = defaultdict(list)
        
    def update_market_data(self, symbol: str, price: float, volume: float = 0):
        """Actualiza datos de mercado para análisis"""
        try:
            self.price_history[symbol].append(price)
        except Exception as e:
            logging.error(f"❌ Error actualizando datos ML: {e}")
    
    def predict_route_success(self, route: List[str]) -> float:
        """Predice probabilidad de éxito para una ruta"""
        try:
            # Score básico basado en historial
            route_key = ' -> '.join(route)
            
            if route_key in self.arbitrage_success:
                recent_results = self.arbitrage_success[route_key][-5:]
                if recent_results:
                    success_rate = sum(1 for r in recent_results if r > 0) / len(recent_results)
                    return success_rate
            
            return 0.5  # Neutral para rutas nuevas
            
        except Exception as e:
            logging.error(f"❌ Error prediciendo ruta: {e}")
            return 0.5
    
    def record_arbitrage_result(self, route: List[str], profit: float):
        """Registra resultado de arbitraje para aprendizaje"""
        try:
            route_key = ' -> '.join(route)
            success_score = 1.0 if profit > 0 else 0.0
            
            if route_key not in self.arbitrage_success:
                self.arbitrage_success[route_key] = []
            
            self.arbitrage_success[route_key].append(success_score)
            
            # Limitar historial
            if len(self.arbitrage_success[route_key]) > 20:
                self.arbitrage_success[route_key] = self.arbitrage_success[route_key][-10:]
                
        except Exception as e:
            logging.error(f"❌ Error registrando resultado: {e}")
    
    def market_timing_score(self) -> float:
        """Score general del timing de mercado"""
        try:
            import datetime
            hour = datetime.datetime.now().hour
            
            # Horas óptimas de trading
            if 8 <= hour <= 18:
                return 0.8
            elif 6 <= hour <= 22:
                return 0.6
            else:
                return 0.4
                
        except Exception:
            return 0.5
    
    def get_ml_stats(self) -> Dict:
        """Obtiene estadísticas del modelo ML"""
        return {
            'symbols_tracked': len(self.price_history),
            'symbols_with_sufficient_data': len([s for s in self.price_history if len(self.price_history[s]) >= 5]),
            'routes_learned': len(self.arbitrage_success),
            'market_timing_score': self.market_timing_score()
        }

# Instancia global
ml_predictor = SimpleMLPredictor()
'''
    create_file_if_not_exists("ml/simple_predictor.py", content)

def setup_init_files():
    """Crea archivos __init__.py necesarios"""
    init_content = "# Auto-generated"
    
    create_file_if_not_exists("detection/__init__.py", init_content)
    create_file_if_not_exists("ml/__init__.py", init_content)

def main():
    """Configura todas las mejoras"""
    print("🚀 Configurando mejoras del bot de arbitraje...")
    
    # Crear archivos necesarios
    setup_init_files()
    setup_enhanced_detector()
    setup_ml_predictor()
    
    print("\n✅ Configuración completada!")
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. Ejecutar: python setup_improvements.py")
    print("2. Modificar main.py para usar run_with_enhancements()")
    print("3. Reiniciar el bot: python main.py")
    print("\n🎯 MEJORAS INCLUIDAS:")
    print("   ✅ Detector de oportunidades mejorado")
    print("   ✅ Predictor ML simple")
    print("   ✅ Threshold adaptativo")
    print("   ✅ Scanner optimizado")

if __name__ == "__main__":
    main()