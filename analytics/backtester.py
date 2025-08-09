# binance_arbitrage_bot/analytics/backtester.py

import logging
import time
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class BacktestResult:
    """Resultado de backtesting"""
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return: float
    total_trades: int
    winning_trades: int
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float

class SimpleBacktester:
    def __init__(self):
        self.trades = []
        self.equity_curve = []
        
    def run_strategy_backtest(self, strategy_params: Dict, days_back: int = 30) -> BacktestResult:
        """Ejecuta backtest de estrategia de arbitraje"""
        try:
            print(f"🔄 Ejecutando backtest para {days_back} días...")
            
            # Simular datos históricos (en producción usar datos reales)
            historical_data = self._generate_sample_data(days_back)
            
            initial_capital = strategy_params.get('initial_capital', 1000.0)
            current_capital = initial_capital
            trades = []
            equity = [initial_capital]
            
            for day_data in historical_data:
                daily_trades = self._simulate_daily_trading(day_data, current_capital, strategy_params)
                trades.extend(daily_trades)
                
                # Actualizar capital
                daily_pnl = sum(trade['profit'] for trade in daily_trades)
                current_capital += daily_pnl
                equity.append(current_capital)
            
            # Calcular métricas
            result = self._calculate_backtest_metrics(
                trades, equity, initial_capital, current_capital, days_back
            )
            
            print(f"✅ Backtest completado:")
            print(f"   📈 Retorno total: {result.total_return:.2f}%")
            print(f"   🎯 Trades totales: {result.total_trades}")
            print(f"   ✅ Tasa de éxito: {(result.winning_trades/max(result.total_trades,1)*100):.1f}%")
            
            return result
            
        except Exception as e:
            logging.error(f"❌ Error en backtest: {e}")
            return self._get_empty_result()
    
    def _generate_sample_data(self, days: int) -> List[Dict]:
        """Genera datos de muestra para backtest"""
        import random
        
        data = []
        for i in range(days):
            # Simular condiciones de mercado variables
            volatility = random.uniform(0.01, 0.05)  # 1-5% volatilidad
            volume_factor = random.uniform(0.8, 1.2)  # Factor de volumen
            
            # Número de oportunidades por día (basado en condiciones)
            if volatility > 0.03:
                opportunities = random.randint(15, 30)  # Más volátil = más oportunidades
            else:
                opportunities = random.randint(5, 15)   # Menos volátil = menos oportunidades
            
            day_data = {
                'date': datetime.now() - timedelta(days=days-i),
                'volatility': volatility,
                'volume_factor': volume_factor,
                'opportunities': opportunities
            }
            data.append(day_data)
        
        return data
    
    def _simulate_daily_trading(self, day_data: Dict, capital: float, params: Dict) -> List[Dict]:
        """Simula trading de un día"""
        import random
        
        trades = []
        max_position = params.get('max_position_size', 50.0)
        profit_threshold = params.get('profit_threshold', 0.008)
        
        for _ in range(day_data['opportunities']):
            # Simular trade
            position_size = min(random.uniform(10, max_position), capital * 0.1)
            
            # Probabilidad de éxito basada en volatilidad
            volatility = day_data['volatility']
            success_prob = 0.75 - (volatility * 5)  # Más volatilidad = menos éxito
            
            if random.random() < success_prob:
                # Trade exitoso
                profit_pct = random.uniform(profit_threshold, profit_threshold * 3)
                profit = position_size * profit_pct
                success = True
            else:
                # Trade fallido
                loss_pct = random.uniform(0.002, 0.01)  # 0.2-1% pérdida
                profit = -position_size * loss_pct
                success = False
            
            trade = {
                'timestamp': day_data['date'],
                'position_size': position_size,
                'profit': profit,
                'profit_pct': profit / position_size,
                'success': success
            }
            trades.append(trade)
        
        return trades
    
    def _calculate_backtest_metrics(self, trades: List[Dict], equity: List[float], 
                                  initial: float, final: float, days: int) -> BacktestResult:
        """Calcula métricas del backtest"""
        try:
            if not trades:
                return self._get_empty_result()
            
            # Métricas básicas
            total_return = ((final - initial) / initial) * 100
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t['success']])
            
            # Drawdown máximo
            max_drawdown = self._calculate_max_drawdown(equity)
            
            # Sharpe ratio simplificado
            daily_returns = [(equity[i] - equity[i-1]) / equity[i-1] 
                           for i in range(1, len(equity))]
            
            if len(daily_returns) > 1:
                import statistics
                mean_return = statistics.mean(daily_returns)
                std_return = statistics.stdev(daily_returns)
                sharpe = (mean_return / std_return * (252**0.5)) if std_return > 0 else 0
            else:
                sharpe = 0
            
            # Profit factor
            gross_profit = sum(t['profit'] for t in trades if t['profit'] > 0)
            gross_loss = abs(sum(t['profit'] for t in trades if t['profit'] < 0))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            return BacktestResult(
                start_date=(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d'),
                initial_capital=initial,
                final_capital=final,
                total_return=total_return,
                total_trades=total_trades,
                winning_trades=winning_trades,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe,
                profit_factor=profit_factor
            )
            
        except Exception as e:
            logging.error(f"❌ Error calculando métricas: {e}")
            return self._get_empty_result()
    
    def _calculate_max_drawdown(self, equity: List[float]) -> float:
        """Calcula el drawdown máximo"""
        try:
            max_dd = 0
            peak = equity[0]
            
            for value in equity:
                if value > peak:
                    peak = value
                
                drawdown = (peak - value) / peak
                if drawdown > max_dd:
                    max_dd = drawdown
            
            return max_dd * 100  # Como porcentaje
            
        except Exception:
            return 0.0
    
    def _get_empty_result(self) -> BacktestResult:
        """Resultado vacío en caso de error"""
        return BacktestResult(
            start_date="", end_date="", initial_capital=0.0, final_capital=0.0,
            total_return=0.0, total_trades=0, winning_trades=0,
            max_drawdown=0.0, sharpe_ratio=0.0, profit_factor=0.0
        )

# Instancia global
backtester = SimpleBacktester()