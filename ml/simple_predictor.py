# ml/simple_predictor.py
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
