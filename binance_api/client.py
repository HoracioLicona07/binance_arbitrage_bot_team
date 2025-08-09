# binance_arbitrage_bot/binance_api/client.py

import os
import time
import requests
from dotenv import load_dotenv
from binance.client import Client

# Load environment variables from .env
load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

def get_server_time_offset():
    """Obtiene el offset de tiempo con el servidor de Binance"""
    try:
        response = requests.get('https://api.binance.com/api/v3/time', timeout=5)
        server_time = response.json()['serverTime']
        local_time = int(time.time() * 1000)
        return server_time - local_time
    except Exception:
        return 0

# Obtener offset de tiempo
time_offset = get_server_time_offset()

# Función personalizada para ajustar timestamp
def adjusted_timestamp():
    """Retorna timestamp ajustado con el servidor"""
    return int(time.time() * 1000) + time_offset

# Initialize Binance Client con configuración optimizada
try:
    client = Client(
        API_KEY, 
        API_SECRET,
        requests_params={
            'timeout': 10,  # Timeout de 10 segundos
        }
    )
    
    # Configurar offset de tiempo si es significativo
    if abs(time_offset) > 1000:  # Más de 1 segundo
        print(f"⏰ Ajustando tiempo del cliente: {time_offset}ms")
        # En versiones nuevas de python-binance
        try:
            client.timestamp_offset = time_offset
        except AttributeError:
            # Para versiones más antiguas
            pass
    
    print(f"✅ Cliente Binance inicializado correctamente")
    
except Exception as e:
    print(f"❌ Error inicializando cliente Binance: {e}")
    # Cliente básico como fallback
    client = Client(API_KEY, API_SECRET)

# Función helper para verificar conexión
def test_connection():
    """Prueba la conexión con Binance"""
    try:
        # Test simple - obtener tiempo del servidor
        server_time = client.get_server_time()
        print(f"✅ Conexión exitosa - Tiempo servidor: {server_time}")
        return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

# Función helper para verificar autenticación
def test_authentication():
    """Prueba la autenticación con las API keys"""
    try:
        # Test de autenticación básico
        account_status = client.get_account_status()
        print(f"✅ Autenticación exitosa - Status: {account_status}")
        return True
    except Exception as e:
        print(f"❌ Error de autenticación: {e}")
        return False

# Función para obtener información básica de la cuenta (sin margin)
def get_basic_account_info():
    """Obtiene información básica de la cuenta"""
    try:
        account = client.get_account()
        balances = {
            balance['asset']: {
                'free': float(balance['free']),
                'locked': float(balance['locked'])
            }
            for balance in account['balances']
            if float(balance['free']) > 0 or float(balance['locked']) > 0
        }
        return balances
    except Exception as e:
        print(f"❌ Error obteniendo info de cuenta: {e}")
        return {}

if __name__ == "__main__":
    print("🧪 Probando conexión con Binance...")
    print(f"🔑 API Key (primeros 8 chars): {API_KEY[:8] if API_KEY else 'No configurada'}...")
    print(f"⏰ Offset de tiempo: {time_offset}ms")
    
    if test_connection():
        if test_authentication():
            balances = get_basic_account_info()
            print(f"💰 Balances con fondos: {len(balances)}")
            for asset, balance in list(balances.items())[:5]:  # Mostrar solo 5
                print(f"   {asset}: {balance['free']:.6f}")
        else:
            print("❌ Autenticación fallida - verifica tus API keys")
    else:
        print("❌ Conexión fallida - verifica tu internet y API keys")