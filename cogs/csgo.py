import asyncio
import bot
import discord
import json
import os
import sqlite3
import traceback
import valve.rcon
import valve.source.a2s

from datetime import date
from discord.ext import commands
from random import choice
from random import randint
from utils.veto_image import VetoImage

# TODO: Allow administrators to update the maplist
active_map_pool = ['de_inferno', 'de_train', 'de_mirage', 'de_nuke', 'de_overpass', 'de_dust2', 'de_vertigo']
reserve_map_pool = ['de_cache', 'de_cbble', 'cs_office', 'cs_agency']
current_map_pool = active_map_pool.copy()

emoji_bank = ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
x_emoji = '❌'

# Veto style 1 2 2 2 1, last two 1s are for if we are playing with coaches
player_veto = [1, 2, 2, 2, 1, 1, 1]


class CSGO(commands.Cog):
    def __init__(self, bot, veto_image):
        self.bot = bot
        self.veto_image = veto_image

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
        # Uncomment for testing
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

        message = await ctx.send('10 man time\nLoading player selection...')
        for emoji in emojis:
            await message.add_reaction(emoji)

        while len(players) > 0:
            message_text = ''
            players_text = ''

            if current_team_player_select == 1:
                message_text += f'<@{team1_captain.id}>'
                current_captain = team1_captain
            elif current_team_player_select == 2:
                message_text += f'<@{team2_captain.id}>'
                current_captain = team2_captain

            message_text += f' select {player_veto[player_veto_count]}\n'
            message_text += 'You have 60 seconds to choose your player(s)\n'

            i = 0
            for player in players:
                players_text += f'{emojis[i]} - <@{player.id}>\n'
                i += 1
            embed = self.player_veto_embed(message_text=message_text, players_text=players_text, team1=team1,
                                           team1_captain=team1_captain, team2=team2, team2_captain=team2_captain)
            await message.edit(content=message_text, embed=embed)

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
                        if current_team_player_select == 1:
                            team1.append(players[index])
                        if current_team_player_select == 2:
                            team2.append(players[index])
                        emojis_selected.append(reaction.emoji)
                        del emojis[index]
                        del players[index]
                        selected_players += 1

                seconds += 1

                if seconds % 60 == 0:
                    for _ in range(0, player_veto[player_veto_count]):
                        index = randint(0, len(players) - 1)
                        if current_team_player_select == 1:
                            team1.append(players[index])
                        if current_team_player_select == 2:
                            team2.append(players[index])
                        emojis_selected.append(emojis[index])
                        del emojis[index]
                        del players[index]
                        selected_players += 1

                if selected_players == player_veto[player_veto_count]:
                    if current_team_player_select == 1:
                        current_team_player_select = 2
                    elif current_team_player_select == 2:
                        current_team_player_select = 1
                    break

            player_veto_count += 1

        message_text = 'Game Loading'
        players_text = 'None'
        embed = self.player_veto_embed(message_text=message_text, players_text=players_text, team1=team1,
                                       team1_captain=team1_captain, team2=team2, team2_captain=team2_captain)
        await message.edit(content=message_text, embed=embed)

        team1_steamIDs = []
        team2_steamIDs = []

        team1_channel = await ctx.author.voice.channel.category.create_voice_channel(
            name=f'{team1_captain.display_name}\'s Team', user_limit=7)
        team2_channel = await ctx.author.voice.channel.category.create_voice_channel(
            name=f'{team2_captain.display_name}\'s Team', user_limit=7)

        for player in team1:
            await player.move_to(channel=team1_channel, reason=f'You are on {team1_captain}\'s Team')
            cursor.execute('SELECT steam_id FROM users WHERE discord_id = ?', (str(player),))
            data = cursor.fetchone()
            team1_steamIDs.append(data[0])

        for player in team2:
            await player.move_to(channel=team2_channel, reason=f'You are on {team2_captain}\'s Team')
            cursor.execute('SELECT steam_id FROM users WHERE discord_id = ?', (str(player),))
            data = cursor.fetchone()
            team2_steamIDs.append(data[0])

        map_list = await self.map_veto(ctx, team1_captain, team2_captain)

        match_config = {
            'matchid': f'PUG {date.today().strftime("%d-%B-%Y")}',
            'num_maps': 1,
            'maplist': map_list,
            'skip_veto': True,
            'veto_first': 'team1',
            'side_type': 'always_knife',
            'players_per_team': len(team2),
            'min_players_to_ready': 1,
            'team1': {
                'name': f'team {team1_captain.display_name}',
                'tag': 'team1',
                'flag': 'IE',
                'players': team1_steamIDs
            },
            'team2': {
                'name': f'team {team2_captain.display_name}',
                'tag': 'team2',
                'flag': 'IE',
                'players': team2_steamIDs
            }
        }

        with open('./match_config.json', 'w') as outfile:
            json.dump(match_config, outfile, ensure_ascii=False, indent=4)

        match_config_json = await ctx.send(file=discord.File('match_config.json', '../match_config.json'))
        await ctx.send('If you are coaching, once you join the server, type .coach')
        await asyncio.sleep(0.3)
        valve.rcon.execute(bot.server_address, bot.RCON_password, 'exec triggers/get5')
        await self.connect(ctx)
        await asyncio.sleep(10)
        valve.rcon.execute(bot.server_address, bot.RCON_password,
                           f'get5_loadmatch_url "{match_config_json.attachments[0].url}"')

    @pug.error
    async def pug_error(self, ctx, error):
        if isinstance(error, commands.UserInputError):
            await ctx.send(error)
        elif isinstance(error, commands.CommandError):
            await ctx.send(error)
        traceback.print_exc(error)

    def player_veto_embed(self, message_text, players_text, team1, team1_captain, team2, team2_captain):
        team1_text = ''
        team2_text = ''
        for team1_player in team1:
            team1_text += f'<@{team1_player.id}>'
            if team1_player is team1_captain:
                team1_text += ' 👑'
            team1_text += '\n'
        for team2_player in team2:
            team2_text += f'<@{team2_player.id}>'
            if team2_player is team2_captain:
                team2_text += ' 👑'
            team2_text += '\n'

        embed = discord.Embed()
        embed.add_field(name=f'Team {team1_captain.display_name}', value=team1_text, inline=True)
        embed.add_field(name='Players', value=players_text, inline=True)
        embed.add_field(name=f'Team {team2_captain.display_name}', value=team2_text, inline=True)
        return embed

    async def map_veto(self, ctx, team1_captain, team2_captain):
        veto_image_fp = 'result.png'

        async def get_embed(current_team_captain, temp_channel):
            attachment = discord.File(veto_image_fp, veto_image_fp)
            img_message = await temp_channel.send(file=attachment)

            embed = discord.Embed(title='__Map veto__', color=discord.Colour(0x650309))
            embed.set_image(url=img_message.attachments[0].url)
            embed.set_footer(text=f'It is now {current_team_captain}\'s turn to veto',
                             icon_url=current_team_captain.avatar_url)
            return embed
        
        async def add_reactions(message, num_maps):
            for index in range(1, num_maps + 1):
                await message.add_reaction(emoji_bank[index])
        
        async def get_next_map_veto(message, current_team_captain):
            for reaction in message.reactions:
                users = await reaction.users().flatten()
                index = emoji_bank.index(reaction.emoji) - 1
                if (reaction.emoji in emoji_bank and not is_vetoed[index] and
                        current_team_captain in users):
                    return map_list[index]

        async def get_chosen_map_embed(chosen_map):
            chosen_map_file_name = chosen_map + self.veto_image.image_extension
            chosen_map_fp = os.path.join(self.veto_image.map_images_fp, chosen_map_file_name)
            attachment = discord.File(chosen_map_fp, chosen_map_file_name)
            image_message = await temp_channel.send(file=attachment)
            chosen_map_image_url = image_message.attachments[0].url
            map_chosen_embed = discord.Embed(title=f'The chosen map is ```{chosen_map}```',
                                            color=discord.Colour(0x650309))
            map_chosen_embed.set_image(url=chosen_map_image_url)

            return map_chosen_embed

        map_list = current_map_pool.copy()
        is_vetoed = [False] * len(map_list)
        num_maps_left = len(map_list)
        current_team_captain = choice((team1_captain, team2_captain))

        current_category = ctx.channel.category
        temp_channel = await ctx.guild.create_text_channel('temp', category=current_category)

        self.veto_image.construct_veto_image(map_list, veto_image_fp,
                                             is_vetoed=is_vetoed, spacing=25)
        embed = await get_embed(current_team_captain, temp_channel)
        message = await ctx.send(embed=embed)

        await add_reactions(message, len(map_list))

        while num_maps_left > 1:
            message = await ctx.fetch_message(message.id)

            if current_team_captain == team1_captain:
                if map_vetoed := await get_next_map_veto(message, current_team_captain):
                    current_team_captain = team2_captain
            else:
                if map_vetoed := await get_next_map_veto(message, current_team_captain):
                    current_team_captain = team1_captain

            if map_vetoed:
                vetoed_map_index = map_list.index(map_vetoed)
                is_vetoed[vetoed_map_index] = True
                self.veto_image.construct_veto_image(map_list, veto_image_fp,
                                                     is_vetoed=is_vetoed, spacing=25)
                embed = await get_embed(current_team_captain, temp_channel)
                await message.edit(embed=embed)
                await message.clear_reaction(emoji_bank[vetoed_map_index + 1])
                num_maps_left -= 1
            
            await asyncio.sleep(1)

        map_list = list(filter(lambda map_name: not is_vetoed[map_list.index(map_name)], map_list))

        await message.clear_reactions()
        chosen_map = map_list[0] 
        chosen_map_embed = await get_chosen_map_embed(chosen_map)
        await message.edit(embed=chosen_map_embed)
        await temp_channel.delete()

        return map_list

    @commands.command(help='This command creates a URL that people can click to connect to the server.',
                      brief='Creates a URL people can connect to')
    async def connect(self, ctx):
        with valve.source.a2s.ServerQuerier(bot.server_address, timeout=20) as server:
            info = server.info()
        embed = discord.Embed(title=info['server_name'], color=0xf4c14e)
        embed.set_thumbnail(url="https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/apps/730/69f7ebe2735c366c65c0b33dae00e12dc40edbe4.jpg")
        embed.add_field(name='Quick Connect',
                        value=f'steam://connect/{bot.server_address[0]}:{bot.server_address[1]}/{bot.server_password}',
                        inline=False)
        embed.add_field(name='Console Connect',
                        value=f'connect {bot.server_address[0]}:{bot.server_address[1]}; password {bot.server_password}',
                        inline=False)
        embed.add_field(name='Players', value=f'{info["player_count"]}/{info["max_players"]}', inline=True)
        embed.add_field(name='Map', value=info['map'], inline=True)
        await ctx.send(embed=embed)

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
    veto_image_generator = VetoImage('images/map_images', 'images/x.png', 'png')
    client.add_cog(CSGO(client, veto_image_generator))
