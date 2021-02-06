import logging
from logging.config import fileConfig

import discord
import valve.rcon
from databases import Database
from discord.ext import commands
from steam.steamid import SteamID, from_url

import checks
from bot import Discord_10man


class Setup(commands.Cog):
    def __init__(self, bot: Discord_10man):
        fileConfig('logging.conf')
        self.logger = logging.getLogger(f'10man.{__name__}')
        self.bot: Discord_10man = bot

        self.logger.debug(f'Loaded {__name__}')

    @commands.command(aliases=['login'],
                      help='This command connects users steam account to the bot.',
                      brief='Connect your SteamID to the bot', usage='<SteamID or CommunityURL>')
    async def link(self, ctx: commands.Context, steamID_input: str):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        steamID = SteamID(steamID_input)
        if not steamID.is_valid():
            steamID = from_url(steamID_input, http_timeout=15)
            if steamID is None:
                steamID = from_url(f'https://steamcommunity.com/id/{steamID_input}/', http_timeout=15)
                if steamID is None:
                    raise commands.UserInputError(message='Please enter a valid SteamID or community url.')
        db = Database('sqlite:///main.sqlite')
        await db.connect()
        await db.execute('''
                        REPLACE INTO users (discord_id, steam_id)
                        VALUES( :discord_id, :steam_id )
                        ''', {"discord_id": str(ctx.author.id), "steam_id": str(steamID.as_steam2_zero)})
        embed = discord.Embed(description=f'Connected {ctx.author.mention} \n `{steamID.as_steam2}`', color=0x00FF00)
        await ctx.send(embed=embed)
        self.logger.info(f'{ctx.author} connected to {steamID.as_steam2}')

    @link.error
    async def link_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.UserInputError):
            await ctx.send(str(error))
            self.logger.warning(f'{ctx.author} did not enter a valid SteamID')
        else:
            self.logger.exception(f'{ctx.command} caused an exception')

    @commands.command(aliases=['spectator', 'spec'],
                      help='Adds this user as a spectator in the config for the next map.',
                      brief='Add user as spectator', usage='<@User>')
    @commands.has_permissions(administrator=True)
    async def add_spectator(self, ctx: commands.Context, spec: discord.Member):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        db = Database('sqlite:///main.sqlite')
        await db.connect()
        data = await db.fetch_one('SELECT 1 FROM users WHERE discord_id = :spectator', {"spectator": str(spec.id)})
        if data is None:
            raise commands.UserInputError(message=f'<@{spec.id}> needs to `.link` their account.')
        self.bot.spectators.append(spec)
        await ctx.send(f'<@{spec.id}> was added as a spectator.')
        self.logger.info(f'{ctx.author} was added as a spectator')

    @add_spectator.error
    async def add_spectator_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.UserInputError):
            await ctx.send(str(error))
            self.logger.warning(str(error))
        else:
            self.logger.exception(f'{ctx.command} caused an exception')

    @commands.command(aliases=['queue_captain', 'captain'],
                      help='Set\'s the queue captain for the next match', usage='<@User> ?<@User>')
    @commands.has_permissions(administrator=True)
    async def set_queue_captain(self, ctx: commands.Context, *args: discord.Member):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        db = Database('sqlite:///main.sqlite')
        await db.connect()
        for captain in args:
            data = await db.fetch_one('SELECT 1 FROM users WHERE discord_id = :spectator',
                                      {"spectator": str(captain.id)})
            if data is None:
                raise commands.UserInputError(message=f'<@{captain.id}> needs to `.link` their account.')
            self.bot.queue_captains.append(captain)
            await ctx.send(f'<@{captain.id}> was added as a captain for the next queue.')
            self.logger.debug(f'<@{captain.id}> was added as a captain for the next queue.')
        self.logger.debug(f'Current Queue Captains: {self.bot.queue_captains}')

    @set_queue_captain.error
    async def set_queue_captain_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.UserInputError):
            await ctx.send(str(error))
            self.logger.debug(str(error))
        else:
            self.logger.exception(f'{ctx.command} caused an exception')

    @commands.command(aliases=['empty'],
                      help='Empties the queue')
    @commands.has_permissions(administrator=True)
    async def empty_queue(self, ctx: commands.Context):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        for member in self.bot.queue_voice_channel.members:
            await member.move_to(channel=None, reason=f'Admin cleared the queue')
        self.logger.debug(f'Admin cleared the queue')

    @empty_queue.error
    async def empty_queue_error(self, ctx: commands.Context, error: Exception):
        self.logger.exception(f'{ctx.command} caused an exception')

    @commands.command(aliases=['remove_spec'],
                      help='Removes this user as a spectator from the config.',
                      brief='Removes user as spectator', usage='<@User>')
    @commands.has_permissions(administrator=True)
    async def remove_spectator(self, ctx: commands.Context, spec: discord.Member):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        db = Database('sqlite:///main.sqlite')
        await db.connect()
        data = await db.fetch_one('SELECT 1 FROM users WHERE discord_id = :spectator',
                                  {"spectator": str(spec.id)})
        if data is None:
            raise commands.UserInputError(
                message=f'User did not `.link` their account and probably is not a spectator.')
        if data[0] in self.bot.spectators:
            self.bot.spectators.remove(spec)
            await ctx.send(f'<@{spec.id}> was removed as a spectator.')
            self.logger.debug(f'<@{spec.id}> was removed as a spectator.')
        else:
            raise commands.CommandError(message=f'<@{spec.id}> is not a spectator.')

    @remove_spectator.error
    async def remove_spectator_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.UserInputError) or isinstance(error, commands.CommandError):
            await ctx.send(str(error))
            self.logger.warning(str(error))
        else:
            self.logger.exception(f'{ctx.command} caused an exception')

    @commands.command(aliases=['dm'],
                      help='Command to enable or disable sending a dm with the connect ip vs posting it in the channel',
                      brief='Enable or disable connect via dm')
    @commands.has_permissions(administrator=True)
    async def connect_dm(self, ctx: commands.Context, enabled: bool = False):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        self.bot.connect_dm = enabled
        await ctx.send(f'Connect message will {"not" if not enabled else ""} be sent via a DM.')

    @commands.command(aliases=['setupqueue', 'queue_setup', 'queuesetup'],
                      help='Command to set the server for the queue system. You must be in a voice channel.',
                      brief='Set\'s the server for the queue')
    @commands.has_permissions(administrator=True)
    @commands.check(checks.voice_channel)
    async def setup_queue(self, ctx: commands.Context, enabled: bool = True):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        self.bot.queue_voice_channel = ctx.author.voice.channel
        self.bot.queue_ctx = ctx
        if enabled:
            if self.bot.cogs['CSGO'].queue_check.is_running():
                self.bot.cogs['CSGO'].queue_check.restart()
                self.logger.warning(f'Queue Restarted')
            else:
                self.bot.cogs['CSGO'].queue_check.start()
                self.logger.debug('Queue Started')
            self.bot.cogs['CSGO'].pug.enabled = False
            self.logger.debug('Pug Disabled')
            self.logger.debug(f'Queue Channel: {self.bot.queue_ctx.author.voice.channel}')
        else:
            self.bot.cogs['CSGO'].queue_check.stop()
            self.bot.cogs['CSGO'].pug.enabled = True
            self.logger.debug('Queue Disabled, Pug Enabled')
        await ctx.send(
            f'{self.bot.queue_ctx.author.voice.channel} is the queue channel.\n'
            f'Queue is {"enabled" if enabled else "disabled"}.\n'
            f'Pug Command is {"enabled" if not enabled else "disabled"}.')

    @setup_queue.error
    async def setup_queue_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandError):
            await ctx.send(str(error))
            self.logger.warning(str(error))
        else:
            self.logger.exception(f'{ctx.command} caused an exception')

    @commands.command(aliases=['restart_queue'],
                      help='The command forcefully restarts the queue.',
                      brief='Restart\'s the queue')
    @commands.has_permissions(administrator=True)
    @commands.check(checks.queue_running)
    async def force_restart_queue(self, ctx: commands.Context):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        self.bot.cogs['CSGO'].queue_check.cancel()
        self.bot.cogs['CSGO'].queue_check.start()
        self.bot.cogs['CSGO'].pug.enabled = False
        await ctx.send('Queue forcefully restarted')
        self.logger.warning('Queue forcefully restarted')

    @force_restart_queue.error
    async def force_restart_queue_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandError):
            await ctx.send(str(error))
            self.logger.warning(str(error))
        else:
            self.logger.exception(f'{ctx.command} caused an exception')

    @commands.command(aliases=['setup_queue_size', 'match_size', 'queue_size', 'set_match_size', 'set_queue_size'],
                      help='This command sets the size of the match and the queue.',
                      brief='Sets the size of the match & queue', usage='<size>')
    @commands.has_permissions(administrator=True)
    async def setup_match_size(self, ctx: commands.Context, size: int):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        if size <= 0:
            raise commands.CommandError(message=f'Invalid match size.')
        if size % 2 != 0:
            raise commands.CommandError(message=f'Match size must be an even number.')
        self.bot.match_size = size
        if self.bot.cogs['CSGO'].queue_check.is_running():
            self.bot.cogs['CSGO'].queue_check.restart()
        await ctx.send(f'Set match size to {self.bot.match_size}.')
        self.logger.debug(f'Set match size to {self.bot.match_size}.')

    @setup_match_size.error
    async def setup_match_size_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.BadArgument):
            await ctx.send('Invalid Argument')
            self.logger.warning('Invalid Argument')
        elif isinstance(error, commands.CommandError):
            await ctx.send(str(error))
            self.logger.warning(str(error))
        else:
            self.logger.exception(f'{ctx.command} caused an exception')

    @commands.command(help='Command to send a test message to the server to verify that RCON is working.',
                      brief='Sends a message to the server to test RCON', usage='<message>')
    @commands.has_permissions(administrator=True)
    async def RCON_message(self, ctx: commands.Context, *, message: str):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        for server in self.bot.servers:
            test_message = valve.rcon.execute((server.server_address, server.server_port), server.RCON_password,
                                              f'say {message}')
            print(f'Server #{server.id} | {test_message}')
            self.logger.debug(f'Server #{server.id} | {test_message}')

    @RCON_message.error
    async def RCON_message_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Only an administrator can send a message using the console')
            self.logger.warning('Only an administrator can send a message using the console')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify the message')
            self.logger.warning('Please specify the message')
        else:
            self.logger.exception(f'{ctx.command} caused an exception')

    @commands.command(help='This command unbans everyone on the server. Useful fix.',
                      brief='Unbans everyone from the server', hidden=True)
    @commands.has_permissions(administrator=True)
    async def RCON_unban(self, ctx: commands.Context):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        for server in self.bot.servers:
            unban = valve.rcon.execute((server.server_address, server.server_port), server.RCON_password,
                                       'removeallids')
            print(f'Server #{server.id} | {unban}')
            self.logger.debug(f'Server #{server.id} | {unban}')

    @RCON_unban.error
    async def RCON_unban_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Only an administrator can unban every player')
            self.logger.warning('Only an administrator can unban every player')
        else:
            self.logger.exception(f'{ctx.command} caused an exception')

    @commands.command(aliases=['end', 'stop'],
                      help='This command force ends a match.',
                      brief='Force ends a match', usage='<ServerID>')
    @commands.has_permissions(administrator=True)
    async def force_end(self, ctx: commands.Context, server_id: int = 0):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        valve.rcon.execute((self.bot.servers[server_id].server_address, self.bot.servers[server_id].server_port),
                           self.bot.servers[server_id].RCON_password, 'get5_endmatch')

    @force_end.error
    async def force_end_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Only an administrator can force end a match.')
        else:
            self.logger.exception(f'{ctx.command} caused an exception')


def setup(client):
    client.add_cog(Setup(client))
