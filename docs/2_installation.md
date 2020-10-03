# Download & Installation

## CSGO Server & Requirements
- [CSGO Server](https://developer.valvesoftware.com/wiki/Counter-Strike:_Global_Offensive_Dedicated_Servers)
- [Metamod](http://www.metamodsource.net/downloads.php)
- [Sourcemod](http://www.sourcemod.net/downloads.php)
- [Get5](https://github.com/splewis/get5)
- [Get5 Event API](https://github.com/yannickgloster/get5_eventapi)

#### Linux
On Linux I would recommend using [LGSM(Linux Game Server Managers)](https://linuxgsm.com/) to facilitate setting up the server:
https://linuxgsm.com/lgsm/csgoserver/.

Once you have your server setup with LGSM, you can run `./csgoserver mi` and select `Metamod` and then you can run `./csgoserver mi` and select `Sourcemod`.

#### Windows & MacOS & Linux
Follow the instructions here to get your server setup:
https://developer.valvesoftware.com/wiki/Counter-Strike:_Global_Offensive_Dedicated_Servers

Once the server is setup, install the latest version of [Metamod](http://www.metamodsource.net/downloads.php) and [Sourcemod](http://www.sourcemod.net/downloads.php) on the server:
http://www.metamodsource.net/downloads.php

http://www.sourcemod.net/downloads.php

#### [Get5](https://github.com/splewis/get5)
The Discord bot requires the latest release of [Get5](https://github.com/splewis/get5) to be installed.
Download the [latest release](http://ci.splewis.net/job/get5/lastSuccessfulBuild/). 
Extract the download archive into the `csgo/` directory on the server.
Once the plugin first loads on the server, you can edit general get5 cvars in the autogenerated `cfg/sourcemod/get5.cfg`.
All the CVARS can be found on the [Get5 Github](https://github.com/splewis/get5/wiki/Full-list-of-get5-cvars).

I would recommend changing the following CVARs:
```
get5_kick_when_no_match_loaded "0"
```

A full installation guide and documentation on the [Get5 Github](https://github.com/splewis/get5#download-and-installation).

#### [Get5 Event API](https://github.com/yannickgloster/get5_eventapi)
Go to the [releases section](https://github.com/yannickgloster/get5_eventapi/releases) of the Github and download the latest `get5_eventapi.smx`.
Copy that file to `csgo/addons/sourcemod/plugins` on your CSGO Server.

## Discord Bot Setup
1) Connecting the Bot to your Server
    1) Head over to the [Discord Developer Portal](https://discord.com/developers/applications) and log in with your Discord account
        
        ![New Application](https://raw.githubusercontent.com/yannickgloster/discord-10man/docs/docs/img/new_application.png)
        
    2) Name it `Discord 10man` and click create
        - You can add an icon afterward and a description to personalize the bot
    3) On the menu on the left hand side, select `bot`
        
        ![Select Bot](https://raw.githubusercontent.com/yannickgloster/discord-10man/docs/docs/img/select_bot.png)
        
    4) Then click on `add bot` on the right
        
        ![Add Bot](https://raw.githubusercontent.com/yannickgloster/discord-10man/docs/docs/img/add_bot.png)
        
    5) Under `token`, click on `copy`.
       This is your secret discord bot token, save it somewhere because we will need it for the `config.json` file.
       *Don't give this to anyone else because then they can take control of your bot.*
       
       ![Discord Token](https://raw.githubusercontent.com/yannickgloster/discord-10man/docs/docs/img/token.png)
       
    6) Scroll down to `SERVER MEMBER INTENT` and toggle it on
       
       ![Server Member Intent](https://raw.githubusercontent.com/yannickgloster/discord-10man/docs/docs/img/intent.png)
       
    7) Click on `Save Changes`
    8) For those familiar with Discord bots, the Perms Integer is `17300560`
    9) Click on `0Auth2` on the menu on the left hand side
       
       ![0Auth2](https://raw.githubusercontent.com/yannickgloster/discord-10man/docs/docs/img/auth2.png)
       
    10) Under `SCOPES` select `bot`
        
        ![Scopes](https://raw.githubusercontent.com/yannickgloster/discord-10man/docs/docs/img/scopes.png)
        
    11) Scroll down to `BOT PERMISSIONS` and select the following:
        - Image
        - Under `GENERAL PERMISSIONS`
            - `Manage Channels`
            - `View Channels`
        - Under `TEXT PERMISSIONS`
            - `Send Messages`
            - `Send TTS Messages`
            - `Manage Messages`
            - `Embed Links`
            - `Attach Files`
            - `Read Message History`
            - `Message Everyone`
            - `Use External Emojis`
            - `Add Reactions`
        - Under `Voice Permissions`
            - `Move Members`
    12) Under `SCOPES`, copy the URL by pressing copy
        
        ![Scopes Copy](https://raw.githubusercontent.com/yannickgloster/discord-10man/docs/docs/img/scopes_copy.png)
        
    13) Paste the link into a new tab in your browser
    14) Select the server you want to add it to!
    15) Now the bot is connected to the server, lets get the bot up and running!
2) Install Python & Python Requirements
    1) Install the latest version of [Python](https://www.python.org/downloads/)
    2) Check that python installed correctly by opening a terminal (Command Prompt on Windows), and running the command `python --version`
        - It should return `Python 3.8.3` (or a greater version number)
    3) Install [Pipenv](https://pipenv.pypa.io/en/latest/) by following these [instructions](https://pipenv.pypa.io/en/latest/install/#installing-pipenv):
        - [https://pipenv.pypa.io/en/latest/install/#installing-pipenv](https://pipenv.pypa.io/en/latest/install/#installing-pipenv)
    4) Verify that Pipenv is installed by opening a terminal (Command Prompt on Windows) and running `pipenv --version`
        - It should return `pipenv, version 2020.8.13` (or a greater version number)
3) Setting Up & Running the Bot
    1) Download the latest release from the [releases tab](https://github.com/yannickgloster/discord-10man/releases) or download the latest development build by click on `code` on the github homepage and then clicking on `Download ZIP` 
    2) Unzip the files
    3) Rename `config_example.json` to `config.json`
    4) Open the file and edit the information:
        - Replace the `discord_token` with the token we got from your bot in Section 1) subsection v.
        - Leave `bot_IP` blank for the time being
        - Fill in your server information
        - If you have multiple servers, the json file might look something like this:
        
        ```json
        {
            "discord_token": "123fkdjsh123alksjfhlaskdjafhlkj1hl3kj4hlkjss",
            "servers": [
                {
                    "server_address": "csgo.yannickgloster.com",
                    "server_port": 27015,
                    "server_password": "pasword1234",
                    "RCON_password": "1234password"
                },
                {
                    "server_address": "123.123.123.123",
                    "server_port": 27015,
                    "server_password": "pasword1234",
                    "RCON_password": "1234password"
                }
            ]
        }
        ```
    5) Open a terminal (Command Prompt on Windows) and go to the folder where the bot is
    6) Install the requirements by running `pipenv install`
    7) Run the bot by running `pipenv run python3 run.py`
    8) Go into the discord and send `.about` into a text channel
        - It should return an embed with the version number
        - Alternatively, run the command `.connect` and it should display an embed with the information on the server. If this doesn't work, the `config.json` file was not configured properly.
    9) To run the bot permanently, you can use [`tmux`](https://www.howtogeek.com/671422/how-to-use-tmux-on-linux-and-why-its-better-than-screen/) on Linux.
        - Example `tmux` command
            - `tmux new-session -d -s discord 'pipenv run python3 run.py'`
            - This creates a new session called Discord
        - There are other cheap hosting alternatives if you don't want to run your PC permanently or don't have a server. The DiscordPY community recommends the following:
        
        ```
        Need to run your bot 24/7? Get a cheap VPS.
        https://www.scaleway.com/     EU            https://www.linode.com/ US/EU/Asia
        https://www.digitalocean.com/ US            https://www.vultr.com/ US
        https://www.ovh.co.uk/        EU/Canada     https://www.hetzner.com/ Germany
        https://www.time4vps.eu/      Lithuania.
        Self-hosting:       Free hosting:                 Kinda free:
        Any computer.    No. Not even heroku.   GCP, AWS have one year free micros.
       ```
    10) If you are self hosting, on a different service, or not on the same server as the csgo server, you will have to portforward `port 3000`
        - If you google the following, you will find a tutorial on how to do so:
        > How do I portforward [INSERT ROUTER NAME/SERVICE NAME]
        - If you portfoward, you will need to edit `config.json`. Open it in a text editor
        - For `bot_IP` put in your public IP
            - [What is my IP](http://letmegooglethat.com/?q=what+is+my+ip)