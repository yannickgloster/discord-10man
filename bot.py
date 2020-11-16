import discord
import logging
import pprint

from databases import Database
from discord.ext import commands
from logging.config import fileConfig
from typing import List
from utils.server import WebServer
from utils.csgo_server import CSGOServer

__version__ = '1.7.0'
__dev__ = 745000319942918303


class Discord_10man(commands.Bot):
    def __init__(self, config: dict, startup_extensions: List[str]):
        # commands.when_mentioned_or('e!')
        super().__init__(command_prefix='.', case_insensitive=True, description='A bot to run CSGO PUGS.',
                         help_command=commands.DefaultHelpCommand(verify_checks=False),
                         intents=discord.Intents(
                             guilds=True, members=True, bans=True, emojis=True, integrations=True, invites=True,
                             voice_states=True, presences=False, messages=True, guild_messages=True, dm_messages=True,
                             reactions=True, guild_reactions=True, dm_reactions=True, typing=True, guild_typing=True,
                             dm_typing=True
                         ))
        fileConfig('logging.conf')
        self.logger = logging.getLogger(f'10man.{__name__}')
        self.logger.debug(f'Version = {__version__}')
        self.logger.debug(f'config.json = \n {pprint.pformat(config)}')

        self.token: str = config['discord_token']
        self.bot_IP: str = config['bot_IP']
        if 'bot_port' in config:
            self.bot_port: int = config['bot_port']
        else:
            self.bot_port: int = 3000
        self.steam_web_api_key = config['steam_web_API_key']
        self.servers: List[CSGOServer] = []
        # Will need to change for when there is multiple server queue
        self.users_not_ready: List[discord.Member] = []
        for i, server in enumerate(config['servers']):
            self.servers.append(
                CSGOServer(i, server['server_address'], server['server_port'], server['server_password'],
                           server['RCON_password']))
        self.web_server = WebServer(bot=self)
        self.dev: bool = False
        self.version: str = __version__
        self.queue_ctx: commands.Context = None
        self.queue_voice_channel: discord.VoiceChannel = None
        self.match_size = 10
        self.spectators: List[discord.Member] = []
        self.connect_dm = False
        self.queue_captains: List[discord.Member] = []

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
        self.logger.debug(f'Dev = {self.dev}')

        await self.web_server.http_start()
        self.logger.info(f'{self.user} connected.')

    async def load(self, extension: str):
        self.load_extension(f'cogs.{extension}')

    async def unload(self, extension: str):
        self.unload_extension(f'cogs.{extension}')

    async def close(self):
        self.logger.warning('Stopping Bot')
        await self.web_server.http_stop()
        await super().close()

    def run(self):
        super().run(self.token, reconnect=True)
