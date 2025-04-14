import discord
from discord.ext import commands, tasks
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

# Tworzenie tabeli nabozenstwa (jeśli nie istnieje)
c.execute('''CREATE TABLE IF NOT EXISTS nabozenstwa
             (data TEXT, godzina TEXT, tytul TEXT, celebrans TEXT, linki TEXT)''')
conn.commit()

# Zmienne globalne
ogloszenie_wiadomosc = None
ogloszenie_data = None
ogloszenie_tresc = None

# Komendy bota

@bot.command()
async def msza_dzis(ctx, godzina: str = None, tytul: str = None, celebrans: str = None, linki: str = None, link_niezbednik: str = None):
    """Dodaje lub wyświetla mszę na dzisiejszy dzień."""
    role = discord.utils.get(ctx.guild.roles, id=config.ROLE_ID)
    if role in ctx.author.roles:
        dzisiejsza_data = datetime.date.today().strftime('%Y-%m-%d')
        if godzina and tytul and celebrans:
            try:
                c.execute("INSERT INTO msze VALUES (?, ?, ?, ?, ?)", (dzisiejsza_data, godzina, tytul, celebrans, linki))
                conn.commit()
                await ctx.send(f"Msza dodana: {dzisiejsza_data}, {godzina}, {tytul}, {celebrans}, {linki}")
            except sqlite3.Error as e:
                await ctx.send(f"Wystąpił błąd podczas dodawania mszy: {e}")
        else:
            try:
                c.execute("SELECT * FROM msze WHERE data=?", (dzisiejsza_data,))
                msze = c.fetchall()
                if msze:
                    embed = discord.Embed(title=f"Msza na {dzisiejsza_data}")
                    if link_niezbednik:
                        embed.url = link_niezbednik
                    for msza in msze:
                        embed.add_field(name=msza[1], value=f"{msza[2]}, {msza[3]}, {msza[4]}", inline=False)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Nie ma zaplanowanych mszy na dzisiaj.")
            except sqlite3.Error as e:
                await ctx.send(f"Wystąpił błąd podczas wyświetlania mszy: {e}")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def nabozenstwo_dzis(ctx, godzina: str = None, tytul: str = None, celebrans: str = None, linki: str = None, link_niezbednik: str = None):
    """Dodaje lub wyświetla nabożeństwo na dzisiejszy dzień."""
    role = discord.utils.get(ctx.guild.roles, id=config.ROLE_ID)
    if role in ctx.author.roles:
        dzisiejsza_data = datetime.date.today().strftime('%Y-%m-%d')
        if godzina and tytul and celebrans:
            try:
                c.execute("INSERT INTO nabozenstwa VALUES (?, ?, ?, ?, ?)", (dzisiejsza_data, godzina, tytul, celebrans, linki))
                conn.commit()
                await ctx.send(f"Nabożeństwo dodane: {dzisiejsza_data}, {godzina}, {tytul}, {celebrans}, {linki}")
            except sqlite3.Error as e:
                await ctx.send(f"Wystąpił błąd podczas dodawania nabożeństwa: {e}")
        else:
            try:
                c.execute("SELECT * FROM nabozenstwa WHERE data=?", (dzisiejsza_data,))
                nabozenstwa = c.fetchall()
                if nabozenstwa:
                    embed = discord.Embed(title=f"Nabożeństwo na {dzisiejsza_data}")
                    if link_niezbednik:
                        embed.url = link_niezbednik
                    for nabozenstwo in nabozenstwa:
                        embed.add_field(name=nabozenstwo[1], value=f"{nabozenstwo[2]}, {nabozenstwo[3]}, {nabozenstwo[4]}", inline=False)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Nie ma zaplanowanych nabożeństw na dzisiaj.")
            except sqlite3.Error as e:
                await ctx.send(f"Wystąpił błąd podczas wyświetlania nabożeństw: {e}")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def msza_usun(ctx, data: str):
    """Usuwa mszę z bazy danych."""
    role = discord.utils.get(ctx.guild.roles, id=config.ROLE_ID)
    if role in ctx.author.roles:
        try:
            c.execute("DELETE FROM msze WHERE data=?", (data,))
            conn.commit()
            await ctx.send(f"Msza usunięta: {data}")
        except sqlite3.Error as e:
            await ctx.send(f"Wystąpił błąd podczas usuwania mszy: {e}")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def msza_zaplanuj(ctx, data: str, godzina: str, tytul: str, celebrans: str, linki: str = None):
    """Planuje msze na przyszłe dni."""
    role = discord.utils.get(ctx.guild.roles, id=config.ROLE_ID)
    if role in ctx.author.roles:
        try:
            c.execute("INSERT INTO msze VALUES (?, ?, ?, ?, ?)", (data, godzina, tytul, celebrans, linki))
            conn.commit()
            await ctx.send(f"Msza zaplanowana: {data}, {godzina}, {tytul}, {celebrans}, {linki}")
        except sqlite3.Error as e:
            await ctx.send(f"Wystąpił błąd podczas planowania mszy: {e}")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def msza_wyswietl(ctx, data: str):
    """Wyświetla szczegóły mszy."""
    role = discord.utils.get(ctx.guild.roles, id=config.ROLE_ID)
    if role in ctx.author.roles:
        try:
            c.execute("SELECT * FROM msze WHERE data=?", (data,))
            msza = c.fetchone()
            if msza:
                await ctx.send(f"Data: {msza[0]}, Godzina: {msza[1]}, Tytuł: {msza[2]}, Celebrans: {msza[3]}, Linki: {msza[4]}")
            else:
                await ctx.send("Nie znaleziono mszy o podanej dacie.")
        except sqlite3.Error as e:
            await ctx.send(f"Wystąpił błąd podczas wyświetlania mszy: {e}")
    else:
        await ctx.send("Nie masz uprawnień do tej komendy.")

@bot.command()
async def wyslij_serwer(ctx, kanal: discord.TextChannel, *, wiadomosc: str):
    """Wysyła wiadomość na serwerze."""
    role = discord.utils.get(ctx.guild.roles, id=config.ROLE_ID)
    if role in ctx.author.roles:
        try:
            await kanal.send(wiadomosc)
            await ctx.send("Wiadomość wysłana.")
        except discord.Forbidden:
            await ctx.send("Nie można wysłać wiadomości na ten kanał.")
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

@bot.command()
async def ogloszenie(ctx, data: str, *, tresc: str):
    """Ustawia ogłoszenie do wysłania."""
    global ogloszenie_data, ogloszenie_tresc
    ogloszenie_data = data
    ogloszenie_tresc = tresc
    await ctx.send("Ogłoszenie ustawione.")

async def wyslij_ogloszenie():
    """Wysyła ogłoszenie na określony kanał."""
    global ogloszenie_wiadomosc, ogloszenie_data, ogloszenie_tresc
    if ogloszenie_data and ogloszenie_tresc:
        kanal = bot.get_channel(config.OGLOSZENIE_KANAL_ID)
        if kanal:
            dzisiejsza_data = datetime.date.today().strftime('%Y-%m-%d')
            if ogloszenie_data == dzisiejsza_data:
                try:
                    c.execute("SELECT * FROM msze WHERE data=?", (dzisiejsza_data,))
                    msze = c.fetchall()
                    msze_tekst = ""
                    if msze:
                        for msza in msze:
                            msze_tekst += f"• {msza[1]} {msza[3]} {msza[4]}\n"

                    c.execute("SELECT * FROM nabozenstwa WHERE data=?", (dzisiejsza_data,))
                    nabozenstwa = c.fetchall()
                    nabozenstwa_tekst = ""
                    if nabozenstwa:
                        for nabozenstwo in nabozenstwa:
                            nabozenstwa_tekst += f"• {nabozenstwo[1]} {nabozenstwo[3]} {nabozenstwo[4]}\n"

                    tresc = ogloszenie_tresc.replace("[MSZE]", msze_tekst).replace("[NABOZENSTWA]", nabozenstwa_tekst)

                    if ogloszenie_wiadomosc:
                        await ogloszenie_wiadomosc.edit(content=tresc)
                    else:
                        ogloszenie_wiadomosc = await kanal.send(tresc)
                except discord.Forbidden:
                    print("Nie mam uprawnień do wysyłania wiadomości na ten kanał.")
                except Exception as e:
                    print(f"Wystąpił błąd podczas wysyłania ogłoszenia: {e}")
            else:
                print("Ogłoszenie jest ustawione na inny dzień.")
        else:
            print("Nie znaleziono kanału o podanym ID.")

@tasks.loop(minutes=60)
async def wysylaj_ogloszenie_co_godzine():
    """Wysyła ogłoszenie co godzinę."""
    await wyslij_ogloszenie()

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
    wysylaj_ogloszenie_co_godzine.start()

# Uruchomienie bota
bot.run(config.TOKEN)
