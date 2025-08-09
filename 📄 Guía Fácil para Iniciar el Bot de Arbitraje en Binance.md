# 📄 Guía Fácil para Iniciar el Bot de Arbitraje en Binance

## 1️⃣ Clonar el repositorio desde GitHub

Primero, necesitamos traer el código a tu computadora.

**Pasos:**

1. Abre una carpeta donde quieras guardar el bot.
2. Haz clic derecho y selecciona **"Git Bash Here"** (o abre una terminal).
3. Escribe:

```
git clone https://github.com/HoracioLicona07/binance_arbitrage_bot_team
```

1. Entra a la carpeta del proyecto:

```
cd binance_arbitrage_bot_team
```

------

## 2️⃣ Actualizar el repositorio (si ya lo tienes clonado)

Si ya tienes el bot en tu PC y quieres actualizarlo con los últimos cambios:

```
git pull origin main
```

------

## 3️⃣ Instalar Python y dependencias

Debes tener **Python 3.10** instalado.
 Luego, en la carpeta del bot, ejecuta:

```
pip install -r requirements.txt
```

------

## 4️⃣ Archivos importantes y para qué sirven

| Archivo                | Función                                                      | Cuándo usarlo                                                |
| ---------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| `main.py`              | Es el **archivo principal** del bot. Aquí se ejecuta la lógica de arbitraje. | Siempre que quieras iniciar el bot.                          |
| `setup_bot.py`         | Configura el bot con las mejoras integradas.                 | Solo una vez al inicio o cuando actualices configuración importante. |
| `check_balances.py`    | Revisa tus saldos en Binance (Spot, Funding, Futures).       | Antes de ejecutar el bot, para confirmar que tienes fondos en la cuenta correcta. |
| `fix_balance_issue.py` | Ajusta el bot para funcionar con pocos fondos.               | Si tienes menos de 10 USDT en Spot.                          |
| `config/settings.py`   | Contiene la configuración del bot (umbral de ganancia, cantidades, etc.). | Solo si quieres ajustar parámetros.                          |



------

## 5️⃣ Ejecución paso a paso (Recomendado)

**Paso 1 – Configurar el bot**

```
python setup_bot.py
```

**Paso 2 – Verificar fondos**

```
python check_balances.py
```

**Paso 3 – Ajustar si tienes pocos fondos**

```
python fix_balance_issue.py
```

*(Solo si tienes menos de 10 USDT en Spot)*

**Paso 4 – Iniciar el bot**

```
python main.py
```

------

## 6️⃣ Cambios clave en la nueva versión

- **Threshold reducido:** de `0.8%` a `0.4%` (más fácil encontrar oportunidades).
- **Más cantidades:** de `[10, 15]` a `[10, 15, 20, 25]` USDT.
- **Más pares:** de `30` a `40` pares.
- **Ciclos más rápidos:** de `3s` a `2s` entre ciclos.
- **Inteligencia adaptativa:** el threshold se ajusta solo.

------

## 7️⃣ Ejecución rápida (30 segundos)

Si solo quieres el cambio mínimo, abre `config/settings.py` y modifica:

```
pythonCopiarEditarPROFIT_THOLD = 0.004
QUANTUMS_USDT = [10, 15, 20, 25]
SLEEP_BETWEEN = 2
TOP_N_PAIRS = 40
```

Luego ejecuta:

```
python main.py
```

------

## 8️⃣ ¿Qué verás al ejecutarlo?

Antes:

```
objectivecCopiarEditar🔍 CICLO 1 - Escaneando...
🎯 Oportunidades: 0
```

Ahora:

```
yamlCopiarEditar🚀 INICIANDO TRADING BÁSICO MEJORADO
💰 OPORTUNIDAD: USDT → BTC → ETH → USDT  (+0.416%)
💰 OPORTUNIDAD: USDT → BNB → ADA → USDT  (+0.446%)
```

------

📌 **Nota:** Siempre verifica que tu API Key y Secret Key de Binance estén configuradas correctamente en el archivo correspondiente antes de iniciar.