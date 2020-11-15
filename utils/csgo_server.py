import discord
import valve.rcon

from discord.ext.commands import Context
from typing import List


class CSGOServer:
    def __init__(self, identifier: int, server_address: str, server_port: int, server_password: str,
                 RCON_password: str):
        self.id: int = identifier
        self.server_address: str = server_address
        self.server_port: int = server_port
        self.server_password: str = server_password
        self.RCON_password: str = RCON_password
        self.available: bool = True
        self.gotv: int = None

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

    def set_team_names(self, team_names: List[str]):
        self.team_names = team_names

    def update_team_scores(self, team_scores: List[int]):
        self.team_scores = team_scores

    def make_available(self):
        self.available: bool = True
        self.ctx: Context = None
        self.channels: List[discord.VoiceChannel] = None
        self.players: List[discord.Member] = None
        self.score_message: discord.Message = None
        self.team_names: List[str] = None
        self.team_scores: List[int] = [0, 0]

    def get_gotv(self) -> int:
        if self.gotv is None:
            tv_port: str = valve.rcon.execute((self.server_address, self.server_port), self.RCON_password, 'tv_port')
            try:
                self.gotv = tv_port[findNthOccur(tv_port, '"', 3) + 1:findNthOccur(tv_port, '"', 4)]
            except ValueError or valve.rcon.RCONMessageError:
                self.gotv = None
        return self.gotv


def findNthOccur(string, ch, N):
    occur = 0

    for i in range(len(string)):
        if string[i] == ch:
            occur += 1

        if occur == N:
            return i

    return -1