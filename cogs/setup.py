import checks
import discord
import traceback
import valve.rcon

from bot import Discord_10man
from databases import Database
from discord.ext import commands
from steam.steamid import SteamID, from_url


class Setup(commands.Cog):
    def __init__(self, bot: Discord_10man):
        self.bot: Discord_10man = bot

    @commands.command(aliases=['login'],
                      help='This command connects users steam account to the bot.',
                      brief='Connect your SteamID to the bot', usage='<SteamID or CommunityURL>')
    async def link(self, ctx: commands.Context, steamID_input: str):
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

    @link.error
    async def link_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.UserInputError):
            await ctx.send(str(error))
        traceback.print_exc()

    @commands.command(aliases=['spectator', 'spec'],
                      help='Adds this user as a spectator in the config for the next map.',
                      brief='Add user as spectator', usage='<@User>')
    @commands.has_permissions(administrator=True)
    async def add_spectator(self, ctx: commands.Context, spec: discord.Member):
        db = Database('sqlite:///main.sqlite')
        await db.connect()
        data = await db.fetch_one('SELECT 1 FROM users WHERE discord_id = :spectator', {"spectator": str(spec.id)})
        if data is None:
            raise commands.UserInputError(message=f'<@{spec.id}> needs to `.link` their account.')
        self.bot.spectators.append(spec)
        await ctx.send(f'<@{spec.id}> was added as a spectator.')

    @add_spectator.error
    async def add_spectator_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.UserInputError):
            await ctx.send(str(error))
        traceback.print_exc()

    @commands.command(aliases=['remove_spec'],
                      help='Removes this user as a spectator from the config.',
                      brief='Removes user as spectator', usage='<@User>')
    @commands.has_permissions(administrator=True)
    async def remove_spectator(self, ctx: commands.Context, spec: discord.Member):
        db = Database('sqlite:///main.sqlite')
        await db.connect()
        data = await db.fetch_one('SELECT 1 FROM users WHERE discord_id = :spectator',
                                  {"spectator": str(spec.id)})
        if data is None:
            raise commands.UserInputError(message=f'User did not `.link` their account and probably is not a spectator.')
        if data[0] in self.bot.spectators:
            self.bot.spectators.remove(spec)
            await ctx.send(f'<@{spec.id}> was added as a spectator.')
        else:
            raise commands.CommandError(message=f'<@{spec.id}> is not a spectator.')

    @remove_spectator.error
    async def remove_spectator_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.UserInputError) or isinstance(error, commands.CommandError):
            await ctx.send(str(error))
        traceback.print_exc()

    @commands.command(aliases=['dm'],
                      help='Command to enable or disable sending a dm with the connect ip vs posting it in the channel',
                      brief='Enable or disable connect via dm')
    @commands.check(checks.voice_channel)
    @commands.has_permissions(administrator=True)
    async def connect_dm(self, ctx: commands.Context, enabled: bool = False):
        self.bot.connect_dm = enabled
        await ctx.send(f'Connect message will {"not" if not enabled else ""} be sent via a DM.')

    @commands.command(aliases=['setupqueue'],
                      help='Command to set the server for the queue system. You must be in a voice channel.',
                      brief='Set\'s the server for the queue')
    @commands.has_permissions(administrator=True)
    @commands.check(checks.voice_channel)
    async def setup_queue(self, ctx: commands.Context, enabled: bool = True):
        self.bot.queue_voice_channel = ctx.author.voice.channel
        self.bot.queue_ctx = ctx
        if enabled:
            if self.bot.cogs['CSGO'].queue_check.is_running():
                self.bot.cogs['CSGO'].queue_check.restart()
            else:
                self.bot.cogs['CSGO'].queue_check.start()
            self.bot.cogs['CSGO'].pug.enabled = False
        else:
            self.bot.cogs['CSGO'].queue_check.stop()
            self.bot.cogs['CSGO'].pug.enabled = True
        await ctx.send(
            f'{self.bot.queue_ctx.author.voice.channel} is the queue channel.\n'
            f'Queue is {"enabled" if enabled else "disabled"}.\n'
            f'Pug Command is {"enabled" if not enabled else "disabled"}.')

    @setup_queue.error
    async def setup_queue_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandError):
            await ctx.send(str(error))
        traceback.print_exc()

    @commands.command(aliases=['restart_queue'],
                      help='The command forcefully restarts the queue.',
                      brief='Restart\'s the queue')
    @commands.has_permissions(administrator=True)
    @commands.check(checks.queue_running)
    async def force_restart_queue(self, ctx: commands.Context):
        self.bot.cogs['CSGO'].queue_check.cancel()
        self.bot.cogs['CSGO'].queue_check.start()
        self.bot.cogs['CSGO'].pug.enabled = False
        await ctx.send('Queue forcefully restarted')


    @commands.command(aliases=['setup_queue_size', 'match_size', 'queue_size', 'set_match_size', 'set_queue_size'],
                      help='This command sets the size of the match and the queue.',
                      brief='Sets the size of the match & queue', usage='<size>')
    @commands.has_permissions(administrator=True)
    async def setup_match_size(self, ctx: commands.Context, size: int):
        if size <= 0:
            raise commands.CommandError(message=f'Invalid match size.')
        if size % 2 != 0:
            raise commands.CommandError(message=f'Match size must be an even number.')
        self.bot.match_size = size
        if self.bot.cogs['CSGO'].queue_check.is_running():
            self.bot.cogs['CSGO'].queue_check.restart()
        await ctx.send(f'Set match size to {self.bot.match_size}.')

    @setup_match_size.error
    async def setup_match_size_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.BadArgument):
            await ctx.send('Invalid Argument')
        elif isinstance(error, commands.CommandError):
            await ctx.send(str(error))
        traceback.print_exc()


    @commands.command(help='Command to send a test message to the server to verify that RCON is working.',
                      brief='Sends a message to the server to test RCON', usage='<message>')
    @commands.has_permissions(administrator=True)
    async def RCON_message(self, ctx: commands.Context, *, message: str):
        for server in self.bot.servers:
            test_message = valve.rcon.execute((server.server_address, server.server_port), server.RCON_password,
                                              f'say {message}')
            print(f'Server #{server.id} | {test_message}')

    @RCON_message.error
    async def RCON_message_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Only an administrator can send a message using the console')
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify the message')
        traceback.print_exc()

    @commands.command(help='This command unbans everyone on the server. Useful fix.',
                      brief='Unbans everyone from the server', hidden=True)
    @commands.has_permissions(administrator=True)
    async def RCON_unban(self, ctx: commands.Context):
        for server in self.bot.servers:
            unban = valve.rcon.execute((server.server_address, server.server_port), server.RCON_password,
                                       'removeallids')
            print(f'Server #{server.id} | {unban}')

    @RCON_unban.error
    async def RCON_unban_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Only an administrator can unban every player')
        traceback.print_exc()

    @commands.command(aliases=['end', 'stop'],
                      help='This command force ends a match.',
                      brief='Force ends a match', usage='<ServerID>')
    @commands.has_permissions(administrator=True)
    async def force_end(self, ctx: commands.Context, server_id: int = 0):
        valve.rcon.execute((self.bot.servers[server_id].server_address, self.bot.servers[server_id].server_port),
                           self.bot.servers[server_id].RCON_password, 'get5_endmatch')

def setup(client):
    client.add_cog(Setup(client))
