import discord

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

        self.ctx: Context = None
        self.channels: List[discord.VoiceChannel] = None
        self.players: List[discord.Member] = None
        self.score_message: discord.Message = None
        self.team_names: List[str] = None

    def get_context(self, ctx: Context, channels: List[discord.VoiceChannel], players: List[discord.Member],
                    score_message: discord.Message):
        self.ctx = ctx
        self.channels = channels
        self.players = players
        self.score_message = score_message

    def set_team_names(self, team_names: List[str]):
        self.team_names = team_names

    def make_available(self):
        self.available: bool = True
        self.ctx: Context = None
        self.channels: List[discord.VoiceChannel] = None
        self.players: List[discord.Member] = None
        self.score_message: discord.Message = None
        self.team_names: List[str] = None
