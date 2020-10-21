import aiohttp
import discord
import checks
import traceback

from bot import Discord_10man
from discord.ext import commands, tasks


class Utils(commands.Cog):
    def __init__(self, bot: Discord_10man):
        self.bot: Discord_10man = bot
        self.check_update.start()

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def load(self, ctx: commands.Context, extension: str):
        extension = f'cogs.{extension}'
        msg = await ctx.send(f'Loading {extension}')
        ctx.bot.load_extension(f'{extension}')
        await msg.edit(content=f'Loaded {extension}')

    @load.error
    async def load_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, ImportError) or isinstance(error, commands.ExtensionNotFound) \
                or isinstance(error, commands.CommandInvokeError):
            await ctx.send(':warning: Extension does not exist.')
        else:
            await ctx.send(str(error))
        traceback.print_exc()

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def unload(self, ctx: commands.Context, extension: str):
        if extension not in ctx.bot.cogs.keys():
            raise commands.CommandError(':warning: Module does not exist.')
        extension = f'cogs.{extension}'
        msg = await ctx.send(f'Loading {extension}')
        ctx.bot.unload_extension(f'{extension}')
        await msg.edit(content=f'Unloaded {extension}')

    @unload.error
    async def unload_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandError):
            await ctx.send(str(error))
        traceback.print_exc()

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx: commands.Context, amount: int):
        await ctx.channel.purge(limit=amount)

    @clear.error
    async def clear_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify an amount of messages to delete')
        traceback.print_exc()

    @tasks.loop(hours=24)
    async def check_update(self):
        session = aiohttp.ClientSession()
        async with session.get('https://api.github.com/repos/yannickgloster/discord-10man/releases/latest') as resp:
            json = await resp.json()
            if self.bot.version < json['tag_name'][1:]:
                embed = discord.Embed(title=f'Discord 10man Update {json["tag_name"]}', url=json["html_url"])
                embed.set_thumbnail(
                    url="https://repository-images.githubusercontent.com/286741783/1df5e700-e141-11ea-9fbc-338769809f24")
                embed.add_field(name='Release Notes', value=f'{json["body"]}', inline=False)
                embed.add_field(name='Download', value=f'{json["html_url"]}', inline=False)
                owner: discord.Member = (await self.bot.application_info()).owner
                await owner.send(embed=embed)
        await session.close()

    @commands.command(aliases=['version'], help='This command gets the bot information and version')
    async def about(self, ctx: commands.Context):
        embed = discord.Embed(color=0xff0000)
        embed.add_field(name=f'Discord 10 Man Bot v{self.bot.version}',
                        value=f'Built by <@125033487051915264> & <@282670937738969088>', inline=False)
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Utils(client))
