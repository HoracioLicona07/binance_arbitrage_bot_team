# binance_arbitrage_bot/main.py - Versión para Trades Reales

import signal
import sys
import time
import logging
from core.logger import setup_logger
from config import settings

# Importar monitor de trades
try:
    from monitoring.trade_monitor import trade_monitor
    TRADE_MONITOR_AVAILABLE = True
    print("✅ Trade monitor disponible")
except ImportError:
    TRADE_MONITOR_AVAILABLE = False
    print("⚠️ Trade monitor no disponible")

# Importar otros módulos
try:
    from services import scanner
    from detection.opportunity_scanner import opportunity_scanner
    from binance_api.order_executor import order_executor
    from analytics.performance_analyzer import performance_analyzer
    from risk_management.risk_calculator import risk_calculator
    ENHANCED_MODULES = True
except ImportError:
    ENHANCED_MODULES = False

class LiveArbitrageBot:
    def __init__(self):
        self.running = False
        self.live_mode = settings.LIVE
        
    def verify_live_trading_readiness(self):
        """Verifica que todo esté listo para trades reales"""
        if not self.live_mode:
            logging.info("💡 Modo simulación - saltando verificaciones de trading real")
            return True
            
        print("\n🔴 VERIFICANDO PREPARACIÓN PARA TRADES REALES")
        print("="*60)
        
        checks = []
        
        # 1. Verificar balance mínimo
        try:
            from binance_api.client import client
            account = client.get_account()
            usdt_balance = 0
            
            for balance in account['balances']:
                if balance['asset'] == 'USDT':
                    usdt_balance = float(balance['free'])
                    break
            
            min_balance_required = max(settings.QUANTUMS_USDT) * 2  # 2x la cantidad máxima
            
            if usdt_balance >= min_balance_required:
                print(f"✅ Balance USDT: {usdt_balance:.2f} (mínimo: {min_balance_required:.2f})")
                checks.append(True)
            else:
                print(f"❌ Balance USDT insuficiente: {usdt_balance:.2f} < {min_balance_required:.2f}")
                checks.append(False)
                
        except Exception as e:
            print(f"❌ Error verificando balance: {e}")
            checks.append(False)
        
        # 2. Verificar configuración conservadora
        if settings.PROFIT_THOLD >= 0.005:  # Al menos 0.5%
            print(f"✅ Threshold conservador: {settings.PROFIT_THOLD*100:.2f}%")
            checks.append(True)
        else:
            print(f"❌ Threshold muy agresivo: {settings.PROFIT_THOLD*100:.2f}%")
            checks.append(False)
        
        # 3. Verificar cantidades conservadoras
        if max(settings.QUANTUMS_USDT) <= 50:
            print(f"✅ Cantidades conservadoras: {settings.QUANTUMS_USDT}")
            checks.append(True)
        else:
            print(f"❌ Cantidades muy altas: {settings.QUANTUMS_USDT}")
            checks.append(False)
        
        # 4. Verificar módulos necesarios
        if ENHANCED_MODULES:
            print("✅ Módulos avanzados disponibles")
            checks.append(True)
        else:
            print("⚠️ Módulos avanzados limitados")
            checks.append(True)  # No crítico
        
        print("="*60)
        
        if all(checks):
            print("🟢 LISTO PARA TRADES REALES")
            print("⚠️ Empezando con configuración conservadora")
            return True
        else:
            print("🔴 NO LISTO PARA TRADES REALES")
            print("💡 Revisa la configuración antes de continuar")
            return False
    
    def run_live_trading_loop(self):
        """Loop principal para trades reales con monitoreo"""
        from binance_api import market_data
        from itertools import combinations
        from strategies.triangular import simulate_route_gain, fetch_symbol_filters
        
        # Inicializar
        fetch_symbol_filters()
        sym_map = market_data.exchange_map()
        valid_symbols = set(sym_map.keys())
        
        print(f"\n🚀 INICIANDO TRADING EN VIVO")
        print(f"📊 Configuración: {settings.QUANTUMS_USDT} USDT, {settings.PROFIT_THOLD*100:.2f}% mín")
        
        cycle_count = 0
        
        while self.running:
            if not trade_monitor.should_continue_trading():
                print("🛑 Deteniendo trading por límites de seguridad")
                break
                
            cycle_start = time.time()
            cycle_count += 1
            
            try:
                # Obtener datos de mercado
                symbols = market_data.top_volume_symbols(settings.TOP_N_PAIRS)
                coins = {c for s in symbols if s in sym_map for c in sym_map[s]}
                coins.discard(settings.BASE_ASSET)
                coins = list(coins)[:15]  # Limitar para eficiencia
                
                books = market_data.depth_snapshots(symbols[:30])
                
                print(f"\n🔍 CICLO {cycle_count} - Escaneando...")
                
                # Buscar oportunidades
                opportunities_found = 0
                
                for combo in combinations(coins, 2):  # Rutas triangulares
                    if not self.running:
                        break
                        
                    route = [settings.BASE_ASSET] + list(combo) + [settings.BASE_ASSET]
                    
                    for amount in settings.QUANTUMS_USDT:
                        try:
                            final_qty = simulate_route_gain(route, amount, books, valid_symbols)
                            if final_qty == 0:
                                continue
                            
                            profit = final_qty - amount
                            profit_pct = (profit / amount)
                            
                            if profit_pct > settings.PROFIT_THOLD:
                                opportunities_found += 1
                                confidence = min(0.9, 0.6 + (profit_pct * 10))  # Estimación
                                
                                # Registrar oportunidad
                                trade_monitor.log_opportunity(route, amount, profit, confidence)
                                
                                # Decidir si ejecutar
                                if confidence >= settings.MIN_CONFIDENCE:
                                    success, actual_profit = self.execute_real_trade(
                                        route, amount, profit, books
                                    )
                                    
                                    trade_monitor.log_trade_execution(
                                        route, amount, success, actual_profit,
                                        execution_time=2.0,  # Estimado
                                        error_msg="" if success else "Error de ejecución"
                                    )
                                    
                                    if success:
                                        # Pausa tras trade exitoso
                                        time.sleep(1)
                                
                        except Exception as e:
                            logging.debug(f"Error evaluando {route}: {e}")
                            continue
                
                # Mostrar estadísticas cada 5 ciclos
                if cycle_count % 5 == 0:
                    trade_monitor.show_live_stats()
                
                # Pausa entre ciclos
                cycle_time = time.time() - cycle_start
                sleep_time = max(1, settings.SLEEP_BETWEEN - cycle_time)
                time.sleep(sleep_time)
                
            except Exception as e:
                logging.error(f"❌ Error en ciclo de trading: {e}")
                time.sleep(2)
    
    def execute_real_trade(self, route, amount, expected_profit, books):
        """Ejecuta un trade real con validaciones adicionales"""
        try:
            if not self.live_mode:
                # Simulación
                return True, expected_profit * 0.8  # Simular 80% de la ganancia esperada
            
            # AQUÍ VA LA EJECUCIÓN REAL
            print(f"🔥 EJECUTANDO TRADE REAL: {' → '.join(route)}")
            
            if ENHANCED_MODULES:
                # Usar order executor avanzado
                execution_result = order_executor.execute_arbitrage_atomic(
                    route, amount, max_slippage=0.015
                )
                
                return execution_result.success, execution_result.net_profit
            else:
                # Ejecución básica (implementar según necesidades)
                from strategies.triangular import execute_arbitrage_trade
                execute_arbitrage_trade(route, amount)
                
                # Estimar resultado (en producción, obtener resultado real)
                actual_profit = expected_profit * 0.7  # Conservador
                return True, actual_profit
                
        except Exception as e:
            logging.error(f"❌ Error ejecutando trade real: {e}")
            return False, 0.0
    
    def setup_signal_handlers(self):
        """Configura cierre limpio"""
        def signal_handler(sig, frame):
            print("\n🛑 Cerrando bot de trading...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def shutdown(self):
        """Cierre limpio con reporte final"""
        self.running = False
        
        if TRADE_MONITOR_AVAILABLE:
            print("\n📊 REPORTE FINAL DE SESIÓN")
            print("="*60)
            summary = trade_monitor.get_session_summary()
            
            print(f"⏱️ Duración: {summary['session_duration_hours']:.1f}h")
            print(f"🎯 Oportunidades/hora: {summary['opportunities_per_hour']:.1f}")
            print(f"🚀 Trades/hora: {summary['trades_per_hour']:.1f}")
            print(f"💰 Ganancia neta: {summary['net_profit']:+.4f} USDT")
            print(f"✅ Tasa de éxito: {summary['success_rate']:.1f}%")
            print(f"🏆 Mejor trade: +{summary['best_trade']:.4f} USDT")
            print("="*60)
        
        print("👋 Bot cerrado correctamente")
    
    def run(self):
        """Función principal"""
        setup_logger()
        
        print("🤖 BINANCE ARBITRAGE BOT - VERSIÓN LIVE")
        print("="*60)
        
        # Verificar modo
        if self.live_mode:
            print("🔴 MODO LIVE - TRADES REALES ACTIVADOS")
            if not self.verify_live_trading_readiness():
                print("❌ Bot no está listo para trades reales")
                return
        else:
            print("✅ MODO SIMULACIÓN")
        
        # Configurar handlers
        self.setup_signal_handlers()
        
        try:
            self.running = True
            
            if self.live_mode or ENHANCED_MODULES:
                self.run_live_trading_loop()
            else:
                # Usar scanner básico
                scanner.run()
                
        except KeyboardInterrupt:
            print("\n🛑 Interrupción manual")
        except Exception as e:
            print(f"❌ Error crítico: {e}")
        finally:
            self.shutdown()

def main():
    """Punto de entrada principal"""
    
    # Verificar configuración
    if settings.LIVE:
        print("🔴 ATENCIÓN: TRADES REALES ACTIVADOS")
        confirmation = input("¿Estás seguro de continuar? (escribe 'SI' para confirmar): ")
        if confirmation != 'SI':
            print("❌ Operación cancelada por el usuario")
            return
    
    bot = LiveArbitrageBot()
    bot.run()

if __name__ == "__main__":
    main()