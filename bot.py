import discord
import logging
import sqlite3

from discord.ext import commands
from utils.server import WebServer

__version__ = '0.9.0'


class Discord_10man(commands.Bot):
    def __init__(self, config: dict, startup_extensions: [str]):
        # TODO: Change prefix to . when syncing
        super().__init__(command_prefix='.', case_insensitive=True, description='A bot to run CSGO PUGS.',
                         help_command=commands.DefaultHelpCommand(verify_checks=False))
        self.token = config['discord_token']
        self.servers = config['servers']
        self.web_server = WebServer(bot=self)
        self.dev = False
        self.version = __version__
        self.queue_voice_channel = None
        self.queue_text_channel = None

        db = sqlite3.connect('./main.sqlite')
        cursor = db.cursor()
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users(
                        discord_id TEXT UNIQUE,
                        steam_id TEXT
                    )''')
        db.close()

        logger = logging.getLogger('discord')
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        logger.addHandler(handler)

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
        await self.web_server.http_stop()
        await super().close()

    def run(self):
        super().run(self.token, reconnect=True)
