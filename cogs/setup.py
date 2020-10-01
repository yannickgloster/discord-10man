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

    @commands.command(help='This command connects users steam account to the bot.',
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
                        ''', {"discord_id": str(ctx.author), "steam_id": str(steamID.as_steam2_zero)})
        await ctx.send(f'Connected {steamID.community_url}')

    @link.error
    async def link_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.UserInputError):
            await ctx.send(str(error))
        traceback.print_exc()

    @commands.command(help='Command to set the server for the queue system. You must be in a voice channel.',
                      brief='Set\'s the server for the queue')
    @commands.check(checks.voice_channel)
    async def setup_queue(self, ctx: commands.Context, enabled: bool = False):
        self.bot.queue_voice_channel = ctx.author.voice.channel
        self.bot.queue_ctx = ctx
        self.bot.cogs['CSGO'].pug.enabled = not enabled
        self.bot.cogs['CSGO'].queue_check.start()
        await ctx.send(
            f'{self.bot.queue_ctx.author.voice.channel} is the queue channel.\n'
            f'Queue is {"enabled" if enabled else "disabled"}.\n'
            f'Pug Command is {"enabled" if not enabled else "disabled"}.')

    @setup_queue.error
    async def setup_queue_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandError):
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
    async def RCON_message_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Only an administrator can send a message using the console')
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify the message')
        traceback.print_exc()

    @commands.command(help='This command unbans everyone on the server. Useful fix',
                      brief='Unbans everyone from the server', hidden=True)
    @commands.has_permissions(administrator=True)
    async def RCON_unban(self, ctx: commands.Context):
        for server in self.bot.servers:
            unban = valve.rcon.execute((server.server_address, server.server_port), server.RCON_password, 'removeallids')
            print(f'Server #{server.id} | {unban}')

    @RCON_unban.error
    async def RCON_unban_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Only an administrator can unban every player')
        traceback.print_exc()


def setup(client):
    client.add_cog(Setup(client))
