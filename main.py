import os
import asyncio
import ccxt
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")

exchange = ccxt.binance({'enableRateLimit': True})
client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

def get_market_data(symbol='ETH/USDT'):
    ticker = exchange.fetch_ticker(symbol)
    price = ticker['last']
    high_24 = ticker['high']
    low_24 = ticker['low']
    
    timeframes = ['5m','15m','30m','1h','2h','4h','6h','12h','1d','2d','3d','1w','1M']
    multi_tf = {}
    for tf in timeframes:
        ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=100)
        df = pd.DataFrame(ohlcv, columns=['ts','o','h','l','c','v'])
        df['rsi'] = ta.rsi(df['c'], length=14)
        df['atr'] = ta.atr(df['h'], df['l'], df['c'], length=14)
        macd_df = ta.macd(df['c'])
        df['macd_hist'] = macd_df['MACDh_12_26_9']
        latest = df.iloc[-1]
        multi_tf[tf] = {
            'price': round(latest['c'], 2),
            'rsi': round(latest['rsi'], 1),
            'macd_hist': round(latest['macd_hist'], 2) if pd.notna(latest['macd_hist']) else 0,
            'atr': round(latest['atr'], 2),
            'support': round(df['l'].tail(20).min(), 2),
            'resistance': round(df['h'].tail(20).max(), 2)
        }
    
    btc = exchange.fetch_ticker('BTC/USDT')
    weekly = "多头排列" if multi_tf['1w']['rsi'] > 55 else ("空头排列" if multi_tf['1w']['rsi'] < 45 else "震荡")
    monthly = "多头排列" if multi_tf['1M']['rsi'] > 55 else ("空头排列" if multi_tf['1M']['rsi'] < 45 else "震荡")
    
    return {
        'symbol': symbol, 'price': price, 'high_24': high_24, 'low_24': low_24,
        'atr_1h': multi_tf['1h']['atr'], 'multi_tf': multi_tf,
        'btc_price': btc['last'], 'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'weekly_trend': weekly, 'monthly_trend': monthly
    }

def call_grok(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="grok-4.20",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Grok调用失败: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 V2.6 Grok 机器人已启动！发送 /quick 开始使用")

async def quick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_market_data('ETH/USDT')
    entry = data['price']
    sl = round(entry - data['atr_1h']*1.7, 2)
    tp1 = round(entry + data['atr_1h']*1.5, 2)
    tp2 = round(entry + data['atr_1h']*3, 2)
    tp3 = round(entry + data['atr_1h']*5, 2)
    
    text = f"""⚡ ETH 快速决策

价格：${entry} | ATR：${data['atr_1h']}
方向：多（周线{data['weekly_trend']} | 月线{data['monthly_trend']}）

计划：
入场 ${entry} | 止损 ${sl}
TP1 ${tp1}（40%）→ 保本
TP2 ${tp2}（40%）→ 锁利
TP3 ${tp3}（20%）→ 移动止损

回复 /calc 你的账户权益 获取精确仓位"""
    await update.message.reply_text(text)

async def calc_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("用法：/calc 10000")
        return
    equity = float(context.args[0])
    data = get_market_data('ETH/USDT')
    risk = equity * 0.01
    r1, r2, r3 = risk*0.4, risk*0.35, risk*0.25
    entry, sl = data['price'], round(data['price'] - data['atr_1h']*1.7, 2)
    pos1 = round(r1 / (entry-sl), 4)
    pos2 = round(r2 / (entry-sl), 4)
    pos3 = round(r3 / (entry-sl), 4)
    
    await update.message.reply_text(
        f"💰 账户 ${equity} 精确仓位\n"
        f"最大风险 ${risk}\n"
        f"第一层 {pos1} ETH | 第二层 {pos2} ETH | 第三层 {pos3} ETH"
    )

async def eth_full(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_market_data('ETH/USDT')
    prompt = f"你是加密交易员，根据以下数据用中文给出简洁分析：价格${data['price']}，周线{data['weekly_trend']}，月线{data['monthly_trend']}，1H RSI {data['multi_tf']['1h']['rsi']}"
    grok_answer = call_grok(prompt)
    await update.message.reply_text(f"🤖 Grok 总结：\n\n{grok_answer}")

async def grok_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("用法：/grok_analyze 现在ETH适合做多吗？")
        return
    question = " ".join(context.args)
    answer = call_grok(f"你是加密货币专家，请用中文回答：{question}")
    await update.message.reply_text(f"🤖 Grok：\n\n{answer}")

async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quick", quick))
    app.add_handler(CommandHandler("calc", calc_position))
    app.add_handler(CommandHandler("eth_full", eth_full))
    app.add_handler(CommandHandler("grok_analyze", grok_analyze))
    print("✅ 机器人启动成功！")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
