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
   * @param {string[]} args - Arguments passwed with the message
   */
  async execute(message, args) {
    try {
      let steamID = await parser.get(args.toString());
      let steamID64 = steamID.getSteamID64(true);

      await prisma.user.create({
        data: {
          discordId: Number(message.author.id),
          steamId: Number(steamID64),
        },
      });
      message.reply(`Connected steam account \`${steamID}\``);
    } catch (e) {
      message.reply("Error in SteamID");
    }
  },
};
