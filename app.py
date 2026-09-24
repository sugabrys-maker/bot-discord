import os
import threading
import discord
from discord.ext import commands
from flask import Flask

# Inicjalizacja aplikacji Flask (wymagane przez Render do utrzymania usługi)
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot Discord z natychmiastowymi komendami / działa na Renderze!", 200


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# Konfiguracja bota Discord
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# WAŻNE: Wpisz tutaj ID swojego serwera Discord, aby komendy pojawiły się natychmiast!
# (Kliknij prawym przyciskiem myszy na nazwę swojego serwera na Discordzie -> Kopiuj ID)
MY_GUILD = discord.Object(
    id=1462137124043227228
)  # <--- ZAMIEŃ TE CYFRY NA SWOJE ID SERWERA


@bot.event
async def on_ready():
  print(f"Zalogowano pomyślnie jako: {bot.user.name}")
  try:
    # Kopiuje i natychmiast synchronizuje komendy dla Twojego serwera (brak opóźnienia)
    bot.tree.copy_global_to(guild=MY_GUILD)
    synced = await bot.tree.sync(guild=MY_GUILD)
    print(
        f"Zsynchronizowano natychmiast {len(synced)} komend(y) dla Twojego"
        " serwera!"
    )
  except Exception as e:
    print(f"Błąd podczas natychmiastowej synchronizacji komend: {e}")


# Definicja komendy /start
@bot.tree.command(
    name="start", description="Rozpocznij pracę z botem na Renderze"
)
async def start_command(interaction: discord.Interaction):
  await interaction.response.send_message(
      "Cześć! Jestem Twoim botem Discord z natychmiastowymi komendami ukośnika"
      " (/) uruchomionym na Renderze."
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

  # Uruchomienie serwera Flask w osobnym wątku (dla Render Web Service)
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.daemon = True
  flask_thread.start()

  # Uruchomienie bota Discord w głównym wątku
  bot.run(TOKEN)