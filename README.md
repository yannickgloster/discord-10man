# Discord 10man Bot

![GitHub Pipenv locked Python version](https://img.shields.io/github/pipenv/locked/python-version/yannickgloster/discord-10man?style=for-the-badge) ![GitHub](https://img.shields.io/github/license/yannickgloster/discord-10man?style=for-the-badge)

Do you have a csgo server and want to organize PUGs with your friends in discord? This bot allows for a command driven or queue driven pick up game system. Essentially your own personal popflash, built right into your discord server.

## Go to the [Wiki](https://github.com/yannickgloster/discord-10man/wiki) for Setup and Usage Instructions

## Features
- Command Based PUG
- Queue Based PUG w/ Ready Up
- Multiple Servers
- Random Captains
- Player Veto
- Map Veto
- Auto Voice Channel Creation for Teams
- Channel Deletion After Game
- Score Updates in Text Channel
- [Get5 Features](https://github.com/splewis/get5#get5)
- Match Statistics Collection ***COMING SOON***
- [Dathost](https://dathost.net/) Support ***COMING SOON***

### Requirements:
- A CSGO Server
- [Get5](https://github.com/splewis/get5)
- [Get5 Event API](https://github.com/yannickgloster/get5_eventapi)

## Commands
#### User Commands
- `.pug`: Starts a pug with the members of a voice channel. There must be 10 members in the voice channel and each member must have used the `.link` command.
- `.link <Steam Community URL or Steam ID>`: Connects a users steam account to the bot. Must have done before running a `.pug`.
- `.connect`: Shows the server connect message.
-  `.matches`: Shows the live matches and their scores.

#### Admin Commands
- `.setup_queue <True | False>`: Enables or disables the queue.
- `.map_pool <list of map names>`: Updates the map pool to the list of maps provided. **Untested.**
    - *Example:* `.map_pool de_dust2 de_mirage de_vertigo`: Sets the map pool to Dust2, Mirage, and Vertigo.
- `.RCON_message <message>`: Sends the RCON command, `say <message` to the CSGO Server to test if RCON works.
- `.RCON_unban`: Unbans all users from the server.
