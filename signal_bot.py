import ccxt
import pandas as pd
import ta
import requests
import time
import io
import matplotlib.pyplot as plt

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
symbols = ['BTC/USDT, 'SOL/USDT', 'WIF/USDT', 'SUI/USDT', 'JUP/USDT', 'PEPE/USDT', 'LINK/USDT', 'AAVE/USDT']
timeframe = '15m'

# === Анализ монеты ===
def analyze(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Индикаторы
        df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        bb = ta.volatility.BollingerBands(df['close'])
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        df['ema20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()

        latest = df.iloc[-1]
        close = latest['close']
        rsi = latest['rsi']
        macd_val = latest['macd']
        macd_sig = latest['macd_signal']
        bb_upper = latest['bb_upper']
        bb_lower = latest['bb_lower']
        ema20 = latest['ema20']

        # Упрощённые условия
        buy_score = 0
        sell_score = 0

        if rsi < 50:
            buy_score += 1
        if macd_val > macd_sig:
            buy_score += 1
        if close < bb_lower:
            buy_score += 1

        if rsi > 50:
            sell_score += 1
        if macd_val < macd_sig:
            sell_score += 1
        if close > bb_upper:
            sell_score += 1

        message = None

        if buy_score >= 2:
            message = f"LONG сигнал по {symbol}\nRSI: {rsi:.1f}, MACD вверх, цена у нижней границы BB."
        elif sell_score >= 2:
            message = f"SHORT сигнал по {symbol}\nRSI: {rsi:.1f}, MACD вниз, цена у верхней границы BB."

        # Доп. алерт по BTC при хорошем росте
        if symbol == 'BTC/USDT' and rsi > 60 and macd_val > macd_sig:
            message = f"⚠️ BTC активно растёт\nЦена: {close:.2f}, RSI: {rsi:.1f}, MACD: {macd_val:.4f} > Signal: {macd_sig:.4f}"

        if message:
            send_telegram_message(message)

    except Exception as e:
        print(f"[Ошибка] {symbol}: {e}")


# === Основной цикл ===
send_telegram_message("✅ Бот запущен и ожидает сигналы.")
while True:
    for symbol in symbols:
        analyze(symbol)
        time.sleep(1)
    time.sleep(60 * 15)  # Проверка каждые 15 минут
