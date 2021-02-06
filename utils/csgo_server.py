import logging
from logging.config import fileConfig
from typing import List

import discord
import valve.rcon
from discord.ext.commands import Context


class CSGOServer:
    def __init__(self, identifier: int, server_address: str, server_port: int, server_password: str,
                 RCON_password: str):
        fileConfig('logging.conf')
        self.logger = logging.getLogger(f'10man.{__name__}')

        self.id: int = identifier
        self.server_address: str = server_address
        self.server_port: int = server_port
        self.server_password: str = server_password
        self.RCON_password: str = RCON_password
        self.available: bool = True
        self.gotv: int = None

        self.logger.debug(f'Created CSGO Server {self.id}')

        self.ctx: Context = None
        self.channels: List[discord.VoiceChannel] = None
        self.players: List[discord.Member] = None
        self.score_message: discord.Message = None
        self.team_names: List[str] = None
        self.team_scores: List[int] = [0, 0]

    def get_context(self, ctx: Context, channels: List[discord.VoiceChannel], players: List[discord.Member],
                    score_message: discord.Message):
        self.ctx = ctx
        self.channels = channels
        self.players = players
        self.score_message = score_message
        self.logger.debug(f'ServerID:{self.id} got context')

    def set_team_names(self, team_names: List[str]):
        self.team_names = team_names
        self.logger.debug(f'ServerID:{self.id} got team_names: {team_names}')

    def update_team_scores(self, team_scores: List[int]):
        self.team_scores = team_scores
        self.logger.debug(f'ServerID:{self.id} got team_names: {team_scores}')

    def make_available(self):
        self.available: bool = True
        self.ctx: Context = None
        self.channels: List[discord.VoiceChannel] = None
        self.players: List[discord.Member] = None
        self.score_message: discord.Message = None
        self.team_names: List[str] = None
        self.team_scores: List[int] = [0, 0]
        self.logger.info(f'ServerID:{self.id} is available')

    def get_gotv(self) -> int:
        if self.gotv is None:
            tv_port: str = valve.rcon.execute((self.server_address, self.server_port), self.RCON_password, 'tv_port')
            self.logger.debug(tv_port)
            try:
                self.gotv = tv_port[CSGOServer.findNthOccur(tv_port, '"', 3) + 1:CSGOServer.findNthOccur(tv_port, '"', 4)]
            except ValueError or valve.rcon.RCONMessageError:
                self.gotv = None

        self.logger.info(f'ServerID={self.id} GoTV={self.gotv}')
        return self.gotv

    @staticmethod
    def findNthOccur(string, ch, N):
        occur = 0

        for i in range(len(string)):
            if string[i] == ch:
                occur += 1

            if occur == N:
                return i

        return -1
