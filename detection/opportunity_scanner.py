# binance_arbitrage_bot/detection/opportunity_scanner.py

import logging
import time
from typing import Dict, List, Tuple, Optional
from itertools import combinations, permutations
from dataclasses import dataclass
from config import settings
from core.utils import avg_price, fee_of
from strategies.triangular import simulate_route_gain, hourly_interest

@dataclass
class ArbitrageOpportunity:
    """Representa una oportunidad de arbitraje detectada"""
    route: List[str]
    amount: float
    expected_profit: float
    profit_percentage: float
    confidence_score: float
    execution_time_estimate: float
    slippage_estimate: float
    risk_score: float
    priority_score: float
    detected_at: float

class AdvancedOpportunityScanner:
    def __init__(self):
        self.min_profit_threshold = settings.PROFIT_THOLD
        self.max_route_length = 5  # Hasta 5 saltos
        self.min_confidence = 0.6  # 60% confianza mínima
        self.opportunity_cache = {}
        self.cache_ttl = 2  # 2 segundos de vida del cache
        self.scanning_patterns = {
            'triangular': True,
            'quadrilateral': True,
            'pentagonal': False,  # Muy complejo, desactivado por defecto
            'reverse_routes': True
        }
        
    def scan_opportunities(self, symbols: List[str], books: Dict, 
                          valid_symbols: set, coins: set) -> List[ArbitrageOpportunity]:
        """
        Escanea oportunidades de arbitraje avanzadas
        
        Returns:
            List[ArbitrageOpportunity]: Lista ordenada por prioridad
        """
        opportunities = []
        scan_start_time = time.time()
        
        try:
            # 1. Triangular tradicional (3 saltos)
            if self.scanning_patterns['triangular']:
                triangular_ops = self._scan_triangular(coins, books, valid_symbols)
                opportunities.extend(triangular_ops)
            
            # 2. Arbitraje cuadrilateral (4 saltos) 
            if self.scanning_patterns['quadrilateral']:
                quad_ops = self._scan_quadrilateral(coins, books, valid_symbols)
                opportunities.extend(quad_ops)
            
            # 3. Rutas inversas optimizadas
            if self.scanning_patterns['reverse_routes']:
                reverse_ops = self._scan_reverse_routes(opportunities, books, valid_symbols)
                opportunities.extend(reverse_ops)
            
            # 4. Filtrar y ordenar por prioridad
            filtered_ops = self._filter_and_rank_opportunities(opportunities)
            
            scan_time = time.time() - scan_start_time
            logging.debug(f"🔍 Scan completado: {len(filtered_ops)} oportunidades en {scan_time:.3f}s")
            
            return filtered_ops
            
        except Exception as e:
            logging.error(f"❌ Error en scanner avanzado: {e}")
            return []
    
    def _scan_triangular(self, coins: set, books: Dict, valid_symbols: set) -> List[ArbitrageOpportunity]:
        """Escanea oportunidades triangulares optimizadas"""
        opportunities = []
        
        # Optimización: usar solo monedas con alto volumen
        high_volume_coins = self._get_high_volume_coins(coins, books)
        
        for combo in combinations(high_volume_coins, 2):  # Solo 2 monedas intermedias
            route = [settings.BASE_ASSET] + list(combo) + [settings.BASE_ASSET]
            
            for amount in settings.QUANTUMS_USDT:
                opportunity = self._analyze_route_opportunity(route, amount, books, valid_symbols)
                if opportunity and opportunity.profit_percentage > self.min_profit_threshold:
                    opportunities.append(opportunity)
        
        return opportunities
    
    def _scan_quadrilateral(self, coins: set, books: Dict, valid_symbols: set) -> List[ArbitrageOpportunity]:
        """Escanea oportunidades cuadrilaterales (4 saltos)"""
        opportunities = []
        
        # Usar solo top coins para evitar explosión combinatoria
        top_coins = self._get_high_volume_coins(coins, books, limit=15)
        
        for combo in combinations(top_coins, 3):  # 3 monedas intermedias
            route = [settings.BASE_ASSET] + list(combo) + [settings.BASE_ASSET]
            
            # Solo probar con amounts más grandes para justificar la complejidad
            for amount in [amt for amt in settings.QUANTUMS_USDT if amt >= 50]:
                opportunity = self._analyze_route_opportunity(route, amount, books, valid_symbols)
                if opportunity and opportunity.profit_percentage > self.min_profit_threshold * 1.5:  # Mayor threshold
                    opportunities.append(opportunity)
        
        return opportunities
    
    def _scan_reverse_routes(self, existing_opportunities: List[ArbitrageOpportunity], 
                           books: Dict, valid_symbols: set) -> List[ArbitrageOpportunity]:
        """Escanea rutas inversas de oportunidades existentes"""
        reverse_opportunities = []
        
        for opp in existing_opportunities[:10]:  # Solo top 10 para optimizar
            # Crear ruta inversa
            reverse_route = list(reversed(opp.route))
            
            # Analizar la ruta inversa
            reverse_opp = self._analyze_route_opportunity(
                reverse_route, opp.amount, books, valid_symbols
            )
            
            if reverse_opp and reverse_opp.profit_percentage > self.min_profit_threshold:
                reverse_opp.priority_score *= 0.8  # Menor prioridad que la original
                reverse_opportunities.append(reverse_opp)
        
        return reverse_opportunities
    
    def _analyze_route_opportunity(self, route: List[str], amount: float, 
                                 books: Dict, valid_symbols: set) -> Optional[ArbitrageOpportunity]:
        """Analiza una ruta específica para detectar oportunidad"""
        try:
            # Cache key para evitar cálculos repetidos
            cache_key = f"{'-'.join(route)}_{amount}"
            current_time = time.time()
            
            if cache_key in self.opportunity_cache:
                cached_opp, timestamp = self.opportunity_cache[cache_key]
                if current_time - timestamp < self.cache_ttl:
                    return cached_opp
            
            # Simular ganancia básica
            final_qty = simulate_route_gain(route, amount, books, valid_symbols)
            if final_qty == 0:
                return None
            
            # Calcular métricas básicas
            factor = final_qty / amount
            hours = max(1, round(settings.HOLD_SECONDS / 3600))
            factor_eff = factor * (1 - hourly_interest(settings.BASE_ASSET) * hours)
            net_gain = factor_eff - 1
            expected_profit = amount * net_gain
            
            if net_gain <= self.min_profit_threshold:
                return None
            
            # Calcular métricas avanzadas
            confidence_score = self._calculate_confidence_score(route, books, valid_symbols)
            execution_time = self._estimate_execution_time(route, amount, books)
            slippage_estimate = self._estimate_total_slippage(route, amount, books, valid_symbols)
            risk_score = self._calculate_risk_score(route, amount, net_gain)
            priority_score = self._calculate_priority_score(
                net_gain, confidence_score, execution_time, risk_score
            )
            
            # Crear oportunidad
            opportunity = ArbitrageOpportunity(
                route=route,
                amount=amount,
                expected_profit=expected_profit,
                profit_percentage=net_gain,
                confidence_score=confidence_score,
                execution_time_estimate=execution_time,
                slippage_estimate=slippage_estimate,
                risk_score=risk_score,
                priority_score=priority_score,
                detected_at=current_time
            )
            
            # Cache resultado
            self.opportunity_cache[cache_key] = (opportunity, current_time)
            
            return opportunity
            
        except Exception as e:
            logging.error(f"❌ Error analizando ruta {route}: {e}")
            return None
    
    def _get_high_volume_coins(self, coins: set, books: Dict, limit: int = 20) -> List[str]:
        """Obtiene monedas con mayor volumen/liquidez"""
        coin_scores = {}
        
        for coin in coins:
            score = 0
            # Verificar pares principales con USDT
            usdt_pair = f"{coin}USDT"
            if usdt_pair in books:
                book = books[usdt_pair]
                if 'bids' in book and 'asks' in book and book['bids'] and book['asks']:
                    # Score basado en profundidad de orderbook
                    bid_depth = sum(float(level[1]) for level in book['bids'][:5])
                    ask_depth = sum(float(level[1]) for level in book['asks'][:5])
                    score += (bid_depth + ask_depth) / 2
            
            coin_scores[coin] = score
        
        # Ordenar por score y retornar top N
        sorted_coins = sorted(coin_scores.items(), key=lambda x: x[1], reverse=True)
        return [coin for coin, score in sorted_coins[:limit] if score > 0]
    
    def _calculate_confidence_score(self, route: List[str], books: Dict, valid_symbols: set) -> float:
        """Calcula score de confianza para una ruta"""
        try:
            confidence = 1.0
            
            # Verificar que todos los pares existan y tengan liquidez
            for i in range(len(route) - 1):
                a, b = route[i], route[i + 1]
                symbol = self._get_symbol_for_pair(a, b, valid_symbols)
                
                if not symbol:
                    confidence *= 0.3  # Penalización severa
                    continue
                
                if symbol not in books:
                    confidence *= 0.5  # Penalización por falta de datos
                    continue
                
                book = books[symbol]
                if not book.get('bids') or not book.get('asks'):
                    confidence *= 0.4
                    continue
                
                # Evaluar spread
                best_bid = float(book['bids'][0][0])
                best_ask = float(book['asks'][0][0])
                spread = (best_ask - best_bid) / best_bid
                
                if spread > 0.01:  # Spread > 1%
                    confidence *= 0.7
                elif spread > 0.005:  # Spread > 0.5%
                    confidence *= 0.85
                
                # Evaluar profundidad
                total_depth = len(book['bids']) + len(book['asks'])
                if total_depth < 10:
                    confidence *= 0.8
            
            return max(0.1, confidence)
            
        except Exception as e:
            logging.error(f"❌ Error calculando confianza: {e}")
            return 0.5
    
    def _estimate_execution_time(self, route: List[str], amount: float, books: Dict) -> float:
        """Estima tiempo total de ejecución de la ruta"""
        base_time_per_step = 0.5  # 500ms por paso
        total_time = len(route) - 1  # Número de pasos
        
        # Ajustar por complejidad de la ruta
        complexity_factor = 1 + (len(route) - 3) * 0.3  # Rutas más largas son más lentas
        
        # Ajustar por tamaño de posición
        size_factor = 1 + (amount / 1000) * 0.1  # Posiciones grandes son más lentas
        
        return base_time_per_step * total_time * complexity_factor * size_factor
    
    def _estimate_total_slippage(self, route: List[str], amount: float, 
                               books: Dict, valid_symbols: set) -> float:
        """Estima slippage total de la ruta"""
        total_slippage = 0.0
        current_amount = amount
        
        try:
            for i in range(len(route) - 1):
                a, b = route[i], route[i + 1]
                symbol = self._get_symbol_for_pair(a, b, valid_symbols)
                
                if not symbol or symbol not in books:
                    total_slippage += 0.01  # Penalización por falta de datos
                    continue
                
                book = books[symbol]
                side = 'BUY' if symbol.startswith(b) else 'SELL'
                levels = book['asks'] if side == 'BUY' else book['bids']
                
                if not levels:
                    total_slippage += 0.01
                    continue
                
                # Calcular slippage para este paso
                best_price = float(levels[0][0])
                avg_px = avg_price(levels, side, current_amount)
                step_slippage = abs(avg_px - best_price) / best_price
                total_slippage += step_slippage
                
                # Actualizar cantidad para siguiente paso
                if side == 'BUY':
                    current_amount = (current_amount / avg_px) * (1 - fee_of(symbol))
                else:
                    current_amount = (current_amount * avg_px) * (1 - fee_of(symbol))
            
            return total_slippage
            
        except Exception as e:
            logging.error(f"❌ Error estimando slippage: {e}")
            return 0.02  # 2% conservador
    
    def _calculate_risk_score(self, route: List[str], amount: float, profit_percentage: float) -> float:
        """Calcula score de riesgo (0=bajo riesgo, 1=alto riesgo)"""
        risk_score = 0.0
        
        # Riesgo por longitud de ruta
        route_risk = (len(route) - 3) * 0.15  # Cada salto adicional añade 15% de riesgo
        risk_score += route_risk
        
        # Riesgo por tamaño de posición
        if amount > 1000:
            size_risk = min(0.3, (amount - 1000) / 10000)  # Hasta 30% de riesgo adicional
            risk_score += size_risk
        
        # Riesgo inverso a la rentabilidad (menor ganancia = mayor riesgo relativo)
        if profit_percentage < 0.001:  # Menos de 0.1%
            risk_score += 0.4
        elif profit_percentage < 0.005:  # Menos de 0.5%
            risk_score += 0.2
        
        return min(1.0, risk_score)
    
    def _calculate_priority_score(self, profit_percentage: float, confidence: float, 
                                execution_time: float, risk_score: float) -> float:
        """Calcula score de prioridad para ordenar oportunidades"""
        # Peso de cada factor
        profit_weight = 0.4
        confidence_weight = 0.3
        speed_weight = 0.2
        risk_weight = 0.1
        
        # Normalizar tiempo de ejecución (menor tiempo = mayor score)
        time_score = max(0, 1 - (execution_time / 10))  # 10s = score 0
        
        # Calcular score compuesto
        priority_score = (
            profit_percentage * profit_weight * 1000 +  # Escalar profit
            confidence * confidence_weight +
            time_score * speed_weight +
            (1 - risk_score) * risk_weight
        )
        
        return priority_score
    
    def _get_symbol_for_pair(self, asset_from: str, asset_to: str, valid_symbols: set) -> Optional[str]:
        """Encuentra el símbolo válido para un par de assets"""
        candidates = [asset_from + asset_to, asset_to + asset_from]
        
        for symbol in candidates:
            if symbol in valid_symbols:
                return symbol
        
        return None
    
    def _filter_and_rank_opportunities(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        """Filtra y ordena oportunidades por prioridad"""
        # Filtrar por criterios mínimos
        filtered = [
            opp for opp in opportunities
            if opp.confidence_score >= self.min_confidence and
               opp.execution_time_estimate <= 10.0 and  # Máximo 10 segundos
               opp.slippage_estimate <= 0.02  # Máximo 2% slippage
        ]
        
        # Ordenar por priority_score descendente
        sorted_opportunities = sorted(filtered, key=lambda x: x.priority_score, reverse=True)
        
        # Limitar a top 20 para evitar spam
        return sorted_opportunities[:20]
    
    def get_scanner_stats(self) -> Dict:
        """Obtiene estadísticas del scanner"""
        current_time = time.time()
        valid_cache_entries = sum(
            1 for _, (_, timestamp) in self.opportunity_cache.items()
            if current_time - timestamp < self.cache_ttl
        )
        
        return {
            'cache_entries': len(self.opportunity_cache),
            'valid_cache_entries': valid_cache_entries,
            'cache_hit_rate': valid_cache_entries / max(len(self.opportunity_cache), 1),
            'scanning_patterns': self.scanning_patterns,
            'min_profit_threshold': self.min_profit_threshold,
            'min_confidence': self.min_confidence
        }
    
    def clear_cache(self):
        """Limpia el cache de oportunidades"""
        self.opportunity_cache.clear()
        logging.info("🗑️ Cache de oportunidades limpiado")

# Instancia global del scanner avanzado
opportunity_scanner = AdvancedOpportunityScanner()