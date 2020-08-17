import discord
from discord.ext import commands
import valve.rcon
from steam.steamid import SteamID, from_url
import sqlite3
import json
from random import randint
from datetime import date
import asyncio
import traceback

bot = commands.Bot(command_prefix='.', case_insensitive=True)
bot_secret: str

server_address: (str, int)
server_password: str
RCON_password: str

team1_channel: discord.VoiceChannel
team2_channel: discord.VoiceChannel

# TODO: Allow administrators to update the maplist
active_map_pool = ['de_inferno', 'de_train', 'de_mirage', 'de_nuke', 'de_overpass', 'de_dust2', 'de_vertigo']
reserve_map_pool = ['de_cache', 'de_cbble', 'cs_office', 'cs_agency']

emoji_bank = ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

# Veto style 1 2 2 2 2 1, last two 1s are for if we are playing with coaches
# player_veto = [1, 2, 2, 2, 2, 1, 1, 1]
player_veto = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

# Loading JSON config file
with open('config.json') as config:
    json_data = json.load(config)
    bot_secret = str(json_data['discord_api'])
    server_address = (str(json_data['server_address']), int(json_data['server_port']))
    server_password = str(json_data['server_password'])
    RCON_password = str(json_data['RCON_password'])


@bot.event
async def on_ready():
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
            discord_id TEXT UNIQUE,
            steam_id TEXT
        )
        ''')
    db.close()
    # TODO: Custom state for waiting for pug or if a pug is already playing
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.playing,
                                                                                    state='Waiting', details='Waiting',
                                                                                    name='CSGO Pug'))
    global server_address, server_password, RCON_password

    print(f'{bot.user} connected.')


@bot.command(help='This command connects the bot to the CSGO server and validates that the connection is valid. It then'
                  ' saves all the information to the config.json file.', brief='Connects the bot to the CSGO server',
             usage='server_address port server_password RCON_password')
@commands.has_permissions(administrator=True)
async def setup_server(ctx, server_address_in, port, password, RCON_password_in):
    test_connection = valve.rcon.RCON((str(server_address_in), int(port)), RCON_password_in)
    test_connection.connect()
    test_connection.authenticate()
    test_connection.close()

    global server_password, server_address, RCON_password
    server_address = (str(server_address_in), int(port))
    server_password = str(password)
    RCON_password = str(RCON_password_in)

    config = {
        'discord_api': bot_secret,
        'server_address': server_address_in,
        'server_port': int(port),
        'server_password': server_password,
        'RCON_password': RCON_password
    }

    with open('config.json', 'w') as outfile:
        json.dump(config, outfile, ensure_ascii=False, indent=4)

    ctx.send(f'Successfully connected to {server_address}')


@setup_server.error
async def setup_server_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('Only an administrator can setup the server')
    if isinstance(error, valve.rcon.RCONAuthenticationError) or isinstance(error, commands.CommandInvokeError):
        await ctx.send('RCON authentication failed')
    traceback.print_exc(error)


@bot.command(help='This command sets the channel that will be used for Team 1.', brief='Sets the channel for Team 1')
@commands.has_permissions(administrator=True)
async def setup_team1(ctx):
    global team1_channel
    team1_channel = ctx.author.voice.channel
    ctx.send(f'{team1_channel} is now the channel for Team 1')


@setup_team1.error
async def setup_team1_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('Only an administrator set the team channel')
    traceback.print_exc(error)


@bot.command(help='This command sets the channel that will be used for Team 2.', brief='Sets the channel for Team 2')
@commands.has_permissions(administrator=True)
async def setup_team2(ctx):
    global team2_channel
    team2_channel = ctx.author.voice.channel
    ctx.send(f'{team2_channel} is now the channel for Team 2')


@setup_team2.error
async def setup_team2_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('Only an administrator set the team channel')
    traceback.print_exc(error)


@bot.command(aliases=['10man', 'setup'], help='This command takes the users in a voice channel and selects two random '
                                              'captains. It then allows those captains to select the members of their '
                                              'team in a 1 2 2 2 2 1 fashion. It then configures the server with the '
                                              'correct config.', brief='Helps automate setting up a PUG')
async def pug(ctx):
    global team1_channel, team2_channel
    if not ctx.author.voice or not ctx.author.voice.channel:
        raise commands.UserInputError(message='You must be in a voice channel.')
    if len(ctx.author.voice.channel.members) < 10:
        raise commands.CommandError(message='There must be 10 members connected to the voice channel')
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    # TODO: Add notification for those who don't have their steam account connected
    for member in ctx.author.voice.channel.members:
        cursor.execute('SELECT 1 FROM users WHERE discord_id = ?', (str(member),))
        data = cursor.fetchone()
        if data is None:
            raise commands.UserInputError(message='All users in the voice channel must connect their steam account ')

    # TODO: Refactor this mess
    # TODO: Add a way to cancel
    players = ctx.author.voice.channel.members.copy()
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

    for player in team1:
        player.move_to(channel=team1_channel, reason='you are on team1')
        cursor.execute('SELECT steam_id FROM users WHERE discord_id = ?', (str(player),))
        data = cursor.fetchone()
        team1_steamIDs.append(data[0])

    for player in team2:
        cursor.execute('SELECT steam_id FROM users WHERE discord_id = ?', (str(player),))
        data = cursor.fetchone()
        team2_steamIDs.append(data[0])

    today = date.today()

    match_config = {
        'matchid': f'PUG {today.strftime("%d-%B-%Y")}',
        'num_maps': 1,
        'maplist': active_map_pool,
        'skip_veto': False,
        'veto_first': 'team1',
        'side_type': 'always_knife',
        'players_per_team': len(team2),
        'min_players_to_ready': 1,
        'team1': {
            'name': 'team1',
            'tag': 'team1',
            'flag': 'IE',
            'players': team1_steamIDs
        },
        'team2': {
            'name': 'team2',
            'tag': 'team2',
            'flag': 'IE',
            'players': team2_steamIDs
        }
    }

    with open('match_config.json', 'w') as outfile:
        json.dump(match_config, outfile, ensure_ascii=False, indent=4)

    match_config_json = await ctx.send(file=discord.File('match_config.json', 'match_config.json'))
    await asyncio.sleep(0.3)
    await connect(ctx=ctx)
    await ctx.send('If you are coaching, once you join the server, type .coach')

    print(match_config_json.attachments[0].url)
    changeToGet5 = valve.rcon.execute(server_address, RCON_password, 'exec triggers/get5')
    print(changeToGet5)
    await asyncio.sleep(10)
    executeMatch = valve.rcon.execute(server_address, RCON_password,
                                      f'get5_loadmatch_url "{match_config_json.attachments[0].url}"')
    print(executeMatch)

    if team1_channel is not None and team2_channel is not None:
        for player in team1:
            await player.move_to(channel=team1_channel, reason='you are on team1')

        for player in team2:
            await player.move_to(channel=team2_channel, reason='you are on team2')

    # TODO: when game is over, change the status of the bot


@pug.error
async def pug_error(ctx, error):
    if isinstance(error, commands.UserInputError):
        await ctx.send(error)
    elif isinstance(error, commands.CommandError):
        await ctx.send(error)
    traceback.print_exc(error)


@bot.command(help='This command creates a URL that people can click to connect to the server.',
             brief='Creates a URL people can connect to')
async def connect(ctx):
    # TODO: Change to be some image or attachment with server info
    await ctx.send(f'steam://connect/{server_address[0]}:{server_address[1]}/{server_password}')


@bot.command(help='This command connects users steam account to the bot.', brief='Connect your SteamID to the bot',
             usage='SteamID or CommunityURL')
async def link(ctx, steamID_input):
    steamID = SteamID(steamID_input)
    if not steamID.is_valid():
        steamID = from_url(steamID_input, http_timeout=15)
        if steamID is None:
            steamID = from_url(f'https://steamcommunity.com/id/{steamID_input}/', http_timeout=15)
            if steamID is None:
                raise commands.UserInputError(message='Please enter a valid SteamID or community url.')
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute('''
                    REPLACE INTO users (discord_id, steam_id)
                    VALUES( ?, ? )
                    ''', (str(ctx.author), str(steamID.as_steam2_zero),))
    db.commit()
    cursor.close()


@link.error
async def link_error(ctx, error):
    if isinstance(error, commands.UserInputError):
        await ctx.send(error)
    traceback.print_exc(error)


@bot.command(help='Command to send a test message to the server to verify that RCON is working.',
             brief='Sends a message to the server to test RCON', usage='message')
@commands.has_permissions(administrator=True)
async def RCON_message(ctx, *, message):
    test = valve.rcon.execute(server_address, RCON_password, f'say {message}')
    print(test)


@RCON_message.error
async def RCON_message_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('Only an administrator set the team channel')
    traceback.print_exc(error)


@bot.command(help='This command unbans everyone on the server. Useful fix', brief='Unbans everyone from the server')
@commands.has_permissions(administrator=True)
async def RCON_unban(ctx):
    test = valve.rcon.execute(server_address, RCON_password, 'removeallids')
    print(test)

@RCON_unban.error
async def RCON_unban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('Only an administrator set the team channel')
    traceback.print_exc(error)


@bot.command(hidden=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount)


@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please specify an amount of messages to delete.')
    traceback.print_exc(error)


# TODO: Make bot api key an env variable
bot.run(bot_secret)
