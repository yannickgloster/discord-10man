const Discord = require("discord.js");
const { Rcon } = require("rcon-client");
const config = require("../../config.json");
const _ = require("lodash");

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

function createPlayerVetoEmbed(team1, playersLeft, team2) {
  const playerVetoEmbed = new Discord.MessageEmbed()
    .setColor("#0099ff")
    .setTitle("Player Veto")
    .setDescription("60 Seconds to pick your players")
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
    const players = new Array(10).fill(message.author.id);
    const pugMessage = await message.channel.send("Loading 10Man");
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

    await pugMessage.edit(createPlayerVetoEmbed(team1, playersLeft, team2));

    // Captains Pick Players
    let currentCaptain = team1[0];
    // For testing
    let captainSwitch = true;
    try {
      while (playersLeft.length > 0) {
        const filter = (reaction, user) => {
          return (
            emojis.includes(reaction.emoji.name) &&
            user.id === currentCaptain.id
          );
        };

        const collected = await pugMessage.awaitReactions(filter, {
          max: 1,
          time: 60000,
          errors: ["time"],
        });

        const selectedPlayer = playersLeft.filter(
          (player) =>
            player.emoji == emojis.indexOf(collected.first().emoji.name)
        );

        playersLeft.splice(playersLeft.indexOf(selectedPlayer[0]), 1);

        if (captainSwitch && currentCaptain === team1[0]) {
          team1.push(selectedPlayer[0]);
          currentCaptain = team2[0];
          // Testing
          captainSwitch = !captainSwitch;
        } else if (currentCaptain === team2[0]) {
          team2.push(selectedPlayer[0]);
          currentCaptain = team1[0];
          // Testing
          captainSwitch = !captainSwitch;
        }
        await collected.first().remove();
        await pugMessage.edit(createPlayerVetoEmbed(team1, playersLeft, team2));
      }
    } catch (e) {
      console.log(e);
    }

    // const rcon = await Rcon.connect({
    //   host: config.servers[0].server_address,
    //   port: config.servers[0].server_port,
    //   password: config.servers[0].RCON_password,
    // });
    // console.log(await rcon.send("say test"));
    // rcon.end();
  },
};
