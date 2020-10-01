import bot
import json

startup_extensions = ['utils', 'setup', 'csgo']

config_file = open('config.json')
config = json.load(config_file)
config_file.close()

discord_bot = bot.Discord_10man(config, startup_extensions)
discord_bot.run()
