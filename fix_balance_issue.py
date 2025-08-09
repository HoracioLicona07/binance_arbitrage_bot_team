# fix_balance_issue.py - Solucionar problema de balance

import os
import shutil

def create_low_balance_config():
    """Crea configuración para balances bajos"""
    
    # Respaldar configuración actual
    if os.path.exists("config/settings.py"):
        shutil.copy("config/settings.py", "config/settings_high_balance.py")
    
    low_balance_settings = '''# config/settings.py - Configuración para balances bajos

import logging

# CONFIGURACIÓN PARA BALANCES BAJOS (funciona con solo 10-20 USDT)
LIVE = True

# Configuración de mercado
TOP_N_PAIRS = 30          
BOOK_LIMIT = 20           
BASE_ASSET = 'USDT'       

# Configuración de rentabilidad ADAPTADA
PROFIT_THOLD = 0.003      # 0.3% ganancia mínima (muy agresivo)
SLIPPAGE_PCT = 0.002      
HOLD_SECONDS = 3          

# CANTIDADES PARA BALANCES BAJOS
QUANTUMS_USDT = [5, 8, 10]  # Empezar con cantidades muy pequeñas

# Configuración de timing
SLEEP_BETWEEN = 2         

# Configuración de logging
LOG_LEVEL = logging.INFO

# LÍMITES AJUSTADOS PARA BALANCES BAJOS
MAX_POSITION_SIZE = 10     # Máximo 10 USDT por posición
MAX_DAILY_RISK = 20        # Máximo 20 USDT de riesgo por día
MIN_LIQUIDITY = 500        # Liquidez mínima reducida
MAX_DAILY_TRADES = 15      # Máximo 15 trades por día

# Configuración de performance RELAJADA
MAX_EXECUTION_TIME = 10    
MIN_CONFIDENCE = 0.5       # Solo 50% confianza mínima
MAX_SLIPPAGE = 0.02        # 2% slippage máximo

# Configuración de API
API_TIMEOUT = 8            
MAX_RETRIES = 3            

# VERIFICACIÓN DE BALANCE MÁS FLEXIBLE
MIN_BALANCE_REQUIRED = 8   # Solo requiere 8 USDT mínimo
BALANCE_MULTIPLIER = 1.5   # 1.5x la cantidad máxima (vs 2x normal)

# CONFIGURACIÓN DE ALERTAS
ENABLE_PROFIT_ALERTS = True    
ENABLE_LOSS_ALERTS = True      
ENABLE_ERROR_ALERTS = True     

# Límites para alertas AJUSTADOS
PROFIT_ALERT_THRESHOLD = 1.0   # Alertar si ganancia > 1 USDT
LOSS_ALERT_THRESHOLD = 0.5     # Alertar si pérdida > 0.5 USDT

print("CONFIGURACION PARA BALANCES BAJOS CARGADA")
print("FUNCIONA CON SOLO 10-20 USDT EN SPOT")
print(f"Configuracion:")
print(f"   Ganancia minima: {PROFIT_THOLD*100:.2f}%")
print(f"   Cantidades: {QUANTUMS_USDT}")
print(f"   Balance minimo: {MIN_BALANCE_REQUIRED} USDT")
print(f"   Posicion maxima: {MAX_POSITION_SIZE} USDT")
'''
    
    with open("config/settings.py", 'w', encoding='utf-8') as f:
        f.write(low_balance_settings)
    
    print("✅ Configuración para balances bajos creada")
    print("✅ Configuración anterior respaldada como settings_high_balance.py")

def modify_main_balance_check():
    """Modifica la verificación de balance en main.py"""
    
    # Leer main.py actual
    try:
        with open("main.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar y reemplazar la verificación de balance
        old_balance_check = "min_balance_required = max(settings.QUANTUMS_USDT) * 2"
        new_balance_check = "min_balance_required = getattr(settings, 'MIN_BALANCE_REQUIRED', max(settings.QUANTUMS_USDT) * getattr(settings, 'BALANCE_MULTIPLIER', 1.5))"
        
        if old_balance_check in content:
            content = content.replace(old_balance_check, new_balance_check)
            
            with open("main.py", 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Verificación de balance modificada en main.py")
        else:
            print("⚠️ No se encontró la línea de verificación de balance")
            
    except Exception as e:
        print(f"❌ Error modificando main.py: {e}")

def create_balance_transfer_helper():
    """Crea helper para transferir fondos"""
    transfer_helper = '''# transfer_funds.py - Helper para transferir fondos entre cuentas

from binance.client import Client
import os
from dotenv import load_dotenv

load_dotenv()
client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))

def transfer_from_funding_to_spot(amount=30):
    """Transfiere USDT de Funding a Spot"""
    try:
        result = client.universal_transfer(
            type='FUNDING_SPOT',
            asset='USDT', 
            amount=amount
        )
        print(f"✅ Transferidos {amount} USDT de Funding a Spot")
        print(f"Transaction ID: {result['tranId']}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def transfer_from_futures_to_spot(amount=30):
    """Transfiere USDT de Futures a Spot"""
    try:
        result = client.futures_transfer(
            asset='USDT',
            amount=amount,
            type=2  # Futures to Spot
        )
        print(f"✅ Transferidos {amount} USDT de Futures a Spot")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Helper de transferencia de fondos")
    print("1. transfer_from_funding_to_spot(30)")
    print("2. transfer_from_futures_to_spot(30)")
'''
    
    with open("transfer_funds.py", 'w', encoding='utf-8') as f:
        f.write(transfer_helper)
    
    print("✅ Helper de transferencia creado: transfer_funds.py")

def main():
    """Solucionar problema de balance"""
    print("SOLUCIONANDO PROBLEMA DE BALANCE")
    print("="*50)
    
    print("1. Creando configuración para balances bajos...")
    create_low_balance_config()
    
    print("2. Modificando verificación de balance...")
    modify_main_balance_check()
    
    print("3. Creando helper de transferencia...")
    create_balance_transfer_helper()
    
    print("\n✅ PROBLEMA SOLUCIONADO!")
    print("="*50)
    print("OPCIONES DISPONIBLES:")
    print("\n1. USAR CON BALANCE BAJO:")
    print("   - Ahora funciona con solo 8-10 USDT")
    print("   - Cantidades: [5, 8, 10] USDT")
    print("   - Ejecutar: python main.py")
    
    print("\n2. VERIFICAR TODOS TUS BALANCES:")
    print("   - Ejecutar: python check_balances.py")
    print("   - Te mostrará SPOT, FUNDING y FUTURES")
    
    print("\n3. TRANSFERIR FONDOS MANUALMENTE:")
    print("   - Binance > Wallet > Overview > Transfer")
    print("   - De Funding/Futures a Trading (Spot)")
    
    print("\n4. TRANSFERIR AUTOMÁTICAMENTE:")
    print("   - python transfer_funds.py")

if __name__ == "__main__":
    main()