from aiohttp import web
import socket
from json import JSONDecodeError


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

        if request.path == '/match/0/finish':
            for player in self.players:
                await player.move_to(channel=self.channels[0], reason=f'Game Over')
            await self.channels[1].delete(reason='Game Over')
            await self.channels[2].delete(reason='Game Over')

            text_response = await request.text()
            text_split = text_response.split('&')
            for s in text_split:
                s_split = s.split('=')
                if s_split[0] == 'winner':
                    await self.ctx.send(f'{s_split[1]} wins!')
                    break

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

    def get_context(self, ctx, channels:list, players:list):
        self.ctx = ctx
        self.channels = channels
        self.players = players
