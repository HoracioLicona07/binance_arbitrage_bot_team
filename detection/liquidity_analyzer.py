# binance_arbitrage_bot/detection/liquidity_analyzer.py

import logging
import math
from typing import Dict, List, Tuple, Optional
from core.utils import avg_price, fee_of
from config import settings
from binance_api.websocket_manager import websocket_manager

class LiquidityAnalyzer:
    def __init__(self):
        self.min_liquidity_threshold = 1000  # USDT mínimo de liquidez
        self.max_slippage_tolerance = 0.005  # 0.5% slippage máximo
        self.min_orderbook_depth = 5  # Mínimo 5 niveles de precio
        
    def analyze_route_liquidity(self, route: List[str], amount: float, books: Dict) -> Dict:
        """
        Analiza la liquidez completa de una ruta de arbitraje
        
        Returns:
        {
            'is_viable': bool,
            'total_slippage': float,
            'bottleneck_step': int,
            'liquidity_scores': List[float],
            'estimated_execution_time': float,
            'risk_factors': List[str]
        }
        """
        analysis = {
            'is_viable': False,
            'total_slippage': 0.0,
            'bottleneck_step': -1,
            'liquidity_scores': [],
            'estimated_execution_time': 0.0,
            'risk_factors': []
        }
        
        try:
            qty = amount
            total_slippage = 0.0
            step_slippages = []
            min_liquidity_score = float('inf')
            bottleneck_step = -1
            
            for i in range(len(route) - 1):
                a, b = route[i], route[i + 1]
                
                # Determinar símbolo y dirección
                symbol, side = self._get_symbol_and_side(a, b)
                if not symbol:
                    analysis['risk_factors'].append(f"Símbolo no encontrado para {a}->{b}")
                    return analysis
                
                # Obtener orderbook (preferir WebSocket)
                orderbook = self._get_fresh_orderbook(symbol, books)
                if not orderbook:
                    analysis['risk_factors'].append(f"Orderbook no disponible para {symbol}")
                    return analysis
                
                # Analizar liquidez del paso
                step_analysis = self._analyze_step_liquidity(symbol, side, qty, orderbook)
                
                if not step_analysis['viable']:
                    analysis['risk_factors'].extend(step_analysis['risk_factors'])
                    analysis['bottleneck_step'] = i
                    return analysis
                
                # Acumular métricas
                step_slippage = step_analysis['slippage']
                step_slippages.append(step_slippage)
                total_slippage += step_slippage
                
                liquidity_score = step_analysis['liquidity_score']
                analysis['liquidity_scores'].append(liquidity_score)
                
                if liquidity_score < min_liquidity_score:
                    min_liquidity_score = liquidity_score
                    bottleneck_step = i
                
                # Calcular cantidad para siguiente paso
                price = step_analysis['avg_price']
                fee = fee_of(symbol)
                
                if side == 'BUY':
                    qty = (qty / price) * (1 - fee)
                else:
                    qty = (qty * price) * (1 - fee)
                
                # Tiempo estimado de ejecución
                analysis['estimated_execution_time'] += step_analysis['execution_time']
            
            # Evaluación final
            analysis['total_slippage'] = total_slippage
            analysis['bottleneck_step'] = bottleneck_step
            
            # Criterios de viabilidad
            viable_conditions = [
                total_slippage <= self.max_slippage_tolerance,
                min_liquidity_score >= 0.3,  # Score mínimo de liquidez
                len(analysis['risk_factors']) == 0,
                analysis['estimated_execution_time'] <= 10.0  # Max 10 segundos
            ]
            
            analysis['is_viable'] = all(viable_conditions)
            
            if not analysis['is_viable']:
                if total_slippage > self.max_slippage_tolerance:
                    analysis['risk_factors'].append(f"Slippage alto: {total_slippage:.4f}")
                if min_liquidity_score < 0.3:
                    analysis['risk_factors'].append(f"Liquidez insuficiente: {min_liquidity_score:.2f}")
                if analysis['estimated_execution_time'] > 10.0:
                    analysis['risk_factors'].append(f"Ejecución lenta: {analysis['estimated_execution_time']:.1f}s")
            
        except Exception as e:
            logging.error(f"❌ Error analizando liquidez: {e}")
            analysis['risk_factors'].append(f"Error de análisis: {str(e)}")
        
        return analysis
    
    def _analyze_step_liquidity(self, symbol: str, side: str, qty: float, orderbook: Dict) -> Dict:
        """Analiza la liquidez de un paso individual"""
        levels = orderbook['asks'] if side == 'BUY' else orderbook['bids']
        
        if not levels or len(levels) < self.min_orderbook_depth:
            return {
                'viable': False,
                'risk_factors': ['Profundidad de orderbook insuficiente'],
                'slippage': float('inf'),
                'liquidity_score': 0.0,
                'avg_price': 0.0,
                'execution_time': 0.0
            }
        
        # Calcular precio promedio y slippage
        avg_px = avg_price(levels, side, qty)
        best_price = float(levels[0][0])
        slippage = abs(avg_px - best_price) / best_price
        
        # Calcular liquidez total disponible
        total_liquidity = sum(float(level[1]) for level in levels[:10])  # Top 10 levels
        
        # Calcular liquidez en USDT
        if side == 'BUY':
            liquidity_usdt = total_liquidity  # Ya está en quote asset (generalmente USDT)
        else:
            liquidity_usdt = total_liquidity * best_price
        
        # Score de liquidez (0-1)
        liquidity_score = min(1.0, liquidity_usdt / (qty * 5))  # Ideal: 5x la cantidad requerida
        
        # Tiempo estimado de ejecución (basado en liquidez y volatilidad)
        execution_time = self._estimate_execution_time(symbol, qty, liquidity_usdt)
        
        # Factores de riesgo
        risk_factors = []
        if slippage > self.max_slippage_tolerance:
            risk_factors.append(f'Slippage alto en {symbol}: {slippage:.4f}')
        if liquidity_usdt < self.min_liquidity_threshold:
            risk_factors.append(f'Liquidez baja en {symbol}: {liquidity_usdt:.0f} USDT')
        if len(levels) < 3:
            risk_factors.append(f'Orderbook delgado en {symbol}')
        
        return {
            'viable': len(risk_factors) == 0 and slippage <= self.max_slippage_tolerance,
            'risk_factors': risk_factors,
            'slippage': slippage,
            'liquidity_score': liquidity_score,
            'avg_price': avg_px,
            'execution_time': execution_time,
            'liquidity_usdt': liquidity_usdt
        }
    
    def _get_symbol_and_side(self, asset_from: str, asset_to: str) -> Tuple[Optional[str], Optional[str]]:
        """Determina el símbolo correcto y el lado de la operación"""
        # Intenta las dos combinaciones posibles
        fwd_symbol = asset_from + asset_to
        rev_symbol = asset_to + asset_from
        
        # Verifica cuál existe usando el cliente
        from binance_api.client import client
        try:
            if client.get_symbol_info(fwd_symbol):
                return fwd_symbol, 'SELL'
        except:
            pass
        
        try:
            if client.get_symbol_info(rev_symbol):
                return rev_symbol, 'BUY'
        except:
            pass
        
        return None, None
    
    def _get_fresh_orderbook(self, symbol: str, books: Dict) -> Optional[Dict]:
        """Obtiene orderbook fresco, preferiendo WebSocket"""
        # Intentar obtener de WebSocket primero
        if websocket_manager.is_data_fresh(symbol):
            ws_orderbook = websocket_manager.get_orderbook(symbol)
            if ws_orderbook:
                return ws_orderbook
        
        # Fallback a orderbook en cache o API
        if symbol in books:
            return books[symbol]
        
        # Último recurso: obtener de API
        try:
            from binance_api.client import client
            orderbook = client.get_order_book(symbol=symbol, limit=settings.BOOK_LIMIT)
            books[symbol] = orderbook  # Cache para uso futuro
            return orderbook
        except Exception as e:
            logging.error(f"❌ Error obteniendo orderbook para {symbol}: {e}")
            return None
    
    def _estimate_execution_time(self, symbol: str, qty: float, liquidity_usdt: float) -> float:
        """Estima el tiempo de ejecución basado en liquidez y condiciones de mercado"""
        # Tiempo base por operación
        base_time = 0.5  # 500ms por operación base
        
        # Ajuste por liquidez (más liquidez = más rápido)
        if liquidity_usdt > qty * 10:
            liquidity_factor = 1.0
        elif liquidity_usdt > qty * 5:
            liquidity_factor = 1.2
        elif liquidity_usdt > qty * 2:
            liquidity_factor = 1.5
        else:
            liquidity_factor = 2.0
        
        # Ajuste por volatilidad (obtener de price data si está disponible)
        volatility_factor = 1.0
        price_data = websocket_manager.get_price_data(symbol)
        if price_data and abs(price_data.get('change', 0)) > 5:  # >5% de cambio
            volatility_factor = 1.3
        
        return base_time * liquidity_factor * volatility_factor
    
    def get_liquidity_summary(self, symbols: List[str]) -> Dict:
        """Obtiene resumen de liquidez para múltiples símbolos"""
        summary = {
            'high_liquidity': [],
            'medium_liquidity': [],
            'low_liquidity': [],
            'total_symbols': len(symbols),
            'avg_liquidity_score': 0.0
        }
        
        total_score = 0.0
        for symbol in symbols:
            orderbook = websocket_manager.get_orderbook(symbol)
            if orderbook:
                score = self._calculate_liquidity_score(symbol, orderbook)
                total_score += score
                
                if score >= 0.7:
                    summary['high_liquidity'].append(symbol)
                elif score >= 0.4:
                    summary['medium_liquidity'].append(symbol)
                else:
                    summary['low_liquidity'].append(symbol)
        
        if len(symbols) > 0:
            summary['avg_liquidity_score'] = total_score / len(symbols)
        
        return summary
    
    def _calculate_liquidity_score(self, symbol: str, orderbook: Dict) -> float:
        """Calcula score de liquidez para un símbolo individual"""
        try:
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])
            
            if not bids or not asks:
                return 0.0
            
            # Calcular spread
            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            spread = (best_ask - best_bid) / best_bid
            
            # Calcular profundidad (top 5 levels)
            bid_depth = sum(float(level[1]) for level in bids[:5])
            ask_depth = sum(float(level[1]) for level in asks[:5])
            total_depth = (bid_depth + ask_depth) / 2
            
            # Score basado en spread y profundidad
            spread_score = max(0, 1 - (spread / 0.001))  # Penalizar spread >0.1%
            depth_score = min(1, total_depth / 1000)      # Normalizar profundidad
            
            return (spread_score * 0.6 + depth_score * 0.4)
            
        except Exception as e:
            logging.error(f"❌ Error calculando score de liquidez para {symbol}: {e}")
            return 0.0

# Instancia global
liquidity_analyzer = LiquidityAnalyzer()