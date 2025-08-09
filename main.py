# binance_arbitrage_bot/main.py

import signal
import sys
import time
import logging
from core.logger import setup_logger
from services import scanner

# Intentar importar módulos mejorados (opcional)
try:
    from binance_api.fee_manager import fee_manager
    FEE_MANAGER_AVAILABLE = True
    print("✅ Fee manager disponible")
except ImportError:
    FEE_MANAGER_AVAILABLE = False
    print("⚠️ Fee manager no disponible - usando fees por defecto")

try:
    from detection.liquidity_analyzer import liquidity_analyzer
    LIQUIDITY_ANALYZER_AVAILABLE = True
    print("✅ Liquidity analyzer disponible")
except ImportError:
    LIQUIDITY_ANALYZER_AVAILABLE = False
    print("⚠️ Liquidity analyzer no disponible")

try:
    from risk_management.risk_calculator import risk_calculator
    RISK_CALCULATOR_AVAILABLE = True
    print("✅ Risk calculator disponible")
except ImportError:
    RISK_CALCULATOR_AVAILABLE = False
    print("⚠️ Risk calculator no disponible")

try:
    from binance_api.order_executor import order_executor
    ORDER_EXECUTOR_AVAILABLE = True
    print("✅ Order executor disponible")
except ImportError:
    ORDER_EXECUTOR_AVAILABLE = False
    print("⚠️ Order executor no disponible")

try:
    from detection.opportunity_scanner import opportunity_scanner
    OPPORTUNITY_SCANNER_AVAILABLE = True
    print("✅ Opportunity scanner disponible")
except ImportError:
    OPPORTUNITY_SCANNER_AVAILABLE = False
    print("⚠️ Opportunity scanner no disponible")

try:
    from analytics.performance_analyzer import performance_analyzer
    PERFORMANCE_ANALYZER_AVAILABLE = True
    print("✅ Performance analyzer disponible")
except ImportError:
    PERFORMANCE_ANALYZER_AVAILABLE = False
    print("⚠️ Performance analyzer no disponible")

# WebSocket deshabilitado temporalmente hasta corregir el error
WEBSOCKET_AVAILABLE = False

class ArbitrageBot:
    def __init__(self):
        self.running = False
        
    def verify_api_configuration(self):
        """Verifica que las API keys estén configuradas correctamente"""
        try:
            from binance_api.client import client, API_KEY, API_SECRET
            
            # Verificar que no sean los valores por defecto
            if not API_KEY or not API_SECRET or API_KEY == "tu_api_key":
                logging.error("❌ API Keys no configuradas correctamente")
                logging.error("   Por favor actualiza tu archivo .env con tus claves reales de Binance")
                return False
            
            # Probar conexión básica
            try:
                server_time = client.get_server_time()
                logging.info(f"✅ Conexión con Binance exitosa")
                return True
            except Exception as e:
                logging.error(f"❌ Error conectando con Binance: {e}")
                if "IP" in str(e):
                    logging.error("   💡 Solución: Añade tu IP a la whitelist de Binance")
                elif "Timestamp" in str(e):
                    logging.error("   💡 Solución: Sincroniza la hora de tu sistema")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error verificando configuración: {e}")
            return False
    
    def initialize_enhanced_features(self):
        """Inicializa características mejoradas disponibles"""
        improvements_active = []
        
        # 1. Fee Manager (con manejo de errores mejorado)
        if FEE_MANAGER_AVAILABLE:
            try:
                logging.info("💰 Inicializando gestión de comisiones...")
                
                # Verificar conexión API primero
                from binance_api.client import client
                try:
                    account = client.get_account()
                    logging.info("✅ API Keys funcionando correctamente")
                except Exception as api_error:
                    logging.warning(f"⚠️ Error de API: {api_error}")
                    logging.warning("   Continuando sin fee manager personalizado")
                    return len(improvements_active) > 0
                
                fee_manager.refresh_fees()
                fee_analysis = fee_manager.get_fee_analysis()
                
                if fee_analysis.get('user_vip_tier') is not None:
                    logging.info(f"📊 Usuario VIP Tier: {fee_analysis['user_vip_tier']}")
                    logging.info(f"💳 Descuento BNB: {'Activo' if fee_analysis['bnb_discount_active'] else 'Inactivo'}")
                    logging.info(f"📈 Comisión actual: {fee_analysis['current_taker_fee']*100:.3f}%")
                    improvements_active.append("Fee Manager")
                
            except Exception as e:
                logging.warning(f"⚠️ Fee manager no completamente funcional: {e}")
        
        # 2. Risk Calculator (con manejo de errores mejorado)
        if RISK_CALCULATOR_AVAILABLE:
            try:
                logging.info("🛡️ Inicializando gestión de riesgos...")
                risk_summary = risk_calculator.get_risk_summary()
                
                if risk_summary.get('available_capital', 0) > 0:
                    logging.info(f"💵 Capital disponible: {risk_summary['available_capital']:.2f} USDT")
                    logging.info(f"📊 Riesgo diario usado: {risk_summary['daily_risk_used_pct']:.1f}%")
                    logging.info(f"💼 Tamaño máximo de posición: {risk_summary['max_position_size']:.2f} USDT")
                    improvements_active.append("Risk Calculator")
                else:
                    logging.warning("⚠️ Risk calculator en modo conservador")
                    improvements_active.append("Risk Calculator (Limitado)")
                    
            except Exception as e:
                logging.warning(f"⚠️ Risk calculator limitado: {e}")
        
        # 3. Performance Analyzer
        if PERFORMANCE_ANALYZER_AVAILABLE:
            try:
                logging.info("📊 Inicializando analizador de rendimiento...")
                performance_analyzer.reset_session(initial_capital=1000.0)
                improvements_active.append("Performance Analyzer")
            except Exception as e:
                logging.warning(f"⚠️ Performance analyzer limitado: {e}")
        
        logging.info(f"🔧 Mejoras activas: {', '.join(improvements_active) if improvements_active else 'Ninguna'}")
        return len(improvements_active) > 0
    
    def setup_signal_handlers(self):
        """Configura manejadores para cierre limpio"""
        def signal_handler(sig, frame):
            logging.info("🛑 Señal de cierre recibida...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def run(self):
        """Ejecuta el bot principal"""
        logging.info("🤖 Iniciando Binance Arbitrage Bot...")
        
        # Configurar manejadores de señales
        self.setup_signal_handlers()
        
        # Verificar configuración API
        if not self.verify_api_configuration():
            logging.error("❌ No se puede continuar sin configuración API válida")
            return
        
        # Intentar inicializar mejoras disponibles
        has_improvements = self.initialize_enhanced_features()
        
        # Mostrar información de inicio
        if OPPORTUNITY_SCANNER_AVAILABLE and ORDER_EXECUTOR_AVAILABLE and has_improvements:
            mode = "🚀 AVANZADO"
        elif has_improvements:
            mode = "⚡ MEJORADO"
        else:
            mode = "📊 BÁSICO"
        
        logging.info("=" * 60)
        logging.info(f"🎯 BOT INICIADO - Modo: {mode} | Datos: 🔄 REST API")
        logging.info("=" * 60)
        
        try:
            self.running = True
            
            # Usar scanner apropiado
            if OPPORTUNITY_SCANNER_AVAILABLE and has_improvements:
                self.run_advanced_scanner()
            elif has_improvements:
                self.run_improved_scanner()
            else:
                # Usar scanner original
                logging.info("📊 Usando scanner original")
                scanner.run()
                
        except KeyboardInterrupt:
            logging.info("🛑 Interrupción por teclado")
        except Exception as e:
            logging.error(f"❌ Error crítico: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.shutdown()
    
    def run_advanced_scanner(self):
        """Scanner avanzado con opportunity scanner"""
        from binance_api import market_data
        from config import settings
        from strategies.triangular import fetch_symbol_filters
        
        # Inicializar
        fetch_symbol_filters()
        
        # Reset de riesgo diario
        if RISK_CALCULATOR_AVAILABLE:
            import datetime
            last_reset = getattr(self, 'last_reset_date', None)
            today = datetime.date.today()
            
            if last_reset != today:
                try:
                    risk_calculator.reset_daily_risk()
                    self.last_reset_date = today
                    logging.info("🔄 Nuevo día - riesgo diario reseteado")
                except:
                    pass
        
        # Obtener información inicial
        sym_map = market_data.exchange_map()
        valid_symbols = set(sym_map.keys())
        
        # Contadores
        cycles_completed = 0
        opportunities_found = 0
        trades_executed = 0
        
        while self.running:
            cycle_start = time.time()
            
            try:
                # Obtener símbolos y monedas
                symbols = market_data.top_volume_symbols(settings.TOP_N_PAIRS)
                coins = {c for s in symbols if s in sym_map for c in sym_map[s]}
                coins.discard(settings.BASE_ASSET)
                
                # Obtener libros de órdenes
                books = market_data.depth_snapshots(symbols)
                
                # Buscar oportunidades con scanner avanzado
                opportunities = opportunity_scanner.scan_opportunities(
                    symbols, books, valid_symbols, coins
                )
                
                cycles_completed += 1
                opportunities_found += len(opportunities)
                
                logging.info(f"▶️ Ciclo {cycles_completed} - Monedas: {len(coins)} | Oportunidades: {len(opportunities)}")
                
                cycle_trades = 0
                
                # Evaluar top oportunidades
                for opportunity in opportunities[:2]:  # Top 2
                    try:
                        # Análisis de liquidez
                        if LIQUIDITY_ANALYZER_AVAILABLE:
                            liquidity_analysis = liquidity_analyzer.analyze_route_liquidity(
                                opportunity.route, opportunity.amount, books
                            )
                            
                            if not liquidity_analysis['is_viable']:
                                logging.debug(f"❌ Oportunidad rechazada por liquidez")
                                continue
                        
                        # Análisis de riesgo
                        optimal_amount = opportunity.amount
                        if RISK_CALCULATOR_AVAILABLE:
                            try:
                                risk_metrics = risk_calculator.calculate_risk_metrics(
                                    opportunity.route, opportunity.amount, 
                                    opportunity.expected_profit, books
                                )
                                
                                should_execute, reason = risk_calculator.should_execute_trade(risk_metrics)
                                if not should_execute:
                                    logging.debug(f"❌ Trade rechazado: {reason}")
                                    continue
                                
                                optimal_amount = min(risk_metrics.recommended_position_size, opportunity.amount)
                            except:
                                pass
                        
                        logging.info(
                            f"💰 OPORTUNIDAD: {' → '.join(opportunity.route)}\n"
                            f"   💵 Cantidad: {optimal_amount:.2f} USDT\n"
                            f"   📈 Ganancia esperada: +{opportunity.expected_profit:.4f} USDT\n"
                            f"   🎯 Confianza: {opportunity.confidence_score:.1%}"
                        )
                        
                        if settings.LIVE:
                            if ORDER_EXECUTOR_AVAILABLE:
                                # Usar executor avanzado
                                try:
                                    execution_result = order_executor.execute_arbitrage_atomic(
                                        opportunity.route, optimal_amount, max_slippage=0.02
                                    )
                                    
                                    if execution_result.success:
                                        cycle_trades += 1
                                        trades_executed += 1
                                        
                                        logging.info(f"✅ Trade exitoso: +{execution_result.net_profit:.4f} USDT")
                                        
                                        # Registrar en performance analyzer
                                        if PERFORMANCE_ANALYZER_AVAILABLE:
                                            try:
                                                performance_analyzer.record_trade(
                                                    route=execution_result.route,
                                                    initial_amount=execution_result.initial_amount,
                                                    final_amount=execution_result.final_amount,
                                                    execution_time=execution_result.execution_time,
                                                    fees_paid=execution_result.total_fees,
                                                    confidence_score=opportunity.confidence_score,
                                                    risk_score=opportunity.risk_score
                                                )
                                            except:
                                                pass
                                    else:
                                        logging.error(f"❌ Error en trade: {execution_result.error_message}")
                                except Exception as e:
                                    logging.error(f"❌ Error en order executor: {e}")
                                    # Fallback a método básico
                                    from strategies.triangular import execute_arbitrage_trade
                                    execute_arbitrage_trade(opportunity.route, optimal_amount)
                                    cycle_trades += 1
                            else:
                                # Método básico
                                from strategies.triangular import execute_arbitrage_trade
                                execute_arbitrage_trade(opportunity.route, optimal_amount)
                                cycle_trades += 1
                        else:
                            logging.info("📝 Modo simulación")
                    
                    except Exception as e:
                        logging.error(f"❌ Error procesando oportunidad: {e}")
                        continue
                
                # Estadísticas cada 10 ciclos
                if cycles_completed % 10 == 0:
                    avg_opportunities = opportunities_found / cycles_completed
                    success_rate = (trades_executed / max(opportunities_found, 1)) * 100
                    
                    logging.info("📊 ESTADÍSTICAS:")
                    logging.info(f"   🔄 Ciclos: {cycles_completed}")
                    logging.info(f"   🎯 Oportunidades/ciclo: {avg_opportunities:.1f}")
                    logging.info(f"   ✅ Trades: {trades_executed} | 📈 Éxito: {success_rate:.1f}%")
                
                # Pausa entre ciclos
                cycle_time = time.time() - cycle_start
                sleep_time = max(0, settings.SLEEP_BETWEEN - cycle_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logging.error(f"❌ Error en ciclo avanzado: {e}")
                time.sleep(1)
    
    def run_improved_scanner(self):
        """Scanner mejorado básico"""
        from binance_api import market_data
        from config import settings
        from itertools import combinations
        from strategies.triangular import (
            simulate_route_gain,
            execute_arbitrage_trade,
            fetch_symbol_filters,
            hourly_interest
        )
        
        # Inicializar
        fetch_symbol_filters()
        sym_map = market_data.exchange_map()
        valid_symbols = set(sym_map.keys())
        
        # Contadores
        cycles_completed = 0
        opportunities_found = 0
        trades_executed = 0
        
        while self.running:
            cycle_start = time.time()
            
            try:
                # Obtener datos de mercado
                symbols = market_data.top_volume_symbols(settings.TOP_N_PAIRS)
                coins = {c for s in symbols if s in sym_map for c in sym_map[s]}
                coins.discard(settings.BASE_ASSET)
                
                books = market_data.depth_snapshots(symbols)
                
                logging.info(f"▶️ Ciclo {cycles_completed + 1} - Monedas: {len(coins)} | Books: {len(books)}")
                
                cycle_opportunities = 0
                cycle_trades = 0
                
                # Buscar oportunidades básicas
                for hops in (3, 4):
                    for combo in combinations(coins, hops - 1):
                        if not self.running:
                            break
                            
                        route = [settings.BASE_ASSET] + list(combo) + [settings.BASE_ASSET]
                        
                        for usdt_amt in settings.QUANTUMS_USDT:
                            # Análisis básico
                            final_qty = simulate_route_gain(route, usdt_amt, books, valid_symbols)
                            if final_qty == 0:
                                continue
                            
                            factor = final_qty / usdt_amt
                            hours = max(1, round(settings.HOLD_SECONDS / 3600))
                            factor_eff = factor * (1 - hourly_interest(settings.BASE_ASSET) * hours)
                            net_gain = factor_eff - 1
                            expected_profit = usdt_amt * net_gain
                            
                            if net_gain > settings.PROFIT_THOLD:
                                cycle_opportunities += 1
                                
                                logging.info(
                                    f"💰 OPORTUNIDAD: {' → '.join(route)}\n"
                                    f"   💵 Cantidad: {usdt_amt:.2f} USDT\n"
                                    f"   📈 Ganancia: +{expected_profit:.4f} USDT ({net_gain*100:.3f}%)"
                                )
                                
                                if settings.LIVE:
                                    logging.info("🟢 Ejecutando arbitraje...")
                                    execute_arbitrage_trade(route, usdt_amt)
                                    cycle_trades += 1
                                else:
                                    logging.info("📝 Modo simulación")
                
                # Estadísticas
                cycles_completed += 1
                opportunities_found += cycle_opportunities
                trades_executed += cycle_trades
                
                cycle_time = time.time() - cycle_start
                
                # Log cada 5 ciclos
                if cycles_completed % 5 == 0:
                    avg_opps = opportunities_found / cycles_completed
                    success_rate = (trades_executed / max(opportunities_found, 1)) * 100
                    
                    logging.info("📊 RESUMEN:")
                    logging.info(f"   🔄 Ciclos: {cycles_completed}")
                    logging.info(f"   🎯 Oportunidades/ciclo: {avg_opps:.1f}")
                    logging.info(f"   ✅ Trades: {trades_executed} | 📈 Éxito: {success_rate:.1f}%")
                
                # Pausa
                sleep_time = max(0, settings.SLEEP_BETWEEN - cycle_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logging.error(f"❌ Error en ciclo: {e}")
                time.sleep(1)
    
    def shutdown(self):
        """Cierre limpio"""
        logging.info("🛑 Cerrando bot...")
        self.running = False
        logging.info("👋 Bot cerrado limpiamente")

def main():
    """Función principal"""
    setup_logger()
    
    bot = ArbitrageBot()
    bot.run()

if __name__ == "__main__":
    main()