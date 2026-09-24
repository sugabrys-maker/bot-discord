import os
import threading
import discord
from discord.ext import commands
from flask import Flask

# Inicjalizacja aplikacji Flask (wymagane przez Render)
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot Discord z komendami / działa poprawnie na Renderze!", 200


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# Konfiguracja bota Discord z użyciem commands.Bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
  print(f"Zalogowano pomyślnie jako: {bot.user.name}")
  try:
    # Synchronizacja komend ukośnika (/) z Discordem
    synced = await bot.tree.sync()
    print(f"Zsynchronizowano pomyślnie {len(synced)} komend(y) ukośnika.")
  except Exception as e:
    print(f"Błąd podczas synchronizacji komend: {e}")


# Definicja komendy /start
@bot.tree.command(
    name="start", description="Rozpocznij pracę z botem na Renderze"
)
async def start_command(interaction: discord.Interaction):
  await interaction.response.send_message(
      "Cześć! Jestem Twoim botem Discord z komendami ukośnika (/)"
      " uruchomionym na Renderze."
  )


# Definicja komendy /ping
@bot.tree.command(name="ping", description="Sprawdź opóźnienie i status bota")
async def ping_command(interaction: discord.Interaction):
  latency = round(bot.latency * 1000)
  await interaction.response.send_message(f"Pong! 🏓 Opóźnienie: {latency}ms")


TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

if __name__ == "__main__":
  if not TOKEN:
    print("BŁĄD: Brak zmiennej środowiskowej DISCORD_BOT_TOKEN!")
    exit(1)

  # Uruchomienie serwera Flask w tle dla Rendera
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.daemon = True
  flask_thread.start()

  # Uruchomienie bota Discord
  bot.run(TOKEN)