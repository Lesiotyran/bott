import discord
from discord.ext import commands
import datetime
import requests
from bs4 import BeautifulSoup
import sqlite3

# Konfiguracja bota
TOKEN = 'MTI4MjM2MDA5MTA1MTI5NDg2Mg.G8DUCf.eJPhho9txikWbzJSkH6NHbfxRfzcb3RjCdtQMQ'
PREFIX = '/'
ROLE_ID = 1276516323387506729  # ID roli uprawnionej do komend

# Inicjalizacja bota
intents = discord.Intents.default()
intents.message_content = True  # Włącz odczytywanie treści wiadomości
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Połączenie z bazą danych SQLite
conn = sqlite3.connect('msze.db')
c = conn.cursor()

# Tworzenie tabeli msze (jeśli nie istnieje)
c.execute('''CREATE TABLE IF NOT EXISTS msze
             (data TEXT, godzina TEXT, tytul TEXT, celebrans TEXT, linki TEXT)''')
conn.commit()

# Funkcja do pobierania danych z Niezbędnika Katolickiego
def pobierz_dane_niezbednik(data):
    url = f"https://niezbednik.niedziela.pl/liturgia/{data}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        tytul_dnia = soup.find('h1', class_='liturgia-title').text.strip()
        return tytul_dnia, url
    else:
        return None, None

# Komendy bota

@bot.command()
async def msza_dodaj(ctx, data: str, godzina: str, tytul: str, celebrans: str, linki: str = None):
    """Dodaje mszę do bazy danych."""
    if ctx.author.get_role(ROLE_ID):
        c.execute("INSERT INTO msze VALUES (?, ?, ?, ?, ?)", (data, godzina, tytul, celebrans, linki))
        conn.commit()
        await ctx.send(f"Msza dodana: {data}, {godzina}, {tytul}, {celebrans}, {linki}")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def msza_usun(ctx, data: str):
    """Usuwa mszę z bazy danych."""
    if ctx.author.get_role(ROLE_ID):
        c.execute("DELETE FROM msze WHERE data=?", (data,))
        conn.commit()
        await ctx.send(f"Msza usunięta: {data}")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def msza_nadzis(ctx):
    """Wyświetla msze na dany dzień."""
    if ctx.author.get_role(ROLE_ID):
        dzisiejsza_data = datetime.date.today().strftime('%Y-%m-%d')
        tytul_dnia, url_niezbednik = pobierz_dane_niezbednik(dzisiejsza_data)
        if tytul_dnia:
            embed = discord.Embed(title=tytul_dnia, url=url_niezbednik)
            c.execute("SELECT * FROM msze WHERE data=?", (dzisiejsza_data,))
            msze = c.fetchall()
            if msze:
                for msza in msze:
                    embed.add_field(name=msza[1], value=f"{msza[2]}, {msza[3]}, {msza[4]}", inline=False)
            else:
                embed.add_field(name="Brak mszy", value="Nie ma zaplanowanych mszy na dzisiaj.")
            await ctx.send(embed=embed)
        else:
            await ctx.send("Nie udało się pobrać danych z Niezbędnika Katolickiego.")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def msza_zaplanuj(ctx, data: str, godzina: str, tytul: str, celebrans: str, linki: str = None):
    """Planuje msze na przyszłe dni."""
    if ctx.author.get_role(ROLE_ID):
        c.execute("INSERT INTO msze VALUES (?, ?, ?, ?, ?)", (data, godzina, tytul, celebrans, linki))
        conn.commit()
        await ctx.send(f"Msza zaplanowana: {data}, {godzina}, {tytul}, {celebrans}, {linki}")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def msza_wyswietl(ctx, data: str):
    """Wyświetla szczegóły mszy."""
    if ctx.author.get_role(ROLE_ID):
        c.execute("SELECT * FROM msze WHERE data=?", (data,))
        msza = c.fetchone()
        if msza:
            await ctx.send(f"Data: {msza[0]}, Godzina: {msza[1]}, Tytuł: {msza[2]}, Celebrans: {msza[3]}, Linki: {msza[4]}")
        else:
            await ctx.send("Nie znaleziono mszy o podanej dacie.")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def ticket(ctx, temat: str, opis: str):
    """Tworzy nowy ticket."""
    kanal_ticket = await ctx.guild.create_text_channel(f'ticket-{ctx.author.name}')
    await kanal_ticket.set_permissions(ctx.author, read_messages=True, send_messages=True)
    await kanal_ticket.set_permissions(ctx.guild.default_role, read_messages=False)
    await kanal_ticket.send(f"**Temat:** {temat}\n**Opis:** {opis}")
    await ctx.send(f"Utworzono ticket: {kanal_ticket.mention}")

@bot.command()
async def ticket_zamknij(ctx, ticket_id: int):
    """Zamyka ticket."""
    if ctx.author.get_role(ROLE_ID):
        kanal_ticket = bot.get_channel(ticket_id)
        if kanal_ticket:
            await kanal_ticket.delete()
            await ctx.send(f"Ticket {ticket_id} zamknięty.")
        else:
            await ctx.send("Nie znaleziono ticketu o podanym ID.")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def wyslij_serwer(ctx, kanal: discord.TextChannel, *, wiadomosc: str):
    """Wysyła wiadomość na serwerze."""
    if ctx.author.get_role(ROLE_ID):
        await kanal.send(wiadomosc)
        await ctx.send("Wiadomość wysłana.")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def wyslij_prywatna(ctx, uzytkownik: discord.Member, *, wiadomosc: str):
    """Wysyła prywatną wiadomość do użytkownika."""
    if ctx.author.get_role(ROLE_ID):
        try:
            await uzytkownik.send(wiadomosc)
            await ctx.send("Wiadomość prywatna wysłana.")
        except discord.Forbidden:
            await ctx.send("Nie można wysłać wiadomości do tego użytkownika.")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

# Uruchomienie bota
bot.run(TOKEN)
