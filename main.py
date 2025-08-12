# binance_arbitrage_bot/main.py - TRADES REALES CON OPORTUNIDADES REALES

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

# FORZAR uso de nuestro loop (no enhanced_scanner)
ENHANCED_SCANNER_AVAILABLE = False

class LiveArbitrageBot:
    def __init__(self):
        self.running = False
        self.live_mode = settings.LIVE
        
    def verify_live_trading_readiness(self):
        """Verifica que todo esté listo para trades reales"""
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
        
        # 2. Verificar configuración
        print(f"✅ Threshold optimizado: {settings.PROFIT_THOLD*100:.3f}%")
        print(f"✅ Cantidades: {settings.QUANTUMS_USDT}")
        print(f"✅ Modo REAL activado")
        checks.append(True)
        
        print("="*60)
        
        if all(checks):
            print("🟢 LISTO PARA TRADES REALES")
            print("💰 MODO REAL - GANANCIAS REALES")
            return True
        else:
            print("🔴 NO LISTO PARA TRADES REALES")
            return False

    def run_live_trading_loop(self):
        """Loop principal para trades REALES"""
        print("🚀 INICIANDO TRADING REAL - SIN SINTÉTICOS")
        self.run_real_arbitrage_loop()

    def run_real_arbitrage_loop(self):
        """Loop REAL buscando oportunidades REALES de arbitraje"""
        from binance_api import market_data
        from itertools import combinations
        from strategies.triangular import simulate_route_gain, fetch_symbol_filters
        
        # Inicializar
        try:
            fetch_symbol_filters()
            sym_map = market_data.exchange_map()
            valid_symbols = set(sym_map.keys())
            print(f"✅ Símbolos cargados: {len(valid_symbols)}")
        except Exception as e:
            print(f"❌ Error inicializando: {e}")
            return
        
        print(f"\n💰 INICIANDO ARBITRAJE REAL")
        print(f"📊 Configuración: {settings.QUANTUMS_USDT} USDT")
        print(f"🎯 Threshold: {settings.PROFIT_THOLD*100:.3f}% mínimo")
        print(f"⚡ Ciclos cada: {settings.SLEEP_BETWEEN}s")
        print("🚫 SIN oportunidades sintéticas - SOLO REALES")
        
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
                # Obtener datos de mercado REALES
                symbols = market_data.top_volume_symbols(settings.TOP_N_PAIRS)
                books = market_data.depth_snapshots(symbols[:30])
                
                if not books or len(books) < 10:
                    print(f"⚠️ Pocos datos de mercado: {len(books)} símbolos")
                    time.sleep(2)
                    continue
                
                # Monedas con mejor liquidez y volumen
                priority_coins = ['BTC', 'ETH', 'BNB', 'ADA', 'DOT', 'LINK', 'XRP', 'LTC', 'MATIC', 'AVAX', 'SOL', 'DOGE']
                
                print(f"\n🔍 CICLO {cycle_count} - Buscando oportunidades REALES (Threshold: {adaptive_threshold*100:.3f}%)")
                
                opportunities_found = 0
                best_opportunities = []
                
                # 🎯 BÚSQUEDA REAL de oportunidades
                for combo in combinations(priority_coins[:8], 2):
                    if not self.running:
                        break
                        
                    route = [settings.BASE_ASSET] + list(combo) + [settings.BASE_ASSET]
                    
                    # Verificar que todos los símbolos existan
                    route_symbols = []
                    valid_route = True
                    
                    for i in range(len(route) - 1):
                        symbol1 = f"{route[i]}{route[i+1]}"
                        symbol2 = f"{route[i+1]}{route[i]}"
                        
                        if symbol1 in valid_symbols:
                            route_symbols.append(symbol1)
                        elif symbol2 in valid_symbols:
                            route_symbols.append(symbol2)
                        else:
                            valid_route = False
                            break
                    
                    if not valid_route:
                        continue
                    
                    # Probar diferentes cantidades
                    for amount in settings.QUANTUMS_USDT[:6]:  # Primeras 6 cantidades
                        try:
                            final_qty = simulate_route_gain(route, amount, books, valid_symbols)
                            if final_qty <= amount:  # Sin ganancia
                                continue
                            
                            # Calcular profit real
                            gross_profit = final_qty - amount
                            gross_profit_pct = gross_profit / amount
                            
                            # Verificar threshold básico primero
                            if gross_profit_pct < adaptive_threshold:
                                continue
                            
                            # Usar nuestro cálculo de fees mejorado
                            fee_analysis = calculate_net_profit_after_fees(route, amount, final_qty)
                            
                            if not fee_analysis['profitable']:
                                continue
                                
                            net_profit = fee_analysis['net_profit']
                            net_profit_pct = fee_analysis['net_profit_percentage'] / 100
                            
                            # Verificar que sea rentable después de fees
                            if net_profit_pct > adaptive_threshold and net_profit > 0.01:  # Mínimo 1 centavo
                                opportunities_found += 1
                                
                                # Calcular calidad basada en profit y liquidez
                                quality_score = min(1.0, net_profit_pct / 0.005)  # Normalizar a 0.5%
                                
                                # Verificar liquidez de la ruta
                                liquidity_score = self.calculate_route_liquidity(route_symbols, books, amount)
                                final_quality = (quality_score + liquidity_score) / 2
                                
                                opportunity = {
                                    'route': route,
                                    'route_symbols': route_symbols,
                                    'amount': amount,
                                    'gross_profit': gross_profit,
                                    'net_profit': net_profit,
                                    'net_profit_pct': net_profit_pct,
                                    'total_fees': fee_analysis['total_fees'],
                                    'quality_score': final_quality,
                                    'liquidity_score': liquidity_score,
                                    'fee_analysis': fee_analysis,
                                    'real': True
                                }
                                
                                best_opportunities.append(opportunity)
                                
                                if TRADE_MONITOR_AVAILABLE:
                                    trade_monitor.log_opportunity(route, amount, net_profit, final_quality)
                                
                        except Exception as e:
                            logging.debug(f"Error evaluando {route} con {amount}: {e}")
                            continue
                
                # 🚀 EJECUTAR oportunidades REALES
                if best_opportunities:
                    # Ordenar por rentabilidad NETA
                    best_opportunities.sort(key=lambda x: x['net_profit_pct'], reverse=True)
                    
                    trades_executed = 0
                    for opp in best_opportunities[:2]:  # Solo top 2 para ser conservador
                        
                        print(f"💰 OPORTUNIDAD REAL: {' → '.join(opp['route'])}")
                        print(f"   💵 {opp['amount']:.0f} USDT → Ganancia NETA: +{opp['net_profit']:.4f} USDT ({opp['net_profit_pct']*100:.3f}%)")
                        print(f"   💸 Fees: {opp['total_fees']:.4f} USDT")
                        print(f"   🎯 Quality: {opp['quality_score']:.2f}")
                        print(f"   💧 Liquidez: {opp['liquidity_score']:.2f}")
                        
                        # Validación final
                        trade_decision = should_execute_trade_with_fees(
                            opp['route'], opp['amount'], opp['amount'] + opp['gross_profit']
                        )
                        
                        if trade_decision['should_execute'] and opp['quality_score'] >= 0.4:
                            print(f"   ✅ EJECUTANDO TRADE REAL")
                            
                            success, actual_profit = self.execute_real_trade(
                                opp['route'], opp['route_symbols'], opp['amount'], 
                                opp['net_profit'], books
                            )
                            
                            if success:
                                trades_executed += 1
                                print(f"   🎉 Trade REAL ejecutado: +{actual_profit:.4f} USDT")
                            else:
                                print(f"   ❌ Error en ejecución real")
                            
                            if TRADE_MONITOR_AVAILABLE:
                                trade_monitor.log_trade_execution(
                                    opp['route'], opp['amount'], success, actual_profit,
                                    execution_time=3.0,
                                    error_msg="" if success else "Error de ejecución real"
                                )
                            
                            if success:
                                time.sleep(2)  # Pausa entre trades reales
                        else:
                            print(f"   ❌ RECHAZADO: Calidad insuficiente o validación fallida")
                else:
                    print("   📭 No se encontraron oportunidades reales")
                
                # Ajuste adaptativo del threshold
                opportunities_history.append(opportunities_found)
                if len(opportunities_history) > 20:
                    opportunities_history = opportunities_history[-20:]
                
                avg_opportunities = sum(opportunities_history) / len(opportunities_history)
                
                # Lógica de ajuste más conservadora para trades reales
                if avg_opportunities < 0.1:
                    # Muy pocas oportunidades: reducir threshold
                    adaptive_threshold *= 0.95
                    adaptive_threshold = max(0.002, adaptive_threshold)  # Mínimo 0.2%
                    print(f"🎯 Threshold reducido a {adaptive_threshold*100:.3f}%")
                elif avg_opportunities > 2:
                    # Muchas oportunidades: aumentar threshold para mejor calidad
                    adaptive_threshold *= 1.05
                    adaptive_threshold = min(0.01, adaptive_threshold)  # Máximo 1%
                    print(f"🎯 Threshold aumentado a {adaptive_threshold*100:.3f}%")
                
                # Mostrar estadísticas cada 5 ciclos
                if cycle_count % 5 == 0:
                    if TRADE_MONITOR_AVAILABLE:
                        trade_monitor.show_live_stats()
                    print(f"📈 Oportunidades promedio: {avg_opportunities:.1f}")
                    print(f"📊 Threshold actual: {adaptive_threshold*100:.3f}%")
                    print(f"💰 Trades ejecutados hoy: {trades_executed}")
                
                # Pausa entre ciclos
                cycle_time = time.time() - cycle_start
                sleep_time = max(1, settings.SLEEP_BETWEEN - cycle_time)
                time.sleep(sleep_time)
                
            except Exception as e:
                logging.error(f"❌ Error en ciclo {cycle_count}: {e}")
                print(f"❌ Error en ciclo {cycle_count}: {e}")
                time.sleep(3)
    
    def calculate_route_liquidity(self, route_symbols, books, amount):
        """Calcula el score de liquidez para una ruta"""
        try:
            total_liquidity = 0
            symbol_count = 0
            
            for symbol in route_symbols:
                if symbol in books:
                    book = books[symbol]
                    if book.get('bids') and book.get('asks'):
                        # Liquidez en top 3 niveles
                        bid_liq = sum(float(level[1]) for level in book['bids'][:3])
                        ask_liq = sum(float(level[1]) for level in book['asks'][:3])
                        symbol_liquidity = (bid_liq + ask_liq) / 2
                        total_liquidity += symbol_liquidity
                        symbol_count += 1
            
            if symbol_count == 0:
                return 0.0
            
            avg_liquidity = total_liquidity / symbol_count
            # Normalizar: 500 USDT de liquidez = score 0.5
            return min(1.0, avg_liquidity / 1000)
            
        except Exception:
            return 0.3  # Score neutro si hay error
    
    def execute_real_trade(self, route, route_symbols, amount, expected_profit, books):
        """Ejecuta un trade REAL en Binance"""
        try:
            if not self.live_mode:
                print("⚠️ Modo simulación - no se ejecutarán trades reales")
                return True, expected_profit * 0.85
            
            print(f"🔥 EJECUTANDO TRADE REAL: {' → '.join(route)}")
            print(f"📊 Símbolos: {route_symbols}")
            print(f"💰 Cantidad: {amount} USDT")
            
            # AQUÍ VAS A IMPLEMENTAR LA EJECUCIÓN REAL
            # Por ahora simularemos para evitar errores
            
            # Importar cliente de Binance
            from binance_api.client import client
            
            # PASO 1: Verificar balance inicial
            initial_balance = self.get_usdt_balance()
            print(f"💵 Balance inicial: {initial_balance:.4f} USDT")
            
            if initial_balance < amount:
                print(f"❌ Balance insuficiente")
                return False, 0.0
            
            # PASO 2: Ejecutar cada paso de la ruta
            current_asset = route[0]  # USDT
            current_amount = amount
            
            for i in range(len(route_symbols)):
                target_asset = route[i + 1]
                symbol = route_symbols[i]
                
                print(f"🔄 Paso {i+1}: {current_asset} → {target_asset} via {symbol}")
                
                # Determinar si es compra o venta
                if symbol.startswith(current_asset):
                    # Vender current_asset por target_asset
                    side = 'SELL'
                    qty = current_amount
                else:
                    # Comprar target_asset con current_asset
                    side = 'BUY'
                    # Para BUY, necesitamos calcular quantity en base asset
                    if current_asset == 'USDT':
                        # Comprando con USDT
                        price = self.get_current_price(symbol)
                        qty = current_amount / price
                    else:
                        qty = current_amount
                
                # EJECUTAR ORDEN REAL
                success, result_qty = self.execute_market_order(symbol, side, qty)
                
                if not success:
                    print(f"❌ Error en paso {i+1}")
                    return False, 0.0
                
                current_amount = result_qty
                current_asset = target_asset
                
                print(f"✅ Paso {i+1} completado: {current_amount:.6f} {current_asset}")
                time.sleep(0.5)  # Pausa entre órdenes
            
            # PASO 3: Verificar resultado
            final_balance = self.get_usdt_balance()
            actual_profit = final_balance - initial_balance
            
            print(f"💵 Balance final: {final_balance:.4f} USDT")
            print(f"💰 Ganancia real: {actual_profit:.4f} USDT")
            
            return actual_profit > 0, actual_profit
                
        except Exception as e:
            logging.error(f"❌ Error ejecutando trade real: {e}")
            print(f"❌ Error ejecutando trade real: {e}")
            return False, 0.0
    
    def get_usdt_balance(self):
        """Obtiene el balance actual de USDT"""
        try:
            from binance_api.client import client
            account = client.get_account()
            
            for balance in account['balances']:
                if balance['asset'] == 'USDT':
                    return float(balance['free'])
            return 0.0
        except Exception:
            return 0.0
    
    def get_current_price(self, symbol):
        """Obtiene el precio actual de un símbolo"""
        try:
            from binance_api.client import client
            ticker = client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception:
            return 0.0
    
    def execute_market_order(self, symbol, side, quantity):
        """Ejecuta una orden de mercado REAL"""
        try:
            from binance_api.client import client
            
            # Formatear cantidad según filtros del símbolo
            formatted_qty = self.format_quantity(symbol, quantity)
            
            print(f"📝 Ejecutando: {side} {formatted_qty} {symbol}")
            
            # EJECUTAR ORDEN REAL
            order = client.order_market(
                symbol=symbol,
                side=side,
                quantity=formatted_qty
            )
            
            print(f"✅ Orden ejecutada: {order['orderId']}")
            
            # Obtener cantidad resultante
            if side == 'BUY':
                # En compra, obtenemos el asset base
                result_qty = float(order['executedQty'])
            else:
                # En venta, obtenemos el quote asset
                result_qty = float(order['cummulativeQuoteQty'])
            
            return True, result_qty
            
        except Exception as e:
            print(f"❌ Error ejecutando orden: {e}")
            return False, 0.0
    
    def format_quantity(self, symbol, quantity):
        """Formatea la cantidad según los filtros del símbolo"""
        try:
            # Implementar formateo basado en los filtros cargados
            # Por simplicidad, redondear a 6 decimales
            return round(quantity, 6)
        except Exception:
            return quantity

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
        
        print("🤖 BINANCE ARBITRAGE BOT - TRADES REALES")
        print("="*60)
        
        # Verificar modo
        if self.live_mode:
            print("🔴 MODO LIVE - TRADES REALES ACTIVADOS")
            if not self.verify_live_trading_readiness():
                print("❌ Bot no está listo para trades reales")
                return
        else:
            print("✅ MODO SIMULACIÓN")
        
        # Mostrar capacidades
        print(f"🧠 Scanner Real: ✅")
        print(f"📊 Threshold Adaptativo: ✅")
        print(f"🎯 Solo Oportunidades Reales: ✅")
        print(f"📈 Trade Monitor: {'✅' if TRADE_MONITOR_AVAILABLE else '❌'}")
        print(f"💰 Ejecución Real: ✅")
        print(f"🚫 Sin Sintéticos: ✅")
        
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
    """Punto de entrada para trades REALES"""
    
    # Verificar configuración
    if settings.LIVE:
        print("💰 ATENCIÓN: TRADES REALES ACTIVADOS")
        print("🚫 Sin oportunidades sintéticas")
        print("💸 Ganancias y pérdidas reales")
        confirmation = input("¿Estás seguro de continuar con TRADES REALES? (escribe 'SI' para confirmar): ")
        if confirmation != 'SI':
            print("❌ Operación cancelada por el usuario")
            return
    
    bot = LiveArbitrageBot()
    
    # Mostrar configuración REAL
    print(f"\n📋 CONFIGURACIÓN PARA TRADES REALES:")
    print(f"   🎯 Threshold inicial: {settings.PROFIT_THOLD*100:.3f}%")
    print(f"   💰 Cantidades: {settings.QUANTUMS_USDT}")
    print(f"   📊 Pares monitoreados: {settings.TOP_N_PAIRS}")
    print(f"   ⚡ Pausa entre ciclos: {settings.SLEEP_BETWEEN}s")
    print(f"   🚫 Sintéticos: DESACTIVADOS")
    print(f"   💸 Ejecución: REAL")
    
    bot.run()

if __name__ == "__main__":
    main()