import os
import telebot
import ccxt
import pandas as pd
import pandas_ta as ta
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
exchange = ccxt.okx({'enableRateLimit': True})
client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

def get_multi_tf_data(symbol='ETH/USDT'):
    timeframes = ['15m', '1h', '4h', '12h', '1d']   # ← 只保留5个关键周期，减轻负担
    result = {}
    for tf in timeframes:
        ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=80)
        df = pd.DataFrame(ohlcv, columns=['ts','o','h','l','c','v'])
        df['rsi'] = ta.rsi(df['c'], length=14)
        df['atr'] = ta.atr(df['h'], df['l'], df['c'], length=14)
        macd = ta.macd(df['c'])
        df['macd_hist'] = macd['MACDh_12_26_9']
        latest = df.iloc[-1]
        result[tf] = {
            'price': round(latest['c'], 2),
            'rsi': round(latest['rsi'], 1),
            'macd': round(latest['macd_hist'], 2),
            'atr': round(latest['atr'], 2),
            'support': round(df['l'].tail(25).min(), 2),
            'resistance': round(df['h'].tail(25).max(), 2)
        }
    return result

def call_grok(prompt):
    try:
        response = client.chat.completions.create(
            model="grok-4.3",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1100,
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Grok调用失败: {str(e)}"

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 Grok 交易机器人（轻量多周期版）已启动！\n\n可用命令：\n/quick - ETH 5周期详细分析\n/calc 10000 - 计算仓位")

@bot.message_handler(commands=['quick'])
def quick(message):
    data = get_multi_tf_data('ETH/USDT')
    
    prompt = f"""你是专业加密货币交易员。请根据以下5个周期数据，用中文给出详细专业分析（控制在650字内）：

当前价格：${data['1h']['price']}

**多周期技术面**：
15m: RSI {data['15m']['rsi']} | MACD {data['15m']['macd']} | 支撑 {data['15m']['support']} | 阻力 {data['15m']['resistance']}
1h : RSI {data['1h']['rsi']}  | MACD {data['1h']['macd']}  | 支撑 {data['1h']['support']} | 阻力 {data['1h']['resistance']}
4h : RSI {data['4h']['rsi']}  | MACD {data['4h']['macd']}  | 支撑 {data['4h']['
