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
symbols = ['SOL/USDT', 'WIF/USDT', 'SUI/USDT', 'JUP/USDT', 'PEPE/USDT', 'LINK/USDT', 'AAVE/USDT']
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
        df['supertrend'] = ta.supertrend(df['high'], df['low'], df['close'])['SUPERT_7_3.0']

        latest = df.iloc[-1]
        close = latest['close']
        rsi = latest['rsi']
        macd_val = latest['macd']
        macd_sig = latest['macd_signal']
        bb_upper = latest['bb_upper']
        bb_lower = latest['bb_lower']
        ema20 = latest['ema20']
        supertrend = latest['supertrend']
        volume = latest['volume']
        avg_volume = df['volume'].iloc[-20:].mean()

        # --- Стакан ордеров ---
        order_book = exchange.fetch_order_book(symbol, limit=5)
        bids = order_book['bids'][:5]
        asks = order_book['asks'][:5]
        best_bid = bids[0][0] if bids else 0
        best_ask = asks[0][0] if asks else 0
        spread = best_ask - best_bid if best_ask and best_bid else 0

        bid_volume = sum(b[1] for b in bids)
        ask_volume = sum(a[1] for a in asks)

        signal = None

        # BUY сигнал
        if (
            rsi < 50 and
            macd_val >= macd_sig and
            close < bb_lower and
            close > ema20 and
            close > supertrend and
            volume > avg_volume * 0.9 and
            bid_volume > ask_volume * 3
        ):
            signal = 'BUY'

        # SELL сигнал
        elif (
            rsi > 50 and
            macd_val <= macd_sig and
            close > bb_upper and
            close < ema20 and
            close < supertrend and
            volume > avg_volume * 0.9 and
            ask_volume > bid_volume * 3
        ):
            signal = 'SELL'

        if signal:
            # График
            plt.figure(figsize=(10, 5))
            plt.plot(df['timestamp'], df['close'], label='Цена', linewidth=2)
            plt.plot(df['timestamp'], df['ema20'], label='EMA20', linestyle='--')
            plt.plot(df['timestamp'], df['supertrend'], label='Supertrend', linestyle='-.')
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
                f"Цена: {close:.4f} | RSI: {rsi:.1f} | Объём: {volume:.1f}\n"
                f"MACD: {macd_val:.4f} | Signal: {macd_sig:.4f}\n"
                f"EMA20: {ema20:.2f} | Supertrend: {supertrend:.2f}\n"
                f"Best Bid: {best_bid:.4f} | Ask: {best_ask:.4f} | Спред: {spread:.4f}\n"
                f"Bid объём (top5): {bid_volume:.1f} | Ask объём (top5): {ask_volume:.1f}"
            )

            requests.post(
                f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto',
                data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption},
                files={'photo': buf}
            )

    except Exception as e:
        print(f"[Ошибка] {symbol}: {e}")

# === Основной цикл ===
send_telegram_message("✅ Бот запущен и ожидает сигналы.")
while True:
    for symbol in symbols:
        analyze(symbol)
        time.sleep(1)
    time.sleep(60 * 15)  # Проверка каждые 15 минут
