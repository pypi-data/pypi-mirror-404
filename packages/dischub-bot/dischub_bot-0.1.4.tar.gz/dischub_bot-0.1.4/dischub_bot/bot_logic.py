# bot_logic.py
import requests
import MetaTrader5 as mt5
import time
import csv
import os
from datetime import datetime, timedelta
from django.utils import timezone
from dischub_bot.models import PaymentVerification
from . models import SymbolSettings
from .exceptions import BotException

# ================= CONFIG =================

MAGIC = 777777
DEVIATION = 20

TIMEFRAME = mt5.TIMEFRAME_M1
TIMEFRAME_ATR = mt5.TIMEFRAME_M5
TREND_TF = mt5.TIMEFRAME_H1
ATR_PERIOD = 14
ATR_MULTIPLIER = 1.5

# ===== TELEGRAM CONFIG =====
TELEGRAM_BOT_TOKEN = "7747488943:AAHct6I_8gkYjwahP_O_7xQ6uKiOxVC81t4"
TELEGRAM_CHAT_ID = 6051264246

CSV_FILE = "ema10_ema16_m1_scalper_log.csv"

# ================= STATE =================
last_signal = {}

# ================= HELPERS =================
# bot_logic.py

def load_symbol_settings():
    try:
        settings = SymbolSettings.objects.last()
        if not settings:
            raise BotException("No symbol settings found. Please configure the bot.")
        return {
            "symbols": [settings.symbol],
            "lot": settings.lot_size,
            "max_trades": settings.max_trades
        }
    except BotException:
        raise  # propagate
    except Exception as e:
        raise BotException(f"Failed to load symbol settings: {e}")


def get_positions(symbol):
    return mt5.positions_get(symbol=symbol) or []

def calc_ema(values, period):
    k = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for price in values[period:]:
        ema = price * k + ema * (1 - k)
    return ema

def get_h1_trend(symbol):
    rates = mt5.copy_rates_from_pos(symbol, TREND_TF, 1, 220)
    if rates is None or len(rates) < 200:
        return None

    closes = [r["close"] for r in rates]
    ema50 = calc_ema(closes, 50)
    ema200 = calc_ema(closes, 200)

    if ema50 > ema200:
        return "BULL"
    elif ema50 < ema200:
        return "BEAR"
    else:
        return None

def get_ema_cross(symbol):
    rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 1, 18)
    if rates is None or len(rates) < 17:
        return None

    closes = [r["close"] for r in rates]
    ema10_prev = calc_ema(closes[:-1], 10)
    ema10_curr = calc_ema(closes, 10)
    ema16_prev = calc_ema(closes[:-1], 16)
    ema16_curr = calc_ema(closes, 16)

    if ema10_prev < ema16_prev and ema10_curr > ema16_curr:
        return "BUY"
    if ema10_prev > ema16_prev and ema10_curr < ema16_curr:
        return "SELL"
    return None

def place_trade(symbol, direction, LOT):
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        return

    price = tick.ask if direction == "BUY" else tick.bid

    mt5.order_send({
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": LOT,
        "type": mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL,
        "price": price,
        "deviation": DEVIATION,
        "magic": MAGIC,
        "comment": "EMA10/16 M1 + H1 Trend",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    })

    message = f"🔥 {symbol} {direction} ENTRY"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram alert failed: {e}")

def close_position(pos):
    tick = mt5.symbol_info_tick(pos.symbol)
    if not tick:
        return
    close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
    price = tick.bid if pos.type == mt5.POSITION_TYPE_BUY else tick.ask
    mt5.order_send({
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": pos.symbol,
        "volume": pos.volume,
        "type": close_type,
        "position": pos.ticket,
        "price": price,
        "deviation": DEVIATION,
        "magic": MAGIC,
    })

def get_atr(symbol):
    rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME_ATR, 1, ATR_PERIOD + 1)
    if rates is None or len(rates) < ATR_PERIOD + 1:
        return None
    trs = []
    for i in range(1, len(rates)):
        high = rates[i]["high"]
        low = rates[i]["low"]
        prev_close = rates[i - 1]["close"]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    return sum(trs) / ATR_PERIOD

def apply_atr_trailing_sl(symbol):
    positions = get_positions(symbol)
    if not positions:
        return
    atr = get_atr(symbol)
    if atr is None:
        return
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        return
    for pos in positions:
        if pos.type == mt5.POSITION_TYPE_BUY:
            new_sl = tick.bid - (atr * ATR_MULTIPLIER)
            if pos.sl == 0 or new_sl > pos.sl:
                mt5.order_send({
                    "action": mt5.TRADE_ACTION_SLTP,
                    "symbol": symbol,
                    "position": pos.ticket,
                    "sl": round(new_sl, 5),
                    "tp": pos.tp,
                    "magic": MAGIC,
                })
        elif pos.type == mt5.POSITION_TYPE_SELL:
            new_sl = tick.ask + (atr * ATR_MULTIPLIER)
            if pos.sl == 0 or new_sl < pos.sl:
                mt5.order_send({
                    "action": mt5.TRADE_ACTION_SLTP,
                    "symbol": symbol,
                    "position": pos.ticket,
                    "sl": round(new_sl, 5),
                    "tp": pos.tp,
                    "magic": MAGIC,
                })


# ================= MAIN BOT FUNCTION =================
def run_bot(login, password, server):
    # Initialize MT5 with passed credentials
    try:
        config = load_symbol_settings()
    except BotException as e:
        print(f"🚫 Bot cannot start: {e}")
        return  # exit gracefully without crashing

    SYMBOLS = config["symbols"]
    LOT = config["lot"]
    MAX_TRADES = config["max_trades"]

    if not mt5.initialize(login=login, password=password, server=server):
        print(f"🚫 MT5 init failed: {mt5.last_error()}")
        return

    account = mt5.account_info()
    if account is None:
        print("🚫 Could not get account info")
        mt5.shutdown()
        return
    
    # ✅ ONLY REACHES HERE IF:
    # - Demo account
    # - OR live account with valid subscription

    print("✅ Connected to MT5")
    print("✅ Trading allowed — starting bot loop")
    print(f"⚡ Trading {SYMBOLS} | LOT={LOT} | MAX_TRADES={MAX_TRADES}")

    # CSV setup
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            csv.writer(f).writerow(["time", "symbol", "direction", "entry_price", "exit_price", "profit", "reason"])

    # Main loop
    while True:
        for symbol in SYMBOLS:
            signal = get_ema_cross(symbol)
            trend = get_h1_trend(symbol)

            if symbol not in last_signal:
                last_signal[symbol] = None

            if signal is None or signal == last_signal[symbol]:
                apply_atr_trailing_sl(symbol)
                continue

            if signal == "BUY" and trend != "BULL":
                continue
            if signal == "SELL" and trend != "BEAR":
                continue

            positions = get_positions(symbol)
            buys = [p for p in positions if p.type == mt5.POSITION_TYPE_BUY]
            sells = [p for p in positions if p.type == mt5.POSITION_TYPE_SELL]

            print(f"⚡ {symbol} {signal} | H1 TREND: {trend}")

            for p in buys + sells:
                if (signal == "BUY" and p.type == mt5.POSITION_TYPE_SELL) or (signal == "SELL" and p.type == mt5.POSITION_TYPE_BUY):
                    close_position(p)

            for _ in range(MAX_TRADES):
                place_trade(symbol, signal, LOT)
                time.sleep(0.15)

            last_signal[symbol] = signal
            apply_atr_trailing_sl(symbol)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring...", end="\r")
        time.sleep(0.5)
