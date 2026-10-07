import asyncio
import base64
import binascii
import os
from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands
from mcstatus import JavaServer


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LOOKUP_TIMEOUT = 5


def lookup_server(address: str):
    server = JavaServer.lookup(address)
    status = server.status(timeout=LOOKUP_TIMEOUT)
    return status


def clean_motd(motd) -> str:
    return " ".join(motd.to_plain().split())[:1000] or "No MOTD provided"


def get_player_names(status) -> list[str]:
    sample = getattr(status.players, "sample", None) or []
    return [player.name for player in sample if getattr(player, "name", None)]


def icon_file(status):
    icon = getattr(status, "icon", None)
    if not icon or not icon.startswith("data:image/png;base64,"):
        return None
    try:
        image = base64.b64decode(icon.split(",", 1)[1], validate=True)
    except (binascii.Error, ValueError):
        return None
    return discord.File(BytesIO(image), filename="server-icon.png")


class MoreInfoView(discord.ui.View):
    def __init__(self, status):
        super().__init__(timeout=15 * 60)
        self.status = status

    @discord.ui.button(label="More info", style=discord.ButtonStyle.secondary)
    async def more_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        names = get_player_names(self.status)
        embed = discord.Embed(title="Server details", color=discord.Color.green())
        embed.add_field(name="MOTD", value=clean_motd(self.status.motd), inline=False)
        embed.add_field(
            name=f"Player names ({len(names)} shown)",
            value="\n".join(names[:25]) if names else "Player names are not available.",
            inline=False,
        )
        if len(names) > 25:
            embed.set_footer(text=f"Showing the first 25 of {len(names)} names")

        image = icon_file(self.status)
        if image:
            embed.set_thumbnail(url="attachment://server-icon.png")
            await interaction.response.send_message(embed=embed, file=image, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


class MinecraftStatusBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()


bot = MinecraftStatusBot()


async def fetch_status(interaction: discord.Interaction, server_ip: str):
    address = server_ip.strip()
    if not address:
        await interaction.response.send_message("Enter a Minecraft server address.", ephemeral=True)
        return None

    await interaction.response.defer(thinking=True)
    try:
        return await asyncio.to_thread(lookup_server, address)
    except (OSError, TimeoutError, ValueError):
        await interaction.followup.send(
            f"Could not get a response from `{discord.utils.escape_markdown(address)}`. It may be offline or unreachable."
        )
    except Exception:
        await interaction.followup.send(
            "Could not check that address. It may be invalid or not a supported Java server."
        )
    return None


@bot.tree.command(name="help", description="Show Minecraft bot commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="Minecraft bot commands", color=discord.Color.blurple())
    embed.add_field(name="/mcinfo server_ip", value="Status, player count, version, and a More info button.", inline=False)
    embed.add_field(name="/mcping server_ip", value="Check whether a server is online and see its response time.", inline=False)
    embed.add_field(name="/mcplayers server_ip", value="See the online player count and names the server shares.", inline=False)
    embed.add_field(name="/mcmotd server_ip", value="Read the server's message of the day.", inline=False)
    embed.add_field(name="/help", value="Show this command list.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="mcinfo", description="Check a Minecraft Java server's status")
@app_commands.describe(server_ip="Server address, such as play.example.net or play.example.net:25565")
async def mcinfo(interaction: discord.Interaction, server_ip: str):
    status = await fetch_status(interaction, server_ip)
    if status is None:
        return

    embed = discord.Embed(
        title="Minecraft server is online",
        description=f"`{discord.utils.escape_markdown(server_ip.strip())}`",
        color=discord.Color.green(),
    )
    embed.add_field(name="Players", value=f"{status.players.online}/{status.players.max}", inline=True)
    embed.add_field(name="Version", value=status.version.name or "Unknown", inline=True)
    embed.add_field(name="Latency", value=f"{round(status.latency)} ms", inline=True)
    await interaction.followup.send(embed=embed, view=MoreInfoView(status))


@bot.tree.command(name="mcping", description="Check a Minecraft server's status and response time")
@app_commands.describe(server_ip="Server address, such as play.example.net")
async def mcping(interaction: discord.Interaction, server_ip: str):
    status = await fetch_status(interaction, server_ip)
    if status is None:
        return
    await interaction.followup.send(
        f"`{discord.utils.escape_markdown(server_ip.strip())}` is online and responded in **{round(status.latency)} ms**."
    )


@bot.tree.command(name="mcplayers", description="Show a Minecraft server's player count and available names")
@app_commands.describe(server_ip="Server address, such as play.example.net")
async def mcplayers(interaction: discord.Interaction, server_ip: str):
    status = await fetch_status(interaction, server_ip)
    if status is None:
        return
    names = get_player_names(status)
    message = f"**Players:** {status.players.online}/{status.players.max}"
    if names:
        message += "\n**Names shared by the server:**\n" + "\n".join(names[:25])
    else:
        message += "\nThis server did not share player names."
    await interaction.followup.send(message)


@bot.tree.command(name="mcmotd", description="Show a Minecraft server's MOTD")
@app_commands.describe(server_ip="Server address, such as play.example.net")
async def mcmotd(interaction: discord.Interaction, server_ip: str):
    status = await fetch_status(interaction, server_ip)
    if status is None:
        return
    embed = discord.Embed(
        title=f"MOTD: {discord.utils.escape_markdown(server_ip.strip())}",
        description=clean_motd(status.motd),
        color=discord.Color.green(),
    )
    await interaction.followup.send(embed=embed)


if not DISCORD_TOKEN:
    raise RuntimeError("Set the DISCORD_TOKEN environment variable before starting the bot.")

bot.run(DISCORD_TOKEN)
