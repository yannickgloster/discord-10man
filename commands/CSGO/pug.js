const Discord = require("discord.js");
const { PrismaClient } = require("@prisma/client");
const { Rcon } = require("rcon-client");
const config = require("../../config.json");
const _ = require("lodash");

const prisma = new PrismaClient();

const emojis = [
  "0️⃣",
  "1️⃣",
  "2️⃣",
  "3️⃣",
  "4️⃣",
  "5️⃣",
  "6️⃣",
  "7️⃣",
  "8️⃣",
  "9️⃣",
  "🔟",
  "👑",
];

const matchSize = 4;

function createPlayerVetoEmbed(
  team1,
  playersLeft,
  team2,
  currentCaptain,
  numToSelect
) {
  const playerVetoEmbed = new Discord.MessageEmbed()
    .setColor("#0099ff")
    .setTitle("Player Veto")
    .setDescription(
      `<@${currentCaptain.id}>, 60 Seconds to pick ${numToSelect} player${
        numToSelect > 1 ? "s" : ""
      }`
    )
    .setTimestamp()
    .setFooter("Built by Yannick & Lexes");

  playerVetoEmbed.addFields({
    name: "Team 1",
    value: team1.map(
      (player, index) => `<@${player.id}>${index == 0 ? " 👑" : ""}`
    ),
    inline: true,
  });

  if (playersLeft.length > 0) {
    playerVetoEmbed.addFields({
      name: "Players",
      value: playersLeft.map(
        (player) => `${emojis[player.emoji]} <@${player.id}>`
      ),
      inline: true,
    });
  }

  playerVetoEmbed.addFields({
    name: "Team 2",
    value: team2.map(
      (player, index) => `<@${player.id}>${index == 0 ? " 👑" : ""}`
    ),
    inline: true,
  });
  return playerVetoEmbed;
}

module.exports = {
  name: "pug",
  description: "CSGO Pug",
  async execute(message) {
    // For testing
    const players = new Array(matchSize).fill(message.author.id);

    const vetoFormat = [];
    if (matchSize == 2) {
      vetoFormat.push(1);
      vetoFormat.push(1);
    } else {
      let i;
      for (i = 0; i < matchSize - 2; i++) {
        if (i == 0 || i == matchSize - 3) {
          vetoFormat.push(1);
        } else if (i % 2 == 0) {
          vetoFormat.push(2);
        }
      }
    }

    const pugMessage = await message.channel.send(`Loading ${matchSize}Man`);
    await Promise.all(
      players.map(
        (player, index) =>
          index < players.length - 2 && pugMessage.react(emojis[index])
      )
    );

    // Check that there are 10 people in voice channel

    // Picking captains
    let captainPick = [...players];
    let team1 = [
      {
        id: _.sample(captainPick, 1),
        emoji: 11,
      },
    ];
    captainPick.splice(
      captainPick.findIndex((player) => player === team1[0]),
      1
    );
    let team2 = [
      {
        id: _.sample(captainPick, 1),
        emoji: 11,
      },
    ];
    captainPick.splice(
      captainPick.findIndex((player) => player === team2[0]),
      1
    );
    let playersLeft = captainPick.map((player, index) => ({
      id: player,
      emoji: index,
    }));

    // Captains Pick Players
    let currentCaptain = team1[0];

    let vetoStage = 0;
    let numSelectedPlayers = 0;

    await pugMessage.edit(
      createPlayerVetoEmbed(
        team1,
        playersLeft,
        team2,
        currentCaptain,
        vetoFormat[vetoStage]
      )
    );

    // For Testing
    let captainSwitch = true;
    try {
      while (playersLeft.length > 0) {
        const filter = (reaction, user) => {
          return (
            emojis.includes(reaction.emoji.name) &&
            user.id === currentCaptain.id
          );
        };

        let selectedPlayer = [_.sample(playersLeft, 1)];

        try {
          const collected = await pugMessage.awaitReactions(filter, {
            max: 1,
            time: 60000,
            errors: ["time"],
          });

          selectedPlayer = playersLeft.filter(
            (player) =>
              player.emoji == emojis.indexOf(collected.first().emoji.name)
          );
        } catch (e) {
          console.log("Player did not select in time");
        }

        playersLeft.splice(playersLeft.indexOf(selectedPlayer[0]), 1);

        numSelectedPlayers = numSelectedPlayers + 1;

        if (captainSwitch && currentCaptain === team1[0]) {
          team1.push(selectedPlayer[0]);
        } else if (currentCaptain === team2[0]) {
          team2.push(selectedPlayer[0]);
        }

        if (numSelectedPlayers == vetoFormat[vetoStage]) {
          if (captainSwitch && currentCaptain === team1[0]) {
            currentCaptain = team2[0];
            // Testing
            captainSwitch = !captainSwitch;
          } else if (currentCaptain === team2[0]) {
            currentCaptain = team1[0];
            // Testing
            captainSwitch = !captainSwitch;
          }

          numSelectedPlayers = 0;
          vetoStage = vetoStage + 1;
        }

        await pugMessage.edit(
          createPlayerVetoEmbed(
            team1,
            playersLeft,
            team2,
            currentCaptain,
            vetoFormat[vetoStage]
          )
        );
      }
    } catch (e) {
      console.log(e);
    }

    await pugMessage.reactions.removeAll();

    const team1SteamIds = await Promise.all(
      team1.map(async (player) => {
        const user = await prisma.user.findFirst({
          where: {
            discordId: Number(player.id),
          },
        });
        return user.steamId;
      })
    );

    const team2SteamIds = await Promise.all(
      team2.map(async (player) => {
        const user = await prisma.user.findFirst({
          where: {
            discordId: Number(player.id),
          },
        });
        return user.steamId;
      })
    );

    console.log(team2SteamIds);

    // Find Common Steam Flag

    const match_config = {
      matchid: `PUG_${new Date().toISOString()}`,
      num_maps: 1,
      maplist: [
        "de_inferno",
        "de_train",
        "de_mirage",
        "de_nuke",
        "de_overpass",
        "de_dust2",
        "de_vertigo",
      ],
      skip_veto: true,
      veto_first: "team1",
      side_type: "always_knife",
      players_per_team: Number(matchSize / 2),
      min_players_to_ready: 1,
      spectators: {
        players: [],
      },
      team1: {
        name: escape(`team1`),
        tag: "team1",
        flag: "IE",
        players: team1SteamIds,
      },
      team2: {
        name: escape(`team2`),
        tag: "team2",
        flag: "IE",
        players: team2SteamIds,
      },
      cvars: {
        get5_event_api_url: "http://{bot_ip}:{self.bot.web_server.port}/",
        get5_print_damage: "1",
      },
    };

    // const rcon = await Rcon.connect({
    //   host: config.servers[0].server_address,
    //   port: config.servers[0].server_port,
    //   password: config.servers[0].RCON_password,
    // });
    // console.log(await rcon.send("say test"));
    // rcon.end();
  },
};
