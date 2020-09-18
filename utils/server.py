from aiohttp import web
import socket
from json import JSONDecodeError
import discord


def _http_error_handler(error=False) -> web.Response:
    """
    Used to handle HTTP error response.
    Parameters
    ----------
    error : bool, optional
        Bool or string to be used, by default False
    Returns
    -------
    web.Response
        AIOHTTP web server response.
    """

    return web.json_response(
        {"error": error},
        status=400 if error else 200
    )


class WebServer:
    def __init__(self, bot):
        self.bot = bot
        self.ctx = None
        self.channels = None
        self.players = None
        self.score_message = None
        self.team_names = None
        self.IP = socket.gethostbyname(socket.gethostname())
        self.port = 3000

    async def _handler(self, request: web.Request) -> web.Response:
        """
        Super simple HTTP handler.
        Parameters
        ----------
        request : web.Request
            AIOHTTP request object.
        """

        # or "Authorization"
        if request.method != 'POST':
            # Used to decline any requests what doesn't match what our
            # API expects.

            return _http_error_handler("request-type")

        try:
            get5_event = await request.json()
        except JSONDecodeError:
            return _http_error_handler("json-body")

        # TODO: Create Checks for the JSON

        if get5_event['event'] == 'series_start':
            self.team_names = [get5_event['params']['team1_name'], get5_event['params']['team2_name']]

        elif get5_event['event'] == 'round_end':
            score_embed = discord.Embed()
            score_embed.add_field(name=f'{get5_event["params"]["team1_score"]}',
                                  value=f'{self.team_names[0]}', inline=True)
            score_embed.add_field(name=f'{get5_event["params"]["team2_score"]}',
                                  value=f'{self.team_names[1]}', inline=True)
            await self.score_message.edit(embed=score_embed)

        elif get5_event['event'] == 'series_end':
            await self.score_message.edit('Game Over')
            for player in self.players:
                await player.move_to(channel=self.channels[0], reason=f'Game Over')
            await self.channels[1].delete(reason='Game Over')
            await self.channels[2].delete(reason='Game Over')

        return _http_error_handler()

    async def http_start(self) -> None:
        """
        Used to start the webserver inside the same context as the bot.
        """

        server = web.Server(self._handler)
        runner = web.ServerRunner(server)
        await runner.setup()
        site = web.TCPSite(runner, self.IP, self.port)
        await site.start()
        print(f'Webserver Started on {self.IP}:{self.port}')

    def get_context(self, ctx, channels: list, players: list, score_message):
        self.ctx = ctx
        self.channels = channels
        self.players = players
        self.score_message = score_message
