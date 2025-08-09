# detection/enhanced_scanner.py
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
