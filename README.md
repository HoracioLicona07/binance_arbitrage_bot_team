# Binance Arbitrage Bot

Este bot realiza arbitraje triangular de criptomonedas en Binance, usando libros de órdenes y comisiones reales, con opción para ejecutar trades reales vía margin.

---

## 🚀 Requisitos

- Python 3.10
- Cuenta de Binance habilitada para trading en margin
- Claves de API (API Key y Secret)

---

## 🔧 Instalación

### 1. Clona el repositorio

```bash

cd binance_arbitrage_bot

2. Crea y activa un entorno virtual

python -m venv venv

Windows CMD o PowerShell:
venv\Scripts\activate

Git Bash:
source venv/Scripts/activate

Linux/macOS:
source venv/bin/activate

3. Instala dependencias

pip install -r requirements.txt

🔑 Configuración
Crea un archivo .env con tu clave de API:

BINANCE_API_KEY=TU_API_KEY
BINANCE_API_SECRET=TU_API_SECRET

▶️ Ejecutar

python main.py

📁 Estructura del proyecto
binance_arbitrage_bot/
├── binance_api/
│   ├── client.py
│   ├── market_data.py
│   └── margin.py
├── config/
│   └── settings.py
├── core/
│   ├── logger.py
│   └── utils.py
├── services/
│   └── scanner.py
├── strategies/
│   └── triangular.py
├── main.py
├── requirements.txt
└── .env