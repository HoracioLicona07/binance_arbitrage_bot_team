# check_balances.py - Verificar todos tus balances en Binance

import os
from dotenv import load_dotenv
from binance.client import Client

# Cargar API keys
load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(API_KEY, API_SECRET)

def check_all_balances():
    """Verifica balances en todas las cuentas"""
    print("VERIFICANDO TODOS TUS BALANCES EN BINANCE")
    print("="*60)
    
    try:
        # 1. BALANCE SPOT (donde opera el bot)
        print("\n1. CUENTA SPOT (donde opera el bot de arbitraje):")
        print("-"*50)
        account = client.get_account()
        
        spot_usdt = 0
        spot_assets = []
        
        for balance in account['balances']:
            free_balance = float(balance['free'])
            locked_balance = float(balance['locked'])
            total_balance = free_balance + locked_balance
            
            if balance['asset'] == 'USDT':
                spot_usdt = free_balance
                print(f"   USDT: {free_balance:.2f} (libre) + {locked_balance:.2f} (bloqueado) = {total_balance:.2f}")
            elif total_balance > 0:
                spot_assets.append(f"{balance['asset']}: {total_balance:.6f}")
        
        if spot_assets:
            print("   Otros assets en SPOT:")
            for asset in spot_assets[:10]:  # Mostrar solo primeros 10
                print(f"     {asset}")
        
        # 2. BALANCE FUNDING (cuenta principal)
        print("\n2. CUENTA FUNDING (cuenta principal):")
        print("-"*50)
        try:
            funding_balances = client.get_funding_wallet()
            funding_usdt = 0
            funding_assets = []
            
            for balance in funding_balances:
                free_balance = float(balance['free'])
                locked_balance = float(balance['locked'])
                total_balance = free_balance + locked_balance
                
                if balance['asset'] == 'USDT' and total_balance > 0:
                    funding_usdt = free_balance
                    print(f"   USDT: {free_balance:.2f} (libre) + {locked_balance:.2f} (bloqueado) = {total_balance:.2f}")
                elif total_balance > 1:  # Solo mostrar balances > 1
                    funding_assets.append(f"{balance['asset']}: {total_balance:.6f}")
            
            if funding_assets:
                print("   Otros assets en FUNDING:")
                for asset in funding_assets[:10]:
                    print(f"     {asset}")
                    
        except Exception as e:
            print(f"   No se pudo acceder a Funding wallet: {e}")
            funding_usdt = 0
        
        # 3. BALANCE FUTURES (si tienes)
        print("\n3. CUENTA FUTURES:")
        print("-"*50)
        try:
            futures_account = client.futures_account()
            futures_usdt = float(futures_account['totalWalletBalance'])
            print(f"   USDT Total: {futures_usdt:.2f}")
            
            if futures_usdt > 0:
                print("   Posiciones abiertas:")
                positions = client.futures_position_information()
                for pos in positions:
                    if float(pos['positionAmt']) != 0:
                        print(f"     {pos['symbol']}: {pos['positionAmt']} (PnL: {pos['unRealizedProfit']})")
                        
        except Exception as e:
            print(f"   No se pudo acceder a Futures: {e}")
            futures_usdt = 0
        
        # 4. RESUMEN Y RECOMENDACIONES
        print("\n" + "="*60)
        print("RESUMEN Y RECOMENDACIONES:")
        print("="*60)
        
        total_usdt = spot_usdt + funding_usdt + futures_usdt
        print(f"USDT Total en todas las cuentas: {total_usdt:.2f}")
        print(f"  - SPOT (para arbitraje): {spot_usdt:.2f}")
        print(f"  - FUNDING: {funding_usdt:.2f}")
        print(f"  - FUTURES: {futures_usdt:.2f}")
        
        if spot_usdt < 25:  # Mínimo para el bot
            print(f"\nPROBLEMA: Solo tienes {spot_usdt:.2f} USDT en SPOT")
            print("El bot de arbitraje necesita fondos en la cuenta SPOT\n")
            
            if funding_usdt > 25:
                print("SOLUCION 1: Transferir USDT de FUNDING a SPOT")
                print("1. Ve a Binance > Wallet > Overview")
                print("2. Click en 'Transfer' entre Funding y Trading (Spot)")
                print(f"3. Transfiere al menos 30 USDT de Funding a Spot")
                print(f"   (Tienes {funding_usdt:.2f} USDT disponibles en Funding)")
                
            elif futures_usdt > 25:
                print("SOLUCION 2: Transferir USDT de FUTURES a SPOT")
                print("1. Ve a Binance > Derivatives > USD-M Futures")
                print("2. Click en 'Transfer' > Futures to Spot")
                print(f"3. Transfiere al menos 30 USDT de Futures a Spot")
                
            else:
                print("SOLUCION 3: Depositar más USDT")
                print("1. Ve a Binance > Wallet > Deposit")
                print("2. Selecciona USDT y deposita al menos 30-50 USDT")
                print("3. Asegúrate de depositarlo en la red correcta")
        
        else:
            print(f"\n¡PERFECTO! Tienes {spot_usdt:.2f} USDT en SPOT")
            print("Tu bot está listo para operar")
            
            # Sugerir cantidades óptimas
            if spot_usdt >= 100:
                print("Cantidades recomendadas: [10, 15, 20, 25, 30]")
            elif spot_usdt >= 50:
                print("Cantidades recomendadas: [10, 15, 20]")
            else:
                print("Cantidades recomendadas: [5, 10, 15]")
        
        return spot_usdt, funding_usdt, futures_usdt
        
    except Exception as e:
        print(f"Error verificando balances: {e}")
        return 0, 0, 0

def transfer_funding_to_spot(amount):
    """Transfiere USDT de Funding a Spot"""
    try:
        print(f"\nTransfiriendo {amount} USDT de FUNDING a SPOT...")
        
        result = client.universal_transfer(
            type='FUNDING_SPOT',  # De Funding a Spot
            asset='USDT',
            amount=amount
        )
        
        print(f"✅ Transferencia exitosa!")
        print(f"Transaction ID: {result['tranId']}")
        return True
        
    except Exception as e:
        print(f"❌ Error en transferencia: {e}")
        print("\nTransfiere manualmente:")
        print("1. Ve a Binance > Wallet > Overview")
        print("2. Click 'Transfer' entre cuentas")
        print("3. De Funding a Trading (Spot)")
        return False

def main():
    """Función principal"""
    spot_usdt, funding_usdt, futures_usdt = check_all_balances()
    
    # Si hay fondos en Funding pero no en Spot, ofrecer transferencia automática
    if spot_usdt < 25 and funding_usdt >= 30:
        print(f"\n🔄 TRANSFERENCIA AUTOMÁTICA DISPONIBLE")
        print(f"Tienes {funding_usdt:.2f} USDT en Funding")
        transfer_amount = min(50, funding_usdt - 5)  # Dejar 5 USDT en Funding
        
        response = input(f"¿Transferir {transfer_amount} USDT a SPOT automáticamente? (SI/NO): ")
        if response.upper() == 'SI':
            if transfer_funding_to_spot(transfer_amount):
                print("\n✅ ¡Transferencia completada!")
                print("Ahora puedes ejecutar el bot: python main.py")
            else:
                print("\n❌ Transferencia manual requerida")
        else:
            print("\n💡 Transfiere manualmente cuando estés listo")

if __name__ == "__main__":
    main()