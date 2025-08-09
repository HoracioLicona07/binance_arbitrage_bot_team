# binance_arbitrage_bot/ml/neural_optimizer.py

import logging
import math
import statistics
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class NeuralInput:
    """Input para red neuronal simple"""
    price_momentum: float      # -1 a 1
    volume_ratio: float        # 0 a 2
    spread_normalized: float   # 0 a 1
    volatility: float          # 0 a 1
    liquidity_score: float     # 0 a 1
    time_factor: float         # 0 a 1

class SimpleNeuralOptimizer:
    """Red neuronal simple para optimizar detección de arbitraje"""
    
    def __init__(self):
        # Pesos de la red (ajustables por aprendizaje)
        self.weights = {
            'hidden_layer_1': {
                'price_momentum': 0.3,
                'volume_ratio': 0.25,
                'spread_normalized': -0.4,  # Spread alto es malo
                'volatility': 0.2,
                'liquidity_score': 0.35,
                'time_factor': 0.1
            },
            'hidden_layer_2': {
                'price_momentum': 0.2,
                'volume_ratio': 0.3,
                'spread_normalized': -0.3,
                'volatility': 0.15,
                'liquidity_score': 0.4,
                'time_factor': 0.05
            },
            'output': {
                'hidden_1': 0.6,
                'hidden_2': 0.4
            }
        }
        
        # Historial para aprendizaje
        self.training_data = []
        self.learning_rate = 0.01
        self.bias = 0.1
        
    def sigmoid(self, x: float) -> float:
        """Función de activación sigmoid"""
        try:
            return 1 / (1 + math.exp(-max(-500, min(500, x))))
        except:
            return 0.5
    
    def prepare_inputs(self, symbol_data: Dict) -> NeuralInput:
        """Prepara inputs normalizados para la red"""
        try:
            # Extraer y normalizar datos
            prices = symbol_data.get('price_history', [])
            volumes = symbol_data.get('volume_history', [])
            current_spread = symbol_data.get('spread', 0.01)
            liquidity = symbol_data.get('liquidity', 1000)
            
            # 1. Price momentum (tendencia reciente)
            price_momentum = 0.0
            if len(prices) >= 3:
                recent_change = (prices[-1] - prices[-3]) / prices[-3]
                price_momentum = max(-1, min(1, recent_change * 100))
            
            # 2. Volume ratio (volumen actual vs promedio)
            volume_ratio = 1.0
            if len(volumes) >= 5:
                avg_volume = statistics.mean(volumes[:-1])
                current_volume = volumes[-1]
                if avg_volume > 0:
                    volume_ratio = min(2.0, current_volume / avg_volume)
            
            # 3. Spread normalizado
            spread_normalized = min(1.0, current_spread / 0.02)  # 2% como máximo
            
            # 4. Volatilidad
            volatility = 0.0
            if len(prices) >= 5:
                price_std = statistics.stdev(prices[-5:])
                price_mean = statistics.mean(prices[-5:])
                if price_mean > 0:
                    volatility = min(1.0, (price_std / price_mean) / 0.1)  # 10% como máximo
            
            # 5. Liquidity score
            liquidity_score = min(1.0, liquidity / 10000)  # 10k como excelente
            
            # 6. Time factor (hora del día)
            import datetime
            hour = datetime.datetime.now().hour
            time_factor = abs(hour - 12) / 12  # Mediodía como óptimo
            
            return NeuralInput(
                price_momentum=price_momentum,
                volume_ratio=volume_ratio,
                spread_normalized=spread_normalized,
                volatility=volatility,
                liquidity_score=liquidity_score,
                time_factor=time_factor
            )
            
        except Exception as e:
            logging.error(f"❌ Error preparando inputs: {e}")
            return NeuralInput(0.0, 1.0, 0.5, 0.5, 0.5, 0.5)
    
    def forward_pass(self, inputs: NeuralInput) -> float:
        """Pase hacia adelante de la red neuronal"""
        try:
            # Capa oculta 1
            hidden_1_sum = (
                inputs.price_momentum * self.weights['hidden_layer_1']['price_momentum'] +
                inputs.volume_ratio * self.weights['hidden_layer_1']['volume_ratio'] +
                inputs.spread_normalized * self.weights['hidden_layer_1']['spread_normalized'] +
                inputs.volatility * self.weights['hidden_layer_1']['volatility'] +
                inputs.liquidity_score * self.weights['hidden_layer_1']['liquidity_score'] +
                inputs.time_factor * self.weights['hidden_layer_1']['time_factor'] +
                self.bias
            )
            hidden_1_output = self.sigmoid(hidden_1_sum)
            
            # Capa oculta 2
            hidden_2_sum = (
                inputs.price_momentum * self.weights['hidden_layer_2']['price_momentum'] +
                inputs.volume_ratio * self.weights['hidden_layer_2']['volume_ratio'] +
                inputs.spread_normalized * self.weights['hidden_layer_2']['spread_normalized'] +
                inputs.volatility * self.weights['hidden_layer_2']['volatility'] +
                inputs.liquidity_score * self.weights['hidden_layer_2']['liquidity_score'] +
                inputs.time_factor * self.weights['hidden_layer_2']['time_factor'] +
                self.bias
            )
            hidden_2_output = self.sigmoid(hidden_2_sum)
            
            # Capa de salida
            output_sum = (
                hidden_1_output * self.weights['output']['hidden_1'] +
                hidden_2_output * self.weights['output']['hidden_2'] +
                self.bias
            )
            
            return self.sigmoid(output_sum)
            
        except Exception as e:
            logging.error(f"❌ Error en forward pass: {e}")
            return 0.5
    
    def predict_opportunity_score(self, symbol_data: Dict) -> float:
        """Predice score de oportunidad para un símbolo"""
        try:
            inputs = self.prepare_inputs(symbol_data)
            score = self.forward_pass(inputs)
            return score
            
        except Exception as e:
            logging.error(f"❌ Error prediciendo score: {e}")
            return 0.5
    
    def train_on_result(self, symbol_data: Dict, actual_profit: float):
        """Entrena la red con resultado real"""
        try:
            inputs = self.prepare_inputs(symbol_data)
            predicted_score = self.forward_pass(inputs)
            
            # Convertir profit real a target (0-1)
            if actual_profit > 0:
                target = min(1.0, actual_profit * 1000)  # Escalar profit
            else:
                target = 0.0
            
            # Calcular error
            error = target - predicted_score
            
            # Backpropagation simple (ajuste proporcional al error)
            adjustment = self.learning_rate * error
            
            # Ajustar pesos (simplificado)
            for layer in ['hidden_layer_1', 'hidden_layer_2']:
                for feature in self.weights[layer]:
                    feature_value = getattr(inputs, feature)
                    self.weights[layer][feature] += adjustment * feature_value * 0.1
            
            # Ajustar bias
            self.bias += adjustment * 0.05
            
            # Guardar para análisis
            self.training_data.append({
                'inputs': inputs,
                'predicted': predicted_score,
                'actual': target,
                'error': abs(error)
            })
            
            # Limitar historial
            if len(self.training_data) > 100:
                self.training_data = self.training_data[-50:]
                
        except Exception as e:
            logging.error(f"❌ Error en entrenamiento: {e}")
    
    def optimize_route_selection(self, available_routes: List[Dict]) -> List[Dict]:
        """Optimiza selección de rutas usando la red neuronal"""
        try:
            # Predecir score para cada ruta
            for route_data in available_routes:
                # Simular datos del símbolo (en producción usar datos reales)
                symbol_data = self._extract_symbol_data_from_route(route_data)
                neural_score = self.predict_opportunity_score(symbol_data)
                
                # Combinar con score existente
                original_score = route_data.get('profit_pct', 0)
                combined_score = original_score * 0.7 + neural_score * 0.3
                
                route_data['neural_score'] = neural_score
                route_data['optimized_score'] = combined_score
            
            # Ordenar por score optimizado
            available_routes.sort(key=lambda x: x.get('optimized_score', 0), reverse=True)
            
            return available_routes
            
        except Exception as e:
            logging.error(f"❌ Error optimizando rutas: {e}")
            return available_routes
    
    def _extract_symbol_data_from_route(self, route_data: Dict) -> Dict:
        """Extrae datos del símbolo desde datos de ruta (simulado)"""
        try:
            # En producción, esto obtendría datos reales del mercado
            return {
                'price_history': [100, 101, 99, 102, 98],  # Datos simulados
                'volume_history': [1000, 1100, 900, 1200, 800],
                'spread': 0.005,  # 0.5%
                'liquidity': route_data.get('amount', 100) * 50  # Estimación
            }
        except:
            return {}
    
    def get_neural_stats(self) -> Dict:
        """Obtiene estadísticas de la red neuronal"""
        try:
            if not self.training_data:
                return {'status': 'No training data'}
            
            recent_errors = [data['error'] for data in self.training_data[-20:]]
            avg_error = statistics.mean(recent_errors) if recent_errors else 0
            
            # Calcular precisión (predicciones dentro de 20% del target)
            accurate_predictions = sum(
                1 for data in self.training_data[-20:]
                if data['error'] < 0.2
            )
            accuracy = accurate_predictions / min(len(self.training_data), 20)
            
            return {
                'training_samples': len(self.training_data),
                'avg_error': avg_error,
                'accuracy': accuracy,
                'bias': self.bias,
                'learning_rate': self.learning_rate,
                'status': 'Active' if accuracy > 0.6 else 'Learning'
            }
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo stats neurales: {e}")
            return {'status': 'Error'}
    
    def adjust_sensitivity(self, market_volatility: float):
        """Ajusta sensibilidad de la red basado en volatilidad del mercado"""
        try:
            if market_volatility > 0.7:  # Alta volatilidad
                self.learning_rate = 0.005  # Aprender más lento
                # Aumentar peso de liquidez
                for layer in ['hidden_layer_1', 'hidden_layer_2']:
                    self.weights[layer]['liquidity_score'] *= 1.1
                    self.weights[layer]['spread_normalized'] *= 1.2
                    
            elif market_volatility < 0.3:  # Baja volatilidad
                self.learning_rate = 0.02  # Aprender más rápido
                # Aumentar peso de momentum
                for layer in ['hidden_layer_1', 'hidden_layer_2']:
                    self.weights[layer]['price_momentum'] *= 1.1
                    
        except Exception as e:
            logging.error(f"❌ Error ajustando sensibilidad: {e}")

# Instancia global del optimizador neural
neural_optimizer = SimpleNeuralOptimizer()