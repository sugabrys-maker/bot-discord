import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Ładowanie tokena bota
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Konfiguracja intencji bota
intents = discord.Intents.default()
intents.message_content = True  # Wymagane do czytania wiadomości z komendami

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Wykonuje się raz po pomyślnym uruchomieniu bota na serwerze."""
    print(f"Zalogowano pomyślnie jako: {bot.user} (ID: {bot.user.id})")
    print("Bot działa stabilnie na darmowym hostingu HeavenCloud!")

@bot.command(name="ping")
async def ping(ctx):
    """Komenda testowa sprawdzająca czy bot odpowiada."""
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! Działam na HeavenCloud! Opóźnienie: {latency}ms")

# Uruchomienie bota
if __name__ == "__main__":
    if not TOKEN:
        print("BŁĄD: Nie znaleziono tokena bota!")
    else:
        bot.run(TOKEN)