import os
import threading
import discord
from discord.ext import commands
from flask import Flask

# Inicjalizacja aplikacji Flask (wymagane przez Render do utrzymania usługi)
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot Discord z komendą /wyslij działa poprawnie na Renderze!", 200


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# Konfiguracja bota Discord
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# TUTAJ WPISZ ID SWOJEGO SERWERA (żeby komendy działały natychmiast)
MY_GUILD = discord.Object(id=1462137124043227228)  # <--- ZMIEŃ NA SWOJE ID


@bot.event
async def on_ready():
  print(f"Zalogowano pomyślnie jako: {bot.user.name}")
  try:
    bot.tree.copy_global_to(guild=MY_GUILD)
    synced = await bot.tree.sync(guild=MY_GUILD)
    print(
        f"Zsynchronizowano natychmiast {len(synced)} komend(y) dla Twojego"
        " serwera!"
    )
  except Exception as e:
    print(f"Błąd podczas natychmiastowej synchronizacji komend: {e}")


# Komenda /start
@bot.tree.command(
    name="start", description="Rozpocznij pracę z botem na Renderze"
)
async def start_command(interaction: discord.Interaction):
  await interaction.response.send_message(
      "Cześć! Jestem Twoim botem Discord uruchomionym na Renderze."
  )


# Komenda /ping
@bot.tree.command(name="ping", description="Sprawdź opóźnienie i status bota")
async def ping_command(interaction: discord.Interaction):
  latency = round(bot.latency * 1000)
  await interaction.response.send_message(f"Pong! 🏓 Opóźnienie: {latency}ms")


# Nowa komenda /wyslij
@bot.tree.command(
    name="wyslij", description="Wysyła określoną wiadomość przez bota"
)
async def wyslij_command(
    interaction: discord.Interaction,
    tekst: str,
    kanal: discord.TextChannel = None,
):
  # Jeśli nie podano kanału, wyślij na obecnym kanale
  docelowy_kanal = kanal or interaction.channel

  # Wysłanie wiadomości przez bota na wskazany kanał
  await docelowy_kanal.send(tekst)

  # Prywatne potwierdzenie dla Ciebie, że wiadomość została wysłana
  await interaction.response.send_message(
      f"✅ Pomyślnie wysłano wiadomość na kanale {docelowy_kanal.mention}!",
      ephemeral=True,
  )


TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

if __name__ == "__main__":
  if not TOKEN:
    print("BŁĄD: Brak zmiennej środowiskowej DISCORD_BOT_TOKEN!")
    exit(1)

  # Uruchomienie serwera Flask w osobnym wątku
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.daemon = True
  flask_thread.start()

  # Uruchomienie bota Discord
  bot.run(TOKEN)