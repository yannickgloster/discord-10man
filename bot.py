import discord
import logging

from databases import Database
from discord.ext import commands
from typing import List
from utils.server import WebServer
from utils.csgo_server import CSGOServer

__version__ = '1.0.6'
__dev__ = 745000319942918303

intents = discord.Intents.default()
intents.members = True


class Discord_10man(commands.Bot):
    def __init__(self, config: dict, startup_extensions: List[str]):
        # TODO: Change prefix to . when syncing
        super().__init__(command_prefix='.', case_insensitive=True, description='A bot to run CSGO PUGS.',
                         help_command=commands.DefaultHelpCommand(verify_checks=False), intents=intents)
        self.token: str = config['discord_token']
        self.bot_IP: str = config['bot_IP']
        self.servers: List[CSGOServer] = []
        for i, server in enumerate(config['servers']):
            self.servers.append(
                CSGOServer(i, server['server_address'], server['server_port'], server['server_password'],
                           server['RCON_password']))
        self.web_server = WebServer(bot=self)
        self.dev: bool = False
        self.version: str = __version__
        self.queue_ctx: commands.Context = None
        self.queue_voice_channel: discord.VoiceChannel = None

        logger = logging.getLogger('discord')
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        logger.addHandler(handler)

        for extension in startup_extensions:
            self.load_extension(f'cogs.{extension}')

    async def on_ready(self):
        db = Database('sqlite:///main.sqlite')
        await db.connect()
        await db.execute('''
                    CREATE TABLE IF NOT EXISTS users(
                        discord_id TEXT UNIQUE,
                        steam_id TEXT
                    )''')

        # TODO: Custom state for waiting for pug or if a pug is already playing
        await self.change_presence(status=discord.Status.idle,
                                   activity=discord.Activity(type=discord.ActivityType.playing,
                                                             state='Waiting', details='Waiting',
                                                             name='CSGO Pug'))

        self.dev = self.user.id == __dev__

        await self.web_server.http_start()
        print(f'{self.user} connected.')

    async def load(self, extension: str):
        self.load_extension(f'cogs.{extension}')

    async def unload(self, extension: str):
        self.unload_extension(f'cogs.{extension}')

    async def close(self):
        await self.web_server.http_stop()
        await super().close()

    def run(self):
        super().run(self.token, reconnect=True)
