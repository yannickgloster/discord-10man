const dotenv = require("dotenv");
const Discord = require("discord.js");
const fs = require("fs");
const express = require("express");
const path = require("path");

const { prefix } = require("./config.json");
const MapVetoImageFactory = require("./util/mapVeto");

dotenv.config();

const client = new Discord.Client({ restTimeOffset: 250 });
client.commands = new Discord.Collection();
client.cooldowns = new Discord.Collection();

const commandFolders = fs.readdirSync("./commands");

for (const folder of commandFolders) {
  const commandFiles = fs
    .readdirSync(`./commands/${folder}`)
    .filter((file) => file.endsWith(".js"));
  for (const file of commandFiles) {
    const command = require(`./commands/${folder}/${file}`);
    client.commands.set(command.name, command);
  }
}

client.once("ready", () => {
  console.log("Bot ready");
});

client.on("message", (message) => {
  if (!message.content.startsWith(prefix) || message.author.bot) return;

  const args = message.content.slice(prefix.length).trim().split(/ +/);
  const commandName = args.shift().toLowerCase();

  const command =
    client.commands.get(commandName) ||
    client.commands.find(
      (cmd) => cmd.aliases && cmd.aliases.includes(commandName)
    );

  if (!command) return;

  if (command.guildOnly && message.channel.type === "dm") {
    return message.reply("I can't execute that command inside DMs!");
  }

  if (command.permissions) {
    const authorPerms = message.channel.permissionsFor(message.author);
    if (!authorPerms || !authorPerms.has(command.permissions)) {
      return message.reply("You can not do this!");
    }
  }

  if (command.args && !args.length) {
    let reply = `You didn't provide any arguments, ${message.author}!`;

    if (command.usage) {
      reply += `\nThe proper usage would be: \`${prefix}${command.name} ${command.usage}\``;
    }

    return message.channel.send(reply);
  }

  const { cooldowns } = client;

  if (!cooldowns.has(command.name)) {
    cooldowns.set(command.name, new Discord.Collection());
  }

  const now = Date.now();
  const timestamps = cooldowns.get(command.name);
  const cooldownAmount = (command.cooldown || 3) * 1000;

  if (timestamps.has(message.author.id)) {
    const expirationTime = timestamps.get(message.author.id) + cooldownAmount;

    if (now < expirationTime) {
      const timeLeft = (expirationTime - now) / 1000;
      return message.reply(
        `please wait ${timeLeft.toFixed(
          1
        )} more second(s) before reusing the \`${command.name}\` command.`
      );
    }
  }

  timestamps.set(message.author.id, now);
  setTimeout(() => timestamps.delete(message.author.id), cooldownAmount);

  try {
    command.execute(message, args);
  } catch (error) {
    console.error(error);
    message.reply("there was an error trying to execute that command!");
  }
});

const app = express();

app.get("/", function (req, res) {
  res.send("Hello World");
});

app.post("/", function (req, res) {
  // match updates indiscord
  console.log(req.body);
  res.end();
});

app.get("/match", function (req, res) {
  res.set("Content-Type", "application/json");
  try {
    const data = fs.readFileSync("./matches/" + req.query.id + ".json", "utf8");
    res.send(data);
  } catch (e) {
    res.send({ error: e });
  }
});

app.listen(3000, () => {
  console.log("Webserver ready");
});

client.login(process.env.TOKEN);

const mapVetoFactory = new MapVetoImageFactory(
  path.join(__dirname, "images/map_images"),
  path.join(__dirname, "images/cross_mark.png"),
  path.join(__dirname, "images/map_veto_assets")
);
mapVetoFactory.initialiseAssets();
