import os
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
            max_tokens=900,
            temperature=0.55
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Grok调用失败: {str(e)}"

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 Grok 交易机器人（V2.4专业版）已启动！\n\n可用命令：\n/quick - ETH专业全盘分析\n/calc 10000 - 计算仓位\n/grok_analyze 现在适合做多吗？")

@bot.message_handler(commands=['quick'])
def quick(message):
    ticker = exchange.fetch_ticker('ETH/USDT')
    price = ticker['last']
    
    prompt = f"""你是专业加密货币交易员。请严格按照以下结构，用中文给出ETH专业分析（控制在350字内）：

**当前价格**：${price}

**快速决策摘要**：
- 主偏向：多 / 空 / 观望（置信度：__ /10）
- 核心驱动：技术面 / 链上 / 宏观
- 建议操作：挂单入场 / 观望
- 预期R:R：至少1:2.5

**技术面判断**（多周期）：
- 短期趋势（1H）：_________
- 中线趋势（4H/日线）：_________
- 关键支撑/阻力：_________ / _________

**风险提示**（至少2点）：
- _________
- _________

**操作建议**：
- 入场区间：_________
- 止损：_________（ATR动态）
- 三档止盈：Tier1 $___ (40%) | Tier2 $___ (40%) | Tier3 $___ (20% + trail)

**一句话结论**：_________"""

    answer = call_grok(prompt)
    bot.reply_to(message, f"📊 ETH 专业分析（V2.4）\n\n{answer}")

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
    answer = call_grok(f"你是加密货币专家，请用中文给出专业分析：{question}")
    bot.reply_to(message, f"🤖 Grok：\n\n{answer}")

print("✅ V2.4专业版机器人启动成功！")
bot.polling()
