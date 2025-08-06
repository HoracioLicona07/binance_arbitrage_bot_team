# binance_arbitrage_bot/main.py

import signal
import sys
import time
import logging
from core.logger import setup_logger
from services import scanner

# Intentar importar módulos mejorados (opcional)
try:
    from binance_api.websocket_manager import websocket_manager
    WEBSOCKET_AVAILABLE = True
    logging.info("✅ WebSocket manager disponible")
except ImportError:
    WEBSOCKET_AVAILABLE = False
    logging.info("⚠️ WebSocket manager no disponible - usando REST API")

try:
    from binance_api.fee_manager import fee_manager
    FEE_MANAGER_AVAILABLE = True
    logging.info("✅ Fee manager disponible")
except ImportError:
    FEE_MANAGER_AVAILABLE = False
    logging.info("⚠️ Fee manager no disponible - usando fees por defecto")

try:
    from detection.liquidity_analyzer import liquidity_analyzer
    LIQUIDITY_ANALYZER_AVAILABLE = True
    logging.info("✅ Liquidity analyzer disponible")
except ImportError:
    LIQUIDITY_ANALYZER_AVAILABLE = False
    logging.info("⚠️ Liquidity analyzer no disponible")

try:
    from risk_management.risk_calculator import risk_calculator
    RISK_CALCULATOR_AVAILABLE = True
    logging.info("✅ Risk calculator disponible")
except ImportError:
    RISK_CALCULATOR_AVAILABLE = False
    logging.info("⚠️ Risk calculator no disponible")

# Determinar modo de operación
ENHANCED_MODE = all([
    WEBSOCKET_AVAILABLE,
    FEE_MANAGER_AVAILABLE, 
    LIQUIDITY_ANALYZER_AVAILABLE,
    RISK_CALCULATOR_AVAILABLE
])

class ArbitrageBot:
    def __init__(self):
        self.running = False
        self.websocket_active = False
        
    def initialize_enhanced_features(self):
        """Inicializa características mejoradas disponibles"""
        improvements_active = []
        
        # 1. Fee Manager
        if FEE_MANAGER_AVAILABLE:
            try:
                logging.info("💰 Inicializando gestión de comisiones...")
                fee_manager.refresh_fees()
                fee_analysis = fee_manager.get_fee_analysis()
                logging.info(f"📊 Usuario VIP Tier: {fee_analysis['user_vip_tier']}")
                logging.info(f"💳 Descuento BNB: {'Activo' if fee_analysis['bnb_discount_active'] else 'Inactivo'}")
                logging.info(f"📈 Comisión actual: {fee_analysis['current_taker_fee']*100:.3f}%")
                improvements_active.append("Fee Manager")
                
                # Mostrar consejos de optimización
                optimization_tips = fee_analysis.get('optimization_tips', [])
                if optimization_tips:
                    logging.info("💡 Consejos de optimización:")
                    for tip in optimization_tips[:2]:
                        logging.info(f"   {tip}")
            except Exception as e:
                logging.error(f"❌ Error inicializando fee manager: {e}")
        
        # 2. Risk Calculator
        if RISK_CALCULATOR_AVAILABLE:
            try:
                logging.info("🛡️ Inicializando gestión de riesgos...")
                risk_summary = risk_calculator.get_risk_summary()
                logging.info(f"💵 Capital disponible: {risk_summary['available_capital']:.2f} USDT")
                logging.info(f"📊 Riesgo diario usado: {risk_summary['daily_risk_used_pct']:.1f}%")
                logging.info(f"💼 Tamaño máximo de posición: {risk_summary['max_position_size']:.2f} USDT")
                improvements_active.append("Risk Calculator")
            except Exception as e:
                logging.error(f"❌ Error inicializando risk calculator: {e}")
        
        # 3. WebSocket Manager
        if WEBSOCKET_AVAILABLE:
            try:
                from binance_api import market_data
                from config import settings
                
                logging.info("🌐 Iniciando streams WebSocket...")
                symbols = market_data.top_volume_symbols(30)  # Reducido para pruebas
                websocket_manager.start(symbols)
                
                time.sleep(1)  # Esperar conexión
                
                status = websocket_manager.get_connection_status()
                connected_streams = sum(1 for s in status.values() if s == 'connected')
                
                if connected_streams > 0:
                    logging.info(f"✅ WebSocket conectado - {connected_streams} streams activos")
                    self.websocket_active = True
                    improvements_active.append("WebSocket")
                else:
                    logging.warning("⚠️ WebSocket no se conectó - usando REST API")
            except Exception as e:
                logging.error(f"❌ Error iniciando WebSocket: {e}")
        
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
        
        # Intentar inicializar mejoras disponibles
        has_improvements = self.initialize_enhanced_features()
        
        # Mostrar información de inicio
        if ENHANCED_MODE:
            mode = "🚀 COMPLETO"
        elif has_improvements:
            mode = "⚡ PARCIAL"
        else:
            mode = "📊 BÁSICO"
        
        ws_status = "🌐 WebSocket" if self.websocket_active else "🔄 REST API"
        
        logging.info("=" * 60)
        logging.info(f"🎯 BOT INICIADO - Modo: {mode} | Datos: {ws_status}")
        logging.info("=" * 60)
        
        try:
            self.running = True
            
            # Usar scanner apropiado
            if has_improvements:
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
    
    def run_improved_scanner(self):
        """Scanner con algunas mejoras disponibles"""
        from binance_api import market_data
        from config import settings
        from itertools import combinations
        from strategies.triangular import (
            simulate_route_gain,
            execute_arbitrage_trade,
            fetch_symbol_filters,
            hourly_interest
        )
        
        # Reset de riesgo diario si está disponible
        if RISK_CALCULATOR_AVAILABLE:
            import datetime
            last_reset = getattr(self, 'last_reset_date', None)
            today = datetime.date.today()
            
            if last_reset != today:
                risk_calculator.reset_daily_risk()
                self.last_reset_date = today
                logging.info("🔄 Nuevo día - riesgo diario reseteado")
        
        # Inicializar filtros de símbolos
        fetch_symbol_filters()
        
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
                if self.websocket_active and WEBSOCKET_AVAILABLE:
                    books = websocket_manager.get_all_orderbooks()
                    # Completar con REST API si es necesario
                    missing_symbols = [s for s in symbols if s not in books]
                    if missing_symbols:
                        rest_books = market_data.depth_snapshots(missing_symbols[:20])  # Limitar
                        books.update(rest_books)
                else:
                    books = market_data.depth_snapshots(symbols)
                
                logging.info(f"▶️ Ciclo {cycles_completed + 1} - Monedas: {len(coins)} | Books: {len(books)}")
                
                cycle_opportunities = 0
                cycle_trades = 0
                
                # Buscar oportunidades
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
                                
                                # Análisis mejorado si está disponible
                                should_execute = True
                                optimal_amount = usdt_amt
                                rejection_reason = ""
                                
                                # Análisis de liquidez si está disponible
                                if LIQUIDITY_ANALYZER_AVAILABLE:
                                    try:
                                        liquidity_analysis = liquidity_analyzer.analyze_route_liquidity(
                                            route, usdt_amt, books
                                        )
                                        
                                        if not liquidity_analysis['is_viable']:
                                            should_execute = False
                                            rejection_reason = f"Liquidez insuficiente: {', '.join(liquidity_analysis.get('risk_factors', []))}"
                                    except Exception as e:
                                        logging.debug(f"Error en análisis de liquidez: {e}")
                                
                                # Análisis de riesgo si está disponible
                                if should_execute and RISK_CALCULATOR_AVAILABLE:
                                    try:
                                        risk_metrics = risk_calculator.calculate_risk_metrics(
                                            route, usdt_amt, expected_profit, books
                                        )
                                        
                                        should_execute, rejection_reason = risk_calculator.should_execute_trade(risk_metrics)
                                        if should_execute:
                                            optimal_amount = min(risk_metrics.recommended_position_size, usdt_amt)
                                    except Exception as e:
                                        logging.debug(f"Error en análisis de riesgo: {e}")
                                
                                # Ejecutar o reportar
                                if should_execute:
                                    logging.info(
                                        f"💰 OPORTUNIDAD: {' → '.join(route)}\n"
                                        f"   💵 Cantidad: {optimal_amount:.2f} USDT\n"
                                        f"   📈 Ganancia: +{expected_profit:.4f} USDT ({net_gain*100:.3f}%)"
                                    )
                                    
                                    if settings.LIVE:
                                        logging.info("🟢 Ejecutando arbitraje...")
                                        execute_arbitrage_trade(route, optimal_amount)
                                        
                                        # Actualizar riesgo si está disponible
                                        if RISK_CALCULATOR_AVAILABLE:
                                            risk_calculator.update_daily_risk(optimal_amount)
                                        
                                        cycle_trades += 1
                                    else:
                                        logging.info("📝 Modo simulación")
                                else:
                                    logging.debug(f"❌ Rechazado: {rejection_reason}")
                
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
                    logging.info(f"   🔄 Ciclos: {cycles_completed} | ⏱️ Tiempo: {cycle_time:.2f}s")
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
        
        if WEBSOCKET_AVAILABLE and self.websocket_active:
            try:
                websocket_manager.stop()
                logging.info("✅ WebSocket cerrado")
            except Exception as e:
                logging.error(f"❌ Error cerrando WebSocket: {e}")
        
        logging.info("👋 Bot cerrado limpiamente")

def main():
    """Función principal"""
    setup_logger()
    
    bot = ArbitrageBot()
    bot.run()

if __name__ == "__main__":
    main()