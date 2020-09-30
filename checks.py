from databases import Database
from discord.ext import commands

async def voice_channel(ctx):
    if ctx.author.voice is None:
        raise commands.CommandError(message='You must be in a voice channel.')
    return True


async def ten_players(ctx):
    if ctx.author.voice is not None and (len(ctx.author.voice.channel.members) < 10 and not ctx.bot.dev):
        raise commands.CommandError(message='There must be 10 members connected to the voice channel')
    return True


async def linked_accounts(ctx):
    if ctx.author.voice is not None:
        db = Database('sqlite:///main.sqlite')
        await db.connect()
        not_connected_members = []
        for member in ctx.author.voice.channel.members:
            data = await db.fetch_one('SELECT 1 FROM users WHERE discord_id = :member', {"member": str(member)})
            if data is None:
                not_connected_members.append(member)
        if len(not_connected_members) > 0:
            error_message = ''
            for member in not_connected_members:
                error_message += f'<@{member.id}> '
            error_message += f'must connect their steam account with the command ```{ctx.bot.command_prefix}link <Steam Profile URL>```'
            raise commands.CommandError(message=error_message)
    return True
