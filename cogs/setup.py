import discord
import json
import sqlite3
import traceback
import valve.rcon

from discord.ext import commands
from steam.steamid import SteamID, from_url


class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help='This command connects users steam account to the bot.',
                      brief='Connect your SteamID to the bot', usage='<SteamID or CommunityURL>')
    async def link(self, ctx, steamID_input):
        steamID = SteamID(steamID_input)
        if not steamID.is_valid():
            steamID = from_url(steamID_input, http_timeout=15)
            if steamID is None:
                steamID = from_url(f'https://steamcommunity.com/id/{steamID_input}/', http_timeout=15)
                if steamID is None:
                    raise commands.UserInputError(message='Please enter a valid SteamID or community url.')
        db = sqlite3.connect('./main.sqlite')
        cursor = db.cursor()
        cursor.execute('''
                        REPLACE INTO users (discord_id, steam_id)
                        VALUES( ?, ? )
                        ''', (str(ctx.author), str(steamID.as_steam2_zero),))
        db.commit()
        cursor.close()
        await ctx.send(f'Connected {steamID.community_url}')

    @link.error
    async def link_error(self, ctx, error):
        if isinstance(error, commands.UserInputError):
            await ctx.send(error)
        traceback.print_exc(error)

    @commands.command(help='Command to send a test message to the server to verify that RCON is working.',
                      brief='Sends a message to the server to test RCON', usage='<message>')
    @commands.has_permissions(administrator=True)
    async def RCON_message(self, ctx, *, message):
        test = valve.rcon.execute((self.bot.servers[0]["server_address"], self.bot.servers[0]["server_port"]),
                           self.bot.servers[0]["RCON_password"], f'say {message}')
        print(test)

    @RCON_message.error
    async def RCON_message_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Only an administrator can send a message using the console')
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify the message')
        traceback.print_exc(error)

    @commands.command(help='This command unbans everyone on the server. Useful fix',
                      brief='Unbans everyone from the server', hidden=True)
    @commands.has_permissions(administrator=True)
    async def RCON_unban(self, ctx):
        unban = valve.rcon.execute((self.bot.servers[0]["server_address"], self.bot.servers[0]["server_port"]),
                           self.bot.servers[0]["RCON_password"], 'removeallids')
        print(unban)

    @RCON_unban.error
    async def RCON_unban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Only an administrator can unban every player')
        traceback.print_exc(error)

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount)

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify an amount of messages to delete')
        traceback.print_exc(error)

    @commands.command(aliases=['version'], help='This command gets the bot information and version')
    async def about(self, ctx):
        embed = discord.Embed(color=0xff0000)
        embed.add_field(name=f'Discord 10 Man Bot V{self.bot.version}',
                        value=f'Built by <@125033487051915264> & <@282670937738969088>', inline=False)
        await ctx.send(embed=embed)

def setup(client):
    client.add_cog(Setup(client))
