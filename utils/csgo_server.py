class CSGOServer:
    def __init__(self, identifier: int, server_address: str, server_port: int, server_password: str, RCON_password: str):
        self.id = identifier
        self.server_address: str = server_address
        self.server_port: int = server_port
        self.server_password: str = server_password
        self.RCON_password: str = RCON_password
        self.available: bool = True

        self.ctx = None
        self.channels = None
        self.players = None
        self.score_message = None
        self.team_names = None

    def get_context(self, ctx, channels: list, players: list, score_message):
        self.ctx = ctx
        self.channels = channels
        self.players = players
        self.score_message = score_message

    def set_team_names(self, team_names: list):
        self.team_names = team_names

    def make_available(self):
        self.available: bool = True
        self.ctx = None
        self.channels = None
        self.players = None
        self.score_message = None
        self.team_names = None
