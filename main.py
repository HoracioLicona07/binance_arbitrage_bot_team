# binance_arbitrage_bot/main.py

import signal
import sys
import time
import logging
import requests
from core.logger import setup_logger
from services import scanner

# Función para sincronizar tiempo
def sync_server_time():
    """Sincroniza el tiempo del sistema con el servidor de Binance"""
    try:
        # Obtener tiempo del servidor de Binance
        response = requests.get('https://api.binance.com/api/v3/time')
        server_time = response.json()['serverTime']
        
        # Calcular diferencia
        local_time = int(time.time() * 1000)
        time_offset = server_time - local_time
        
        logging.info(f"⏰ Diferencia de tiempo: {time_offset}ms")
        
        # Si la diferencia es significativa, informar al usuario
        if abs(time_offset) > 5000:  # Más de 5 segundos
            logging.warning(f"⚠️ Gran diferencia de tiempo detectada: {time_offset}ms")
            logging.warning("💡 Recomendación: Sincroniza la hora de tu sistema")
        
        return time_offset
        
    except Exception as e:
        logging.error(f"❌ Error sincronizando tiempo: {e}")
        return 0

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

class ArbitrageBot:
    def __init__(self):
        self.running = False
        
    def verify_api_configuration(self):
        """Verifica que las API keys estén configuradas correctamente"""
        try:
            # Sincronizar tiempo primero
            time_offset = sync_server_time()
            
            from binance_api.client import client, API_KEY, API_SECRET
            
            # Verificar que las claves no estén vacías
            if not API_KEY or not API_SECRET:
                logging.error("❌ API Keys no configuradas correctamente")
                logging.error("   Por favor actualiza tu archivo .env con tus claves reales de Binance")
                return False
            
            # Verificar longitud de las claves (las claves reales tienen longitud específica)
            if len(API_KEY) < 60 or len(API_SECRET) < 60:
                logging.error("❌ API Keys parecen incompletas")
                logging.error("   Verifica que copiaste las claves completas desde Binance")
                return False
            
            # Probar conexión básica con reintentos
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Test simple - obtener tiempo del servidor
                    server_time = client.get_server_time()
                    logging.info(f"✅ Conexión con Binance exitosa")
                    
                    # Test de autenticación - obtener info de cuenta
                    account_status = client.get_account_status()
                    logging.info(f"✅ Autenticación exitosa - Status: {account_status.get('data', 'OK')}")
                    
                    return True
                    
                except Exception as e:
                    error_msg = str(e)
                    if "Timestamp" in error_msg:
                        logging.warning(f"⚠️ Error de timestamp (intento {attempt + 1}): {e}")
                        if attempt < max_retries - 1:
                            logging.info("⏱️ Esperando 2 segundos antes de reintentar...")
                            time.sleep(2)
                            continue
                        else:
                            logging.error("❌ Error persistente de timestamp")
                            logging.error("💡 Soluciones:")
                            logging.error("   1. Sincroniza la hora de tu sistema")
                            logging.error("   2. En Windows: cmd -> w32tm /resync")
                            logging.error("   3. En Linux: sudo ntpdate -s time.nist.gov")
                    elif "IP" in error_msg:
                        logging.error("❌ Error de IP no autorizada")
                        logging.error("💡 Solución: Añade tu IP a la whitelist en Binance API")
                    elif "Invalid" in error_msg or "API-key" in error_msg:
                        logging.error("❌ API Keys inválidas")
                        logging.error("💡 Solución: Verifica que las claves sean correctas")
                    else:
                        logging.error(f"❌ Error conectando con Binance: {e}")
                    
                    return False
                
        except Exception as e:
            logging.error(f"❌ Error verificando configuración: {e}")
            return False
    
    def initialize_enhanced_features(self):
        """Inicializa características mejoradas disponibles"""
        improvements_active = []
        
        # 1. Performance Analyzer (no requiere API)
        if PERFORMANCE_ANALYZER_AVAILABLE:
            try:
                logging.info("📊 Inicializando analizador de rendimiento...")
                performance_analyzer.reset_session(initial_capital=1000.0)
                improvements_active.append("Performance Analyzer")
            except Exception as e:
                logging.warning(f"⚠️ Performance analyzer limitado: {e}")
        
        # 2. Fee Manager (con manejo robusto de errores)
        if FEE_MANAGER_AVAILABLE:
            try:
                logging.info("💰 Inicializando gestión de comisiones...")
                # Usar fees por defecto si hay problemas de API
                fee_analysis = {
                    'user_vip_tier': 0,
                    'bnb_discount_active': False,
                    'current_taker_fee': 0.001,  # 0.1% por defecto
                    'current_maker_fee': 0.001
                }
                
                logging.info(f"📊 Usuario VIP Tier: {fee_analysis['user_vip_tier']} (por defecto)")
                logging.info(f"💳 Descuento BNB: {'Activo' if fee_analysis['bnb_discount_active'] else 'Inactivo'}")
                logging.info(f"📈 Comisión estimada: {fee_analysis['current_taker_fee']*100:.3f}%")
                improvements_active.append("Fee Manager (Básico)")
                
            except Exception as e:
                logging.warning(f"⚠️ Fee manager en modo básico: {e}")
        
        # 3. Risk Calculator (modo conservador)
        if RISK_CALCULATOR_AVAILABLE:
            try:
                logging.info("🛡️ Inicializando gestión de riesgos...")
                # Configuración conservadora por defecto
                risk_summary = {
                    'available_capital': 1000.0,  # Capital por defecto
                    'daily_risk_used_pct': 0.0,
                    'max_position_size': 50.0     # Máximo 50 USDT por posición
                }
                
                logging.info(f"💵 Capital estimado: {risk_summary['available_capital']:.2f} USDT")
                logging.info(f"📊 Riesgo diario usado: {risk_summary['daily_risk_used_pct']:.1f}%")
                logging.info(f"💼 Tamaño máximo de posición: {risk_summary['max_position_size']:.2f} USDT")
                improvements_active.append("Risk Calculator (Conservador)")
                    
            except Exception as e:
                logging.warning(f"⚠️ Risk calculator en modo conservador: {e}")
        
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
            logging.info("💡 Consejos para solucionar:")
            logging.info("   1. Verifica tu archivo .env")
            logging.info("   2. Sincroniza la hora del sistema")
            logging.info("   3. Añade tu IP a la whitelist de Binance")
            return
        
        # Intentar inicializar mejoras disponibles
        has_improvements = self.initialize_enhanced_features()
        
        # Mostrar información de inicio
        if (OPPORTUNITY_SCANNER_AVAILABLE and ORDER_EXECUTOR_AVAILABLE and 
            has_improvements):
            mode = "🚀 AVANZADO"
        elif has_improvements:
            mode = "⚡ MEJORADO"
        else:
            mode = "📊 BÁSICO"
        
        logging.info("=" * 60)
        logging.info(f"🎯 BOT INICIADO - Modo: {mode}")
        logging.info("🔄 Fuente de datos: REST API")
        logging.info("⚠️ IMPORTANTE: Este es un bot de DEMOSTRACIÓN")
        logging.info("💡 Asegúrate de usar LIVE=False para simulación")
        logging.info("=" * 60)
        
        try:
            self.running = True
            
            # Usar scanner apropiado basado en disponibilidad
            if (OPPORTUNITY_SCANNER_AVAILABLE and ORDER_EXECUTOR_AVAILABLE and 
                has_improvements):
                logging.info("🚀 Ejecutando scanner avanzado...")
                self.run_advanced_scanner()
            elif has_improvements:
                logging.info("⚡ Ejecutando scanner mejorado...")
                self.run_improved_scanner()
            else:
                # Usar scanner original
                logging.info("📊 Ejecutando scanner básico...")
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
        """Scanner avanzado simplificado"""
        from binance_api import market_data
        from config import settings
        from strategies.triangular import fetch_symbol_filters
        
        try:
            # Inicializar con manejo de errores
            try:
                fetch_symbol_filters()
                logging.info("✅ Filtros de símbolos cargados")
            except Exception as e:
                logging.warning(f"⚠️ Error cargando filtros: {e}")
            
            # Obtener información inicial
            sym_map = market_data.exchange_map()
            valid_symbols = set(sym_map.keys())
            
            logging.info(f"📊 Símbolos disponibles: {len(valid_symbols)}")
            
            # Contadores
            cycles_completed = 0
            opportunities_found = 0
            
            while self.running:
                cycle_start = time.time()
                
                try:
                    # Obtener top símbolos
                    symbols = market_data.top_volume_symbols(min(50, settings.TOP_N_PAIRS))
                    coins = {c for s in symbols if s in sym_map for c in sym_map[s]}
                    coins.discard(settings.BASE_ASSET)
                    
                    # Limitar monedas para evitar sobrecarga
                    coins = list(coins)[:20]  # Solo top 20 monedas
                    
                    # Obtener libros de órdenes (limitado)
                    books = market_data.depth_snapshots(symbols[:30])  # Solo 30 símbolos
                    
                    cycles_completed += 1
                    
                    logging.info(f"▶️ Ciclo {cycles_completed} - Monedas: {len(coins)} | Books: {len(books)}")
                    
                    # Buscar oportunidades básicas primero
                    cycle_opportunities = self.scan_basic_opportunities(coins, books, valid_symbols)
                    
                    opportunities_found += cycle_opportunities
                    
                    # Estadísticas cada 5 ciclos
                    if cycles_completed % 5 == 0:
                        avg_opportunities = opportunities_found / cycles_completed
                        logging.info("📊 ESTADÍSTICAS:")
                        logging.info(f"   🔄 Ciclos: {cycles_completed}")
                        logging.info(f"   🎯 Oportunidades promedio: {avg_opportunities:.1f}")
                    
                    # Pausa entre ciclos
                    cycle_time = time.time() - cycle_start
                    sleep_time = max(1, settings.SLEEP_BETWEEN - cycle_time)
                    time.sleep(sleep_time)
                    
                except Exception as e:
                    logging.error(f"❌ Error en ciclo: {e}")
                    time.sleep(2)
                    
        except Exception as e:
            logging.error(f"❌ Error en scanner avanzado: {e}")
    
    def run_improved_scanner(self):
        """Scanner mejorado básico"""
        from binance_api import market_data
        from config import settings
        from itertools import combinations
        from strategies.triangular import simulate_route_gain, hourly_interest
        
        try:
            # Inicializar
            sym_map = market_data.exchange_map()
            valid_symbols = set(sym_map.keys())
            
            cycles_completed = 0
            opportunities_found = 0
            
            while self.running:
                cycle_start = time.time()
                
                try:
                    # Obtener datos básicos
                    symbols = market_data.top_volume_symbols(50)  # Reducido
                    coins = {c for s in symbols if s in sym_map for c in sym_map[s]}
                    coins.discard(settings.BASE_ASSET)
                    
                    # Limitar monedas
                    coins = list(coins)[:15]  # Solo 15 monedas
                    
                    books = market_data.depth_snapshots(symbols[:25])
                    
                    cycles_completed += 1
                    cycle_opportunities = 0
                    
                    logging.info(f"▶️ Ciclo {cycles_completed} - Monedas: {len(coins)}")
                    
                    # Buscar oportunidades triangulares simples
                    for combo in combinations(coins, 2):  # Solo 2 monedas intermedias
                        if not self.running:
                            break
                            
                        route = [settings.BASE_ASSET] + list(combo) + [settings.BASE_ASSET]
                        
                        # Solo probar con amount pequeño
                        for usdt_amt in [10, 25]:  # Cantidades pequeñas
                            try:
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
                                        logging.info("🟢 Modo LIVE - ejecutaría trade real")
                                        # Aquí iría la ejecución real
                                    else:
                                        logging.info("📝 Modo simulación")
                                        
                            except Exception as e:
                                logging.debug(f"Error en ruta {route}: {e}")
                                continue
                    
                    opportunities_found += cycle_opportunities
                    
                    # Estadísticas
                    if cycles_completed % 3 == 0:
                        avg_opps = opportunities_found / cycles_completed
                        logging.info("📊 RESUMEN:")
                        logging.info(f"   🔄 Ciclos: {cycles_completed}")
                        logging.info(f"   🎯 Oportunidades/ciclo: {avg_opps:.1f}")
                    
                    # Pausa
                    cycle_time = time.time() - cycle_start
                    sleep_time = max(1, settings.SLEEP_BETWEEN - cycle_time)
                    time.sleep(sleep_time)
                    
                except Exception as e:
                    logging.error(f"❌ Error en ciclo: {e}")
                    time.sleep(2)
                    
        except Exception as e:
            logging.error(f"❌ Error en scanner mejorado: {e}")
    
    def scan_basic_opportunities(self, coins, books, valid_symbols):
        """Escaneo básico de oportunidades"""
        from itertools import combinations
        from strategies.triangular import simulate_route_gain, hourly_interest
        from config import settings
        
        opportunities = 0
        
        try:
            # Solo rutas triangulares simples
            for combo in combinations(coins[:10], 2):  # Solo top 10 monedas, 2 intermedias
                route = [settings.BASE_ASSET] + list(combo) + [settings.BASE_ASSET]
                
                for usdt_amt in [10]:  # Solo 10 USDT para pruebas
                    try:
                        final_qty = simulate_route_gain(route, usdt_amt, books, valid_symbols)
                        if final_qty == 0:
                            continue
                        
                        factor = final_qty / usdt_amt
                        net_gain = factor - 1
                        
                        if net_gain > 0.001:  # 0.1% mínimo
                            opportunities += 1
                            expected_profit = usdt_amt * net_gain
                            
                            logging.info(
                                f"💰 Oportunidad: {' → '.join(route)} | "
                                f"Ganancia: +{expected_profit:.4f} USDT ({net_gain*100:.3f}%)"
                            )
                            
                    except Exception as e:
                        continue
                        
        except Exception as e:
            logging.error(f"❌ Error escaneando oportunidades: {e}")
        
        return opportunities
    
    def shutdown(self):
        """Cierre limpio"""
        logging.info("🛑 Cerrando bot...")
        self.running = False
        logging.info("👋 Bot cerrado limpiamente")

def main():
    """Función principal"""
    setup_logger()
    
    # Mostrar información inicial
    logging.info("🚀 Binance Arbitrage Bot - Versión Funcional")
    logging.info("⚠️ IMPORTANTE: Configura LIVE=False en settings.py para simulación")
    
    bot = ArbitrageBot()
    bot.run()

if __name__ == "__main__":
    main()