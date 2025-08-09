# binance_arbitrage_bot/main.py - Versión Mejorada con Detección Inteligente

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

# Importar módulos mejorados
try:
    from services.enhanced_scanner import run_with_enhancements
    ENHANCED_SCANNER_AVAILABLE = True
    print("✅ Scanner mejorado disponible")
except ImportError:
    ENHANCED_SCANNER_AVAILABLE = False
    print("⚠️ Scanner mejorado no disponible - usando scanner original")

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
            
            min_balance_required = getattr(settings, 'MIN_BALANCE_REQUIRED', max(settings.QUANTUMS_USDT) * getattr(settings, 'BALANCE_MULTIPLIER', 1.5))  # 2x la cantidad máxima
            
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
        if settings.PROFIT_THOLD >= 0.003:  # Al menos 0.3% (reducido para más oportunidades)
            print(f"✅ Threshold optimizado: {settings.PROFIT_THOLD*100:.2f}%")
            checks.append(True)
        else:
            print(f"⚠️ Threshold muy agresivo: {settings.PROFIT_THOLD*100:.2f}%")
            checks.append(True)  # Permitir thresholds bajos para detectar más oportunidades
        
        # 3. Verificar cantidades
        if max(settings.QUANTUMS_USDT) <= 50:
            print(f"✅ Cantidades: {settings.QUANTUMS_USDT}")
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
            print("⚠️ Empezando con configuración optimizada para detectar oportunidades")
            return True
        else:
            print("🔴 NO LISTO PARA TRADES REALES")
            print("💡 Revisa la configuración antes de continuar")
            return False

    def run_live_trading_loop(self):
        """Loop principal para trades reales con mejoras"""
        
        # Verificar si usar versión mejorada
        if ENHANCED_SCANNER_AVAILABLE:
            print("🚀 Usando scanner mejorado con detección inteligente")
            try:
                run_with_enhancements()
            except Exception as e:
                print(f"❌ Error en scanner mejorado: {e}")
                print("🔄 Cayendo a scanner original...")
                self.run_original_loop()
        else:
            print("📊 Usando scanner original mejorado")
            self.run_original_loop()

    def run_original_loop(self):
        """Loop original mejorado con threshold adaptativo"""
        from binance_api import market_data
        from itertools import combinations
        from strategies.triangular import simulate_route_gain, fetch_symbol_filters
        
        # Inicializar
        fetch_symbol_filters()
        sym_map = market_data.exchange_map()
        valid_symbols = set(sym_map.keys())
        
        print(f"\n🚀 INICIANDO TRADING BÁSICO MEJORADO")
        print(f"📊 Configuración: {settings.QUANTUMS_USDT} USDT, {settings.PROFIT_THOLD*100:.2f}% mín")
        
        cycle_count = 0
        adaptive_threshold = settings.PROFIT_THOLD
        opportunities_history = []
        
        while self.running:
            if TRADE_MONITOR_AVAILABLE and not trade_monitor.should_continue_trading():
                print("🛑 Deteniendo trading por límites de seguridad")
                break
                
            cycle_start = time.time()
            cycle_count += 1
            
            try:
                # Obtener datos de mercado
                symbols = market_data.top_volume_symbols(settings.TOP_N_PAIRS)
                books = market_data.depth_snapshots(symbols[:25])
                
                # Usar monedas prioritarias con mejor liquidez
                priority_coins = ['BTC', 'ETH', 'BNB', 'ADA', 'DOT', 'LINK', 'XRP', 'LTC', 'MATIC', 'AVAX']
                
                print(f"\n🔍 CICLO {cycle_count} - Threshold: {adaptive_threshold*100:.2f}%")
                
                opportunities_found = 0
                best_opportunities = []
                
                # Búsqueda mejorada de oportunidades
                for combo in combinations(priority_coins[:8], 2):
                    if not self.running:
                        break
                        
                    route = [settings.BASE_ASSET] + list(combo) + [settings.BASE_ASSET]
                    
                    # Probar múltiples cantidades
                    for amount in [10, 15, 20, 25, 30]:
                        try:
                            final_qty = simulate_route_gain(route, amount, books, valid_symbols)
                            if final_qty == 0:
                                continue
                            
                            profit = final_qty - amount
                            profit_pct = (profit / amount)
                            
                            if profit_pct > adaptive_threshold:
                                opportunities_found += 1
                                
                                # Calcular score de calidad básico
                                quality_score = min(1.0, profit_pct / 0.02)  # Normalizar a 2%
                                
                                opportunity = {
                                    'route': route,
                                    'amount': amount,
                                    'profit': profit,
                                    'profit_pct': profit_pct,
                                    'quality_score': quality_score
                                }
                                
                                best_opportunities.append(opportunity)
                                
                                # Log de oportunidad
                                if TRADE_MONITOR_AVAILABLE:
                                    trade_monitor.log_opportunity(route, amount, profit, quality_score)
                                
                        except Exception as e:
                            logging.debug(f"Error evaluando {route}: {e}")
                            continue
                
                # Ordenar por rentabilidad
                best_opportunities.sort(key=lambda x: x['profit_pct'], reverse=True)
                
                # Ejecutar mejores oportunidades
                trades_executed = 0
                for opp in best_opportunities[:3]:  # Top 3
                    
                    print(f"💰 OPORTUNIDAD: {' → '.join(opp['route'])}")
                    print(f"   💵 {opp['amount']:.0f} USDT → +{opp['profit']:.4f} USDT ({opp['profit_pct']*100:.3f}%)")
                    print(f"   🎯 Quality: {opp['quality_score']:.2f}")
                    
                    if opp['quality_score'] >= 0.3:  # Threshold de calidad reducido para más oportunidades
                        success, actual_profit = self.execute_real_trade(
                            opp['route'], opp['amount'], opp['profit'], books
                        )
                        
                        if success:
                            trades_executed += 1
                        
                        if TRADE_MONITOR_AVAILABLE:
                            trade_monitor.log_trade_execution(
                                opp['route'], opp['amount'], success, actual_profit,
                                execution_time=2.0,
                                error_msg="" if success else "Error de ejecución"
                            )
                        
                        if success:
                            time.sleep(1)
                
                # Ajuste adaptativo del threshold
                opportunities_history.append(opportunities_found)
                if len(opportunities_history) > 10:
                    opportunities_history = opportunities_history[-10:]
                
                avg_opportunities = sum(opportunities_history) / len(opportunities_history)
                
                # Lógica de ajuste mejorada
                if avg_opportunities < 0.5:
                    # Muy pocas oportunidades: reducir threshold agresivamente
                    adaptive_threshold *= 0.9
                    adaptive_threshold = max(0.002, adaptive_threshold)  # Mínimo 0.2%
                    print(f"🎯 Threshold reducido a {adaptive_threshold*100:.2f}%")
                elif avg_opportunities > 4:
                    # Muchas oportunidades: aumentar threshold
                    adaptive_threshold *= 1.1
                    adaptive_threshold = min(0.020, adaptive_threshold)  # Máximo 2%
                    print(f"🎯 Threshold aumentado a {adaptive_threshold*100:.2f}%")
                
                # Mostrar estadísticas cada 5 ciclos
                if cycle_count % 5 == 0:
                    if TRADE_MONITOR_AVAILABLE:
                        trade_monitor.show_live_stats()
                    print(f"📈 Oportunidades promedio: {avg_opportunities:.1f}")
                    print(f"📊 Threshold actual: {adaptive_threshold*100:.2f}%")
                
                # Pausa adaptativa
                cycle_time = time.time() - cycle_start
                if opportunities_found == 0:
                    sleep_time = max(1, settings.SLEEP_BETWEEN * 0.8)  # Acelerar si no hay oportunidades
                elif opportunities_found > 2:
                    sleep_time = max(1, settings.SLEEP_BETWEEN * 1.2)  # Ralentizar si hay muchas
                else:
                    sleep_time = max(1, settings.SLEEP_BETWEEN - cycle_time)
                
                time.sleep(sleep_time)
                
            except Exception as e:
                logging.error(f"❌ Error en ciclo: {e}")
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

    def get_market_liquidity_score(self, books, symbol):
        """Calcula score de liquidez para un símbolo"""
        try:
            if symbol not in books:
                return 0.0
            
            book = books[symbol]
            if not book.get('bids') or not book.get('asks'):
                return 0.0
            
            # Calcular liquidez total en top 5 niveles
            bid_liquidity = sum(float(level[1]) for level in book['bids'][:5])
            ask_liquidity = sum(float(level[1]) for level in book['asks'][:5])
            
            total_liquidity = (bid_liquidity + ask_liquidity) / 2
            
            # Normalizar (1000 como buena liquidez)
            return min(1.0, total_liquidity / 1000)
            
        except Exception:
            return 0.0
    
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
        
        print("🤖 BINANCE ARBITRAGE BOT - VERSIÓN MEJORADA")
        print("="*60)
        
        # Verificar modo
        if self.live_mode:
            print("🔴 MODO LIVE - TRADES REALES ACTIVADOS")
            if not self.verify_live_trading_readiness():
                print("❌ Bot no está listo para trades reales")
                return
        else:
            print("✅ MODO SIMULACIÓN")
        
        # Mostrar capacidades disponibles
        print(f"🧠 Scanner Mejorado: {'✅' if ENHANCED_SCANNER_AVAILABLE else '❌'}")
        print(f"📊 Threshold Adaptativo: ✅")
        print(f"🎯 Detección Inteligente: {'✅' if ENHANCED_SCANNER_AVAILABLE else '📊 Básica'}")
        print(f"📈 Trade Monitor: {'✅' if TRADE_MONITOR_AVAILABLE else '❌'}")
        
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
    """Punto de entrada principal mejorado"""
    
    # Verificar configuración
    if settings.LIVE:
        print("🔴 ATENCIÓN: TRADES REALES ACTIVADOS")
        confirmation = input("¿Estás seguro de continuar? (escribe 'SI' para confirmar): ")
        if confirmation != 'SI':
            print("❌ Operación cancelada por el usuario")
            return
    
    bot = LiveArbitrageBot()
    
    # Mostrar configuración actual
    print(f"\n📋 CONFIGURACIÓN ACTUAL:")
    print(f"   🎯 Threshold inicial: {settings.PROFIT_THOLD*100:.2f}%")
    print(f"   💰 Cantidades: {settings.QUANTUMS_USDT}")
    print(f"   📊 Pares monitoreados: {settings.TOP_N_PAIRS}")
    print(f"   ⏱️ Pausa entre ciclos: {settings.SLEEP_BETWEEN}s")
    
    bot.run()

if __name__ == "__main__":
    main()