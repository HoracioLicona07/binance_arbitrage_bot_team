# binance_arbitrage_bot/strategies/triangular.py

import logging
import math
import time
from binance_api.client import client
from core.utils import avg_price, fee_of
from config import settings

# Cache global para filtros y configuración
symbol_filters = {}
margin_enabled_assets = {}
exchange_info_cache = None
cache_timestamp = 0

def fetch_symbol_filters():
    """Obtiene y cachea los filtros de símbolos de Binance"""
    global symbol_filters, exchange_info_cache, cache_timestamp
    
    try:
        current_time = time.time()
        
        # Usar cache si es reciente (5 minutos)
        if exchange_info_cache and (current_time - cache_timestamp) < 300:
            return
        
        logging.info("📥 Obteniendo información del exchange...")
        info = client.get_exchange_info()
        exchange_info_cache = info
        cache_timestamp = current_time
        
        symbol_filters.clear()
        
        for s in info['symbols']:
            if s['status'] != 'TRADING':
                continue
                
            filters = {}
            for f in s['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    filters['stepSize'] = float(f['stepSize'])
                    filters['minQty'] = float(f['minQty'])
                elif f['filterType'] == 'MIN_NOTIONAL':
                    filters['minNotional'] = float(f['minNotional'])
                elif f['filterType'] == 'PRICE_FILTER':
                    filters['tickSize'] = float(f['tickSize'])
            
            if filters:
                symbol_filters[s['symbol']] = filters
        
        logging.info(f"✅ Filtros cargados para {len(symbol_filters)} símbolos")
        
    except Exception as e:
        logging.error(f"❌ Error obteniendo filtros: {e}")
        # Usar filtros por defecto si falla
        if not symbol_filters:
            logging.info("📄 Usando filtros por defecto")

def format_quantity(symbol, qty):
    """Formatea la cantidad según los filtros del símbolo"""
    try:
        if symbol not in symbol_filters:
            # Formateo básico si no hay filtros
            return round(qty, 8)
        
        filters = symbol_filters[symbol]
        step_size = filters.get('stepSize', 0.00000001)
        min_qty = filters.get('minQty', 0.00000001)
        
        # Calcular precisión basada en step_size
        if step_size >= 1:
            precision = 0
        else:
            precision = int(round(-math.log10(step_size)))
        
        # Formatear cantidad
        formatted_qty = math.floor(qty / step_size) * step_size
        formatted_qty = round(formatted_qty, precision)
        
        # Verificar cantidad mínima
        if formatted_qty < min_qty:
            return 0.0
        
        return formatted_qty
        
    except Exception as e:
        logging.error(f"❌ Error formateando cantidad para {symbol}: {e}")
        return round(qty, 8)

def simulate_route_gain(route, usdt_amount, books, valid_symbols):
    """
    Simula la ganancia de una ruta de arbitraje triangular
    
    Args:
        route: Lista de assets ['USDT', 'BTC', 'ETH', 'USDT']
        usdt_amount: Cantidad inicial en USDT
        books: Diccionario de libros de órdenes
        valid_symbols: Set de símbolos válidos
    
    Returns:
        float: Cantidad final en USDT (0 si falla)
    """
    try:
        qty = usdt_amount
        
        for i in range(len(route) - 1):
            asset_from, asset_to = route[i], route[i + 1]
            
            # Determinar símbolo y lado de la operación
            symbol, side = get_trading_direction(asset_from, asset_to, valid_symbols)
            
            if not symbol:
                logging.debug(f"❌ No se encontró símbolo para {asset_from} -> {asset_to}")
                return 0.0
            
            # Obtener o descargar libro de órdenes
            if symbol not in books:
                try:
                    books[symbol] = client.get_order_book(symbol=symbol, limit=settings.BOOK_LIMIT)
                except Exception as e:
                    logging.debug(f"❌ Error obteniendo libro para {symbol}: {e}")
                    return 0.0
            
            book = books[symbol]
            
            # Verificar que el libro tenga datos
            if not book.get('bids') or not book.get('asks'):
                logging.debug(f"❌ Libro vacío para {symbol}")
                return 0.0
            
            # Seleccionar lado correcto del libro
            levels = book['asks'] if side == 'BUY' else book['bids']
            
            if not levels:
                logging.debug(f"❌ No hay {side} levels para {symbol}")
                return 0.0
            
            # Calcular precio promedio
            try:
                px = avg_price(levels, side, qty)
                if px <= 0:
                    return 0.0
            except Exception as e:
                logging.debug(f"❌ Error calculando precio promedio: {e}")
                return 0.0
            
            # Aplicar conversión y fees
            fee = fee_of(symbol)
            
            if side == 'BUY':
                # Comprando asset_to con asset_from
                qty = (qty / px) * (1 - fee)
            else:
                # Vendiendo asset_from por asset_to
                qty = (qty * px) * (1 - fee)
            
            # Verificar que la cantidad siga siendo positiva
            if qty <= 0:
                return 0.0
        
        return qty
        
    except Exception as e:
        logging.error(f"❌ Error simulando ruta {route}: {e}")
        return 0.0

def get_trading_direction(asset_from, asset_to, valid_symbols):
    """
    Determina el símbolo y dirección de trading para dos assets
    
    Returns:
        tuple: (symbol, side) donde side es 'BUY' o 'SELL'
    """
    # Intentar forward: asset_from + asset_to
    fwd_symbol = asset_from + asset_to
    if fwd_symbol in valid_symbols:
        return fwd_symbol, 'SELL'  # Vendemos asset_from por asset_to
    
    # Intentar reverse: asset_to + asset_from  
    rev_symbol = asset_to + asset_from
    if rev_symbol in valid_symbols:
        return rev_symbol, 'BUY'   # Compramos asset_to con asset_from
    
    return None, None

def get_valid_symbol(asset_a, asset_b, valid_symbols):
    """
    Obtiene el símbolo válido para un par de assets (legacy)
    """
    symbol, _ = get_trading_direction(asset_a, asset_b, valid_symbols)
    if symbol:
        return symbol, 'fwd' if symbol == asset_a + asset_b else 'rev'
    return None, None

def hourly_interest(asset):
    """
    Obtiene la tasa de interés por hora para un asset (para margin trading)
    """
    return margin_enabled_assets.get(asset, 0.0)

def execute_arbitrage_trade(route, usdt_amt):
    """
    Ejecuta un trade de arbitraje (versión básica)
    
    Args:
        route: Lista de assets de la ruta
        usdt_amt: Cantidad en USDT
    """
    try:
        if settings.LIVE:
            logging.warning("🔴 TRADE REAL - Implementación básica")
            # Aquí iría la implementación real del trade
            # Por seguridad, solo loggear en esta versión básica
            logging.info(f"💰 Ejecutaría trade real: {' → '.join(route)} con {usdt_amt} USDT")
            logging.warning("⚠️ Implementación de ejecución real pendiente")
        else:
            logging.info(f"📝 SIMULACIÓN: Trade {' → '.join(route)} con {usdt_amt} USDT")
            
    except Exception as e:
        logging.error(f"❌ Error ejecutando trade: {e}")

def analyze_route_profitability(route, amount, books, valid_symbols):
    """
    Analiza la rentabilidad detallada de una ruta
    
    Returns:
        dict: Análisis detallado de la ruta
    """
    try:
        analysis = {
            'route': route,
            'initial_amount': amount,
            'final_amount': 0.0,
            'profit_usdt': 0.0,
            'profit_percentage': 0.0,
            'viable': False,
            'steps': [],
            'total_fees': 0.0
        }
        
        qty = amount
        total_fees = 0.0
        
        for i in range(len(route) - 1):
            asset_from, asset_to = route[i], route[i + 1]
            symbol, side = get_trading_direction(asset_from, asset_to, valid_symbols)
            
            step = {
                'from': asset_from,
                'to': asset_to,
                'symbol': symbol,
                'side': side,
                'input_qty': qty,
                'output_qty': 0.0,
                'price': 0.0,
                'fee': 0.0
            }
            
            if not symbol or symbol not in books:
                step['error'] = 'Symbol not available'
                analysis['steps'].append(step)
                return analysis
            
            book = books[symbol]
            levels = book['asks'] if side == 'BUY' else book['bids']
            
            if not levels:
                step['error'] = 'No liquidity'
                analysis['steps'].append(step)
                return analysis
            
            # Calcular conversión
            px = avg_price(levels, side, qty)
            fee = fee_of(symbol)
            fee_amount = qty * fee
            
            if side == 'BUY':
                qty = (qty / px) * (1 - fee)
            else:
                qty = (qty * px) * (1 - fee)
            
            step['output_qty'] = qty
            step['price'] = px
            step['fee'] = fee_amount
            total_fees += fee_amount
            
            analysis['steps'].append(step)
        
        analysis['final_amount'] = qty
        analysis['profit_usdt'] = qty - amount
        analysis['profit_percentage'] = (qty - amount) / amount * 100
        analysis['total_fees'] = total_fees
        analysis['viable'] = qty > amount and analysis['profit_percentage'] > settings.PROFIT_THOLD * 100
        
        return analysis
        
    except Exception as e:
        logging.error(f"❌ Error analizando ruta: {e}")
        return {'viable': False, 'error': str(e)}

def find_best_routes(coins, books, valid_symbols, max_routes=5):
    """
    Encuentra las mejores rutas de arbitraje disponibles
    
    Returns:
        list: Lista de las mejores rutas ordenadas por rentabilidad
    """
    from itertools import combinations
    
    best_routes = []
    
    try:
        # Solo rutas triangulares (3 saltos)
        for combo in combinations(coins, 2):
            route = [settings.BASE_ASSET] + list(combo) + [settings.BASE_ASSET]
            
            for amount in settings.QUANTUMS_USDT:
                analysis = analyze_route_profitability(route, amount, books, valid_symbols)
                
                if analysis.get('viable', False):
                    best_routes.append(analysis)
        
        # Ordenar por rentabilidad
        best_routes.sort(key=lambda x: x.get('profit_percentage', 0), reverse=True)
        
        return best_routes[:max_routes]
        
    except Exception as e:
        logging.error(f"❌ Error buscando mejores rutas: {e}")
        return []

# Funciones de utilidad adicionales
def get_symbol_info(symbol):
    """Obtiene información de un símbolo específico"""
    try:
        return client.get_symbol_info(symbol)
    except Exception as e:
        logging.debug(f"Symbol {symbol} not found: {e}")
        return None

def validate_route(route, valid_symbols):
    """Valida que una ruta sea ejecutable"""
    try:
        for i in range(len(route) - 1):
            symbol, _ = get_trading_direction(route[i], route[i + 1], valid_symbols)
            if not symbol:
                return False
        return True
    except:
        return False

# Inicialización automática
try:
    fetch_symbol_filters()
    logging.info("✅ Módulo triangular inicializado")
except Exception as e:
    logging.warning(f"⚠️ Error inicializando módulo triangular: {e}")

if __name__ == "__main__":
    # Test básico del módulo
    print("🧪 Testing módulo triangular...")
    fetch_symbol_filters()
    print(f"📊 Filtros cargados: {len(symbol_filters)}")
    
    # Test de formateo
    test_qty = format_quantity("BTCUSDT", 0.001234567)
    print(f"🔢 Test formateo: {test_qty}")
    
    print("✅ Módulo triangular funcionando")