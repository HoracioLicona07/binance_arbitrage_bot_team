# binance_arbitrage_bot/binance_api/websocket_manager.py

import asyncio
import websockets
import json
import logging
import time
from collections import defaultdict
from threading import Thread, Lock
from binance_api.client import client
from config import settings

class WebSocketManager:
    def __init__(self):
        self.orderbooks = {}
        self.price_data = {}
        self.lock = Lock()
        self.running = False
        self.connections = {}
        self.last_update = {}
        self.update_callbacks = []
        
    def start(self, symbols):
        """Inicia los streams de WebSocket para los símbolos dados"""
        self.running = True
        self.symbols = symbols
        
        # Crear streams para orderbooks
        orderbook_thread = Thread(target=self._start_orderbook_streams, args=(symbols,))
        orderbook_thread.daemon = True
        orderbook_thread.start()
        
        # Crear streams para precios
        price_thread = Thread(target=self._start_price_streams, args=(symbols,))
        price_thread.daemon = True
        price_thread.start()
        
        logging.info(f"🌐 WebSocket streams iniciados para {len(symbols)} símbolos")
    
    def stop(self):
        """Detiene todos los streams"""
        self.running = False
        for conn in self.connections.values():
            if conn and not conn.closed:
                asyncio.create_task(conn.close())
        logging.info("🔴 WebSocket streams detenidos")
    
    def _start_orderbook_streams(self, symbols):
        """Inicia streams de orderbook en un hilo separado"""
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._orderbook_listener(symbols))
    
    def _start_price_streams(self, symbols):
        """Inicia streams de precios en un hilo separado"""
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._price_listener(symbols))
    
    async def _orderbook_listener(self, symbols):
        """Escucha actualizaciones de orderbook via WebSocket"""
        # Crear streams para orderbook depth
        streams = [f"{symbol.lower()}@depth20@100ms" for symbol in symbols[:10]]  # Limite de 10 para evitar rate limits
        stream_url = f"wss://stream.binance.com:9443/ws/{'/'.join(streams)}"
        
        try:
            async with websockets.connect(stream_url) as websocket:
                self.connections['orderbook'] = websocket
                logging.info(f"📡 Conectado a orderbook stream: {len(streams)} símbolos")
                
                while self.running:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        
                        if 'stream' in data:
                            symbol = data['stream'].split('@')[0].upper()
                            orderbook_data = data['data']
                            
                            with self.lock:
                                self.orderbooks[symbol] = {
                                    'bids': orderbook_data['bids'],
                                    'asks': orderbook_data['asks'],
                                    'lastUpdateId': orderbook_data.get('lastUpdateId', 0)
                                }
                                self.last_update[symbol] = time.time()
                            
                            # Notificar callbacks
                            self._notify_callbacks('orderbook', symbol, self.orderbooks[symbol])
                                
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        logging.error(f"❌ Error en orderbook stream: {e}")
                        break
                        
        except Exception as e:
            logging.error(f"❌ Error conectando orderbook stream: {e}")
    
    async def _price_listener(self, symbols):
        """Escucha actualizaciones de precios via WebSocket"""
        # Stream para precios individuales
        streams = [f"{symbol.lower()}@ticker" for symbol in symbols[:20]]  # Limite para rate limits
        stream_url = f"wss://stream.binance.com:9443/ws/{'/'.join(streams)}"
        
        try:
            async with websockets.connect(stream_url) as websocket:
                self.connections['price'] = websocket
                logging.info(f"💲 Conectado a price stream: {len(streams)} símbolos")
                
                while self.running:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        
                        if 'stream' in data:
                            symbol = data['stream'].split('@')[0].upper()
                            ticker_data = data['data']
                            
                            with self.lock:
                                self.price_data[symbol] = {
                                    'price': float(ticker_data['c']),  # Close price
                                    'bid': float(ticker_data['b']),   # Best bid
                                    'ask': float(ticker_data['a']),   # Best ask
                                    'volume': float(ticker_data['v']), # Volume
                                    'change': float(ticker_data['P']), # Price change %
                                    'timestamp': time.time()
                                }
                            
                            # Notificar callbacks
                            self._notify_callbacks('price', symbol, self.price_data[symbol])
                                
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        logging.error(f"❌ Error en price stream: {e}")
                        break
                        
        except Exception as e:
            logging.error(f"❌ Error conectando price stream: {e}")
    
    def get_orderbook(self, symbol):
        """Obtiene el orderbook más reciente para un símbolo"""
        with self.lock:
            if symbol in self.orderbooks:
                age = time.time() - self.last_update.get(symbol, 0)
                if age < 5:  # Datos frescos (menos de 5 segundos)
                    return self.orderbooks[symbol]
                else:
                    logging.warning(f"⚠️ Orderbook obsoleto para {symbol}: {age:.1f}s")
        
        # Fallback a API REST si no hay datos frescos
        try:
            orderbook = client.get_order_book(symbol=symbol, limit=settings.BOOK_LIMIT)
            with self.lock:
                self.orderbooks[symbol] = orderbook
                self.last_update[symbol] = time.time()
            return orderbook
        except Exception as e:
            logging.error(f"❌ Error obteniendo orderbook {symbol}: {e}")
            return None
    
    def get_price_data(self, symbol):
        """Obtiene datos de precio más recientes para un símbolo"""
        with self.lock:
            return self.price_data.get(symbol)
    
    def get_all_orderbooks(self):
        """Obtiene todos los orderbooks disponibles"""
        with self.lock:
            return self.orderbooks.copy()
    
    def get_all_prices(self):
        """Obtiene todos los datos de precios disponibles"""
        with self.lock:
            return self.price_data.copy()
    
    def add_callback(self, callback_func):
        """Añade un callback para notificaciones de actualizaciones"""
        self.update_callbacks.append(callback_func)
    
    def _notify_callbacks(self, data_type, symbol, data):
        """Notifica a todos los callbacks registrados"""
        for callback in self.update_callbacks:
            try:
                callback(data_type, symbol, data)
            except Exception as e:
                logging.error(f"❌ Error en callback: {e}")
    
    def is_data_fresh(self, symbol, max_age=2):
        """Verifica si los datos de un símbolo están frescos"""
        with self.lock:
            last_update = self.last_update.get(symbol, 0)
            return (time.time() - last_update) < max_age
    
    def get_connection_status(self):
        """Obtiene el estado de las conexiones WebSocket"""
        status = {}
        for name, conn in self.connections.items():
            if conn:
                status[name] = 'connected' if not conn.closed else 'disconnected'
            else:
                status[name] = 'not_initialized'
        return status

# Instancia global del manager
websocket_manager = WebSocketManager()

def start_websocket_streams(symbols):
    """Función helper para iniciar streams"""
    websocket_manager.start(symbols)

def get_realtime_orderbook(symbol):
    """Función helper para obtener orderbook en tiempo real"""
    return websocket_manager.get_orderbook(symbol)

def get_realtime_price(symbol):
    """Función helper para obtener precio en tiempo real"""
    return websocket_manager.get_price_data(symbol)