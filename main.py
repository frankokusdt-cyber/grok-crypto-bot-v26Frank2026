import os
import time
import telebot
import ccxt
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
exchange = ccxt.okx({'enableRateLimit': True})
client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

def call_grok(prompt):
    try:
        response = client.chat.completions.create(
            model="grok-4.20",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Grok调用失败: {str(e)}"

@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot.reply_to(message, 
        "🚀 Grok 交易机器人（OKX专业版）已启动！\n\n"
        "可用命令：\n"
        "/quick - ETH详细全盘分析\n"
        "/btc - BTC详细分析\n"
        "/eth_btc - ETH/BTC相对强弱\n"
        "/funding - 资金费率快照\n"
        "/oi - 未平仓合约分析\n"
        "/calc 10000 - 计算精确仓位\n"
        "/grok_analyze 现在适合做多吗？"
    )

@bot.message_handler(commands=['quick'])
def quick(message):
    time.sleep(1.5)  # 防止限流
    try:
        ticker = exchange.fetch_ticker('ETH/USDT')
        price = ticker['last']
        
        prompt = f"""你是专业加密货币交易员。请用中文给出详细专业分析（控制在650字内）：

当前ETH价格：${price}

**快速决策摘要**
- 主偏向 + 置信度（1-10分）
- 核心驱动
- 建议操作 + 预期R:R

**技术面判断**
- 短期趋势 + 中线趋势
- 关键支撑/阻力
- RSI、MACD、ATR状态

**风险提示**（至少3点）
**操作建议**
- 入场区间 + 止损 + 三档止盈 + 杠杆 + 仓位控制

**一句话结论**"""

        answer = call_grok(prompt)
        bot.reply_to(message, f"📊 ETH 详细分析\n\n{answer}")
    except Exception as e:
        bot.reply_to(message, f"暂时无法获取数据，请稍后再试。错误：{str(e)}")

@bot.message_handler(commands=['btc'])
def btc(message):
    time.sleep(1.5)
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
        prompt = f"当前BTC价格${price}，请用中文给出详细分析（决策摘要 + 技术面 + 风险 + 操作建议 + 结论）。"
        answer = call_grok(prompt)
        bot.reply_to(message, f"📊 BTC 详细分析\n\n{answer}")
    except:
        bot.reply_to(message, "暂时无法获取BTC数据，请稍后再试。")

@bot.message_handler(commands=['eth_btc'])
def eth_btc(message):
    time.sleep(1.5)
    try:
        ticker = exchange.fetch_ticker('ETH/BTC')
        ratio = ticker['last']
        prompt = f"当前ETH/BTC汇率是{ratio}，请用中文分析相对强弱和机会。"
        answer = call_grok(prompt)
        bot.reply_to(message, f"📊 ETH/BTC 相对强弱分析\n\n{answer}")
    except:
        bot.reply_to(message, "暂时无法获取数据，请稍后再试。")

@bot.message_handler(commands=['funding
