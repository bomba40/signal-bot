import ccxt
import pandas as pd
import ta
import requests
import time
import matplotlib.pyplot as plt
import io

# === Telegram настройки ===
TELEGRAM_TOKEN = '7743689513:AAHwd8J0QGKGR1-0Ulnlm8Q_XRVvyktqwTA'
TELEGRAM_CHAT_ID = '779831901'

# === Подключение к Bybit ===
exchange = ccxt.bybit({'enableRateLimit': True})

# === Монеты и таймфрейм ===
symbols = ['SOL/USDT', 'WIF/USDT', 'SUI/USDT', 'JUP/USDT', 'PEPE/USDT', 'LINK/USDT', 'AAVE/USDT']
timeframe = '15m'

def analyze(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()

        rsi = df['rsi'].iloc[-1]
        macd_val = df['macd'].iloc[-1]
        macd_sig = df['macd_signal'].iloc[-1]

        signal = None
        if rsi < 45 and macd_val > macd_sig:
            signal = 'BUY'
        elif rsi > 60 and macd_val < macd_sig:
            signal = 'SELL'

        if signal:
            # Построить график
            plt.figure(figsize=(10, 5))
            plt.plot(df['timestamp'], df['close'], label='Цена')
            plt.title(f"{symbol} сигнал: {signal}")
            plt.xlabel("Время")
            plt.ylabel("Цена")
            plt.legend()

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close()

            files = {'photo': buf}
            data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': f"{signal} сигнал по {symbol}\nRSI: {rsi:.1f}, MACD пересечение"}
            requests.post(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto', data=data, files=files)

    except Exception as e:
        print(f"[Ошибка] {symbol}: {e}")

# === Цикл проверки ===
while True:
    for symbol in symbols:
        analyze(symbol)
        time.sleep(1)
    time.sleep(60 * 15)
