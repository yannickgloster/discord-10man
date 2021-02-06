import json
import os

import bot

startup_extensions = ['utils', 'setup', 'csgo']

config_file = open('config.json')
config = json.load(config_file)
config_file.close()

config_properties = ['discord_token', 'bot_IP', 'bot_port', 'steam_web_API_key', 'server_address', 'server_port',
                     'server_password' 'RCON_password']
for key in config_properties:
    if key not in config:
        config[key] = os.getenv(key.upper())

discord_bot = bot.Discord_10man(config, startup_extensions)
discord_bot.run()
