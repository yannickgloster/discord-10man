import logging
from logging.config import fileConfig

import aiohttp
import discord
from discord.ext import commands, tasks

from bot import Discord_10man


class Utils(commands.Cog):
    def __init__(self, bot: Discord_10man):
        fileConfig('logging.conf')
        self.logger = logging.getLogger(f'10man.{__name__}')
        self.logger.debug(f'Loaded {__name__}')

        self.bot: Discord_10man = bot
        self.check_update.start()

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def load(self, ctx: commands.Context, extension: str):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        extension = f'cogs.{extension}'
        msg = await ctx.send(f'Loading {extension}')
        ctx.bot.load_extension(f'{extension}')
        await msg.edit(content=f'Loaded {extension}')
        self.logger.debug(f'Loaded {extension} via command')

    @load.error
    async def load_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, ImportError) or isinstance(error, commands.ExtensionNotFound) \
                or isinstance(error, commands.CommandInvokeError):
            await ctx.send(':warning: Extension does not exist.')
            self.logger.warning('Extension does not exist')
        else:
            await ctx.send(str(error))
            self.logger.exception('load command exception')

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def unload(self, ctx: commands.Context, extension: str):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        if extension not in ctx.bot.cogs.keys():
            raise commands.CommandError(':warning: Extension does not exist.')
        extension = f'cogs.{extension}'
        msg = await ctx.send(f'Loading {extension}')
        ctx.bot.unload_extension(f'{extension}')
        await msg.edit(content=f'Unloaded {extension}')
        self.logger.debug(f'Unloaded {extension} via command')

    @unload.error
    async def unload_error(self, ctx: commands.Context, error):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        if isinstance(error, commands.CommandError):
            await ctx.send(str(error))
            self.logger.warning('Extension does not exist')
        self.logger.exception('unload command exception')

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx: commands.Context, amount: int):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        await ctx.channel.purge(limit=amount)
        self.logger.debug(f'Purged {amount} in {ctx.channel}')

    @clear.error
    async def clear_error(self, ctx: commands.Context, error):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify an amount of messages to delete')
            self.logger.warning(f'{ctx.author} did not specify number of messages to delete.')
        self.logger.exception('clear command exception')

    @tasks.loop(hours=24)
    async def check_update(self):
        self.logger.info('Checking for update.')
        session = aiohttp.ClientSession()
        async with session.get('https://api.github.com/repos/yannickgloster/discord-10man/releases/latest') as resp:
            json = await resp.json()
            if self.bot.version < json['tag_name'][1:]:
                self.bot.logger.info(f'{self.bot.version} bot is out of date, please update to {json["tag_name"]}')
                embed = discord.Embed(title=f'Discord 10man Update {json["tag_name"]}', url=json["html_url"])
                embed.set_thumbnail(
                    url="https://repository-images.githubusercontent.com/286741783/1df5e700-e141-11ea-9fbc-338769809f24")
                embed.add_field(name='Release Notes', value=f'{json["body"]}', inline=False)
                embed.add_field(name='Download', value=f'{json["html_url"]}', inline=False)
                owner: discord.Member = (await self.bot.application_info()).owner
                await owner.send(embed=embed)
        await session.close()

    @commands.command(aliases=['version', 'v', 'a'], help='This command gets the bot information and version')
    async def about(self, ctx: commands.Context):
        self.logger.debug(f'{ctx.author}: {ctx.prefix}{ctx.invoked_with} {ctx.args[2:]}')
        embed = discord.Embed(color=0xff0000)
        embed.add_field(name=f'Discord 10 Man Bot v{self.bot.version}',
                        value=f'Built by <@125033487051915264> & <@282670937738969088>', inline=False)
        await ctx.send(embed=embed)
        self.logger.debug(f'{ctx.author} got bot about info.')


def setup(client):
    client.add_cog(Utils(client))
