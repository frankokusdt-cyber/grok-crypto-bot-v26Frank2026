import os
import telebot
import ccxt
from openai import OpenAI

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
exchange = ccxt.binance({'enableRateLimit': True})
client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

def call_grok(prompt):
    try:
        response = client.chat.completions.create(
            model="grok-4.20",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        return response.choices[0].message.content
    except:
        return "Grok暂时无法回答"

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 Grok 交易机器人已启动！\n\n可用命令：\n/quick - ETH快速分析\n/calc 10000 - 计算仓位\n/grok_analyze 现在适合做多吗？")

@bot.message_handler(commands=['quick'])
def quick(message):
    ticker = exchange.fetch_ticker('ETH/USDT')
    price = ticker['last']
    prompt = f"当前ETH价格是${price}，请用中文给出简短分析和交易建议"
    answer = call_grok(prompt)
    bot.reply_to(message, f"📊 ETH 快速分析\n\n{answer}")

@bot.message_handler(commands=['calc'])
def calc(message):
    try:
        equity = float(message.text.split()[1])
        risk = equity * 0.01
        bot.reply_to(message, f"💰 账户 ${equity}\n最大风险：${risk}（1%规则）")
    except:
        bot.reply_to(message, "用法：/calc 10000")

@bot.message_handler(commands=['grok_analyze'])
def grok_analyze(message):
    question = message.text.replace('/grok_analyze', '').strip()
    if not question:
        bot.reply_to(message, "用法：/grok_analyze 现在ETH适合做多吗？")
        return
    answer = call_grok(f"你是加密货币专家，请用中文回答：{question}")
    bot.reply_to(message, f"🤖 Grok：\n\n{answer}")

print("✅ 机器人启动成功！")
bot.polling()
