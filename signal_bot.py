import ccxt
import pandas as pd
import ta
import requests
import time

# === Telegram настройки ===
TELEGRAM_TOKEN = '7743689513:AAHwd8J0QGKGR1-0Ulnlm8Q_XRVvyktqwTA'
TELEGRAM_CHAT_ID = '779831901'

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    requests.post(url, data=data)

# === Подключение к Bybit ===
exchange = ccxt.bybit({'enableRateLimit': True})

# === Настройки монет и таймфрейма ===
symbols = ['SOL/USDT', 'WIF/USDT', 'SUI/USDT', 'JUP/USDT', 'PEPE/USDT', 'LINK/USDT', 'AAVE/USDT']
timeframe = '15m'

# === Анализ монеты ===
def analyze(symbol):
    try:

        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()

        rsi = df['rsi'].iloc[-1]
        macd_val = df['macd'].iloc[-1]
        macd_sig = df['macd_signal'].iloc[-1]

        # Сигнал на long
        if rsi < 45 and macd_val > macd_sig:
            message = f"BUY сигнал по {symbol}\nRSI: {rsi:.1f}, MACD пересечение вверх"
            send_telegram_message(message)

        # Сигнал на short
        elif rsi > 60 and macd_val < macd_sig:
            message = f"SELL сигнал по {symbol}\nRSI: {rsi:.1f}, MACD пересечение вниз"
            send_telegram_message(message)

    except Exception as e:
        print(f"[Ошибка] {symbol}: {e}")
        

# === Основной цикл ===
send_telegram_message("✅ Бот запущен и готов анализировать рынок.")
while True:
    for symbol in symbols:
        analyze(symbol)
        time.sleep(1)
    time.sleep(60 * 15)  # ждать 15 минут
