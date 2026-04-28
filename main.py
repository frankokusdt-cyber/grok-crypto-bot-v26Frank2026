import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from openai import OpenAI
import ccxt

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")

exchange = ccxt.binance({'enableRateLimit': True})
client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

def call_grok(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="grok-4.20",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Grok调用失败: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Grok 交易机器人（稳定版）已启动！\n\n"
        "可用命令：\n"
        "/quick - ETH快速分析\n"
        "/calc 10000 - 计算精确仓位\n"
        "/grok_analyze 现在ETH适合做多吗？"
    )

async def quick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ticker = exchange.fetch_ticker('ETH/USDT')
    price = ticker['last']
    prompt = f"当前ETH价格是${price}，请用中文给出简短分析和交易建议（多/空/观望 + 理由 + 风险）"
    answer = call_grok(prompt)
    await update.message.reply_text(f"📊 ETH 快速分析\n\n{answer}")

async def calc_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("用法：/calc 10000（输入账户总权益）")
        return
    equity = float(context.args[0])
    ticker = exchange.fetch_ticker('ETH/USDT')
    price = ticker['last']
    risk = equity * 0.01
    await update.message.reply_text(
        f"💰 账户 ${equity}\n"
        f"最大风险：${risk}（1%规则）\n"
        f"当前ETH价格：${price}\n\n"
        f"建议：根据1%风险规则手动计算仓位"
    )

async def grok_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("用法：/grok_analyze 现在比特币适合长期持有吗？")
        return
    question = " ".join(context.args)
    answer = call_grok(f"你是加密货币专家，请用中文回答：{question}")
    await update.message.reply_text(f"🤖 Grok 回答：\n\n{answer}")

async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quick", quick))
    app.add_handler(CommandHandler("calc", calc_position))
    app.add_handler(CommandHandler("grok_analyze", grok_analyze))
    print("✅ 稳定版机器人启动成功！")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
