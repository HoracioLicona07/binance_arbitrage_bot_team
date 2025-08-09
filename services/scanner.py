# binance_arbitrage_bot/services/scanner.py - Versión Mejorada

import time
import logging
from itertools import combinations
from config import settings
from binance_api import market_data
from binance_api.margin import get_valid_margin_pairs
from strategies.triangular import (
    simulate_route_gain,
    execute_arbitrage_trade,
    fetch_symbol_filters,
    hourly_interest
)

# Intentar importar módulos mejorados
try:
    from detection.opportunity_scanner import opportunity_scanner
    OPPORTUNITY_SCANNER_AVAILABLE = True
except ImportError:
    OPPORTUNITY_SCANNER_AVAILABLE = False
    logging.warning("⚠️ Opportunity scanner no disponible - usando scanner básico")

try:
    from binance_api.order_executor import order_executor
    ORDER_EXECUTOR_AVAILABLE = True
except ImportError:
    ORDER_EXECUTOR_AVAILABLE = False
    logging.warning("⚠️ Order executor no disponible - usando ejecución básica")

try:
    from analytics.performance_analyzer import performance_analyzer
    PERFORMANCE_ANALYZER_AVAILABLE = True
except ImportError:
    PERFORMANCE_ANALYZER_AVAILABLE = False
    logging.warning("⚠️ Performance analyzer no disponible")

try:
    from binance_api.websocket_manager import websocket_manager
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

try:
    from detection.liquidity_analyzer import liquidity_analyzer
    LIQUIDITY_ANALYZER_AVAILABLE = True
except ImportError:
    LIQUIDITY_ANALYZER_AVAILABLE = False

try:
    from risk_management.risk_calculator import risk_calculator
    RISK_CALCULATOR_AVAILABLE = True
except ImportError:
    RISK_CALCULATOR_AVAILABLE = False

def run():
    """Función principal del scanner - versión mejorada"""
    # Determinar modo de operación
    enhanced_mode = OPPORTUNITY_SCANNER_AVAILABLE and ORDER_EXECUTOR_AVAILABLE
    
    if enhanced_mode:
        logging.info("🚀 Ejecutando scanner en modo MEJORADO")
        run_enhanced_scanner()
    else:
        logging.info("📊 Ejecutando scanner en modo BÁSICO")
        run_basic_scanner()

def run_enhanced_scanner():
    """Scanner mejorado con todos los módulos avanzados"""
    # Inicialización
    sym_map = market_data.exchange_map()
    valid_symbols = set(sym_map.keys())
    valid_margin_symbols = get_valid_margin_pairs()
    fetch_symbol_filters()
    
    # Configurar performance analyzer
    if PERFORMANCE_ANALYZER_AVAILABLE:
        performance_analyzer.reset_session(initial_capital=1000.0)
    
    # Estadísticas de sesión
    session_stats = {
        'cycles_completed': 0,
        'opportunities_found': 0,
        'trades_executed': 0,
        'total_profit': 0.0,
        'start_time': time.time()
    }
    
    while True:
        cycle_start = time.time()
        
        try:
            # 1. Obtener datos de mercado
            symbols = market_data.top_volume_symbols(settings.TOP_N_PAIRS)
            coins = {c for s in symbols if s in sym_map for c in sym_map[s]}
            coins.discard(settings.BASE_ASSET)
            
            # 2. Obtener libros de órdenes (preferir WebSocket)
            if WEBSOCKET_AVAILABLE:
                books = websocket_manager.get_all_orderbooks()
                # Completar con REST API si es necesario
                missing_symbols = [s for s in symbols if s not in books]
                if missing_symbols:
                    rest_books = market_data.depth_snapshots(missing_symbols[:50])
                    books.update(rest_books)
            else:
                books = market_data.depth_snapshots(symbols)
            
            # 3. Buscar oportunidades con scanner avanzado
            opportunities = opportunity_scanner.scan_opportunities(
                symbols, books, valid_symbols, coins
            )
            
            session_stats['cycles_completed'] += 1
            session_stats['opportunities_found'] += len(opportunities)
            
            logging.info(
                f"▶️ Ciclo {session_stats['cycles_completed']} - "
                f"Monedas: {len(coins)} | Books: {len(books)} | "
                f"Oportunidades: {len(opportunities)}"
            )
            
            # 4. Evaluar y ejecutar las mejores oportunidades
            cycle_trades = 0
            for opportunity in opportunities[:5]:  # Top 5 oportunidades
                try:
                    # Análisis adicional de liquidez si está disponible
                    if LIQUIDITY_ANALYZER_AVAILABLE:
                        liquidity_analysis = liquidity_analyzer.analyze_route_liquidity(
                            opportunity.route, opportunity.amount, books
                        )
                        
                        if not liquidity_analysis['is_viable']:
                            logging.debug(f"❌ Oportunidad rechazada por liquidez: {opportunity.route}")
                            continue
                    
                    # Análisis de riesgo si está disponible
                    if RISK_CALCULATOR_AVAILABLE:
                        risk_metrics = risk_calculator.calculate_risk_metrics(
                            opportunity.route, opportunity.amount, 
                            opportunity.expected_profit, books
                        )
                        
                        should_execute, reason = risk_calculator.should_execute_trade(risk_metrics)
                        if not should_execute:
                            logging.debug(f"❌ Trade rechazado por riesgo: {reason}")
                            continue
                        
                        # Usar tamaño optimizado
                        optimal_amount = risk_metrics.recommended_position_size
                    else:
                        optimal_amount = opportunity.amount
                    
                    # Log de oportunidad aprobada
                    logging.info(
                        f"💰 OPORTUNIDAD APROBADA: {' → '.join(opportunity.route)}\n"
                        f"   💵 Cantidad: {optimal_amount:.2f} USDT\n"
                        f"   📈 Ganancia esperada: +{opportunity.expected_profit:.4f} USDT ({opportunity.profit_percentage*100:.3f}%)\n"
                        f"   🎯 Confianza: {opportunity.confidence_score:.1%}\n"
                        f"   ⏱️ Tiempo estimado: {opportunity.execution_time_estimate:.1f}s\n"
                        f"   📊 Prioridad: {opportunity.priority_score:.2f}"
                    )
                    
                    if settings.LIVE:
                        # Ejecutar con order executor mejorado
                        execution_result = order_executor.execute_arbitrage_atomic(
                            opportunity.route, optimal_amount, max_slippage=0.02
                        )
                        
                        if execution_result.success:
                            cycle_trades += 1
                            session_stats['trades_executed'] += 1
                            session_stats['total_profit'] += execution_result.net_profit
                            
                            logging.info(
                                f"✅ Trade ejecutado exitosamente:\n"
                                f"   💰 Ganancia real: +{execution_result.net_profit:.4f} USDT\n"
                                f"   ⏱️ Tiempo: {execution_result.execution_time:.2f}s\n"
                                f"   💸 Fees: {execution_result.total_fees:.4f} USDT"
                            )
                            
                            # Registrar en performance analyzer
                            if PERFORMANCE_ANALYZER_AVAILABLE:
                                performance_analyzer.record_trade(
                                    route=execution_result.route,
                                    initial_amount=execution_result.initial_amount,
                                    final_amount=execution_result.final_amount,
                                    execution_time=execution_result.execution_time,
                                    fees_paid=execution_result.total_fees,
                                    slippage=0.0,  # TODO: calcular slippage real
                                    confidence_score=opportunity.confidence_score,
                                    risk_score=opportunity.risk_score
                                )
                            
                            # Actualizar riesgo usado
                            if RISK_CALCULATOR_AVAILABLE:
                                risk_calculator.update_daily_risk(optimal_amount)
                        
                        else:
                            logging.error(
                                f"❌ Error ejecutando trade: {execution_result.error_message}"
                            )
                    else:
                        logging.info("📝 Modo simulación - trade no ejecutado")
                
                except Exception as e:
                    logging.error(f"❌ Error procesando oportunidad: {e}")
                    continue
            
            # 5. Estadísticas cada 10 ciclos
            if session_stats['cycles_completed'] % 10 == 0:
                log_session_statistics(session_stats)
            
            # 6. Reporte de rendimiento cada 50 ciclos
            if (PERFORMANCE_ANALYZER_AVAILABLE and 
                session_stats['cycles_completed'] % 50 == 0 and 
                session_stats['trades_executed'] > 0):
                
                try:
                    report = performance_analyzer.generate_performance_report(hours_back=1)
                    logging.info(f"\n{report}")
                except Exception as e:
                    logging.error(f"❌ Error generando reporte: {e}")
            
            # 7. Pausa entre ciclos
            cycle_time = time.time() - cycle_start
            sleep_time = max(0, settings.SLEEP_BETWEEN - cycle_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
                
        except Exception as e:
            logging.error(f"❌ Error en ciclo de scanner mejorado: {e}")
            time.sleep(1)

def run_basic_scanner():
    """Scanner básico - funcionalidad original"""
    sym_map = market_data.exchange_map()
    valid_symbols = set(sym_map.keys())
    valid_margin_symbols = get_valid_margin_pairs()
    
    fetch_symbol_filters()
    
    cycles_completed = 0
    
    while True:
        cycle_start = time.time()
        cycles_completed += 1
        
        try:
            symbols = market_data.top_volume_symbols(settings.TOP_N_PAIRS)
            coins = {c for s in symbols if s in sym_map for c in sym_map[s]}
            coins.discard(settings.BASE_ASSET)
            
            books = market_data.depth_snapshots(symbols)
            logging.info(f"▶️ Ciclo {cycles_completed} - Monedas candidatas: {len(coins)}")
            
            checked = 0
            profitable = 0
            
            for hops in (3, 4):
                for combo in combinations(coins, hops - 1):
                    route = [settings.BASE_ASSET] + list(combo) + [settings.BASE_ASSET]
                    for usdt_amt in settings.QUANTUMS_USDT:
                        final_qty = simulate_route_gain(route, usdt_amt, books, valid_symbols)
                        if final_qty == 0:
                            continue
                        factor = final_qty / usdt_amt
                        hours = max(1, round(settings.HOLD_SECONDS / 3600))
                        factor_eff = factor * (1 - hourly_interest(settings.BASE_ASSET) * hours)
                        net_gain = factor_eff - 1
                        if net_gain > settings.PROFIT_THOLD:
                            profitable += 1
                            logging.info("💰 Ruta %s | size≈%.2f USDT | +%.3f%%",
                                         " → ".join(route), usdt_amt, net_gain * 100)
                            if settings.LIVE:
                                logging.info(f"🟢 Ejecutando arbitraje real para {route}")
                                execute_arbitrage_trade(route, usdt_amt)
                        checked += 1
            
            logging.info("🔎 Rutas evaluadas: %d – rentables: %d", checked, profitable)
            
        except Exception as e:
            logging.error(f"❌ Error en ciclo básico: {e}")
        
        # Pausa
        sleep_time = max(0, settings.SLEEP_BETWEEN - (time.time() - cycle_start))
        if sleep_time > 0:
            time.sleep(sleep_time)

def log_session_statistics(session_stats):
    """Log de estadísticas de sesión"""
    try:
        elapsed_time = time.time() - session_stats['start_time']
        avg_opportunities = session_stats['opportunities_found'] / max(session_stats['cycles_completed'], 1)
        success_rate = (session_stats['trades_executed'] / max(session_stats['opportunities_found'], 1)) * 100
        avg_profit = session_stats['total_profit'] / max(session_stats['trades_executed'], 1)
        
        logging.info("📊 ESTADÍSTICAS DE SESIÓN:")
        logging.info(f"   🔄 Ciclos completados: {session_stats['cycles_completed']}")
        logging.info(f"   ⏱️ Tiempo transcurrido: {elapsed_time/3600:.1f}h")
        logging.info(f"   🎯 Oportunidades encontradas: {session_stats['opportunities_found']}")
        logging.info(f"   📈 Oportunidades/ciclo: {avg_opportunities:.1f}")
        logging.info(f"   ✅ Trades ejecutados: {session_stats['trades_executed']}")
        logging.info(f"   📊 Tasa de éxito: {success_rate:.1f}%")
        logging.info(f"   💰 Ganancia total: {session_stats['total_profit']:.4f} USDT")
        if session_stats['trades_executed'] > 0:
            logging.info(f"   💵 Ganancia promedio: {avg_profit:.4f} USDT/trade")
        
        # Estadísticas adicionales si están disponibles
        if ORDER_EXECUTOR_AVAILABLE:
            executor_stats = order_executor.get_execution_stats()
            logging.info(f"   ⚡ Tiempo promedio ejecución: {executor_stats['avg_execution_time_sec']:.2f}s")
        
        if OPPORTUNITY_SCANNER_AVAILABLE:
            scanner_stats = opportunity_scanner.get_scanner_stats()
            logging.info(f"   🔍 Cache hit rate: {scanner_stats['cache_hit_rate']:.1%}")
        
        if RISK_CALCULATOR_AVAILABLE:
            risk_summary = risk_calculator.get_risk_summary()
            logging.info(f"   🛡️ Riesgo diario usado: {risk_summary['daily_risk_used_pct']:.1f}%")
        
    except Exception as e:
        logging.error(f"❌ Error calculando estadísticas: {e}")

def get_scanner_status():
    """Obtiene estado actual del scanner y módulos disponibles"""
    status = {
        'enhanced_mode': OPPORTUNITY_SCANNER_AVAILABLE and ORDER_EXECUTOR_AVAILABLE,
        'modules': {
            'opportunity_scanner': OPPORTUNITY_SCANNER_AVAILABLE,
            'order_executor': ORDER_EXECUTOR_AVAILABLE,
            'performance_analyzer': PERFORMANCE_ANALYZER_AVAILABLE,
            'websocket_manager': WEBSOCKET_AVAILABLE,
            'liquidity_analyzer': LIQUIDITY_ANALYZER_AVAILABLE,
            'risk_calculator': RISK_CALCULATOR_AVAILABLE
        },
        'active_features': []
    }
    
    # Determinar features activas
    if OPPORTUNITY_SCANNER_AVAILABLE:
        status['active_features'].append('Scanner Avanzado')
    if ORDER_EXECUTOR_AVAILABLE:
        status['active_features'].append('Ejecución Atómica')
    if PERFORMANCE_ANALYZER_AVAILABLE:
        status['active_features'].append('Análisis de Rendimiento')
    if WEBSOCKET_AVAILABLE:
        status['active_features'].append('Datos en Tiempo Real')
    if LIQUIDITY_ANALYZER_AVAILABLE:
        status['active_features'].append('Análisis de Liquidez')
    if RISK_CALCULATOR_AVAILABLE:
        status['active_features'].append('Gestión de Riesgos')
    
    return status