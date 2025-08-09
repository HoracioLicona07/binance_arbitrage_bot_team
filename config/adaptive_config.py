# binance_arbitrage_bot/config/adaptive_config.py

import logging
import time
import json
from typing import Dict, List
from dataclasses import dataclass, asdict
from config import settings

@dataclass
class AdaptiveSettings:
    """Configuración adaptativa del bot"""
    profit_threshold: float = 0.008
    max_position_size: float = 20.0
    sleep_between_cycles: float = 3.0
    top_coins_limit: int = 8
    opportunity_quality_threshold: float = 0.6
    
    # Factores de ajuste
    low_opportunity_factor: float = 0.95
    high_opportunity_factor: float = 1.05
    volatility_sensitivity: float = 0.5
    
    # Límites
    min_profit_threshold: float = 0.003
    max_profit_threshold: float = 0.015
    min_sleep: float = 1.0
    max_sleep: float = 10.0

class AdaptiveConfigManager:
    """Gestor de configuración adaptativa"""
    
    def __init__(self):
        self.settings = AdaptiveSettings()
        self.performance_history = []
        self.market_conditions_history = []
        self.last_adjustment = time.time()
        self.adjustment_interval = 300  # 5 minutos
        
    def update_performance(self, opportunities_found: int, trades_executed: int, 
                          total_profit: float, market_volatility: float):
        """Actualiza métricas de rendimiento"""
        try:
            performance_data = {
                'timestamp': time.time(),
                'opportunities_found': opportunities_found,
                'trades_executed': trades_executed,
                'total_profit': total_profit,
                'market_volatility': market_volatility,
                'profit_threshold': self.settings.profit_threshold,
                'success_rate': trades_executed / max(opportunities_found, 1)
            }
            
            self.performance_history.append(performance_data)
            
            # Mantener solo últimas 100 mediciones
            if len(self.performance_history) > 100:
                self.performance_history = self.performance_history[-50:]
            
            # Verificar si es tiempo de ajustar
            if time.time() - self.last_adjustment > self.adjustment_interval:
                self.auto_adjust_settings()
                
        except Exception as e:
            logging.error(f"❌ Error actualizando performance: {e}")
    
    def auto_adjust_settings(self):
        """Ajusta configuración automáticamente"""
        try:
            if len(self.performance_history) < 5:
                return
            
            # Analizar últimas 10 mediciones
            recent_data = self.performance_history[-10:]
            
            # Calcular métricas
            avg_opportunities = sum(d['opportunities_found'] for d in recent_data) / len(recent_data)
            avg_success_rate = sum(d['success_rate'] for d in recent_data) / len(recent_data)
            avg_profit = sum(d['total_profit'] for d in recent_data) / len(recent_data)
            avg_volatility = sum(d['market_volatility'] for d in recent_data) / len(recent_data)
            
            adjustments_made = []
            
            # 1. Ajustar profit threshold
            old_threshold = self.settings.profit_threshold
            
            if avg_opportunities < 0.5:  # Muy pocas oportunidades
                self.settings.profit_threshold *= self.settings.low_opportunity_factor
                self.settings.profit_threshold = max(
                    self.settings.min_profit_threshold, 
                    self.settings.profit_threshold
                )
                adjustments_made.append(f"Threshold reducido: {old_threshold:.4f} → {self.settings.profit_threshold:.4f}")
                
            elif avg_opportunities > 3:  # Muchas oportunidades
                self.settings.profit_threshold *= self.settings.high_opportunity_factor
                self.settings.profit_threshold = min(
                    self.settings.max_profit_threshold, 
                    self.settings.profit_threshold
                )
                adjustments_made.append(f"Threshold aumentado: {old_threshold:.4f} → {self.settings.profit_threshold:.4f}")
            
            # 2. Ajustar velocidad de ciclos
            old_sleep = self.settings.sleep_between_cycles
            
            if avg_opportunities > 2:  # Muchas oportunidades: acelerar
                self.settings.sleep_between_cycles *= 0.9
                self.settings.sleep_between_cycles = max(
                    self.settings.min_sleep, 
                    self.settings.sleep_between_cycles
                )
                adjustments_made.append(f"Ciclos acelerados: {old_sleep:.1f}s → {self.settings.sleep_between_cycles:.1f}s")
                
            elif avg_opportunities < 0.5:  # Pocas oportunidades: ralentizar
                self.settings.sleep_between_cycles *= 1.1
                self.settings.sleep_between_cycles = min(
                    self.settings.max_sleep, 
                    self.settings.sleep_between_cycles
                )
                adjustments_made.append(f"Ciclos ralentizados: {old_sleep:.1f}s → {self.settings.sleep_between_cycles:.1f}s")
            
            # 3. Ajustar tamaño de posición basado en volatilidad
            old_size = self.settings.max_position_size
            
            if avg_volatility > 0.7:  # Alta volatilidad: reducir posición
                self.settings.max_position_size *= 0.9
                self.settings.max_position_size = max(10.0, self.settings.max_position_size)
                adjustments_made.append(f"Posición reducida por volatilidad: {old_size:.1f} → {self.settings.max_position_size:.1f}")
                
            elif avg_volatility < 0.3 and avg_success_rate > 0.8:  # Baja volatilidad + buen éxito: aumentar
                self.settings.max_position_size *= 1.05
                self.settings.max_position_size = min(50.0, self.settings.max_position_size)
                adjustments_made.append(f"Posición aumentada: {old_size:.1f} → {self.settings.max_position_size:.1f}")
            
            # 4. Ajustar threshold de calidad
            if avg_success_rate < 0.6:  # Bajo éxito: ser más selectivo
                self.settings.opportunity_quality_threshold = min(0.8, self.settings.opportunity_quality_threshold * 1.1)
                adjustments_made.append(f"Mayor selectividad requerida: {self.settings.opportunity_quality_threshold:.2f}")
                
            elif avg_success_rate > 0.9:  # Alto éxito: ser menos restrictivo
                self.settings.opportunity_quality_threshold = max(0.4, self.settings.opportunity_quality_threshold * 0.95)
                adjustments_made.append(f"Menor selectividad: {self.settings.opportunity_quality_threshold:.2f}")
            
            # Log de ajustes
            if adjustments_made:
                logging.info("🔧 AJUSTES AUTOMÁTICOS APLICADOS:")
                for adj in adjustments_made:
                    logging.info(f"   • {adj}")
                logging.info(f"📊 Métricas recientes: Ops={avg_opportunities:.1f}, "
                           f"Éxito={avg_success_rate:.1%}, Vol={avg_volatility:.2f}")
            
            self.last_adjustment = time.time()
            
        except Exception as e:
            logging.error(f"❌ Error en ajuste automático: {e}")
    
    def get_current_settings(self) -> Dict:
        """Obtiene configuración actual"""
        try:
            return asdict(self.settings)
        except Exception:
            return {}
    
    def force_adjustment(self, **kwargs):
        """Fuerza ajuste manual de parámetros"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)
                    logging.info(f"🔧 Ajuste manual: {key} = {value}")
        except Exception as e:
            logging.error(f"❌ Error en ajuste manual: {e}")
    
    def reset_to_defaults(self):
        """Resetea a configuración por defecto"""
        self.settings = AdaptiveSettings()
        logging.info("🔄 Configuración reseteada a valores por defecto")
    
    def save_settings(self, filename: str = "adaptive_settings.json"):
        """Guarda configuración en archivo"""
        try:
            data = {
                'settings': asdict(self.settings),
                'last_update': time.time(),
                'performance_summary': self.get_performance_summary()
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
                
            logging.info(f"💾 Configuración guardada en {filename}")
            
        except Exception as e:
            logging.error(f"❌ Error guardando configuración: {e}")
    
    def load_settings(self, filename: str = "adaptive_settings.json"):
        """Carga configuración desde archivo"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            settings_data = data.get('settings', {})
            for key, value in settings_data.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)
            
            logging.info(f"📁 Configuración cargada desde {filename}")
            
        except FileNotFoundError:
            logging.info("📁 Archivo de configuración no encontrado, usando valores por defecto")
        except Exception as e:
            logging.error(f"❌ Error cargando configuración: {e}")
    
    def get_performance_summary(self) -> Dict:
        """Obtiene resumen de rendimiento"""
        try:
            if not self.performance_history:
                return {'status': 'No data'}
            
            recent = self.performance_history[-20:]  # Últimas 20 mediciones
            
            return {
                'total_measurements': len(self.performance_history),
                'avg_opportunities_per_cycle': sum(d['opportunities_found'] for d in recent) / len(recent),
                'avg_success_rate': sum(d['success_rate'] for d in recent) / len(recent),
                'total_profit': sum(d['total_profit'] for d in recent),
                'avg_market_volatility': sum(d['market_volatility'] for d in recent) / len(recent),
                'current_profit_threshold': self.settings.profit_threshold,
                'adjustments_made': len([d for d in recent if d.get('adjusted', False)])
            }
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo resumen: {e}")
            return {'status': 'Error'}
    
    def get_optimization_recommendations(self) -> List[str]:
        """Obtiene recomendaciones de optimización"""
        recommendations = []
        
        try:
            summary = self.get_performance_summary()
            
            if summary.get('avg_opportunities_per_cycle', 0) < 1:
                recommendations.append("🎯 Considerar reducir profit threshold para más oportunidades")
            
            if summary.get('avg_success_rate', 0) < 0.7:
                recommendations.append("🛡️ Aumentar quality threshold para mayor selectividad")
            
            if summary.get('avg_market_volatility', 0) > 0.6:
                recommendations.append("📉 Reducir position size debido a alta volatilidad")
            
            if summary.get('total_profit', 0) < 0:
                recommendations.append("🔍 Revisar estrategia - rentabilidad negativa")
            
            if not recommendations:
                recommendations.append("✅ Configuración actual funciona bien")
            
        except Exception as e:
            recommendations.append(f"❌ Error generando recomendaciones: {e}")
        
        return recommendations

# Instancia global del gestor adaptativo
adaptive_config = AdaptiveConfigManager()