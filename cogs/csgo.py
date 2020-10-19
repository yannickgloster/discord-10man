import aiohttp
import asyncio
import checks
import discord
import json
import os
import socket
import traceback
import valve.rcon
import valve.source.a2s

from bot import Discord_10man
from databases import Database
from datetime import date
from discord.ext import commands, tasks
from random import choice
from random import randint
from typing import List
from utils.csgo_server import CSGOServer
from utils.veto_image import VetoImage

# TODO: Allow administrators to update the maplist
active_map_pool = ['de_inferno', 'de_train', 'de_mirage', 'de_nuke', 'de_overpass', 'de_dust2', 'de_vertigo']
reserve_map_pool = ['de_cache', 'de_cbble', 'cs_office', 'cs_agency']
current_map_pool = active_map_pool.copy()

emoji_bank = ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

# Veto style 1 2 2 2 1, last two 1s are for if we are playing with coaches
player_veto = [1, 2, 2, 2, 1, 1, 1]


class CSGO(commands.Cog):
    def __init__(self, bot: Discord_10man, veto_image):
        self.bot: Discord_10man = bot
        self.veto_image = veto_image
        self.readied_up: bool = False

    @commands.command(aliases=['10man', 'setup'],
                      help='This command takes the users in a voice channel and selects two random '
                           'captains. It then allows those captains to select the members of their '
                           'team in a 1 2 2 2 1 fashion. It then configures the server with the '
                           'correct config.', brief='Helps automate setting up a PUG')
    @commands.check(checks.voice_channel)
    @commands.check(checks.ten_players)
    @commands.check(checks.linked_accounts)
    @commands.check(checks.available_server)
    async def pug(self, ctx: commands.Context):
        # TODO: Refactor this mess
        db = Database('sqlite:///main.sqlite')
        await db.connect()
        csgo_server = self.bot.servers[0]
        for server in self.bot.servers:
            if server.available:
                server.available = False
                csgo_server = server
                break
        channel_original = ctx.author.voice.channel
        players: List[discord.Member] = ctx.author.voice.channel.members.copy()
        players = players[0: 13]
        if self.bot.dev:
            players = [ctx.author] * 10
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

        emoji_remove = []

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
            if len(emoji_remove) > 0:
                for emoji in emoji_remove:
                    await message.clear_reaction(emoji)
                emoji_remove = []

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
                        emoji_remove.append(reaction.emoji)
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

        message_text = 'Map Veto Loading'
        players_text = 'None'
        embed = self.player_veto_embed(message_text=message_text, players_text=players_text, team1=team1,
                                       team1_captain=team1_captain, team2=team2, team2_captain=team2_captain)
        await message.edit(content=message_text, embed=embed)
        await message.clear_reactions()

        team1_steamIDs = []
        team2_steamIDs = []

        if ctx.author.voice.channel.category is None:
            team1_channel = await ctx.guild.create_voice_channel(name=f'team_{team1_captain.display_name}',
                                                                 user_limit=7)
            team2_channel = await ctx.guild.create_voice_channel(name=f'team_{team2_captain.display_name}',
                                                                          user_limit=7)
        else:
            team1_channel = await ctx.author.voice.channel.category.create_voice_channel(
                name=f'team_{team1_captain.display_name}', user_limit=7)
            team2_channel = await ctx.author.voice.channel.category.create_voice_channel(
                name=f'team_{team2_captain.display_name}', user_limit=7)

        for player in team1:
            await player.move_to(channel=team1_channel, reason=f'You are on {team1_captain}\'s Team')
            data = await db.fetch_one('SELECT steam_id FROM users WHERE discord_id = :player',
                                      {"player": str(player.id)})
            team1_steamIDs.append(data[0])

        for player in team2:
            await player.move_to(channel=team2_channel, reason=f'You are on {team2_captain}\'s Team')
            data = await db.fetch_one('SELECT steam_id FROM users WHERE discord_id = :player',
                                      {"player": str(player.id)})
            team2_steamIDs.append(data[0])

        map_list = await self.map_veto(ctx, team1_captain, team2_captain)

        bot_ip = self.bot.web_server.IP
        if self.bot.bot_IP != "":
            bot_ip = self.bot.bot_IP

        match_config = {
            'matchid': f'PUG-{date.today().strftime("%d-%B-%Y")}',
            'num_maps': 1,
            'maplist': map_list,
            'skip_veto': True,
            'veto_first': 'team1',
            'side_type': 'always_knife',
            'players_per_team': len(team2),
            'min_players_to_ready': 1,
            'team1': {
                'name': f'team_{team1_captain.display_name}',
                'tag': 'team1',
                'flag': 'IE',
                'players': team1_steamIDs
            },
            'team2': {
                'name': f'team_{team2_captain.display_name}',
                'tag': 'team2',
                'flag': 'IE',
                'players': team2_steamIDs
            },
            'cvars': {
                'get5_event_api_url': f'http://{bot_ip}:{self.bot.web_server.port}/'
            }
        }

        with open('./match_config.json', 'w') as outfile:
            json.dump(match_config, outfile, ensure_ascii=False, indent=4)

        await ctx.send('If you are coaching, once you join the server, type .coach')
        loading_map_message = await ctx.send('Server is being configured')
        await asyncio.sleep(0.3)
        valve.rcon.execute((csgo_server.server_address, csgo_server.server_port), csgo_server.RCON_password,
                           'exec triggers/get5')
        await asyncio.sleep(10)
        await loading_map_message.delete()
        valve.rcon.execute((csgo_server.server_address, csgo_server.server_port), csgo_server.RCON_password,
                           f'get5_loadmatch_url "{bot_ip}:{self.bot.web_server.port}/match"')

        await asyncio.sleep(5)
        connect_embed = await self.connect_embed(csgo_server)
        await ctx.send(embed=connect_embed)
        score_embed = discord.Embed()
        score_embed.add_field(name='0', value=f'team_{team1_captain.display_name}', inline=True)
        score_embed.add_field(name='0', value=f'team_{team2_captain.display_name}', inline=True)
        score_message = await ctx.send('Match in Progress', embed=score_embed)

        csgo_server.get_context(ctx=ctx, channels=[channel_original, team1_channel, team2_channel],
                                players=team1 + team2, score_message=score_message)
        csgo_server.set_team_names(['team1', 'team2'])
        self.bot.web_server.add_server(csgo_server)


        if not self.pug.enabled:
            self.queue_check.start()

    @pug.error
    async def pug_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandError):
            await ctx.send(str(error))
        traceback.print_exc()

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

    async def map_veto(self, ctx: commands.Context, team1_captain, team2_captain):
        '''Returns :class:`list` of :class:`str` which is the remaining map
        after the veto

        Embed image updates as the maps are vetoed. The team captains can
        veto a map by reacting to the map number to be vetoed

        Parameters
        -----------
        ctx: :class:`discord.Context`
            The context object provided
        team1_captain: :class:`discord.Member`
            One of the team captains
        team2_captain: :class:`discord.Member`
            The other team captain
        '''

        veto_image_fp = 'result.png'
        session = aiohttp.ClientSession()
        base_url = f'http://{self.bot.bot_IP}:{self.bot.web_server.port}'

        async def get_embed(current_team_captain):
            ''' Returns :class:`discord.Embed` which contains the map veto
            image and the current team captain who has to make a veto

            Parameters
            -----------
            current_team_captain: :class:`discord.Member`
                The current team captain
            '''
            embed = discord.Embed(title='__Map veto__',
                                  color=discord.Colour(0x650309))
            response = await session.get(f'{base_url}/map-veto')
            path = (await response.json())['path']
            url = base_url + path
            embed.set_image(url=url)
            embed.set_footer(text=f'It is now {current_team_captain}\'s turn to veto',
                             icon_url=current_team_captain.avatar_url)
            return embed

        async def add_reactions(message, num_maps):
            ''' Adds the number emoji reactions to the message. This is used
            to select the veto map

            Parameters
            -----------
            message: :class:`discord.Message`
                The veto message to add the number emoji reactions to
            num_maps: :class:`int`
                The number of maps there are to chose from
            '''

            for index in range(1, num_maps + 1):
                await message.add_reaction(emoji_bank[index])

        async def get_next_map_veto(message, current_team_captain):
            ''' Obtains the next map which was vetoed

            Parameters
            -----------
            message: :class:`discord.Message`
                The veto message which has the number emoji reactions
            num_maps: :class:`discord.Member`
                The current team captain
            '''

            check = lambda reaction, user: reaction.emoji in emoji_bank and user == current_team_captain
            (reaction, _) = await self.bot.wait_for('reaction_add', check=check)
            index = emoji_bank.index(reaction.emoji) - 1

            return map_list[index]

        async def get_chosen_map_embed(chosen_map):
            ''' Returns a :class:`discord.Embed` which contains an image of
            the map chosen on completion of the veto

            Parameters
            -----------
            chosen_map: :class:`str`
                The chosen map name string
            '''

            chosen_map_file_name = chosen_map + self.veto_image.image_extension
            chosen_map_fp = os.path.join(
                self.veto_image.map_images_fp, chosen_map_file_name)
            percentage = 0.25
            VetoImage.resize(chosen_map_fp, percentage, output_fp=veto_image_fp)
            response = await session.get(f'{base_url}/map-veto')
            path = (await response.json())['path']
            chosen_map_image_url = base_url + path
            map_chosen_embed = discord.Embed(title=f'The chosen map is ```{chosen_map}```',
                                             color=discord.Colour(0x650309))
            map_chosen_embed.set_image(url=chosen_map_image_url)

            return map_chosen_embed

        map_list = current_map_pool.copy()
        is_vetoed = [False] * len(map_list)
        num_maps_left = len(map_list)
        current_team_captain = choice((team1_captain, team2_captain))

        current_category = ctx.channel.category

        self.veto_image.construct_veto_image(map_list, veto_image_fp,
                                             is_vetoed=is_vetoed, spacing=25)
        embed = await get_embed(current_team_captain)
        message = await ctx.send(embed=embed)

        await add_reactions(message, len(map_list))

        while num_maps_left > 1:
            message = await ctx.fetch_message(message.id)

            map_vetoed = await get_next_map_veto(message, current_team_captain)
            vetoed_map_index = map_list.index(map_vetoed)
            is_vetoed[vetoed_map_index] = True

            if current_team_captain == team1_captain:
                current_team_captain = team2_captain
            else:
                current_team_captain = team1_captain

            self.veto_image.construct_veto_image(map_list, veto_image_fp,
                                                 is_vetoed=is_vetoed, spacing=25)
            embed = await get_embed(current_team_captain)
            await asyncio.gather(message.edit(embed=embed),
                                 message.clear_reaction(emoji_bank[vetoed_map_index + 1]))

            num_maps_left -= 1

        map_list = list(filter(lambda map_name: not is_vetoed[map_list.index(map_name)], map_list))

        chosen_map = map_list[0]
        chosen_map_embed = await get_chosen_map_embed(chosen_map)
        await asyncio.gather(message.clear_reactions(),
                             message.edit(embed=chosen_map_embed),
                             session.close())
        return map_list

    @tasks.loop(seconds=5.0)
    async def queue_check(self):
        available: bool = False
        for server in self.bot.servers:
            if server.available:
                available = True
                break
        if len(self.bot.queue_voice_channel.members) >= 10 & available:
            embed = discord.Embed()
            embed.add_field(name='You have 60 seconds to ready up!', value='Ready: ✅', inline=False)
            ready_up_message = await self.bot.queue_ctx.send(embed=embed)
            await ready_up_message.add_reaction('✅')
            self.ready_up.start(message=ready_up_message, members=self.bot.queue_voice_channel.members)
            self.queue_check.stop()

    @tasks.loop(seconds=1.0, count=60)
    async def ready_up(self, message: discord.Message, members: List[discord.Member]):
        message = await self.bot.queue_ctx.fetch_message(message.id)

        # TODO: Add check for only the first 10 users
        check_emoji = None
        for reaction in message.reactions:
            if reaction.emoji == '✅':
                check_emoji = reaction
                break

        users = await check_emoji.users().flatten()
        ready = True
        for member in members:
            if member not in users:
                ready = False
                break

        if ready:
            self.readied_up = True
            self.ready_up.stop()

    @ready_up.after_loop
    async def ready_up_cancel(self):
        if self.readied_up:
            self.readied_up = False
            await self.pug(self.bot.queue_ctx)
        else:
            # TODO: Kick people who haven't readied up
            await self.bot.queue_ctx.send('Not everyone readied up')
            self.queue_check.start()

    @commands.command(help='This command creates a URL that people can click to connect to the server.',
                      brief='Creates a URL people can connect to', usage='<ServerID>', hidden=True)
    async def connect(self, ctx: commands.Context, server_id: int = 0):
        embed = await self.connect_embed(self.bot.servers[server_id])
        test = await ctx.send(embed=embed)

    @connect.error
    async def connect_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error.__cause__, valve.source.NoResponseError) or isinstance(error.__cause__, socket.gaierror):
            embed = discord.Embed(color=0xff0000)
            embed.add_field(name="Cannot Connect to Server", value="No Response from Server", inline=False)
            await ctx.send(embed=embed)
        elif isinstance(error.__cause__, IndexError):
            embed = discord.Embed(color=0xff0000)
            embed.add_field(name="Cannot Connect to Server", value="Not valid Server ID", inline=False)
            await ctx.send(embed=embed)
        traceback.print_exc()

    async def connect_embed(self, csgo_server: CSGOServer) -> discord.Embed:
        with valve.source.a2s.ServerQuerier((csgo_server.server_address, csgo_server.server_port),
                                            timeout=20) as server:
            info = server.info()

        embed = discord.Embed(title=info['server_name'], color=0xf4c14e)
        embed.set_thumbnail(
            url="https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/apps/730/69f7ebe2735c366c65c0b33dae00e12dc40edbe4.jpg")
        embed.add_field(name='Quick Connect',
                        value=f'steam://connect/{csgo_server.server_address}:{csgo_server.server_port}/{csgo_server.server_password}',
                        inline=False)
        embed.add_field(name='Console Connect',
                        value=f'connect {csgo_server.server_address}:{csgo_server.server_port}; password {csgo_server.server_password}',
                        inline=False)
        embed.add_field(name='Players', value=f'{info["player_count"]}/{info["max_players"]}', inline=True)
        embed.add_field(name='Map', value=info['map'], inline=True)
        gotv = csgo_server.get_gotv()
        if gotv is None:
            embed.add_field(name='GOTV',
                            value='Not Configured',
                            inline=False)
        else:
            embed.add_field(name='GOTV',
                            value=f'connect {csgo_server.server_address}:{gotv}',
                            inline=False)
        return embed

    @commands.command(aliases=['maps'], help='This command allows the user to change the map pool. '
                                             'Must have odd number of maps. Use "active" or "reserve" for the respective map pools.',
                      brief='Changes map pool', usage='<lists of maps> or "active" or "reserve"')
    @commands.has_permissions(administrator=True)
    async def map_pool(self, ctx: commands.Context, *, args):
        global current_map_pool
        if args == 'active':
            current_map_pool = active_map_pool.copy()
        elif args == 'reserve':
            current_map_pool = reserve_map_pool.copy()
        else:
            current_map_pool = args.split().copy()

    @commands.command(aliases=['live', 'live_matches'], help='This command shows the current live matches.',
                      brief='Shows the current live matches')
    @commands.check(checks.active_game)
    async def matches(self, ctx: commands.Context):
        for server in self.bot.servers:
            if not server.available:
                score_embed = discord.Embed(color=0x00ff00)
                score_embed.add_field(name=f'{server.team_scores[0]}',
                                      value=f'{server.team_names[0]}', inline=True)
                score_embed.add_field(name=f'{server.team_scores[1]}',
                                      value=f'{server.team_names[1]}', inline=True)
                gotv = server.get_gotv()
                if gotv is None:
                    score_embed.add_field(name='GOTV',
                                          value='Not Configured',
                                          inline=False)
                else:
                    score_embed.add_field(name='GOTV',
                                          value=f'connect {server.server_address}:{gotv}',
                                          inline=False)
                score_embed.set_footer(text="🟢 Live")
                await ctx.send(embed=score_embed)

    @matches.error
    async def matches_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandError):
            await ctx.send(str(error))
        traceback.print_exc()


def setup(client):
    veto_image_generator = VetoImage('images/map_images', 'images/x.png', 'png')
    client.add_cog(CSGO(client, veto_image_generator))
