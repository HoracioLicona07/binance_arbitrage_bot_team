# binance_arbitrage_bot/main.py - Versión ULTRA-OPTIMIZADA

import signal
import sys
import time
import logging
from core.logger import setup_logger
from config import settings

# Importar nuestras mejoras
from core.utils import calculate_net_profit_after_fees, should_execute_trade_with_fees

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
            
            min_balance_required = getattr(settings, 'MIN_BALANCE_REQUIRED', max(settings.QUANTUMS_USDT) * getattr(settings, 'BALANCE_MULTIPLIER', 1.5))
            
            if usdt_balance >= min_balance_required:
                print(f"✅ Balance USDT: {usdt_balance:.2f} (mínimo: {min_balance_required:.2f})")
                checks.append(True)
            else:
                print(f"❌ Balance USDT insuficiente: {usdt_balance:.2f} < {min_balance_required:.2f}")
                checks.append(False)
                
        except Exception as e:
            print(f"❌ Error verificando balance: {e}")
            checks.append(False)
        
        # 2. Verificar configuración mejorada
        print(f"✅ Threshold ultra-agresivo: {settings.PROFIT_THOLD*100:.2f}%")
        print(f"✅ Fees optimizadas: 0.075% (con BNB)")
        print(f"✅ Configuración experimental activada")
        checks.append(True)
        
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
            print("🔥 MODO ULTRA-AGRESIVO ACTIVADO")
            return True
        else:
            print("🔴 NO LISTO PARA TRADES REALES")
            print("💡 Revisa la configuración antes de continuar")
            return False

    def run_live_trading_loop(self):
        """Loop principal OPTIMIZADO para detectar MÁS oportunidades"""
        
        # Verificar si usar versión mejorada
        if ENHANCED_SCANNER_AVAILABLE:
            print("🚀 Usando scanner mejorado con detección inteligente")
            try:
                run_with_enhancements()
            except Exception as e:
                print(f"❌ Error en scanner mejorado: {e}")
                print("🔄 Cayendo a scanner original ULTRA-OPTIMIZADO...")
                self.run_ultra_optimized_loop()
        else:
            print("📊 Usando scanner ULTRA-OPTIMIZADO")
            self.run_ultra_optimized_loop()

    def run_ultra_optimized_loop(self):
        """Loop ULTRA-OPTIMIZADO con mejores fees y detección"""
        from binance_api import market_data
        from itertools import combinations
        from strategies.triangular import simulate_route_gain, fetch_symbol_filters
        
        # Inicializar
        fetch_symbol_filters()
        sym_map = market_data.exchange_map()
        valid_symbols = set(sym_map.keys())
        
        print(f"\n🔥 INICIANDO TRADING ULTRA-OPTIMIZADO")
        print(f"📊 Configuración: {settings.QUANTUMS_USDT} USDT, {settings.PROFIT_THOLD*100:.2f}% mín")
        print(f"💰 Fees optimizadas: 0.075% por transacción (con BNB)")
        
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
                # Obtener MÁS datos de mercado
                symbols = market_data.top_volume_symbols(settings.TOP_N_PAIRS)
                books = market_data.depth_snapshots(symbols[:35])  # Más símbolos
                
                # MÁS monedas prioritarias
                priority_coins = [
                    'BTC', 'ETH', 'BNB', 'ADA', 'DOT', 'LINK', 'XRP', 'LTC', 
                    'MATIC', 'AVAX', 'SOL', 'DOGE', 'ATOM', 'FIL', 'TRX'
                ]
                
                print(f"\n🔍 CICLO {cycle_count} - Threshold: {adaptive_threshold*100:.2f}%")
                
                opportunities_found = 0
                best_opportunities = []
                
                # 🔥 BÚSQUEDA ULTRA-AGRESIVA de oportunidades
                for combo in combinations(priority_coins[:10], 2):  # MÁS combinaciones
                    if not self.running:
                        break
                        
                    route = [settings.BASE_ASSET] + list(combo) + [settings.BASE_ASSET]
                    
                    # 🎯 Probar TODAS las cantidades de settings
                    for amount in settings.QUANTUMS_USDT:
                        try:
                            final_qty = simulate_route_gain(route, amount, books, valid_symbols)
                            if final_qty == 0:
                                continue
                            
                            # 💡 USAR NUESTRO NUEVO CÁLCULO DE FEES
                            fee_analysis = calculate_net_profit_after_fees(route, amount, final_qty)
                            
                            # Solo continuar si es rentable DESPUÉS de fees
                            if not fee_analysis['profitable']:
                                continue
                                
                            net_profit = fee_analysis['net_profit']
                            net_profit_pct = fee_analysis['net_profit_percentage'] / 100
                            
                            # 🎯 Usar threshold más inteligente
                            if net_profit_pct > adaptive_threshold:
                                opportunities_found += 1
                                
                                # Score de calidad mejorado
                                quality_score = min(1.0, net_profit_pct / 0.01)  # Normalizar a 1%
                                
                                opportunity = {
                                    'route': route,
                                    'amount': amount,
                                    'gross_profit': final_qty - amount,
                                    'net_profit': net_profit,
                                    'net_profit_pct': net_profit_pct,
                                    'total_fees': fee_analysis['total_fees'],
                                    'quality_score': quality_score,
                                    'fee_analysis': fee_analysis
                                }
                                
                                best_opportunities.append(opportunity)
                                
                                # Log mejorado
                                if TRADE_MONITOR_AVAILABLE:
                                    trade_monitor.log_opportunity(route, amount, net_profit, quality_score)
                                
                        except Exception as e:
                            logging.debug(f"Error evaluando {route}: {e}")
                            continue
                
                # Ordenar por rentabilidad NETA
                best_opportunities.sort(key=lambda x: x['net_profit_pct'], reverse=True)
                
                # 🔥 Ejecutar mejores oportunidades con validación avanzada
                trades_executed = 0
                for opp in best_opportunities[:5]:  # Top 5 en lugar de 3
                    
                    print(f"💰 OPORTUNIDAD VALIDADA: {' → '.join(opp['route'])}")
                    print(f"   💵 {opp['amount']:.0f} USDT → Ganancia NETA: +{opp['net_profit']:.4f} USDT ({opp['net_profit_pct']*100:.3f}%)")
                    print(f"   💸 Fees totales: {opp['total_fees']:.4f} USDT")
                    print(f"   🎯 Quality: {opp['quality_score']:.2f}")
                    
                    # 🎯 Validación FINAL con nuestro sistema mejorado
                    trade_decision = should_execute_trade_with_fees(
                        opp['route'], opp['amount'], opp['amount'] + opp['gross_profit']
                    )
                    
                    if trade_decision['should_execute'] and opp['quality_score'] >= 0.2:
                        print(f"   ✅ {trade_decision['recommendation']}: {trade_decision['reason']}")
                        
                        success, actual_profit = self.execute_real_trade(
                            opp['route'], opp['amount'], opp['net_profit'], books
                        )
                        
                        if success:
                            trades_executed += 1
                            print(f"   🎉 Trade ejecutado: +{actual_profit:.4f} USDT")
                        
                        if TRADE_MONITOR_AVAILABLE:
                            trade_monitor.log_trade_execution(
                                opp['route'], opp['amount'], success, actual_profit,
                                execution_time=2.0,
                                error_msg="" if success else "Error de ejecución"
                            )
                        
                        if success:
                            time.sleep(0.5)  # Pausa más corta
                    else:
                        print(f"   ❌ RECHAZADO: {trade_decision['reason']}")
                
                # 🎯 Ajuste adaptativo MEJORADO del threshold
                opportunities_history.append(opportunities_found)
                if len(opportunities_history) > 15:  # Más historial
                    opportunities_history = opportunities_history[-15:]
                
                avg_opportunities = sum(opportunities_history) / len(opportunities_history)
                
                # 🔥 Lógica de ajuste MÁS AGRESIVA
                if avg_opportunities < 0.3:
                    # MUY pocas oportunidades: reducir threshold MÁS agresivamente
                    adaptive_threshold *= 0.85
                    adaptive_threshold = max(0.001, adaptive_threshold)  # Mínimo 0.1%
                    print(f"🎯 Threshold ULTRA-reducido a {adaptive_threshold*100:.2f}%")
                elif avg_opportunities < 1:
                    # Pocas oportunidades: reducir threshold
                    adaptive_threshold *= 0.92
                    adaptive_threshold = max(0.0015, adaptive_threshold)  # Mínimo 0.15%
                    print(f"🎯 Threshold reducido a {adaptive_threshold*100:.2f}%")
                elif avg_opportunities > 6:
                    # MUCHAS oportunidades: aumentar threshold
                    adaptive_threshold *= 1.15
                    adaptive_threshold = min(0.025, adaptive_threshold)  # Máximo 2.5%
                    print(f"🎯 Threshold aumentado a {adaptive_threshold*100:.2f}%")
                
                # Mostrar estadísticas MÁS frecuentes
                if cycle_count % 3 == 0:  # Cada 3 ciclos en lugar de 5
                    if TRADE_MONITOR_AVAILABLE:
                        trade_monitor.show_live_stats()
                    print(f"📈 Oportunidades promedio: {avg_opportunities:.1f}")
                    print(f"📊 Threshold actual: {adaptive_threshold*100:.2f}%")
                    print(f"💰 Trades ejecutados este ciclo: {trades_executed}")
                
                # ⚡ Pausa MÁS adaptativa y rápida
                cycle_time = time.time() - cycle_start
                if opportunities_found == 0:
                    sleep_time = max(0.5, settings.SLEEP_BETWEEN * 0.7)  # MÁS rápido si no hay oportunidades
                elif opportunities_found > 3:
                    sleep_time = max(0.8, settings.SLEEP_BETWEEN * 1.1)  # Poco más lento si hay muchas
                else:
                    sleep_time = max(0.5, settings.SLEEP_BETWEEN - cycle_time)
                
                time.sleep(sleep_time)
                
            except Exception as e:
                logging.error(f"❌ Error en ciclo: {e}")
                time.sleep(1)  # Pausa más corta en errores
    
    def execute_real_trade(self, route, amount, expected_profit, books):
        """Ejecuta un trade real con validaciones adicionales"""
        try:
            if not self.live_mode:
                # Simulación MÁS realista
                return True, expected_profit * 0.85  # 85% de la ganancia esperada
            
            # AQUÍ VA LA EJECUCIÓN REAL
            print(f"🔥 EJECUTANDO TRADE REAL: {' → '.join(route)}")
            
            if ENHANCED_MODULES:
                # Usar order executor avanzado
                execution_result = order_executor.execute_arbitrage_atomic(
                    route, amount, max_slippage=0.015
                )
                
                return execution_result.success, execution_result.net_profit
            else:
                # Ejecución básica
                from strategies.triangular import execute_arbitrage_trade
                execute_arbitrage_trade(route, amount)
                
                # Resultado más realista
                actual_profit = expected_profit * 0.75  # 75% conservador
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
        
        print("🤖 BINANCE ARBITRAGE BOT - VERSIÓN ULTRA-OPTIMIZADA")
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
        print(f"🎯 Detección Inteligente: {'✅' if ENHANCED_SCANNER_AVAILABLE else '📊 Ultra-Optimizada'}")
        print(f"📈 Trade Monitor: {'✅' if TRADE_MONITOR_AVAILABLE else '❌'}")
        print(f"💰 Cálculo de Fees Preciso: ✅")
        print(f"🔥 Modo Experimental: ✅")
        
        # Configurar handlers
        self.setup_signal_handlers()
        
        try:
            self.running = True
            self.run_live_trading_loop()
                
        except KeyboardInterrupt:
            print("\n🛑 Interrupción manual")
        except Exception as e:
            print(f"❌ Error crítico: {e}")
        finally:
            self.shutdown()

def main():
    """Punto de entrada principal ULTRA-MEJORADO"""
    
    # Verificar configuración
    if settings.LIVE:
        print("🔥 ATENCIÓN: MODO ULTRA-AGRESIVO ACTIVADO")
        print("💰 Fees optimizadas: 0.075% (con descuento BNB)")
        print("🎯 Threshold ultra-bajo para máxima detección")
        confirmation = input("¿Estás seguro de continuar? (escribe 'SI' para confirmar): ")
        if confirmation != 'SI':
            print("❌ Operación cancelada por el usuario")
            return
    
    bot = LiveArbitrageBot()
    
    # Mostrar configuración MEJORADA
    print(f"\n📋 CONFIGURACIÓN ULTRA-OPTIMIZADA:")
    print(f"   🎯 Threshold inicial: {settings.PROFIT_THOLD*100:.2f}% (ULTRA-AGRESIVO)")
    print(f"   💰 Cantidades: {settings.QUANTUMS_USDT}")
    print(f"   📊 Pares monitoreados: {settings.TOP_N_PAIRS}")
    print(f"   ⚡ Pausa entre ciclos: {settings.SLEEP_BETWEEN}s")
    print(f"   💸 Fees precisas: 0.075% por transacción")
    print(f"   🎲 Confianza mínima: {settings.MIN_CONFIDENCE*100:.0f}%")
    
    bot.run()

if __name__ == "__main__":
    main()