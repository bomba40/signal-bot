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

        # Индикаторы
        df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        bb = ta.volatility.BollingerBands(df['close'])
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        df['ema20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
        df['ema50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()

        # Последняя строка
        latest = df.iloc[-1]
        close = latest['close']
        rsi = latest['rsi']
        macd_val = latest['macd']
        macd_sig = latest['macd_signal']
        bb_upper = latest['bb_upper']
        bb_lower = latest['bb_lower']
        ema20 = latest['ema20']
        ema50 = latest['ema50']
        volume = latest['volume']
        avg_volume = df['volume'].iloc[-20:].mean()

        # Свечной паттерн: молот
        body = abs(latest['close'] - latest['open'])
        candle_range = latest['high'] - latest['low']
        lower_shadow = min(latest['open'], latest['close']) - latest['low']
        is_hammer = lower_shadow > body * 2 and body < candle_range * 0.3

        signal = None

        # --- BUY условия ---
        if (
            rsi < 35 and
            macd_val > macd_sig and
            close < bb_lower and
            close > ema20 > ema50 and
            volume > avg_volume and
            is_hammer
        ):
            signal = 'BUY'

        # --- SELL условия ---
        elif (
            rsi > 65 and
            macd_val < macd_sig and
            close > bb_upper and
            close < ema20 < ema50 and
            volume > avg_volume
        ):
            signal = 'SELL'

        if signal:
            # Построить график
            plt.figure(figsize=(10, 5))
            plt.plot(df['timestamp'], df['close'], label='Цена', linewidth=2)
            plt.plot(df['timestamp'], df['ema20'], label='EMA20', linestyle='--')
            plt.plot(df['timestamp'], df['ema50'], label='EMA50', linestyle='--')
            plt.axhline(bb_upper, color='red', linestyle=':', label='BB Верхняя')
            plt.axhline(bb_lower, color='green', linestyle=':', label='BB Нижняя')
            plt.title(f"{symbol} сигнал: {signal}")
            plt.xlabel("Время")
            plt.ylabel("Цена")
            plt.legend()

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close()

            caption = (
                f"{signal} сигнал по {symbol}\n"
                f"RSI: {rsi:.1f}, Объём: {volume:.1f}\n"
                f"MACD: {macd_val:.4f} | Signal: {macd_sig:.4f}\n"
                f"EMA20: {ema20:.2f}, EMA50: {ema50:.2f}\n"
                f"Цена: {close:.4f}"
            )

            requests.post(
                f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto',
                data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption},
                files={'photo': buf}
            )

    except Exception as e:
        print(f"[Ошибка] {symbol}: {e}")

# === Цикл проверки ===
while True:
    for symbol in symbols:
        analyze(symbol)
        time.sleep(1)
    time.sleep(60 * 15)
