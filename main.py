import discord
from discord.ext import commands
from collections import defaultdict
from dotenv import load_dotenv
import os
import random
import time

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ── Bot setup ──────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ── Config ─────────────────────────────────────────────────────────────────────
TARGET_USERNAME = "lyamkatz"  # only watch this user
TARGET_CHANNEL  = "chess"          # only watch this channel

STREAK_LIMIT = 5          # consecutive messages before streak response
TOTAL_LIMIT  = 50         # total messages before total response
RAPID_LIMIT  = 3          # messages within RAPID_WINDOW seconds triggers rapid response
RAPID_WINDOW = 3.0        # seconds

# { channel_id: int } — consecutive message streak
streak_counts: dict[int, int] = defaultdict(int)

# global total message count for the target user (across all channels)
total_count: int = 0

# rapid-fire tracking: list of timestamps of recent messages (per channel)
rapid_timestamps: dict[int, list] = defaultdict(list)

# ── Bot responses (change these to whatever you want) ──────────────────────────

# Fired after 5 consecutive messages
STREAK_RESPONSES = [
    "Please go to #dailylyamyapping"
]

# Fired after 50 total messages
TOTAL_RESPONSES = [
    "Please go on an diet"
]

# Fired when 2 messages are sent within 3 seconds
RAPID_RESPONSES = [
    "Please take a break from yapping"
]

# Fired when a single message has more than 10 words
LONG_MESSAGE_RESPONSES = [
    " HOLY YAP, no one asked, please save it for when the moon turns red"
]

LONG_MESSAGE_LIMIT = 18   # word count threshold

# ── Events ─────────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


@bot.event
async def on_message(message: discord.Message):
    global total_count

    # Ignore messages from bots (including ourselves)
    if message.author.bot:
        return

    # Only act in the #chess channel
    if message.channel.name != TARGET_CHANNEL:
        await bot.process_commands(message)
        return

    channel_id = message.channel.id

    if message.author.name == TARGET_USERNAME:
        now = time.monotonic()

        # ── Feature 1: 5 consecutive messages ─────────────────────────────────
        streak_counts[channel_id] += 1
        if streak_counts[channel_id] == STREAK_LIMIT:
            await message.channel.send(f"{message.author.mention} {random.choice(STREAK_RESPONSES)}")
            streak_counts[channel_id] = 0

        # ── Feature 2: 50 total messages ──────────────────────────────────────
        total_count += 1
        if total_count % TOTAL_LIMIT == 0:
            await message.channel.send(f"{message.author.mention} {random.choice(TOTAL_RESPONSES)}")

        # ── Feature 3: 2 messages within 3 seconds ────────────────────────────
        timestamps = rapid_timestamps[channel_id]
        timestamps.append(now)
        # Keep only timestamps within the window
        rapid_timestamps[channel_id] = [t for t in timestamps if now - t <= RAPID_WINDOW]
        if len(rapid_timestamps[channel_id]) >= RAPID_LIMIT:
            await message.channel.send(f"{message.author.mention} {random.choice(RAPID_RESPONSES)}")
            # Clear so it doesn't spam repeatedly
            rapid_timestamps[channel_id] = []

        # ── Feature 4: message over 10 words ──────────────────────────────────
        word_count = len(message.content.split())
        if word_count > LONG_MESSAGE_LIMIT:
            await message.channel.send(f"{message.author.mention} {random.choice(LONG_MESSAGE_RESPONSES)}")

    else:
        # Someone else spoke — reset the consecutive streak
        streak_counts[channel_id] = 0

    # Allow commands to still work
    await bot.process_commands(message)


# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not TOKEN:
        raise ValueError(
            "No DISCORD_TOKEN found. Add it to a .env file:\n"
            "  DISCORD_TOKEN=your-token-here"
        )
    bot.run(TOKEN)
