from databases import Database
from discord.ext import commands


async def voice_channel(ctx: commands.Context):
    if ctx.author.voice is None:
        raise commands.CommandError(message='You must be in a voice channel.')
    return True


async def ten_players(ctx: commands.Context):
    if ctx.author.voice is not None and (len(ctx.author.voice.channel.members) < ctx.bot.match_size and not ctx.bot.dev):
        raise commands.CommandError(message='There must be 10 members connected to the voice channel')
    return True


async def linked_accounts(ctx: commands.Context):
    if ctx.author.voice is not None:
        db = Database('sqlite:///main.sqlite')
        await db.connect()
        not_connected_members = []
        for member in ctx.author.voice.channel.members:
            data = await db.fetch_one('SELECT 1 FROM users WHERE discord_id = :member', {"member": str(member.id)})
            if data is None:
                not_connected_members.append(member)
        if len(not_connected_members) > 0:
            error_message = ''
            for member in not_connected_members:
                error_message += f'<@{member.id}> '
            error_message += f'must connect their steam account with the command ```{ctx.bot.command_prefix}link <Steam Profile URL>```'
            raise commands.CommandError(message=error_message)
    return True


async def available_server(ctx: commands.Context):
    available: bool = False
    for server in ctx.bot.servers:
        if server.available:
            available = True
            break
    if not available:
        raise commands.CommandError(message='There are no servers available')
    return True


async def active_game(ctx: commands.Context):
    active: bool = False
    for server in ctx.bot.servers:
        if not server.available:
            active = False
            break
    if not active:
        raise commands.CommandError(message='There are no live matches')
    return True


async def queue_running(ctx: commands.Context):
    if not ctx.bot.cogs['CSGO'].queue_check.is_running():
        raise commands.CommandError(message='Queue not running.')
    return True
