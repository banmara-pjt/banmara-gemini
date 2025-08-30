import os
import threading
import asyncio
from flask import Flask, jsonify
import discord
from discord.ext import commands

# Flask アプリ
app = Flask(__name__)

@app.route("/")
def index():
    return "Hello, Render & Discord Bot!"

@app.route("/json")
def json_route():
    return jsonify({"message": "Hello from JSON!", "status": "ok"})

# Discord Bot 設定
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# ---- Intent 設定（重要！）----
intents = discord.Intents.default()
intents.message_content = True   # Message Content Intent を有効化
# --------------------------------

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# Flask から Discord に通知を送るエンドポイント
@app.route("/notify")
def notify():
    if CHANNEL_ID is None:
        return "CHANNEL_ID not set in environment."

    channel = bot.get_channel(int(CHANNEL_ID))
    if channel:
        asyncio.run_coroutine_threadsafe(channel.send("テスト通知です！"), bot.loop)
        return "Notification sent!"
    return "Channel not found."

# Bot を別スレッドで起動
def run_bot():
    bot.run(TOKEN)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
