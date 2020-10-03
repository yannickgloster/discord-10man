# Usage and Commands
**IMPORTANT FOR BOTH SYSTEMS**
Every user that joins the channel must send the message `.link <STEAM COMMUNITY URL or STEAM ID>` to link their steam account to the bot.

### Command Based System

Get ten people in a voice channel and type `.pug` into a text channel. The team veto process will begin.
Once teams are selected, the team channels will auto be created and people will automatically be moved. 
The map veto process will then begin. Once both of these steps are completed, the server will be automatically configured.
The users can now click the server link and start the PUG.
The score will update in Discord after every round.
Once the game is over, everyone will be moved back into the original voice channel and the team voice channels will be deleted.

### Queue System
*An admin in the Discord server must set this up.*

Create a voice channel you wish to use as the queue. Join the voice channel and then in your text channel, send the message `.setup_queue True`
This will set the voice channel to be the queue and the text channel to be where the veto process takes place.
This will also disable the `.pug` command. Once 10 people join the queue, they will be asked to ready up.
Once everyone readies up, the team veto will be begin. Once teams are selected, the team channels will auto be created and people will automatically be moved. 
The map veto process will then begin. Once both of these steps are completed, the server will be automatically configured.
The users can now click the server link and start the PUG.
The score will update in Discord after every round.
Once the game is over the team channels will be deleted but users will not be put back into the queue.

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