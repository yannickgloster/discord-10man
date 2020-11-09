# Discord 10man Bot

![GitHub Pipenv locked Python version](https://img.shields.io/github/pipenv/locked/python-version/yannickgloster/discord-10man?style=for-the-badge) ![GitHub](https://img.shields.io/github/license/yannickgloster/discord-10man?color=orange&style=for-the-badge) ![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/yannickgloster/discord-10man?color=green&style=for-the-badge) [![Discord](https://img.shields.io/discord/762204302348517377?color=blue&style=for-the-badge)](https://discord.gg/aZfjp6V)

Do you have a csgo server and want to organize PUGs with your friends in discord? This bot allows for a command driven or queue driven pick up game system. Essentially your own personal popflash, built right into your discord server.

## Go to the [Wiki](https://github.com/yannickgloster/discord-10man/wiki) for Setup and Usage Instructions

## Features
- Command Based PUG
- Queue Based PUG w/ Ready Up
- Multiple Servers
- Random Captains
- Selected Captains
- Player Veto
- Map Veto
- Selected Map
- Auto Voice Channel Creation for Teams
- Channel Deletion After Game
- Score Updates in Text Channel
- Auto Server Configuration
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
    - `.pug` has a series of optional arguments. You can use as many of the optional arguments together as you'd like:
      - `.pug @user`: sets the user as a team captain
      - `.pug <map_name>`: sets the map
      - `.pug random`: randomizes the teams
    - Examples:
      - `.pug @retsol @lexes`: will set retsol and lexes as team captains
      - `.pug random`: a pug with a map veto but random teams
      - `.pug de_dust2`: a pug on de_dust2 with a player veto 
      - `.pug random de_dust2`: a pug with random teams on de_dust2
      - `.pug de_dust2 random`: a pug with random teams on de_dust2
- `.link <Steam Community URL or Steam ID>`: Connects a users steam account to the bot. Must have done before running a `.pug`.
- `.connect ?<server id>`: Shows the server connect message. Optional server id if there are more than 1 servers.
- `.matches`: Shows the live matches and their scores.
- `.about`: Get's the bot's version number

#### Admin Commands
- `.setup_match_size`: Set's the number of players in a match. The default value is 10. It also changes the queue size if enabled.
- `.connect_dm <True | False>`: If set to true, instead of posting the ip to your csgo server in the general message, it sends the user a DM.
- `.add_spectator @user`: Adds the tagged users as spectators in the server.
- `.remove_spectator @user`: Removes the tagged users as spectators in the server.
- `.setup_queue <True | False>`: Enables or disables the queue.
- `.set_queue_captain @user`: Adds the tagged users as captains in the queue. Once they are a captain, they won't be a captain again unless you specify it with this command
- `.empty_queue`: Kicks all voice members from the queue.
- `.force_restart_queue`: Restarts the queue task.
- `.force_end ?<server id>`: force ends a match on a server. Defaults to the first server if you don't provide a server ID.
- `.map_pool <list of map names>`: Updates the map pool to the list of maps provided. **Untested.**
    - *Example:* `.map_pool de_dust2 de_mirage de_vertigo`: Sets the map pool to Dust2, Mirage, and Vertigo.
- `.RCON_message <message>`: Sends the RCON command, `say <message` to the CSGO Server to test if RCON works.
- `.RCON_unban`: Unbans all users from the server.
