# transfer_funds.py - Helper para transferir fondos entre cuentas

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
