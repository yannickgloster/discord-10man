const Discord = require("discord.js");
const { PrismaClient } = require("@prisma/client");
const Parser = require("steamid-parser");
const parser = new Parser(process.env.STEAM_API_KEY || "YOUR_API_KEY", {
  // Options object are set by default to these values
  checkForAccountID: false,
  checkNumberForVanity: true,
});

const prisma = new PrismaClient();

module.exports = {
  name: "link",
  description: "Link steam account to bot",
  args: true,
  /**
   * @param {Discord.Message} message - Discord Message that triggered the command
   * @param {string[]} args - Arguments passed with the message
   */
  async execute(message, args) {
    try {
      let steamID = await parser.get(args.toString());
      let steamID64 = steamID.getSteamID64(true);

      await prisma.user.upsert({
        where: {
          discordId_steamId: {
            discordId: Number(message.author.id),
            steamId: Number(steamID64),
          },
        },
        update: {
          steamId: Number(steamID64),
        },
        create: {
          discordId: Number(message.author.id),
          steamId: Number(steamID64),
        },
      });

      const linkedEmbed = new Discord.MessageEmbed()
        .setColor("#0099ff")
        .setTitle(`${message.author.username} linked`)
        .setURL(`https://steamcommunity.com/profiles/${steamID64}`)
        .setTimestamp()
        .setFooter(
          `${message.author.username}`,
          message.author.avatarURL({ format: "jpg" })
        );

      message.reply(linkedEmbed);
    } catch (e) {
      message.reply("Error in SteamID");
    }
  },
};
