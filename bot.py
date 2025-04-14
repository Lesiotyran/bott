import discord
from discord.ext import commands
import datetime
import sqlite3
import config
from aiohttp import web
import os

# Inicjalizacja bota
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Połączenie z bazą danych SQLite
conn = sqlite3.connect('msze.db')
c = conn.cursor()

# Tworzenie tabeli msze (jeśli nie istnieje)
c.execute('''CREATE TABLE IF NOT EXISTS msze
             (data TEXT, godzina TEXT, tytul TEXT, celebrans TEXT, linki TEXT)''')
conn.commit()

# Komendy bota

@bot.command()
async def msza_dodaj(ctx, data: str, godzina: str, tytul: str, celebrans: str, linki: str = None):
    """Dodaje mszę do bazy danych."""
    role = discord.utils.get(ctx.guild.roles, id=config.ROLE_ID)
    if role in ctx.author.roles:
        c.execute("INSERT INTO msze VALUES (?, ?, ?, ?, ?)", (data, godzina, tytul, celebrans, linki))
        conn.commit()
        await ctx.send(f"Msza dodana: {data}, {godzina}, {tytul}, {celebrans}, {linki}")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def msza_usun(ctx, data: str):
    """Usuwa mszę z bazy danych."""
    role = discord.utils.get(ctx.guild.roles, id=config.ROLE_ID)
    if role in ctx.author.roles:
        c.execute("DELETE FROM msze WHERE data=?", (data,))
        conn.commit()
        await ctx.send(f"Msza usunięta: {data}")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def msza_nadzis(ctx, link_niezbednik: str = None):
    """Wyświetla msze na dany dzień."""
    role = discord.utils.get(ctx.guild.roles, id=config.ROLE_ID)
    if role in ctx.author.roles:
        dzisiejsza_data = datetime.date.today().strftime('%Y-%m-%d')
        embed = discord.Embed(title=f"Msza na {dzisiejsza_data}")
        if link_niezbednik:
            embed.url = link_niezbednik
        c.execute("SELECT * FROM msze WHERE data=?", (dzisiejsza_data,))
        msze = c.fetchall()
        if msze:
            for msza in msze:
                embed.add_field(name=msza[1], value=f"{msza[2]}, {msza[3]}, {msza[4]}", inline=False)
        else:
            embed.add_field(name="Brak mszy", value="Nie ma zaplanowanych mszy na dzisiaj.")
        await ctx.send(embed=embed)
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def msza_zaplanuj(ctx, data: str, godzina: str, tytul: str, celebrans: str, linki: str = None):
    """Planuje msze na przyszłe dni."""
    role = discord.utils.get(ctx.guild.roles, id=config.ROLE_ID)
    if role in ctx.author.roles:
        c.execute("INSERT INTO msze VALUES (?, ?, ?, ?, ?)", (data, godzina, tytul, celebrans, linki))
        conn.commit()
        await ctx.send(f"Msza zaplanowana: {data}, {godzina}, {tytul}, {celebrans}, {linki}")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def msza_wyswietl(ctx, data: str):
    """Wyświetla szczegóły mszy."""
    role = discord.utils.get(ctx.guild.roles, id=config.ROLE_ID)
    if role in ctx.author.roles:
        c.execute("SELECT * FROM msze WHERE data=?", (data,))
        msza = c.fetchone()
        if msza:
            await ctx.send(f"Data: {msza[0]}, Godzina: {msza[1]}, Tytuł: {msza[2]}, Celebrans: {msza[3]}, Linki: {msza[4]}")
        else:
            await ctx.send("Nie znaleziono mszy o podanej dacie.")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def wyslij_serwer(ctx, kanal: discord.TextChannel, *, wiadomosc: str):
    """Wysyła wiadomość na serwerze."""
    role = discord.utils.get(ctx.guild.roles, id=config.ROLE_ID)
    if role in ctx.author.roles:
        await kanal.send(wiadomosc)
        await ctx.send("Wiadomość wysłana.")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def wyslij_prywatna(ctx, uzytkownik: discord.Member, *, wiadomosc: str):
    """Wysyła prywatną wiadomość do użytkownika."""
    role = discord.utils.get(ctx.guild.roles, id=config.ROLE_ID)
    if role in ctx.author.roles:
        try:
            await uzytkownik.send(wiadomosc)
            await ctx.send("Wiadomość prywatna wysłana.")
        except discord.Forbidden:
            await ctx.send("Nie można wysłać wiadomości do tego użytkownika.")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

async def ping(request):
    return web.Response(text="Ping!")

async def start_web_server():
    async def handle(request):
        return web.Response(text="Bot is running!")

    app = web.Application()
    app.add_routes([web.get('/', handle), web.get('/ping', ping)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', config.PORT)
    await site.start()

@bot.event
async def on_ready():
    print(f'Zalogowano jako {bot.user.name}')
    await start_web_server()

# Uruchomienie bota
bot.run(config.TOKEN)
