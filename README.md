# discord-10man

![GitHub Pipenv locked Python version](https://img.shields.io/github/pipenv/locked/python-version/yannickgloster/discord-10man?style=for-the-badge) ![GitHub](https://img.shields.io/github/license/yannickgloster/discord-10man?style=for-the-badge)

Discord bot for CS:GO Scrims and Pugs

#### config.json example:
```json
{
    "discord_token": "123fkdjsh123alksjfhlaskdjafhlkj1hl3kj4hlkjss",
    "servers": [
        {
            "server_address": "csgo.yannickgloster.com",
            "server_port": 27015,
            "server_password": "pasword1234",
            "RCON_password": "1234password"
        }
    ]
}
```

Perms Integer: 17300560

Using:
- [get5 (CSGO Server Plugin)](https://github.com/splewis/get5)
- [discord.py 1.5.0](https://pypi.org/project/discord.py/)
- [python.valve 0.2.1](https://pypi.org/project/python-valve/)
- [steam 1.0.2](https://steam.readthedocs.io/en/stable/intro.html#)
- [aiohttp[speedups]](https://docs.aiohttp.org/en/stable/index.html#aiohttp-installation)
