import discord
import sqlite3

from discord.ext import commands
from utils.server import WebServer

__version__ = '0.7.0'


class Discord_10man(commands.Bot):
    def __init__(self, config:dict, startup_extensions):
        # TODO: Change prefix to . when syncing
        super().__init__(command_prefix='.', case_insensitive=True, description='A bot to run CSGO PUGS.')
        self.token = config['discord_token']
        self.servers = config['servers']
        self.web_server = WebServer(bot=self)
        self.dev = False
        self.version = __version__

        db = sqlite3.connect('./main.sqlite')
        cursor = db.cursor()
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users(
                        discord_id TEXT UNIQUE,
                        steam_id TEXT
                    )''')
        db.close()

        for extension in startup_extensions:
            self.load_extension(f'cogs.{extension}')

    async def on_ready(self):
        # TODO: Custom state for waiting for pug or if a pug is already playing
        await self.change_presence(status=discord.Status.idle,
                                   activity=discord.Activity(type=discord.ActivityType.playing,
                                                             state='Waiting', details='Waiting',
                                                             name='CSGO Pug'))

        self.dev = self.user.id == 745000319942918303

        await self.web_server.http_start()
        print(f'{self.user} connected.')

    async def load(self, ctx, extension):
        self.load_extension(f'cogs.{extension}')

    async def unload(self, ctx, extension):
        self.unload_extension(f'cogs.{extension}')

    async def close(self):
        await super().close()
        # TODO: Close Webserver

    def run(self):
        super().run(self.token, reconnect=True)
