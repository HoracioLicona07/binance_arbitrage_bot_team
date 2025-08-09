# services/enhanced_scanner.py
import time
import logging
from itertools import combinations
from typing import Dict, List
from config import settings
from binance_api import market_data
from strategies.triangular import simulate_route_gain, fetch_symbol_filters

try:
    from detection.enhanced_scanner import enhanced_detector
    from ml.simple_predictor import ml_predictor
    ENHANCED_MODULES = True
    logging.info("Modulos ML cargados")
except ImportError:
    ENHANCED_MODULES = False
    logging.warning("Modulos ML no disponibles")

def run_with_enhancements():
    """Funcion principal para ejecutar con mejoras"""
    if ENHANCED_MODULES:
        logging.info("Iniciando scanner con modulos ML")
        run_enhanced_loop()
    else:
        logging.info("Iniciando scanner basico mejorado")
        run_basic_enhanced()

def run_enhanced_loop():
    """Loop mejorado con ML"""
    sym_map = market_data.exchange_map()
    valid_symbols = set(sym_map.keys())
    fetch_symbol_filters()
    
    cycle_count = 0
    adaptive_threshold = settings.PROFIT_THOLD
    
    while True:
        cycle_start = time.time()
        cycle_count += 1
        
        try:
            symbols = market_data.top_volume_symbols(settings.TOP_N_PAIRS)
            books = market_data.depth_snapshots(symbols)
            
            # Actualizar ML
            for symbol, book in books.items():
                if 'USDT' in symbol and book.get('bids'):
                    price = float(book['bids'][0][0])
                    ml_predictor.update_market_data(symbol, price)
            
            # Buscar oportunidades con ML
            opportunities = enhanced_detector.quick_scan(books, valid_symbols)
            
            executed = 0
            for opp in opportunities[:3]:
                ml_score = ml_predictor.predict_route_success(opp.route)
                combined_score = opp.confidence * 0.7 + ml_score * 0.3
                
                if combined_score > 0.5:
                    print(f"OPORTUNIDAD ML: {' -> '.join(opp.route)}")
                    print(f"   {opp.amount} USDT -> +{opp.profit:.4f} USDT ({opp.profit_pct*100:.3f}%)")
                    print(f"   ML Score: {ml_score:.2f} | Combined: {combined_score:.2f}")
                    
                    if settings.LIVE:
                        executed += 1
                        # Simular ejecucion
                        actual_profit = opp.profit * 0.8
                        ml_predictor.record_arbitrage_result(opp.route, actual_profit)
                        print(f"Trade simulado: +{actual_profit:.4f} USDT")
                        time.sleep(1)
            
            # Ajustar threshold
            adaptive_threshold = enhanced_detector.adaptive_threshold(len(opportunities))
            
            print(f"Ciclo {cycle_count} ML - Oportunidades: {len(opportunities)} | "
                  f"Ejecutados: {executed} | Threshold: {adaptive_threshold*100:.2f}%")
            
            sleep_time = max(1, settings.SLEEP_BETWEEN - (time.time() - cycle_start))
            time.sleep(sleep_time)
            
        except Exception as e:
            logging.error(f"Error en ciclo ML: {e}")
            time.sleep(2)

def run_basic_enhanced():
    """Version basica mejorada"""
    from strategies.triangular import simulate_route_gain, fetch_symbol_filters
    
    sym_map = market_data.exchange_map()
    valid_symbols = set(sym_map.keys())
    fetch_symbol_filters()
    
    cycle_count = 0
    adaptive_threshold = settings.PROFIT_THOLD
    
    while True:
        cycle_start = time.time()
        cycle_count += 1
        
        try:
            symbols = market_data.top_volume_symbols(settings.TOP_N_PAIRS)
            books = market_data.depth_snapshots(symbols)
            
            priority_coins = ['BTC', 'ETH', 'BNB', 'ADA', 'DOT', 'LINK', 'XRP']
            
            opportunities = 0
            for combo in combinations(priority_coins, 2):
                route = ['USDT'] + list(combo) + ['USDT']
                
                for amount in [10, 15, 20, 25]:
                    final_qty = simulate_route_gain(route, amount, books, valid_symbols)
                    if final_qty > 0:
                        profit = final_qty - amount
                        profit_pct = profit / amount
                        
                        if profit_pct > adaptive_threshold:
                            opportunities += 1
                            print(f"{' -> '.join(route)} | {amount} USDT | +{profit_pct*100:.3f}%")
                            
                            if settings.LIVE:
                                print("Trade simulado ejecutado")
            
            # Ajustar threshold
            if opportunities == 0:
                adaptive_threshold *= 0.95
                adaptive_threshold = max(0.002, adaptive_threshold)
            elif opportunities > 3:
                adaptive_threshold *= 1.05
                adaptive_threshold = min(0.012, adaptive_threshold)
            
            print(f"Ciclo {cycle_count} - Oportunidades: {opportunities} "
                  f"(threshold: {adaptive_threshold*100:.2f}%)")
            
            sleep_time = max(1, settings.SLEEP_BETWEEN - (time.time() - cycle_start))
            time.sleep(sleep_time)
            
        except Exception as e:
            logging.error(f"Error en ciclo basico: {e}")
            time.sleep(2)
