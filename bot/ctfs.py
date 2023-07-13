import re
import asyncio

import ctf_model
import db
from bson import ObjectId
from config import config
from ctf_model import delete, exportChannels, save
from discord.ext import commands
from discord.ext.tasks import loop
from discord.member import Member
from discord.utils import get
from exceptions import ChannelDeleteFailedException, ChannelNotFoundException

from bot import embed_help


def verify_owner():
    def predicate(ctx):
        chk_fetch_chal(ctx).check_done(ctx.author)
        return True

    return commands.check(predicate)



class Ctfs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ctfname = ""

        self.limit = 400
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
        chan_id, messages = await respond_with_reaction(
            ctx, emoji, ctf_model.CtfTeam.create, ctx.channel.guild, name
        )
        # TODO: Find a way to get the id of the newly created TextChannel
        db.teamdb[str(ctx.channel.guild.id)].update_one(
            {"name": name+"-"+str(chan_id)}, {"$set": {"msg_id": messages[0].id}}
        )

    ##################################################################################
    # CTF main channel commands
    ##################################################################################

    @commands.bot_has_permissions(manage_channels=True)
    @commands.command()
    async def add(self, ctx, *words):
        name = " ".join(words)
        name = check_name(name)
        emoji = "🔨"
        _, messages = await respond_with_reaction(ctx, emoji, chk_fetch_team(ctx).add_chal, name)
        db.challdb[str(ctx.channel.guild.id)].update_one(
            {"name": name+"-"+str(messages[0].channel.id)}, {"$set": {"msg_id": messages[0].id}}
        )

    @commands.bot_has_permissions(manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @commands.command()
    async def delete(self, ctx, name):
        name = check_name(name)
        await respond(ctx, chk_fetch_team(ctx).del_chal, name)
        
    @commands.command()
    async def status(self, ctx, state="lol"): #Legge til statuscheck
        chals = chk_fetch_team(ctx).challenges
        if len(chals) == 0:
            await ctx.send("No challenges added...")
            return
        uns = True
        if str(state).lower()=="unsolved":
            uns = False
        
        msg_len = 50
        lines = []
        for chal in chals:
            status = await chal.status()
            if status.lower()[:4] != "unso" and not uns:
                continue
            chall_line = f"[{chal.team.name}] [{chal.name}] - {status}"
            msg_len += len(chall_line) + 1
            if msg_len > 1000:  # Over limit
                lines = "\n".join(lines)
                await ctx.send(f"```ini\n{lines}```")
                lines = []
                msg_len = len(chall_line) + 51
            lines.append(chall_line)
        if len(lines)==0:
            await ctx.send(f"Every started challenge is completed! :tada:") 
        else:
            lines = "\n".join(lines)
            await ctx.send(f"```ini\n{lines}```")  


    @commands.command()
    async def working(self, ctx): 
        # chk_fetch_team(ctx).refresh
        chals = chk_fetch_team(ctx).challenges
        if len(chals) == 0:
            await ctx.send("No challenges added...")
            return
        if not config['react_for_challenge']:
            await ctx.send("Makes no sense to check who is working when everyone has joined every thread...")
            return
        
        msg_len = 50
        lines = []
        for chal in chals:
            status = await chal.status()
            if status.lower()[:4] != "unso":
                continue
            workers = await chal.working()
            if not workers:
                chall_line = f"[{chal.team.name}] [{chal.name}] - No one works this challenge..."
            else:
                chall_line = f"[{chal.team.name}] [{chal.name}] - {workers} works on this challenge"
            msg_len += len(chall_line) + 1
            if msg_len > 1000:  # Over limit
                lines = "\n".join(lines)
                await ctx.send(f"```ini\n{lines}```")
                lines = []
                msg_len = len(chall_line) + 51
            lines.append(chall_line)
        if len(lines)==0:
            await ctx.send(f"No one is working on any unsolved challenge...") 
        else:
            lines = "\n".join(lines)
            await ctx.send(f"```ini\n{lines}```")     
        
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
        try:
            await respond(ctx, chk_fetch_team(ctx).archive)
        except ChannelNotFoundException as e:
            await ctx.send(str(e))

    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @commands.command()
    async def unarchive(self, ctx):
        try:
            await respond(ctx, chk_fetch_team(ctx).unarchive)
        except ChannelNotFoundException as e:
            await ctx.send(str(e))

    @commands.has_permissions(manage_channels=True)
    @commands.command()
    async def deletectf(self, ctx, ctf_name):
        try:
            await chk_fetch_team(ctx).deletectf(ctx.author, ctf_name)
        except ChannelDeleteFailedException as e:
            await ctx.send(str(e))


    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    # @commands.has_permissions(manage_channels=True)
    @commands.command()
    async def export(self, ctx):
        await respond(ctx, ctf_model.export, ctx, ctx.author)
        
        
    ##################################################################################
    # CTF challenge specific commands
    ##################################################################################
    @commands.bot_has_permissions(manage_channels=True)
    #@verify_owner()
    @commands.command()
    async def done(self, ctx, *withlist: Member):
        users = list(set(withlist))
        await respond(ctx, chk_fetch_chal(ctx).done, ctx.author, users)

    @commands.bot_has_permissions(manage_channels=True)
    #@verify_owner()
    @commands.command()
    async def undone(self, ctx):
        await respond(ctx, chk_fetch_chal(ctx).undone)


    ##################################################################################
    # Automatic cleanup
    ##################################################################################
    @loop(minutes=30)
    async def cleanup(self):
        for guild_id, guild in self.guilds.items():

            #Archive threads in archived ctf channels and make sure threads in active CTFs is not archived
            for channel in guild.channels:
                if config['categories']["archive-prefix"].lower() in str(channel.category).lower():
                    for thread in channel.threads:
                        if not thread.archived:
                            await thread.edit(archived=True)
                elif config['categories']["working"].lower() in str(channel.category).lower():
                    for thread in channel.threads:
                        if "❌" in thread.name:
                            await thread.edit(archived=False)

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
            chan =  ctx.channel
            msg = await chan.send(msg)
            #Just in case we don't want to add reaction, which was really not needed for add challenge
            if emoji:
                await msg.add_reaction(emoji)
            messages.append(msg)
    return chan_id, messages

#TODO find out which filters is needed for threads
def check_name(name):
    if len(name) > 32:
        raise ctf_model.TaskFailed("Challenge name is too long!")

    if not re.match(r"[-._!0-9A-Za-z æøåÆØÅ]+$", name):
        raise ctf_model.TaskFailed("Challenge contains invalid characters!")

    # Replace spaces with a dash with a configured delimiter
    return re.sub(r" +", " ", name).lower()


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
            "Please type this command in the channel of a CTF."
        )
    return team

def chk_fetch_chal(ctx):
    chal = ctf_model.Challenge.fetch(ctx.channel.guild, ctx.channel.id)
    if not chal:
        raise ctf_model.TaskFailed("Please type this command in a challenge channel.")
    return chal


async def setup(bot):
    await bot.add_cog(Ctfs(bot))
