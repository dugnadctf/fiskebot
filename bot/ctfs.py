import re

import ctf_model
import db
from bson import ObjectId
from config import config
from ctf_model import delete, exportChannels, save
from discord.ext import commands
from discord.ext.tasks import loop
from discord.member import Member
from discord.utils import get

from bot import embed_help


def verify_owner():
    def predicate(ctx):
        chk_fetch_chal(ctx).check_done(ctx.author)
        return True

    return commands.check(predicate)


class Ctfs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.challenges = {}
        self.ctfname = ""

        self.limit = 20
        self.guilds = {}
        self.cleanup.start()

    ##################################################################################
    # Core commands
    ##################################################################################
    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    @commands.guild_only()
    @commands.command()
    async def create(self, ctx, *name):
        name = config["challenge_name_delimiter"].join(name)
        emoji = "🏃"
        messages = await respond_with_reaction(
            ctx, emoji, ctf_model.CtfTeam.create, ctx.channel.guild, name
        )
        db.teamdb[str(ctx.channel.guild.id)].update_one(
            {"name": name}, {"$set": {"msg_id": messages[0].id}}
        )

    ##################################################################################
    # CTF main channel commands
    ##################################################################################
    @commands.bot_has_permissions(manage_channels=True)
    @commands.command()
    async def add(self, ctx, *words):
        name = config["challenge_name_delimiter"].join(words)
        name = check_name(name)
        emoji = "🔨"
        await respond_with_reaction(ctx, emoji, chk_fetch_team(ctx).add_chal, name)

    @commands.bot_has_permissions(manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @commands.command()
    async def delete(self, ctx, name):
        name = check_name(name)
        await respond(ctx, chk_fetch_team(ctx).del_chal, name)

    @commands.bot_has_permissions(manage_roles=True)
    @commands.command()
    async def join(self, ctx, name=None):
        if name is None:
            await ctx.send(
                f'Please specify a CTF to join:\n```{config["prefix"]}join <ctf name>```'
            )
        await respond(ctx, chk_fetch_team_by_name(ctx, name).join, ctx.author)

    @commands.bot_has_permissions(manage_roles=True)
    @commands.command()
    async def leave(self, ctx):
        await respond(ctx, chk_fetch_team(ctx).leave, ctx.author)

    @commands.bot_has_permissions(manage_roles=True)
    @commands.command()
    async def invite(self, ctx, user: Member):
        await respond(ctx, chk_fetch_team(ctx).invite, ctx.author, user)

    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @commands.command()
    async def archive(self, ctx):
        await respond(ctx, chk_fetch_team(ctx).archive)

    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @commands.command()
    async def unarchive(self, ctx):
        await respond(ctx, chk_fetch_team(ctx).unarchive)

    @commands.command()
    async def status(self, ctx):
        chals = chk_fetch_team(ctx).challenges
        if len(chals) == 0:
            await ctx.send("No challenges added...")
            return

        msg_len = 50
        lines = []
        for chal in chals:
            chall_line = f"[{chal.team.name}] [{chal.name}] - {await chal.status()}"
            msg_len += len(chall_line) + 1
            if msg_len > 1000:  # Over limit
                lines = "\n".join(lines)
                await ctx.send(f"```ini\n{lines}```")
                lines = []
                msg_len = len(chall_line) + 51
            lines.append(chall_line)

        lines = "\n".join(lines)
        await ctx.send(f"```ini\n{lines}```")

    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    # @commands.has_permissions(manage_channels=True)
    @commands.command()
    async def export(self, ctx):
        await respond(ctx, ctf_model.export, ctx, ctx.author)

    ##################################################################################
    # CTF challenge specific commands
    ##################################################################################
    @commands.bot_has_permissions(manage_channels=True)
    @verify_owner()
    @commands.command()
    async def done(self, ctx, *withlist: Member):
        users = list(set(withlist))
        await respond(ctx, chk_fetch_chal(ctx).done, ctx.author, users)

    @commands.bot_has_permissions(manage_channels=True)
    @verify_owner()
    @commands.command()
    async def undone(self, ctx):
        await respond(ctx, chk_fetch_chal(ctx).undone)

    # TODO: delete? not really used as everyone has the same role
    @commands.bot_has_permissions(manage_channels=True)
    @commands.command()
    async def leave_challenge(self, ctx):
        await respond(ctx, chk_fetch_chal(ctx).leave, ctx.author)

    ##################################################################################
    # Automatic cleanup
    ##################################################################################
    @loop(minutes=30)
    async def cleanup(self):
        for guild_id, guild in self.guilds.items():
            archived = sorted(
                [
                    (ObjectId(ctf["_id"]).generation_time, ctf)
                    for ctf in db.teamdb[str(guild_id)].find({"archived": True})
                    if get(guild.text_channels, name=ctf["name"]) is not None
                ],
                reverse=True,
            )
            if len(archived) <= self.limit:
                return
            for time, ctf in archived[self.limit :]:
                ids = []
                ids.append(ctf["chan_id"])
                for chal in ctf["chals"]:
                    ids.append(int(str(chal)))
                channels = [chn for chn in guild.channels if chn.id in ids]
                if len(channels) == 0:
                    return
                CTF = await exportChannels(channels)
                await save(guild, guild.name, ctf["name"], CTF)
                await delete(guild, channels)
                break  # safety measure to take only one

    @cleanup.before_loop
    async def cleanup_before(self):
        await self.bot.wait_until_ready()
        for guild_id in config["guild_ids"]:
            self.guilds[guild_id] = self.bot.get_guild(guild_id)


##################################################################################
# Helper functions
##################################################################################
async def respond(ctx, callback, *args):
    messages = []
    guild = ctx.channel.guild
    async with ctx.channel.typing():
        for chan_id, msg in await callback(*args):
            chan = guild.get_channel(chan_id) if chan_id else ctx.channel
            msg = await chan.send(msg)
            messages.append(msg)
    return messages


async def respond_with_reaction(ctx, emoji, callback, *args):
    messages = []
    guild = ctx.channel.guild
    async with ctx.channel.typing():
        for chan_id, msg in await callback(*args):
            chan = guild.get_channel(chan_id) if chan_id else ctx.channel
            msg = await chan.send(msg)
            await msg.add_reaction(emoji)
            messages.append(msg)
    return messages


def check_name(name):
    if len(name) > 32:
        raise ctf_model.TaskFailed("Challenge name is too long!")

    if not re.match(r"[-._!0-9A-Za-z æøåÆØÅ]+$", name):
        raise ctf_model.TaskFailed("Challenge contains invalid characters!")

    # Replace spaces with a dash with a configured delimiter
    return re.sub(r" +", config["challenge_name_delimiter"], name).lower()


def chk_fetch_team_by_name(ctx, name):
    channels = ctx.guild.channels
    if len([channel.id for channel in channels if name == channel.name]) > 1:
        raise ctf_model.TaskFailed("Multiple channels with same name exists")

    found_channel_id = ""
    for channel in channels:
        if channel.name == name:
            found_channel_id = channel.id
    team = ctf_model.CtfTeam.fetch(ctx.channel.guild, found_channel_id)
    if not team:
        raise ctf_model.TaskFailed("Failed to join CTF")
    return team


def chk_fetch_team(ctx):
    team = ctf_model.CtfTeam.fetch(ctx.channel.guild, ctx.channel.id)
    if not team:
        raise ctf_model.TaskFailed(
            "Please type this command in the main channel of a CTF."
        )
    return team


def chk_fetch_chal(ctx):
    chal = ctf_model.Challenge.fetch(ctx.channel.guild, ctx.channel.id)
    if not chal:
        raise ctf_model.TaskFailed("Please type this command in a challenge channel.")
    return chal


def setup(bot):
    bot.add_cog(Ctfs(bot))
