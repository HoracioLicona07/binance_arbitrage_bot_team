# binance_arbitrage_bot/monitoring/trade_monitor.py

import logging
import time
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass
from config import settings

@dataclass
class TradeEvent:
    """Evento de trade para monitoreo"""
    timestamp: str
    type: str  # 'OPPORTUNITY', 'EXECUTION', 'PROFIT', 'LOSS', 'ERROR'
    message: str
    amount: float
    profit: float
    route: List[str]
    confidence: float

class TradeMonitor:
    def __init__(self):
        self.events = []
        self.session_stats = {
            'start_time': time.time(),
            'opportunities_detected': 0,
            'trades_executed': 0,
            'successful_trades': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'max_profit_trade': 0.0,
            'max_loss_trade': 0.0
        }
        self.daily_trade_count = 0
        self.last_reset_day = datetime.now().day
        
    def log_opportunity(self, route: List[str], amount: float, 
                       expected_profit: float, confidence: float):
        """Registra una oportunidad detectada"""
        self._check_daily_reset()
        
        event = TradeEvent(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            type='OPPORTUNITY',
            message=f"🎯 Oportunidad: {' → '.join(route)}",
            amount=amount,
            profit=expected_profit,
            route=route,
            confidence=confidence
        )
        
        self.events.append(event)
        self.session_stats['opportunities_detected'] += 1
        
        # Log con formato bonito
        profit_pct = (expected_profit / amount) * 100
        print(f"\n{'='*60}")
        print(f"🎯 OPORTUNIDAD DETECTADA - {event.timestamp}")
        print(f"{'='*60}")
        print(f"📍 Ruta: {' → '.join(route)}")
        print(f"💰 Cantidad: {amount:.2f} USDT")
        print(f"📈 Ganancia esperada: +{expected_profit:.4f} USDT ({profit_pct:.3f}%)")
        print(f"🎲 Confianza: {confidence:.1%}")
        print(f"{'='*60}")
        
        self._limit_events()
    
    def log_trade_execution(self, route: List[str], amount: float, success: bool,
                          actual_profit: float = 0.0, execution_time: float = 0.0,
                          error_msg: str = ""):
        """Registra la ejecución de un trade"""
        self.daily_trade_count += 1
        
        if success:
            event_type = 'PROFIT' if actual_profit > 0 else 'EXECUTION'
            message = f"✅ Trade ejecutado: {' → '.join(route)}"
            self.session_stats['trades_executed'] += 1
            self.session_stats['successful_trades'] += 1
            self.session_stats['total_profit'] += actual_profit
            
            if actual_profit > self.session_stats['max_profit_trade']:
                self.session_stats['max_profit_trade'] = actual_profit
                
        else:
            event_type = 'ERROR'
            message = f"❌ Trade fallido: {error_msg}"
            loss = min(amount * 0.01, 1.0)  # Estimar pérdida conservadora
            self.session_stats['total_loss'] += loss
            
            if loss > self.session_stats['max_loss_trade']:
                self.session_stats['max_loss_trade'] = loss
        
        event = TradeEvent(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            type=event_type,
            message=message,
            amount=amount,
            profit=actual_profit,
            route=route,
            confidence=0.0
        )
        
        self.events.append(event)
        
        # Log detallado del trade
        print(f"\n{'🟢' if success else '🔴'} TRADE EJECUTADO - {event.timestamp}")
        print(f"{'='*60}")
        print(f"📍 Ruta: {' → '.join(route)}")
        print(f"💰 Cantidad: {amount:.2f} USDT")
        
        if success:
            profit_pct = (actual_profit / amount) * 100
            print(f"✅ Estado: EXITOSO")
            print(f"📈 Ganancia real: +{actual_profit:.4f} USDT ({profit_pct:.3f}%)")
            print(f"⏱️ Tiempo ejecución: {execution_time:.2f}s")
            print(f"📊 Trades hoy: {self.daily_trade_count}/{settings.MAX_DAILY_TRADES}")
        else:
            print(f"❌ Estado: FALLIDO")
            print(f"🚨 Error: {error_msg}")
        
        print(f"{'='*60}")
        
        # Alertas especiales
        if success and actual_profit > settings.PROFIT_ALERT_THRESHOLD:
            self._alert_big_profit(actual_profit, route)
        elif not success:
            self._alert_trade_failure(error_msg, route)
            
        self._limit_events()
    
    def show_live_stats(self):
        """Muestra estadísticas en tiempo real"""
        elapsed = time.time() - self.session_stats['start_time']
        hours = elapsed / 3600
        
        net_profit = self.session_stats['total_profit'] - self.session_stats['total_loss']
        success_rate = 0
        if self.session_stats['trades_executed'] > 0:
            success_rate = (self.session_stats['successful_trades'] / 
                          self.session_stats['trades_executed']) * 100
        
        print(f"\n📊 ESTADÍSTICAS EN VIVO - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*50}")
        print(f"⏱️ Tiempo sesión: {hours:.1f}h")
        print(f"🎯 Oportunidades: {self.session_stats['opportunities_detected']}")
        print(f"🚀 Trades ejecutados: {self.session_stats['trades_executed']}")
        print(f"✅ Tasa éxito: {success_rate:.1f}%")
        print(f"💰 Ganancia neta: {net_profit:+.4f} USDT")
        print(f"📈 Mejor trade: +{self.session_stats['max_profit_trade']:.4f} USDT")
        print(f"📊 Trades hoy: {self.daily_trade_count}/{settings.MAX_DAILY_TRADES}")
        
        # Mostrar últimos eventos
        print(f"\n📋 ÚLTIMOS EVENTOS:")
        for event in self.events[-3:]:
            icon = self._get_event_icon(event.type)
            print(f"   {icon} {event.timestamp} - {event.message}")
        
        print(f"{'='*50}")
    
    def _check_daily_reset(self):
        """Verifica si necesita resetear el contador diario"""
        current_day = datetime.now().day
        if current_day != self.last_reset_day:
            self.daily_trade_count = 0
            self.last_reset_day = current_day
            print(f"🌅 Nuevo día - Reset contador diario de trades")
    
    def _alert_big_profit(self, profit: float, route: List[str]):
        """Alerta de ganancia grande"""
        print(f"\n🚨 ALERTA DE GANANCIA GRANDE 🚨")
        print(f"💰 Ganancia: +{profit:.4f} USDT")
        print(f"📍 Ruta: {' → '.join(route)}")
        print(f"🎉 ¡Excelente trade!")
    
    def _alert_trade_failure(self, error: str, route: List[str]):
        """Alerta de trade fallido"""
        print(f"\n⚠️ ALERTA DE TRADE FALLIDO ⚠️")
        print(f"📍 Ruta: {' → '.join(route)}")
        print(f"🚨 Error: {error}")
        print(f"💡 Revisando próximas oportunidades...")
    
    def _get_event_icon(self, event_type: str) -> str:
        """Obtiene icono para tipo de evento"""
        icons = {
            'OPPORTUNITY': '🎯',
            'EXECUTION': '🚀',
            'PROFIT': '💰',
            'LOSS': '📉',
            'ERROR': '❌'
        }
        return icons.get(event_type, '📋')
    
    def _limit_events(self):
        """Limita el número de eventos en memoria"""
        if len(self.events) > 50:
            self.events = self.events[-30:]  # Mantener últimos 30
    
    def should_continue_trading(self) -> bool:
        """Verifica si debe continuar trading"""
        # Verificar límite diario de trades
        if self.daily_trade_count >= settings.MAX_DAILY_TRADES:
            print(f"🛑 Límite diario de trades alcanzado: {self.daily_trade_count}")
            return False
        
        # Verificar pérdidas excesivas
        net_loss = self.session_stats['total_loss'] - self.session_stats['total_profit']
        if net_loss > settings.MAX_DAILY_RISK:
            print(f"🛑 Límite de pérdida diaria alcanzado: {net_loss:.2f} USDT")
            return False
        
        return True
    
    def get_session_summary(self) -> Dict:
        """Obtiene resumen de la sesión"""
        elapsed = time.time() - self.session_stats['start_time']
        
        return {
            'session_duration_hours': elapsed / 3600,
            'opportunities_per_hour': self.session_stats['opportunities_detected'] / max(elapsed/3600, 0.1),
            'trades_per_hour': self.session_stats['trades_executed'] / max(elapsed/3600, 0.1),
            'net_profit': self.session_stats['total_profit'] - self.session_stats['total_loss'],
            'success_rate': (self.session_stats['successful_trades'] / 
                           max(self.session_stats['trades_executed'], 1)) * 100,
            'daily_trades_remaining': settings.MAX_DAILY_TRADES - self.daily_trade_count,
            'best_trade': self.session_stats['max_profit_trade'],
            'worst_trade': -self.session_stats['max_loss_trade']
        }

# Instancia global del monitor
trade_monitor = TradeMonitor()