# binance_arbitrage_bot/diagnostic.py
"""
Script de diagnóstico para problemas de conexión con Binance
"""

import os
import requests
import time
from dotenv import load_dotenv
from binance.client import Client

def check_internet_connection():
    """Verifica conexión a internet"""
    try:
        response = requests.get('https://www.google.com', timeout=5)
        print("✅ Conexión a internet: OK")
        return True
    except:
        print("❌ Sin conexión a internet")
        return False

def get_public_ip():
    """Obtiene la IP pública"""
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        ip = response.text.strip()
        print(f"🌐 Tu IP pública: {ip}")
        return ip
    except:
        print("❌ No se pudo obtener IP pública")
        return None

def test_binance_connection():
    """Prueba conexión básica con Binance"""
    try:
        response = requests.get('https://api.binance.com/api/v3/ping', timeout=5)
        if response.status_code == 200:
            print("✅ Binance API accesible")
            return True
        else:
            print(f"❌ Binance API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando a Binance: {e}")
        return False

def check_server_time():
    """Verifica sincronización de tiempo"""
    try:
        response = requests.get('https://api.binance.com/api/v3/time', timeout=5)
        server_time = response.json()['serverTime']
        local_time = int(time.time() * 1000)
        offset = server_time - local_time
        
        print(f"⏰ Tiempo servidor Binance: {server_time}")
        print(f"⏰ Tiempo local: {local_time}")
        print(f"⏰ Diferencia: {offset}ms")
        
        if abs(offset) > 5000:
            print("⚠️ PROBLEMA: Diferencia de tiempo muy grande")
            print("💡 Solución: Sincroniza la hora del sistema")
            return False
        else:
            print("✅ Sincronización de tiempo: OK")
            return True
    except Exception as e:
        print(f"❌ Error verificando tiempo: {e}")
        return False

def test_api_keys():
    """Prueba las API keys"""
    load_dotenv()
    
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    print(f"🔑 API Key encontrada: {api_key[:8]}..." if api_key else "❌ API Key no encontrada")
    print(f"🔐 API Secret encontrado: {api_secret[:8]}..." if api_secret else "❌ API Secret no encontrado")
    
    if not api_key or not api_secret:
        print("❌ Faltan credenciales en archivo .env")
        return False
    
    # Verificar longitud
    if len(api_key) < 60 or len(api_secret) < 60:
        print("⚠️ API Keys parecen incompletas")
        return False
    
    print("✅ Credenciales básicas: OK")
    return True

def test_api_permissions():
    """Prueba permisos de API"""
    load_dotenv()
    
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ No hay credenciales para probar")
        return False
    
    try:
        client = Client(api_key, api_secret)
        
        # Test 1: Conexión básica
        print("🧪 Probando conexión básica...")
        server_time = client.get_server_time()
        print("✅ Conexión básica: OK")
        
        # Test 2: Permisos de lectura
        print("🧪 Probando permisos de lectura...")
        account_status = client.get_account_status()
        print("✅ Permisos de lectura: OK")
        print(f"📊 Estado cuenta: {account_status.get('data', 'Activa')}")
        
        # Test 3: Información de cuenta
        print("🧪 Probando acceso a información de cuenta...")
        account = client.get_account()
        print("✅ Acceso a cuenta: OK")
        
        # Mostrar algunos balances
        balances = [b for b in account['balances'] if float(b['free']) > 0][:5]
        print(f"💰 Balances activos (top 5):")
        for balance in balances:
            print(f"   {balance['asset']}: {balance['free']}")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error en permisos: {e}")
        
        if "Invalid API-key" in error_msg:
            print("💡 Problema: API Key inválida")
            print("   - Verifica que copiaste la clave correcta")
            print("   - Asegúrate que la API Key esté activa")
        elif "IP" in error_msg:
            print("💡 Problema: IP no autorizada")
            print("   - Añade tu IP a la whitelist en Binance")
            print(f"   - Tu IP pública: {get_public_ip()}")
        elif "permissions" in error_msg:
            print("💡 Problema: Permisos insuficientes")
            print("   - Habilita 'Enable Reading' en la API")
            print("   - Habilita 'Enable Spot & Margin Trading' si planeas tradear")
        elif "Timestamp" in error_msg:
            print("💡 Problema: Timestamp incorrecto")
            print("   - Sincroniza la hora del sistema")
        
        return False

def main():
    """Ejecuta diagnóstico completo"""
    print("🔍 DIAGNÓSTICO COMPLETO DE BINANCE BOT")
    print("=" * 50)
    
    issues = []
    
    # Test 1: Internet
    if not check_internet_connection():
        issues.append("Sin conexión a internet")
    
    print()
    
    # Test 2: IP Pública
    public_ip = get_public_ip()
    
    print()
    
    # Test 3: Binance accesible
    if not test_binance_connection():
        issues.append("Binance API no accesible")
    
    print()
    
    # Test 4: Sincronización tiempo
    if not check_server_time():
        issues.append("Problema de sincronización de tiempo")
    
    print()
    
    # Test 5: API Keys
    if not test_api_keys():
        issues.append("Problema con API Keys")
    
    print()
    
    # Test 6: Permisos
    if not test_api_permissions():
        issues.append("Problema con permisos de API")
    
    print()
    print("=" * 50)
    print("📋 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 50)
    
    if not issues:
        print("🎉 ¡Todo está configurado correctamente!")
        print("✅ El bot debería funcionar sin problemas")
    else:
        print("❌ Se encontraron los siguientes problemas:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        
        print("\n💡 PASOS PARA SOLUCIONAR:")
        print("1. Ve a https://www.binance.com/en/my/settings/api-management")
        print("2. Edita tu API Key")
        print("3. En 'API restrictions' añade tu IP:")
        if public_ip:
            print(f"   - IP a añadir: {public_ip}")
        print("4. Asegúrate que 'Enable Reading' esté habilitado")
        print("5. Si planeas hacer trades reales, habilita 'Enable Spot & Margin Trading'")
        print("6. Guarda los cambios y espera unos minutos")

if __name__ == "__main__":
    main()