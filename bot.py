import discord
from discord.ext import commands
import sqlite3
import json
from utils.server import WebServer

__version__ = '0.5.0'

startup_extensions = ["setup", "csgo"]

# TODO: Change prefix to . when syncing
bot = commands.Bot(command_prefix='.', case_insensitive=True, description='A bot to run CSGO PUGS.')
bot_secret: str

# TODO: Refactor these variables to pass through into the init of the cog instead of importing the file
server_address: (str, int)
server_password: str
RCON_password: str

# Loading JSON config file
with open('config.json') as config:
    json_data = json.load(config)
    bot_secret = str(json_data['discord_api'])
    server_address = (str(json_data['server_address']), int(json_data['server_port']))
    server_password = str(json_data['server_password'])
    RCON_password = str(json_data['RCON_password'])


@bot.event
async def on_ready():
    db = sqlite3.connect('./main.sqlite')
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
            discord_id TEXT UNIQUE,
            steam_id TEXT
        )''')
    db.close()
    # TODO: Custom state for waiting for pug or if a pug is already playing
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.playing,
                                                                                    state='Waiting', details='Waiting',
                                                                                    name='CSGO Pug'))
    global server_address, server_password, RCON_password
    if bot.user.id == 745000319942918303:
        bot.dev = True

    bot.version = __version__

    bot.web_server = WebServer(bot=bot)
    await bot.web_server.http_start()
    print(f'{bot.user} connected.')


@bot.command()
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')


@bot.command()
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')


for extension in startup_extensions:
    bot.load_extension(f'cogs.{extension}')


bot.run(bot_secret)
