# binance_arbitrage_bot/risk_management/risk_calculator.py

import logging
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from config import settings
from binance_api.fee_manager import fee_manager
from detection.liquidity_analyzer import liquidity_analyzer

@dataclass
class RiskMetrics:
    """Métricas de riesgo para una operación de arbitraje"""
    max_loss_usdt: float
    max_loss_percentage: float
    probability_of_loss: float
    expected_return: float
    risk_reward_ratio: float
    confidence_score: float
    risk_factors: List[str]
    recommended_position_size: float

class RiskCalculator:
    def __init__(self):
        # Parámetros de riesgo configurables
        self.max_position_risk = 0.02  # 2% del capital por operación
        self.max_daily_risk = 0.10     # 10% del capital por día
        self.max_drawdown = 0.15       # 15% drawdown máximo
        self.min_risk_reward = 2.0     # Ratio riesgo/recompensa mínimo
        
        # Factores de riesgo por mercado
        self.market_risk_factors = {
            'high_volatility': 1.5,
            'low_liquidity': 2.0,
            'news_event': 1.3,
            'weekend': 1.2,
            'high_correlation': 1.4
        }
        
        # Tracking de posiciones y riesgo acumulado
        self.daily_risk_used = 0.0
        self.open_positions = []
        self.current_drawdown = 0.0
        
    def calculate_risk_metrics(self, route: List[str], amount: float, 
                              expected_profit: float, books: Dict) -> RiskMetrics:
        """
        Calcula métricas completas de riesgo para una operación de arbitraje
        
        Args:
            route: Ruta de arbitraje ['USDT', 'BTC', 'ETH', 'USDT']
            amount: Cantidad a invertir en USDT
            expected_profit: Beneficio esperado en USDT
            books: Libros de órdenes actuales
            
        Returns:
            RiskMetrics: Métricas completas de riesgo
        """
        try:
            # 1. Análisis de liquidez
            liquidity_analysis = liquidity_analyzer.analyze_route_liquidity(route, amount, books)
            
            # 2. Cálculo de pérdida máxima
            max_loss = self._calculate_max_loss(route, amount, liquidity_analysis)
            
            # 3. Probabilidad de pérdida
            loss_probability = self._calculate_loss_probability(route, liquidity_analysis)
            
            # 4. Retorno esperado ajustado por riesgo
            risk_adjusted_return = self._calculate_risk_adjusted_return(
                expected_profit, max_loss, loss_probability
            )
            
            # 5. Ratio riesgo/recompensa
            risk_reward = expected_profit / max_loss if max_loss > 0 else 0
            
            # 6. Score de confianza
            confidence = self._calculate_confidence_score(route, liquidity_analysis)
            
            # 7. Factores de riesgo
            risk_factors = self._identify_risk_factors(route, amount, liquidity_analysis)
            
            # 8. Tamaño de posición recomendado
            recommended_size = self._calculate_optimal_position_size(
                amount, max_loss, expected_profit, confidence
            )
            
            return RiskMetrics(
                max_loss_usdt=max_loss,
                max_loss_percentage=max_loss / amount * 100,
                probability_of_loss=loss_probability,
                expected_return=risk_adjusted_return,
                risk_reward_ratio=risk_reward,
                confidence_score=confidence,
                risk_factors=risk_factors,
                recommended_position_size=recommended_size
            )
            
        except Exception as e:
            logging.error(f"❌ Error calculando métricas de riesgo: {e}")
            return self._get_conservative_risk_metrics(amount)
    
    def _calculate_max_loss(self, route: List[str], amount: float, 
                           liquidity_analysis: Dict) -> float:
        """Calcula la pérdida máxima posible"""
        try:
            # Pérdida base por slippage
            slippage_loss = amount * liquidity_analysis.get('total_slippage', 0.01)
            
            # Pérdida por comisiones
            fee_loss = amount * fee_manager.get_arbitrage_total_fee(route, amount)
            
            # Pérdida por movimientos adversos de precio (basado en volatilidad)
            volatility_loss = self._estimate_volatility_loss(route, amount)
            
            # Pérdida por fallos de ejecución
            execution_risk_loss = amount * 0.001  # 0.1% por riesgo de ejecución
            
            # Pérdida máxima total (no todos los factores ocurren simultáneamente)
            max_loss = slippage_loss + fee_loss + (volatility_loss * 0.5) + execution_risk_loss
            
            # Aplicar factor de seguridad
            safety_factor = 1.2
            return min(max_loss * safety_factor, amount * 0.05)  # Máximo 5% del capital
            
        except Exception as e:
            logging.error(f"❌ Error calculando pérdida máxima: {e}")
            return amount * 0.03  # 3% conservador
    
    def _estimate_volatility_loss(self, route: List[str], amount: float) -> float:
        """Estima pérdida por volatilidad de precios"""
        try:
            from binance_api.websocket_manager import websocket_manager
            
            total_volatility_risk = 0.0
            
            for i in range(len(route) - 1):
                asset_from, asset_to = route[i], route[i + 1]
                symbol = self._get_symbol_for_assets(asset_from, asset_to)
                
                if symbol:
                    price_data = websocket_manager.get_price_data(symbol)
                    if price_data:
                        # Usar cambio de precio reciente como proxy de volatilidad
                        volatility = abs(price_data.get('change', 0)) / 100
                        volatility_risk = amount * volatility * 0.1  # Factor de impacto
                        total_volatility_risk += volatility_risk
            
            return total_volatility_risk
            
        except Exception as e:
            logging.error(f"❌ Error estimando riesgo de volatilidad: {e}")
            return amount * 0.005  # 0.5% por defecto
    
    def _calculate_loss_probability(self, route: List[str], 
                                   liquidity_analysis: Dict) -> float:
        """Calcula la probabilidad de pérdida"""
        try:
            base_probability = 0.1  # 10% base
            
            # Ajustes basados en liquidez
            if not liquidity_analysis.get('is_viable', True):
                base_probability += 0.3
            
            if liquidity_analysis.get('total_slippage', 0) > 0.005:
                base_probability += 0.2
            
            # Ajustes basados en condiciones de mercado
            market_conditions = self._assess_market_conditions()
            if market_conditions.get('high_volatility', False):
                base_probability += 0.15
            
            if market_conditions.get('low_volume', False):
                base_probability += 0.1
            
            # Ajustes basados en tiempo de ejecución
            execution_time = liquidity_analysis.get('estimated_execution_time', 0)
            if execution_time > 5:  # Más de 5 segundos
                base_probability += min(0.2, execution_time / 25)
            
            return min(base_probability, 0.8)  # Máximo 80%
            
        except Exception as e:
            logging.error(f"❌ Error calculando probabilidad de pérdida: {e}")
            return 0.3  # 30% conservador
    
    def _calculate_risk_adjusted_return(self, expected_profit: float, 
                                       max_loss: float, loss_probability: float) -> float:
        """Calcula retorno esperado ajustado por riesgo"""
        success_probability = 1 - loss_probability
        expected_return = (expected_profit * success_probability) - (max_loss * loss_probability)
        return expected_return
    
    def _calculate_confidence_score(self, route: List[str], 
                                   liquidity_analysis: Dict) -> float:
        """Calcula score de confianza (0-1)"""
        try:
            score = 1.0
            
            # Penalizar por problemas de liquidez
            if not liquidity_analysis.get('is_viable', True):
                score -= 0.4
            
            # Penalizar por alto slippage
            slippage = liquidity_analysis.get('total_slippage', 0)
            if slippage > 0.002:
                score -= min(0.3, slippage * 100)
            
            # Penalizar por baja liquidez
            avg_liquidity = sum(liquidity_analysis.get('liquidity_scores', [0])) / max(len(liquidity_analysis.get('liquidity_scores', [1])), 1)
            if avg_liquidity < 0.5:
                score -= 0.2
            
            # Penalizar por tiempo de ejecución largo
            execution_time = liquidity_analysis.get('estimated_execution_time', 0)
            if execution_time > 3:
                score -= min(0.2, execution_time / 20)
            
            # Bonificar por buen historial (si está disponible)
            # TODO: Implementar análisis histórico de la ruta
            
            return max(0.1, score)  # Mínimo 10%
            
        except Exception as e:
            logging.error(f"❌ Error calculando score de confianza: {e}")
            return 0.5  # 50% por defecto
    
    def _identify_risk_factors(self, route: List[str], amount: float, 
                              liquidity_analysis: Dict) -> List[str]:
        """Identifica factores de riesgo específicos"""
        risk_factors = []
        
        # Factores de liquidez
        if not liquidity_analysis.get('is_viable', True):
            risk_factors.append("Liquidez insuficiente en la ruta")
        
        if liquidity_analysis.get('total_slippage', 0) > 0.005:
            risk_factors.append(f"Alto slippage: {liquidity_analysis['total_slippage']:.3f}")
        
        # Factores de mercado
        market_conditions = self._assess_market_conditions()
        if market_conditions.get('high_volatility', False):
            risk_factors.append("Alta volatilidad de mercado")
        
        if market_conditions.get('low_volume', False):
            risk_factors.append("Bajo volumen de trading")
        
        # Factores de timing
        execution_time = liquidity_analysis.get('estimated_execution_time', 0)
        if execution_time > 5:
            risk_factors.append(f"Tiempo de ejecución largo: {execution_time:.1f}s")
        
        # Factores de posición
        if amount > self._get_available_capital() * 0.1:
            risk_factors.append("Posición grande relativa al capital")
        
        # Factores de riesgo acumulado
        if self.daily_risk_used > self.max_daily_risk * 0.8:
            risk_factors.append("Riesgo diario cerca del límite")
        
        return risk_factors
    
    def _calculate_optimal_position_size(self, requested_amount: float, 
                                        max_loss: float, expected_profit: float, 
                                        confidence: float) -> float:
        """Calcula el tamaño óptimo de posición usando Kelly Criterion adaptado"""
        try:
            available_capital = self._get_available_capital()
            
            # Kelly Criterion adaptado para arbitraje
            if max_loss > 0:
                win_probability = confidence
                loss_probability = 1 - confidence
                
                if loss_probability > 0:
                    kelly_fraction = (win_probability * expected_profit - loss_probability * max_loss) / max_loss
                    kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Limitar a 25%
                else:
                    kelly_fraction = 0.1
            else:
                kelly_fraction = 0.1
            
            # Aplicar limitaciones de riesgo
            max_by_position_risk = available_capital * self.max_position_risk
            max_by_daily_risk = available_capital * (self.max_daily_risk - self.daily_risk_used)
            kelly_size = available_capital * kelly_fraction
            
            # Tomar el menor de todos los límites
            optimal_size = min(
                requested_amount,
                max_by_position_risk,
                max_by_daily_risk,
                kelly_size
            )
            
            return max(0, optimal_size)
            
        except Exception as e:
            logging.error(f"❌ Error calculando tamaño óptimo: {e}")
            return min(requested_amount * 0.5, self._get_available_capital() * 0.01)
    
    def _assess_market_conditions(self) -> Dict[str, bool]:
        """Evalúa las condiciones actuales del mercado"""
        try:
            from binance_api.websocket_manager import websocket_manager
            
            conditions = {
                'high_volatility': False,
                'low_volume': False,
                'trending_market': False,
                'weekend': False
            }
            
            # Evaluar volatilidad usando BTC como proxy
            btc_data = websocket_manager.get_price_data('BTCUSDT')
            if btc_data:
                price_change = abs(btc_data.get('change', 0))
                if price_change > 5:  # Más de 5% de cambio
                    conditions['high_volatility'] = True
                
                volume = btc_data.get('volume', 0)
                # Comparar con volumen promedio (simplificado)
                if volume < 10000:  # Umbral simplificado
                    conditions['low_volume'] = True
            
            # Verificar si es fin de semana
            import datetime
            now = datetime.datetime.now()
            if now.weekday() >= 5:  # Sábado o Domingo
                conditions['weekend'] = True
            
            return conditions
            
        except Exception as e:
            logging.error(f"❌ Error evaluando condiciones de mercado: {e}")
            return {'high_volatility': False, 'low_volume': False, 'trending_market': False, 'weekend': False}
    
    def _get_available_capital(self) -> float:
        """Obtiene el capital disponible para trading"""
        try:
            from binance_api.client import client
            account = client.get_account()
            
            # Buscar balance de USDT
            for balance in account['balances']:
                if balance['asset'] == 'USDT':
                    return float(balance['free'])
            
            return 1000.0  # Fallback por defecto
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo capital disponible: {e}")
            return 1000.0  # Fallback conservador
    
    def _get_symbol_for_assets(self, asset_from: str, asset_to: str) -> Optional[str]:
        """Obtiene el símbolo para un par de assets"""
        # Intentar ambas combinaciones
        symbols = [asset_from + asset_to, asset_to + asset_from]
        
        for symbol in symbols:
            try:
                from binance_api.client import client
                if client.get_symbol_info(symbol):
                    return symbol
            except:
                continue
        
        return None
    
    def _get_conservative_risk_metrics(self, amount: float) -> RiskMetrics:
        """Retorna métricas conservadoras en caso de error"""
        return RiskMetrics(
            max_loss_usdt=amount * 0.05,
            max_loss_percentage=5.0,
            probability_of_loss=0.4,
            expected_return=amount * 0.001,
            risk_reward_ratio=0.2,
            confidence_score=0.3,
            risk_factors=["Error en cálculo de riesgo"],
            recommended_position_size=amount * 0.5
        )
    
    def should_execute_trade(self, risk_metrics: RiskMetrics) -> Tuple[bool, str]:
        """
        Determina si se debe ejecutar un trade basado en las métricas de riesgo
        
        Returns:
            Tuple[bool, str]: (should_execute, reason)
        """
        try:
            # Verificar ratio riesgo/recompensa
            if risk_metrics.risk_reward_ratio < self.min_risk_reward:
                return False, f"Ratio R/R bajo: {risk_metrics.risk_reward_ratio:.2f} < {self.min_risk_reward}"
            
            # Verificar confianza mínima
            if risk_metrics.confidence_score < 0.4:
                return False, f"Confianza baja: {risk_metrics.confidence_score:.2f}"
            
            # Verificar retorno esperado positivo
            if risk_metrics.expected_return <= 0:
                return False, f"Retorno esperado negativo: {risk_metrics.expected_return:.4f}"
            
            # Verificar límites de riesgo
            if risk_metrics.max_loss_percentage > 3:  # Máximo 3% de pérdida
                return False, f"Riesgo muy alto: {risk_metrics.max_loss_percentage:.2f}%"
            
            # Verificar riesgo diario acumulado
            if self.daily_risk_used >= self.max_daily_risk:
                return False, "Límite de riesgo diario alcanzado"
            
            # Verificar factores de riesgo críticos
            critical_factors = [
                "Liquidez insuficiente",
                "Error en cálculo",
                "Riesgo diario cerca del límite"
            ]
            
            for factor in risk_metrics.risk_factors:
                if any(critical in factor for critical in critical_factors):
                    return False, f"Factor de riesgo crítico: {factor}"
            
            return True, "Trade aprobado por análisis de riesgo"
            
        except Exception as e:
            logging.error(f"❌ Error evaluando si ejecutar trade: {e}")
            return False, "Error en evaluación de riesgo"
    
    def update_daily_risk(self, amount_used: float):
        """Actualiza el riesgo diario usado"""
        capital = self._get_available_capital()
        if capital > 0:
            self.daily_risk_used += amount_used / capital
    
    def reset_daily_risk(self):
        """Resetea el contador de riesgo diario"""
        self.daily_risk_used = 0.0
        logging.info("🔄 Riesgo diario reseteado")
    
    def get_risk_summary(self) -> Dict:
        """Obtiene resumen del estado de riesgo actual"""
        available_capital = self._get_available_capital()
        
        return {
            'available_capital': available_capital,
            'daily_risk_used_pct': self.daily_risk_used * 100,
            'daily_risk_remaining_pct': (self.max_daily_risk - self.daily_risk_used) * 100,
            'max_position_size': available_capital * self.max_position_risk,
            'open_positions': len(self.open_positions),
            'current_drawdown_pct': self.current_drawdown * 100,
            'risk_limits': {
                'max_position_risk_pct': self.max_position_risk * 100,
                'max_daily_risk_pct': self.max_daily_risk * 100,
                'max_drawdown_pct': self.max_drawdown * 100,
                'min_risk_reward': self.min_risk_reward
            }
        }

# Instancia global del calculador de riesgo
risk_calculator = RiskCalculator()