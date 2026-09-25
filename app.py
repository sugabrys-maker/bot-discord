import asyncio
import os
import threading
import time
import discord
from discord.ext import commands
from flask import Flask

# Inicjalizacja aplikacji Flask (wymagane przez Render i UptimeRobot)
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot Discord z systemem ticketów i banerów działa na Renderze!", 200


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# Konfiguracja bota Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ID Twojego serwera Discord
MY_GUILD = discord.Object(id=1462137124043227228)


# Modal do podania powodu zamknięcia ticketa przez administratora
class CloseTicketModal(discord.ui.Modal, title="Powód zamknięcia ticketa"):

  def __init__(self, ticket_type, creator, claimed_by):
    super().__init__()
    self.ticket_type = ticket_type
    self.creator = creator
    self.claimed_by = claimed_by

  powod = discord.ui.TextInput(
      label="Powód zamknięcia",
      placeholder="Wpisz powód zamknięcia ticketa...",
      style=discord.TextStyle.paragraph,
      required=True,
  )

  async def on_submit(self, interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    powod_tekst = self.powod.value
    admin = interaction.user
    guild = interaction.guild
    channel = interaction.channel

    log_channel = discord.utils.get(guild.text_channels, name="ticket-logs")
    if not log_channel:
      category = discord.utils.get(guild.categories, name="TICKETS")
      log_channel = await guild.create_text_channel(
          "ticket-logs", category=category
      )

    log_embed = discord.Embed(
        title="📁 ARCHIWUM / HISTORIA TICKETA", color=discord.Color.dark_red()
    )
    log_embed.add_field(
        name="Typ ticketa", value=self.ticket_type.capitalize(), inline=True
    )
    log_embed.add_field(
        name="Autor zgłoszenia",
        value=self.creator.mention if self.creator else "Nieznany",
        inline=True,
    )
    log_embed.add_field(
        name="Przyjęty przez",
        value=(
            self.claimed_by.mention
            if self.claimed_by != "Nikt"
            else "Nikt nie przyjął"
        ),
        inline=True,
    )
    log_embed.add_field(
        name="Zamknięty przez", value=admin.mention, inline=True
    )
    log_embed.add_field(
        name="Powód zamknięcia", value=powod_tekst, inline=False
    )
    log_embed.set_footer(text=f"Zamknięty kanał: {channel.name}")

    if log_channel:
      await log_channel.send(embed=log_embed)

    await interaction.followup.send(
        f"🔒 **Ticket zamknięty przez:** {admin.mention}\n**Powód:**"
        f" {powod_tekst}\n*Kanał zostanie usunięty za 3 sekundy...*",
        ephemeral=True,
    )
    await asyncio.sleep(3)
    try:
      await channel.delete()
    except Exception:
      pass


# Panel zarządzania wewnątrz ticketa (Przyjmij / Zamknij)
class TicketManageView(discord.ui.View):

  def __init__(self, ticket_type, creator):
    super().__init__(timeout=86400)
    self.ticket_type = ticket_type
    self.creator = creator
    self.claimed_by = "Nikt"

  @discord.ui.button(
      label="Przyjmij ticket",
      style=discord.ButtonStyle.blurple,
      custom_id="ticket_claim_btn",
      emoji="🙋‍♂️",
  )
  async def claim_ticket(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    self.claimed_by = interaction.user
    button.disabled = True
    button.label = f"Przyjęte: {interaction.user.name}"
    button.style = discord.ButtonStyle.green

    embed = interaction.message.embeds[0]
    found = False
    for field in embed.fields:
      if field.name == "📌 Status":
        found = True
        break
    if not found:
      embed.add_field(
          name="📌 Status",
          value=f"Ticket przyjęty przez: {interaction.user.mention}",
          inline=False,
      )

    await interaction.message.edit(embed=embed, view=self)
    await interaction.response.send_message(
        f"✅ Pomyślnie przyjęto ticket przez {interaction.user.mention}!",
        ephemeral=True,
    )

  @discord.ui.button(
      label="Zamknij ticket",
      style=discord.ButtonStyle.red,
      custom_id="ticket_close_btn",
      emoji="🔒",
  )
  async def close_ticket(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    await interaction.response.send_modal(
        CloseTicketModal(self.ticket_type, self.creator, self.claimed_by)
    )


# Rozwijane menu z opcjami ticketów
class TicketSelect(discord.ui.Select):

  def __init__(self):
    options = [
        discord.SelectOption(
            label="Pomoc",
            value="pomoc",
            description="Uzyskaj pomoc od administracji",
            emoji="💡",
        ),
        discord.SelectOption(
            label="Backup",
            value="backup",
            description="Sprawy związane z backupami",
            emoji="💾",
        ),
        discord.SelectOption(
            label="Zgłoś gracza",
            value="zglos",
            description="Zgłoś nieuczciwego gracza",
            emoji="⚠️",
        ),
        discord.SelectOption(
            label="Media",
            value="media",
            description="Sprawy dotyczące rangi Media",
            emoji="🎥",
        ),
        discord.SelectOption(
            label="Inne",
            value="inne",
            description="Inne zapytania",
            emoji="📌",
        ),
    ]
    super().__init__(
        placeholder="Wybierz typ ticketa...",
        min_values=1,
        max_values=1,
        options=options,
        custom_id="persistent_ticket_select",
    )

  async def callback(self, interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    user = interaction.user
    ticket_type = self.values[0]

    type_names = {
        "pomoc": "pomoc",
        "backup": "backup",
        "zglos": "zgloszenie",
        "media": "media",
        "inne": "inne",
    }

    channel_name = f"{type_names.get(ticket_type, 'ticket')}-{user.name.lower()}"

    existing_channel = discord.utils.get(
        guild.text_channels, name=channel_name
    )
    if existing_channel:
      await interaction.followup.send(
          f"Masz już otwarty taki ticket: {existing_channel.mention}",
          ephemeral=True,
      )
      return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        ),
    }

    category = discord.utils.get(guild.categories, name="TICKETS")
    if not category:
      category = await guild.create_category("TICKETS")

    ticket_channel = await guild.create_text_channel(
        channel_name, category=category, overwrites=overwrites
    )

    ticket_embed = discord.Embed(
        title=f"🎫 TICKET: {ticket_type.upper()}",
        description=(
            f"Witaj {user.mention}!\nWybrany typ ticketa:"
            f" **{ticket_type.capitalize()}**.\nOpisz swój problem"
            " szczegółowo, administracja wkrótce odpowie."
        ),
        color=discord.Color.green(),
    )

    await ticket_channel.send(
        embed=ticket_embed, view=TicketManageView(ticket_type, user)
    )
    await interaction.followup.send(
        f"✅ Utworzono Twój ticket: {ticket_channel.mention}!", ephemeral=True
    )


class TicketSelectView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)
    self.add_item(TicketSelect())


@bot.event
async def on_ready():
  print(f"Zalogowano pomyślnie jako: {bot.user.name}")

  bot.add_view(TicketSelectView())

  try:
    bot.tree.copy_global_to(guild=MY_GUILD)
    synced = await bot.tree.sync(guild=MY_GUILD)
    print(
        f"Zsynchronizowano natychmiast {len(synced)} komend(y) dla Twojego"
        " serwera!"
    )
  except Exception as e:
    print(f"Błąd podczas natychmiastowej synchronizacji komend: {e}")


# Komendy bota
@bot.tree.command(
    name="start", description="Rozpocznij pracę z botem na Renderze"
)
async def start_command(interaction: discord.Interaction):
  await interaction.response.send_message(
      "Cześć! Jestem Twoim botem uruchomionym na Renderze."
  )


@bot.tree.command(name="ping", description="Sprawdź opóźnienie i status bota")
async def ping_command(interaction: discord.Interaction):
  latency = round(bot.latency * 1000)
  await interaction.response.send_message(f"Pong! 🏓 Opóźnienie: {latency}ms")


@bot.tree.command(
    name="wyslij",
    description=(
        "Wysyła ogłoszenie w stylu BLOWHC (niebieski pasek, logo i treść)"
    ),
)
async def wyslij_command(
    interaction: discord.Interaction,
    tytul: str,
    tresc: str,
    logo_url: str = None,
    kanal: discord.TextChannel = None,
):
  docelowy_kanal = kanal or interaction.channel
  embed = discord.Embed(
      title=tytul, description=tresc, color=discord.Color.from_rgb(52, 152, 219)
  )

  uzyte_logo = logo_url or (
      interaction.guild.icon.url if interaction.guild.icon else None
  )
  if uzyte_logo:
    embed.set_thumbnail(url=uzyte_logo)

  embed.set_author(name="BLOWHC.PL • OGŁOSZENIE", icon_url=uzyte_logo)
  embed.set_footer(
      text=f"Wprowadzone przez: {interaction.user.name}",
      icon_url=interaction.user.display_avatar.url,
  )

  await docelowy_kanal.send(embed=embed)
  await interaction.response.send_message(
      f"✅ Pomyślnie wysłano ogłoszenie BLOWHC na kanale"
      f" {docelowy_kanal.mention}!",
      ephemeral=True,
  )


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


@bot.tree.command(
    name="ticket",
    description=(
        "Wysyła panel strefy pomocy (ticketów) z banerem w środku tekstu"
    ),
)
async def ticket_command(
    interaction: discord.Interaction,
    baner_url: str = None,
    kanal: discord.TextChannel = None,
):
  docelowy_kanal = kanal or interaction.channel
  color = discord.Color.from_rgb(114, 137, 218)

  embed_top = discord.Embed(
      title="STREFA POMOCY • BLOWHC.PL",
      description=(
          "Jeżeli potrzebujesz pomocy, zgłosić gracza, otrzymać backup,"
          " wybierz odpowiednią opcję w menu poniżej!"
      ),
      color=color,
  )

  embed_bottom = discord.Embed(
      description=(
          "> ➢ **Cierpliwość:** Prosimy cierpliwie czekać, maksymalny czas"
          " to **72h**!\n> ➢ **Ważne:** Nie oznaczaj zarządu"
          " (Właścicieli/Developerów). To zadanie administracji!"
      ),
      color=color,
  )

  if baner_url:
    embed_banner = discord.Embed(color=color)
    embed_banner.set_image(url=baner_url)
    embeds_list = [embed_top, embed_banner, embed_bottom]
  else:
    embed_top.description += f"\n\n{embed_bottom.description}"
    embeds_list = [embed_top]

  await docelowy_kanal.send(embeds=embeds_list, view=TicketSelectView())
  await interaction.response.send_message(
      f"✅ Pomyślnie wysłano panel ticketów na kanał {docelowy_kanal.mention}!",
      ephemeral=True,
  )


TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

if __name__ == "__main__":
  if not TOKEN:
    print("BŁĄD: Brak zmiennej środowiskowej DISCORD_BOT_TOKEN!")
    exit(1)

  # Uruchomienie serwera Flask w tle
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.daemon = True
  flask_thread.start()

  # Bezpieczna pętla startowa bota (zapobiega crashom i pętlam restartów przy Cloudflare 1015)
  while True:
    try:
      print("Próba połączenia z Discordem...")
      bot.run(TOKEN)
    except Exception as e:
      print(f"Błąd połączenia z Discordem (prawdopodobnie blokada Cloudflare): {e}")
      print(
          "Czekam 60 sekund przed ponowną próbą, aby serwer Flask pozostał"
          " włączony..."
      )
      time.sleep(60)