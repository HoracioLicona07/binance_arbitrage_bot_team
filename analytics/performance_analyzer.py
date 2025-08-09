# binance_arbitrage_bot/analytics/performance_analyzer.py

import logging
import time
import statistics
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json

@dataclass
class TradePerformance:
    """Métricas de rendimiento de un trade individual"""
    timestamp: float
    route: List[str]
    initial_amount: float
    final_amount: float
    profit_usdt: float
    profit_percentage: float
    execution_time: float
    fees_paid: float
    slippage: float
    confidence_score: float
    risk_score: float

@dataclass
class PerformanceMetrics:
    """Métricas agregadas de rendimiento"""
    # Métricas básicas
    total_trades: int
    successful_trades: int
    failed_trades: int
    success_rate: float
    
    # Métricas de rentabilidad
    total_profit: float
    avg_profit_per_trade: float
    max_profit: float
    min_profit: float
    profit_std_dev: float
    
    # Métricas de riesgo
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    
    # Métricas de tiempo
    avg_execution_time: float
    max_execution_time: float
    min_execution_time: float
    
    # Métricas de eficiencia
    avg_fees_percentage: float
    avg_slippage: float
    capital_efficiency: float

class PerformanceAnalyzer:
    def __init__(self):
        self.trade_history: List[TradePerformance] = []
        self.session_start_time = time.time()
        self.initial_capital = 0.0
        self.current_capital = 0.0
        self.peak_capital = 0.0
        self.max_drawdown_value = 0.0
        
        # Configuración de análisis
        self.analysis_window_hours = 24  # Análisis de las últimas 24 horas
        self.min_trades_for_analysis = 5
        
    def record_trade(self, route: List[str], initial_amount: float, final_amount: float,
                    execution_time: float, fees_paid: float, slippage: float = 0.0,
                    confidence_score: float = 0.0, risk_score: float = 0.0):
        """Registra un trade para análisis de rendimiento"""
        try:
            profit_usdt = final_amount - initial_amount
            profit_percentage = (profit_usdt / initial_amount) * 100 if initial_amount > 0 else 0.0
            
            trade = TradePerformance(
                timestamp=time.time(),
                route=route.copy(),
                initial_amount=initial_amount,
                final_amount=final_amount,
                profit_usdt=profit_usdt,
                profit_percentage=profit_percentage,
                execution_time=execution_time,
                fees_paid=fees_paid,
                slippage=slippage,
                confidence_score=confidence_score,
                risk_score=risk_score
            )
            
            self.trade_history.append(trade)
            
            # Actualizar capital tracking
            self.current_capital += profit_usdt
            if self.current_capital > self.peak_capital:
                self.peak_capital = self.current_capital
            
            # Calcular drawdown
            if self.peak_capital > 0:
                current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
                if current_drawdown > self.max_drawdown_value:
                    self.max_drawdown_value = current_drawdown
            
            # Limitar historial para memoria
            if len(self.trade_history) > 1000:
                self.trade_history = self.trade_history[-800:]  # Mantener últimos 800
            
            logging.debug(f"📊 Trade registrado: {profit_usdt:.4f} USDT ({profit_percentage:.3f}%)")
            
        except Exception as e:
            logging.error(f"❌ Error registrando trade: {e}")
    
    def get_performance_metrics(self, hours_back: Optional[int] = None) -> PerformanceMetrics:
        """Calcula métricas de rendimiento para el período especificado"""
        try:
            # Filtrar trades por tiempo si se especifica
            if hours_back:
                cutoff_time = time.time() - (hours_back * 3600)
                relevant_trades = [t for t in self.trade_history if t.timestamp >= cutoff_time]
            else:
                relevant_trades = self.trade_history
            
            if len(relevant_trades) < self.min_trades_for_analysis:
                return self._get_default_metrics()
            
            # Métricas básicas
            total_trades = len(relevant_trades)
            successful_trades = len([t for t in relevant_trades if t.profit_usdt > 0])
            failed_trades = total_trades - successful_trades
            success_rate = (successful_trades / total_trades) * 100
            
            # Métricas de rentabilidad
            profits = [t.profit_usdt for t in relevant_trades]
            total_profit = sum(profits)
            avg_profit_per_trade = statistics.mean(profits)
            max_profit = max(profits)
            min_profit = min(profits)
            profit_std_dev = statistics.stdev(profits) if len(profits) > 1 else 0.0
            
            # Métricas de riesgo
            wins = [t.profit_usdt for t in relevant_trades if t.profit_usdt > 0]
            losses = [abs(t.profit_usdt) for t in relevant_trades if t.profit_usdt < 0]
            
            win_rate = (len(wins) / total_trades) * 100
            avg_win = statistics.mean(wins) if wins else 0.0
            avg_loss = statistics.mean(losses) if losses else 0.0
            
            profit_factor = (sum(wins) / sum(losses)) if losses and sum(losses) > 0 else float('inf')
            sharpe_ratio = self._calculate_sharpe_ratio(profits)
            
            # Métricas de tiempo
            execution_times = [t.execution_time for t in relevant_trades]
            avg_execution_time = statistics.mean(execution_times)
            max_execution_time = max(execution_times)
            min_execution_time = min(execution_times)
            
            # Métricas de eficiencia
            fees_percentages = [(t.fees_paid / t.initial_amount) * 100 for t in relevant_trades if t.initial_amount > 0]
            avg_fees_percentage = statistics.mean(fees_percentages) if fees_percentages else 0.0
            avg_slippage = statistics.mean([t.slippage for t in relevant_trades])
            
            # Capital efficiency (profit per dollar risked)
            total_capital_used = sum(t.initial_amount for t in relevant_trades)
            capital_efficiency = (total_profit / total_capital_used) * 100 if total_capital_used > 0 else 0.0
            
            return PerformanceMetrics(
                total_trades=total_trades,
                successful_trades=successful_trades,
                failed_trades=failed_trades,
                success_rate=success_rate,
                total_profit=total_profit,
                avg_profit_per_trade=avg_profit_per_trade,
                max_profit=max_profit,
                min_profit=min_profit,
                profit_std_dev=profit_std_dev,
                max_drawdown=self.max_drawdown_value * 100,  # Como porcentaje
                sharpe_ratio=sharpe_ratio,
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss,
                profit_factor=profit_factor,
                avg_execution_time=avg_execution_time,
                max_execution_time=max_execution_time,
                min_execution_time=min_execution_time,
                avg_fees_percentage=avg_fees_percentage,
                avg_slippage=avg_slippage,
                capital_efficiency=capital_efficiency
            )
            
        except Exception as e:
            logging.error(f"❌ Error calculando métricas: {e}")
            return self._get_default_metrics()
    
    def _calculate_sharpe_ratio(self, profits: List[float], risk_free_rate: float = 0.02) -> float:
        """Calcula el ratio de Sharpe"""
        try:
            if len(profits) < 2:
                return 0.0
            
            # Convertir a returns diarios
            mean_return = statistics.mean(profits)
            std_return = statistics.stdev(profits)
            
            if std_return == 0:
                return 0.0
            
            # Ajustar risk-free rate para período de trading
            daily_risk_free = risk_free_rate / 365
            
            sharpe = (mean_return - daily_risk_free) / std_return
            return sharpe
            
        except Exception as e:
            logging.error(f"❌ Error calculando Sharpe ratio: {e}")
            return 0.0
    
    def _get_default_metrics(self) -> PerformanceMetrics:
        """Retorna métricas por defecto cuando no hay suficientes datos"""
        return PerformanceMetrics(
            total_trades=0,
            successful_trades=0,
            failed_trades=0,
            success_rate=0.0,
            total_profit=0.0,
            avg_profit_per_trade=0.0,
            max_profit=0.0,
            min_profit=0.0,
            profit_std_dev=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            win_rate=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            profit_factor=0.0,
            avg_execution_time=0.0,
            max_execution_time=0.0,
            min_execution_time=0.0,
            avg_fees_percentage=0.0,
            avg_slippage=0.0,
            capital_efficiency=0.0
        )
    
    def get_route_performance_analysis(self) -> Dict[str, Dict]:
        """Analiza rendimiento por ruta específica"""
        route_stats = {}
        
        try:
            for trade in self.trade_history:
                route_key = " → ".join(trade.route)
                
                if route_key not in route_stats:
                    route_stats[route_key] = {
                        'trades': [],
                        'total_profit': 0.0,
                        'success_count': 0,
                        'total_count': 0
                    }
                
                route_stats[route_key]['trades'].append(trade)
                route_stats[route_key]['total_profit'] += trade.profit_usdt
                route_stats[route_key]['total_count'] += 1
                
                if trade.profit_usdt > 0:
                    route_stats[route_key]['success_count'] += 1
            
            # Calcular métricas por ruta
            route_analysis = {}
            for route_key, stats in route_stats.items():
                if stats['total_count'] >= 3:  # Mínimo 3 trades para análisis
                    profits = [t.profit_usdt for t in stats['trades']]
                    
                    route_analysis[route_key] = {
                        'total_trades': stats['total_count'],
                        'success_rate': (stats['success_count'] / stats['total_count']) * 100,
                        'total_profit': stats['total_profit'],
                        'avg_profit': statistics.mean(profits),
                        'max_profit': max(profits),
                        'min_profit': min(profits),
                        'profit_std_dev': statistics.stdev(profits) if len(profits) > 1 else 0.0,
                        'avg_execution_time': statistics.mean([t.execution_time for t in stats['trades']]),
                        'profitability_score': self._calculate_route_score(stats['trades'])
                    }
            
            return route_analysis
            
        except Exception as e:
            logging.error(f"❌ Error en análisis por rutas: {e}")
            return {}
    
    def _calculate_route_score(self, trades: List[TradePerformance]) -> float:
        """Calcula score de rentabilidad para una ruta"""
        try:
            if not trades:
                return 0.0
            
            profits = [t.profit_usdt for t in trades]
            win_rate = len([p for p in profits if p > 0]) / len(profits)
            avg_profit = statistics.mean(profits)
            consistency = 1 - (statistics.stdev(profits) / abs(avg_profit)) if avg_profit != 0 else 0
            
            # Score compuesto
            score = (win_rate * 0.4 + 
                    min(avg_profit / 1.0, 1.0) * 0.4 +  # Normalizar a 1 USDT máximo
                    max(0, consistency) * 0.2)
            
            return min(1.0, score)
            
        except Exception as e:
            logging.error(f"❌ Error calculando score de ruta: {e}")
            return 0.0
    
    def generate_performance_report(self, hours_back: int = 24) -> str:
        """Genera reporte completo de rendimiento"""
        try:
            metrics = self.get_performance_metrics(hours_back)
            route_analysis = self.get_route_performance_analysis()
            
            report = []
            report.append("=" * 60)
            report.append(f"📊 REPORTE DE RENDIMIENTO - Últimas {hours_back}h")
            report.append("=" * 60)
            
            # Métricas básicas
            report.append("\n🎯 MÉTRICAS GENERALES:")
            report.append(f"   Total de trades: {metrics.total_trades}")
            report.append(f"   Trades exitosos: {metrics.successful_trades}")
            report.append(f"   Tasa de éxito: {metrics.success_rate:.1f}%")
            report.append(f"   Ganancia total: {metrics.total_profit:.4f} USDT")
            report.append(f"   Ganancia promedio: {metrics.avg_profit_per_trade:.4f} USDT")
            
            # Métricas de riesgo
            report.append("\n🛡️ MÉTRICAS DE RIESGO:")
            report.append(f"   Máximo drawdown: {metrics.max_drawdown:.2f}%")
            report.append(f"   Ratio de Sharpe: {metrics.sharpe_ratio:.2f}")
            report.append(f"   Factor de ganancia: {metrics.profit_factor:.2f}")
            
            # Métricas de eficiencia
            report.append("\n⚡ MÉTRICAS DE EFICIENCIA:")
            report.append(f"   Tiempo promedio: {metrics.avg_execution_time:.2f}s")
            report.append(f"   Comisiones promedio: {metrics.avg_fees_percentage:.3f}%")
            report.append(f"   Slippage promedio: {metrics.avg_slippage:.3f}%")
            report.append(f"   Eficiencia de capital: {metrics.capital_efficiency:.2f}%")
            
            # Top rutas
            if route_analysis:
                report.append("\n🏆 TOP RUTAS POR RENTABILIDAD:")
                sorted_routes = sorted(route_analysis.items(), 
                                     key=lambda x: x[1]['profitability_score'], 
                                     reverse=True)
                for i, (route, stats) in enumerate(sorted_routes[:5]):
                    report.append(f"   {i+1}. {route}")
                    report.append(f"      Trades: {stats['total_trades']} | "
                                f"Éxito: {stats['success_rate']:.1f}% | "
                                f"Ganancia: {stats['total_profit']:.4f} USDT")
            
            # Recomendaciones básicas
            report.append("\n💡 RECOMENDACIONES:")
            if metrics.success_rate < 70:
                report.append("   • Mejorar filtros de oportunidades - tasa de éxito baja")
            if metrics.avg_profit_per_trade < 0.5:
                report.append("   • Buscar oportunidades más rentables")
            if metrics.max_drawdown > 10:
                report.append("   • Reducir tamaños de posición - drawdown alto")
            if metrics.avg_execution_time > 5:
                report.append("   • Optimizar velocidad de ejecución")
            if not any([metrics.success_rate < 70, metrics.avg_profit_per_trade < 0.5, 
                       metrics.max_drawdown > 10, metrics.avg_execution_time > 5]):
                report.append("   • Rendimiento óptimo - continuar estrategia actual")
            
            report.append("\n" + "=" * 60)
            
            return "\n".join(report)
            
        except Exception as e:
            logging.error(f"❌ Error generando reporte: {e}")
            return f"Error generando reporte: {e}"
    
    def export_data(self, filename: Optional[str] = None) -> str:
        """Exporta datos de rendimiento a JSON"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"performance_data_{timestamp}.json"
            
            export_data = {
                'session_start': self.session_start_time,
                'export_timestamp': time.time(),
                'trade_count': len(self.trade_history),
                'trades': [asdict(trade) for trade in self.trade_history],
                'current_capital': self.current_capital,
                'peak_capital': self.peak_capital,
                'max_drawdown': self.max_drawdown_value
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logging.info(f"📁 Datos exportados a {filename}")
            return filename
            
        except Exception as e:
            logging.error(f"❌ Error exportando datos: {e}")
            return ""
    
    def reset_session(self, initial_capital: float = 1000.0):
        """Resetea la sesión de análisis"""
        self.trade_history.clear()
        self.session_start_time = time.time()
        self.initial_capital = initial_capital
        self.current_capital = 0.0
        self.peak_capital = 0.0
        self.max_drawdown_value = 0.0
        
        logging.info(f"🔄 Sesión de análisis reseteada - Capital inicial: {initial_capital} USDT")

# Instancia global del analizador
performance_analyzer = PerformanceAnalyzer()