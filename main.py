import os
import asyncio
import discord
from discord.ext import commands
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

# 1. Konfiguracja bota Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"[DISCORD] Zalogowano pomyślnie jako: {bot.user} (ID: {bot.user.id})")

@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! Strona i bot działają razem na Renderze! Opóźnienie: {latency}ms")

# 2. Uruchomienie bota w tle podczas startu serwera (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("[BŁĄD] Brak tokena bota w zmiennych środowiskowych!")
    else:
        # Uruchamiamy bota jako zadanie w tle, żeby nie blokować serwera WWW
        asyncio.create_task(bot.start(token))
    yield
    # Zamknięcie bota przy wyłączaniu serwera
    await bot.close()

# 3. Inicjalizacja strony internetowej FastAPI
app = FastAPI(lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    
    
    
        
        HeavenCloud & Render Bot