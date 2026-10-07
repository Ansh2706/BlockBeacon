# Minecraft Server Status Bot

A Discord bot for Minecraft Java Edition servers. It shows online/offline status, player count, version, latency, MOTD, available player names, and the server icon when available.

## Commands

- `/mcinfo server_ip` - Status, player count, version, latency, and a **More info** button.
- `/mcping server_ip` - Online status and response time.
- `/mcplayers server_ip` - Player count and any names the server shares.
- `/mcmotd server_ip` - Server MOTD.
- `/help` - Show the command list in Discord.

Player names are not guaranteed: servers can hide the sample list, and the bot only displays names provided by the server. This starter checks Java Edition servers.

## Deploy to a host

You do not need to keep the bot running on your PC. Deploy this folder to a hosting provider that supports an always-on Python worker or background service. Do not choose a static website host.

1. Create an application and bot in the [Discord Developer Portal](https://discord.com/developers/applications).
2. Invite it to your Discord server with the `bot` and `applications.commands` scopes. It does not need privileged intents or message-reading permissions.
3. Upload this project folder to a Git repository that your hosting provider can access.
4. In the hosting provider, create a Python worker/background service from that repository. Configure:
   - Runtime: Python 3.10 or newer
   - Install command: `pip install -r requirements.txt`
   - Start command: `python bot.py`
   - Environment variable: `DISCORD_TOKEN` set to your bot token
5. Deploy the service and leave it running. The host will keep the bot online; you only need to return to the host dashboard to manage or restart it.

Keep the token private and only add it in the host's secret/environment-variable settings, not in the source code or Git repository. If it is exposed, reset it in the Developer Portal.

Slash commands sync when the bot starts. A newly registered global command may take a short time to appear in Discord.

