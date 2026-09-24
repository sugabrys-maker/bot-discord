import asyncio
import os
import threading
import discord
from discord.ext import commands
from flask import Flask

# Inicjalizacja aplikacji Flask (wymagane przez Render)
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot Discord z systemem ticketów działa poprawnie na Renderze!", 200


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# Konfiguracja bota Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ID Twojego serwera Discord
MY_GUILD = discord.Object(id=1462137124043227228)


# Widok przycisku do tworzenia ticketu (trwały)
class TicketButtonView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(
      label="Utwórz ticket",
      style=discord.ButtonStyle.green,
      custom_id="persistent_create_ticket",
      emoji="📩",
  )
  async def create_ticket(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    guild = interaction.guild
    user = interaction.user

    # Sprawdzenie, czy użytkownik ma już otwarto kanał ticketu
    existing_channel = discord.utils.get(
        guild.text_channels, name=f"ticket-{user.name.lower()}"
    )
    if existing_channel:
      await interaction.response.send_message(
          f"Masz już otwarty ticket: {existing_channel.mention}", ephemeral=True
      )
      return

    # Uprawnienia: widzi tylko użytkownik, bot i administratorzy
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        ),
    }

    # Pobierz lub utwórz kategorię TICKETS
    category = discord.utils.get(guild.categories, name="TICKETS")
    if not category:
      category = await guild.create_category("TICKETS")

    # Tworzenie prywatnego kanału
    ticket_channel = await guild.create_text_channel(
        f"ticket-{user.name}", category=category, overwrites=overwrites
    )

    # Wiadomość powitalna w tickecie z przyciskiem zamknięcia
    await ticket_channel.send(
        f"Witaj {user.mention}! W czym możemy Ci pomóc?\nAdministracja wkrótce"
        " odpowie.",
        view=CloseTicketView(),
    )

    await interaction.response.send_message(
        f"✅ Utworzono Twój ticket: {ticket_channel.mention}!", ephemeral=True
    )


# Widok przycisku do zamykania ticketu
class CloseTicketView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(
      label="Zamknij ticket",
      style=discord.ButtonStyle.red,
      custom_id="persistent_close_ticket",
      emoji="🔒",
  )
  async def close_ticket(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    await interaction.response.send_message(
        "🔒 Zamykanie ticketa za 3 sekundy..."
    )
    await asyncio.sleep(3)
    try:
      await interaction.channel.delete()
    except Exception:
      pass


@bot.event
async def on_ready():
  print(f"Zalogowano pomyślnie jako: {bot.user.name}")

  # Rejestracja trwała widoków przycisków, aby działały po restarcie bota
  bot.add_view(TicketButtonView())
  bot.add_view(CloseTicketView())

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


# Komenda /wyslij (obsługuje emotki poprawnie)
@bot.tree.command(
    name="wyslij",
    description=(
        "Wysyła określoną wiadomość przez bota (obsługuje emotki)"
    ),
)
async def wyslij_command(
    interaction: discord.Interaction,
    tekst: str,
    kanal: discord.TextChannel = None,
):
  docelowy_kanal = kanal or interaction.channel
  await docelowy_kanal.send(tekst)
  await interaction.response.send_message(
      f"✅ Pomyślnie wysłano wiadomość na kanale {docelowy_kanal.mention}!",
      ephemeral=True,
  )


# Komenda /changelog (w stylu BLOWHC.PL)
@bot.tree.command(
    name="changelog", description="Tworzy profesjonalny changelog serwera"
)
async def changelog_command(
    interaction: discord.Interaction,
    tryb: str,
    zmiany: str,
    wiadomosc_wstepna: str = "Wprowadziliśmy zmiany na serwerze!",
    kanal: discord.TextChannel = None,
):
  docelowy_kanal = kanal or interaction.channel

  embed = discord.Embed(
      title=f"🛠️ AKTUALIZACJA ({tryb.upper()})",
      description=f"{wiadomosc_wstepna}\n\n> {zmiany}",
      color=discord.Color.gold(),
  )
  embed.set_author(name="BLOWHC.PL • CHANGELOG")
  embed.set_footer(
      text=f"Wprowadzone przez: {interaction.user.name}",
      icon_url=interaction.user.display_avatar.url,
  )

  await docelowy_kanal.send(embed=embed)
  await interaction.response.send_message(
      f"✅ Pomyślnie opublikowano changelog na kanale"
      f" {docelowy_kanal.mention}!",
      ephemeral=True,
  )


# Nowa komenda /ticket wysyłająca panel do tworzenia ticketów
@bot.tree.command(
    name="ticket", description="Wysyła panel do tworzenia ticketów na kanał"
)
async def ticket_command(
    interaction: discord.Interaction, kanal: discord.TextChannel = None
):
  docelowy_kanal = kanal or interaction.channel

  embed = discord.Embed(
      title="🎫 SYSTEM TICKETÓW - BLOWHC.PL",
      description=(
          "Masz problem, pytanie lub chcesz coś zgłosić?\nKliknij przycisk"
          " poniżej, aby utworzyć prywatny ticket z administracją."
      ),
      color=discord.Color.blue(),
  )
  embed.set_footer(text="BLOWHC.PL • System Pomocy")

  await docelowy_kanal.send(embed=embed, view=TicketButtonView())
  await interaction.response.send_message(
      f"✅ Pomyślnie wysłano panel ticketów na kanał {docelowy_kanal.mention}!",
      ephemeral=True,
  )


TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

if __name__ == "__main__":
  if not TOKEN:
    print("BŁĄD: Brak zmiennej środowiskowej DISCORD_BOT_TOKEN!")
    exit(1)

  flask_thread = threading.Thread(target=run_flask)
  flask_thread.daemon = True
  flask_thread.start()

  bot.run(TOKEN)