import discord
from discord.ext import commands
from random import randint
from datetime import date
import sqlite3
import valve.rcon
import asyncio
import traceback
import json
import bot


# TODO: Allow administrators to update the maplist
active_map_pool = ['de_inferno', 'de_train', 'de_mirage', 'de_nuke', 'de_overpass', 'de_dust2', 'de_vertigo']
reserve_map_pool = ['de_cache', 'de_cbble', 'cs_office', 'cs_agency']
current_map_pool = active_map_pool.copy()

emoji_bank = ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

# Veto style 1 2 2 2 1, last two 1s are for if we are playing with coaches
player_veto = [1, 2, 2, 2, 1, 1, 1]


class CSGO(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['10man', 'setup'],
                      help='This command takes the users in a voice channel and selects two random '
                           'captains. It then allows those captains to select the members of their '
                           'team in a 1 2 2 2 2 1 fashion. It then configures the server with the '
                           'correct config.', brief='Helps automate setting up a PUG')
    async def pug(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.UserInputError(message='You must be in a voice channel.')
        if len(ctx.author.voice.channel.members) < 10:
            raise commands.CommandError(message='There must be 10 members connected to the voice channel')
        db = sqlite3.connect('./main.sqlite')
        cursor = db.cursor()
        not_connected_members = []
        for member in ctx.author.voice.channel.members:
            cursor.execute('SELECT 1 FROM users WHERE discord_id = ?', (str(member),))
            data = cursor.fetchone()
            if data is None:
                not_connected_members.append(member)
        if len(not_connected_members) > 0:
            error_message = ''
            for member in not_connected_members:
                error_message += f'<@{member.id}> '
            error_message += 'must connect their steam account with the command ```.connect <Steam Profile URL>```'
            raise commands.UserInputError(message=error_message)

        # TODO: Refactor this mess
        # TODO: Add a way to cancel
        players = ctx.author.voice.channel.members.copy()
        # players = [ctx.author] * 10
        emojis = emoji_bank.copy()
        del emojis[len(players) - 2:len(emojis)]
        emojis_selected = []
        team1 = []
        team2 = []
        team1_captain = players[randint(0, len(players) - 1)]
        team1.append(team1_captain)
        players.remove(team1_captain)
        team2_captain = players[randint(0, len(players) - 1)]
        team2.append(team2_captain)
        players.remove(team2_captain)

        current_team_player_select = 1

        current_captain = team1_captain
        player_veto_count = 0

        message = await ctx.send('10 man time')

        while len(players) > 0:
            players_pretty = ''
            if current_team_player_select == 1:
                players_pretty += f'<@{team1_captain.id}>'
                current_captain = team1_captain
            elif current_team_player_select == 2:
                players_pretty += f'<@{team2_captain.id}>'
                current_captain = team2_captain

            print(player_veto_count)
            players_pretty += f' select {player_veto[player_veto_count]}\n'
            players_pretty += 'You have 60 seconds to choose your player(s)\n'

            i = 0
            for player in players:
                players_pretty += f'{emojis[i]} - <@{player.id}>\n'
                i += 1
            players_pretty += 'Team 1:\n'
            for team1_player in team1:
                players_pretty += f'<@{team1_player.id}>\n'
            players_pretty += 'Team 2:\n'
            for team2_player in team2:
                players_pretty += f'<@{team2_player.id}>\n'

            await message.edit(content=players_pretty)
            if player_veto_count == 0:
                for emoji in emojis:
                    await message.add_reaction(emoji)

            selected_players = 0
            seconds = 0
            while True:
                await asyncio.sleep(1)
                message = await ctx.fetch_message(message.id)

                for reaction in message.reactions:
                    users = await reaction.users().flatten()
                    if current_captain in users and selected_players < player_veto[player_veto_count] and not (
                            reaction.emoji in emojis_selected):
                        index = emojis.index(reaction.emoji)
                        print(emojis_selected)
                        if current_team_player_select == 1:
                            team1.append(players[index])
                        if current_team_player_select == 2:
                            team2.append(players[index])
                        print(reaction.emoji)
                        emojis_selected.append(reaction.emoji)
                        del emojis[index]
                        del players[index]
                        selected_players += 1

                seconds += 1
                if selected_players == player_veto[player_veto_count]:
                    if current_team_player_select == 1:
                        current_team_player_select = 2
                    elif current_team_player_select == 2:
                        current_team_player_select = 1
                    break

                if seconds % 60 == 0:
                    await ctx.send(f'<@{team1_captain.id}>')
                    break
            player_veto_count += 1

        team1_steamIDs = []
        team2_steamIDs = []

        team1_channel = await ctx.author.voice.channel.category.create_voice_channel(name=f'{team1_captain}\'s Team',
                                                                                     user_limit=7)
        team2_channel = await ctx.author.voice.channel.category.create_voice_channel(name=f'{team2_captain}\'s Team',
                                                                                     user_limit=7)

        for player in team1:
            player.move_to(channel=team1_channel, reason=f'You are on {team1_captain}\'s Team')
            cursor.execute('SELECT steam_id FROM users WHERE discord_id = ?', (str(player),))
            data = cursor.fetchone()
            team1_steamIDs.append(data[0])

        for player in team2:
            player.move_to(channel=team2_channel, reason=f'You are on {team2_captain}\'s Team')
            cursor.execute('SELECT steam_id FROM users WHERE discord_id = ?', (str(player),))
            data = cursor.fetchone()
            team2_steamIDs.append(data[0])

        today = date.today()

        maps_string = 'Veto Maps Pool: '
        for map in current_map_pool:
            maps_string += f'{map}, '

        await ctx.send(maps_string[:-2])

        match_config = {
            'matchid': f'PUG {today.strftime("%d-%B-%Y")}',
            'num_maps': 1,
            'maplist': current_map_pool,
            'skip_veto': False,
            'veto_first': 'team1',
            'side_type': 'always_knife',
            'players_per_team': len(team2),
            'min_players_to_ready': 1,
            'team1': {
                'name': f'{team1_captain}\'s Team',
                'tag': 'team1',
                'flag': 'IE',
                'players': team1_steamIDs
            },
            'team2': {
                'name': f'{team2_captain}\'s Team',
                'tag': 'team2',
                'flag': 'IE',
                'players': team2_steamIDs
            }
        }

        with open('./match_config.json', 'w') as outfile:
            json.dump(match_config, outfile, ensure_ascii=False, indent=4)

        match_config_json = await ctx.send(file=discord.File('match_config.json', '../match_config.json'))
        await asyncio.sleep(0.3)
        await self.connect(ctx)
        await ctx.send('If you are coaching, once you join the server, type .coach')

        print(match_config_json.attachments[0].url)
        changeToGet5 = valve.rcon.execute(bot.server_address, bot.RCON_password, 'exec triggers/get5')
        print(changeToGet5)
        await asyncio.sleep(10)
        executeMatch = valve.rcon.execute(bot.server_address, bot.RCON_password,
                                          f'get5_loadmatch_url "{match_config_json.attachments[0].url}"')
        print(executeMatch)

        # TODO: when game is over, change the status of the bot

    @pug.error
    async def pug_error(self, ctx, error):
        if isinstance(error, commands.UserInputError):
            await ctx.send(error)
        elif isinstance(error, commands.CommandError):
            await ctx.send(error)
        traceback.print_exc(error)

    @commands.command(help='This command creates a URL that people can click to connect to the server.',
                      brief='Creates a URL people can connect to')
    async def connect(self, ctx):
        # TODO: Change to be some image or attachment with server info
        await ctx.send(f'steam://connect/{bot.server_address[0]}:{bot.server_address[1]}/{bot.server_password}')

    @commands.command(aliases=['maps'], help='This command allows the user to change the map pool. '
                                             'Must have odd number of maps. Use "active" or "reserve" for the respective map pools.',
                      brief='Changes map pool', usage='<lists of maps> or "active" or "reserve"')
    async def map_pool(self, ctx, *, args):
        global current_map_pool
        if args == 'active':
            current_map_pool = active_map_pool.copy()
        elif args == 'reserve':
            current_map_pool = reserve_map_pool.copy()
        else:
            current_map_pool = args.split().copy()


def setup(client):
    client.add_cog(CSGO(client))
