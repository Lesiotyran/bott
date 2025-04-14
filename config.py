import os

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
ROLE_ID = int(os.environ.get("DISCORD_ROLE_ID"))
PORT = int(os.environ.get("PORT", 8080)) # Port, na którym ma nasłuchiwać serwer webowy
