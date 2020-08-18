import discord
from discord.ext import commands
import valve.rcon
from steam.steamid import SteamID, from_url
import sqlite3
import json
import traceback
import bot


class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        help='This command connects the bot to the CSGO server and validates that the connection is valid. It then'
             ' saves all the information to the config.json file.', brief='Connects the bot to the CSGO server',
        usage='server_address port server_password RCON_password')
    @commands.has_permissions(administrator=True)
    async def setup_server(self, ctx, server_address_in, port, password, RCON_password_in):
        test_connection = valve.rcon.RCON((str(server_address_in), int(port)), RCON_password_in)
        test_connection.connect()
        test_connection.authenticate()
        test_connection.close()

        bot.server_address = (str(server_address_in), int(port))
        bot.server_password = str(password)
        bot.RCON_password = str(RCON_password_in)

        config = {
            'discord_api': bot.bot_secret,
            'server_address': server_address_in,
            'server_port': int(port),
            'server_password': password,
            'RCON_password': RCON_password_in
        }

        with open('./config.json', 'w') as outfile:
            json.dump(config, outfile, ensure_ascii=False, indent=4)

        ctx.send(f'Successfully connected to {bot.server_address}')

    @setup_server.error
    async def setup_server_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Only an administrator can setup the server')
        if isinstance(error, valve.rcon.RCONAuthenticationError) or isinstance(error, commands.CommandInvokeError):
            await ctx.send('RCON authentication failed')
        traceback.print_exc(error)

    @commands.command(help='This command sets the channel that will be used for Team 1.',
                      brief='Sets the channel for Team 1')
    @commands.has_permissions(administrator=True)
    async def setup_team1(self, ctx):
        bot.team1_channel = ctx.author.voice.channel
        await ctx.send(f'{bot.team1_channel} is now the channel for Team 1')

    @setup_team1.error
    async def setup_team1_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Only an administrator set the team channel')
        traceback.print_exc(error)

    @commands.command(help='This command sets the channel that will be used for Team 2.',
                      brief='Sets the channel for Team 2')
    @commands.has_permissions(administrator=True)
    async def setup_team2(self, ctx):
        bot.team2_channel = ctx.author.voice.channel
        await ctx.send(f'{bot.team2_channel} is now the channel for Team 2')

    @setup_team2.error
    async def setup_team2_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Only an administrator set the team channel')
        traceback.print_exc(error)

    @commands.command(help='This command connects users steam account to the bot.',
                      brief='Connect your SteamID to the bot', usage='SteamID or CommunityURL')
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
                      brief='Sends a message to the server to test RCON', usage='message')
    @commands.has_permissions(administrator=True)
    async def RCON_message(self, ctx, *, message):
        test = valve.rcon.execute(bot.server_address, bot.RCON_password, f'say {message}')
        print(test)

    @RCON_message.error
    async def RCON_message_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Only an administrator set the team channel')
        traceback.print_exc(error)

    @commands.command(help='This command unbans everyone on the server. Useful fix',
                      brief='Unbans everyone from the server')
    @commands.has_permissions(administrator=True)
    async def RCON_unban(self, ctx):
        unban = valve.rcon.execute(bot.server_address, bot.RCON_password, 'removeallids')
        print(unban)

    @RCON_unban.error
    async def RCON_unban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Only an administrator set the team channel')
        traceback.print_exc(error)

    @commands.command(hidden=True)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount)

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify an amount of messages to delete.')
        traceback.print_exc(error)


def setup(client):
    client.add_cog(Setup(client))
