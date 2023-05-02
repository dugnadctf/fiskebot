#!/usr/bin/env python3
import asyncio
import logging
import os.path
import sys
import traceback

import ctf_model
import db
import discord
from config import config
from constants import ADMIN_ROLE_NAME, SOURCES_TEXT
from ctf_model import only_read
from discord import Permissions
from discord.ext import commands
from helpers import helpers
from logger import BotLogger

# TODO: Append channel id to naming in db to fix naming conflicts. For both teams and challenges
# Possible naming convention:
# f"{name}-{ctx.channel.id}"

logger = BotLogger("bot")

if not config["token"]:
    logger.error("DISCORD_TOKEN has not been set")
    exit(1)

#Need to figure out which intents is needed
intents = discord.Intents.all()
intents.members = True
intents.typing = True
intents.presences = True
intents.messages = True
intents.reactions = True

client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix=config["prefix"],intents=intents)



intents = discord.Intents.default()
intents.members = True

bot.remove_command("help")


@bot.event
async def on_ready():
    logger.add_discord_log_handler(bot)
    logger.info(f"<{bot.user.name} Online>")
    logger.info(f"discord.py {discord.__version__}")
    await bot.change_presence(activity=discord.Game(name=f'{config["prefix"]}help'))


@bot.event
async def on_message(message):
    await bot.process_commands(message)


@bot.event
async def on_error(evt_type, ctx=None):
    if evt_type == "on_message" and ctx:
        await ctx.send("An error has occurred... :disappointed:")
    logger.error(f"Ignoring exception at {evt_type}")
    logger.error(traceback.format_exc())


@bot.event
async def on_command_error(ctx, err):
    logger.debug(f"Command error occured with command: {ctx.command}\n{err}\n")
    if isinstance(err, commands.MissingPermissions):
        await ctx.send(
            "You do not have permission to do that! ¯\\_(ツ)_/¯"
        )  # pylint: disable=anomalous-backslash-in-string
    elif isinstance(err, commands.BotMissingPermissions):
        await ctx.send(
            f""":cry: I can\'t do that. Please ask server ops
        to add all the permission for me!

        ```{str(err)}```"""
        )
    elif isinstance(err, commands.DisabledCommand):
        await ctx.send(":skull: Command has been disabled!")
    elif isinstance(err, commands.CommandNotFound):
        await ctx.send("Invalid command passed. Use !help.")
    elif isinstance(err, ctf_model.TaskFailed):
        await ctx.send(f":bangbang: {str(err)}")
    elif isinstance(err, commands.NoPrivateMessage):
        await ctx.send(":bangbang: This command cannot be used in PMs.")
    else:
        logger.error(
            f"Exception in command {ctx.command}\n"
            + "".join(traceback.format_exception(type(err), err, err.__traceback__))
        )
        msg = await ctx.send(f"An error has occurred... :disappointed: \n`{err}`\n")
        await asyncio.sleep(15)
        await msg.delete()


@bot.event
async def on_raw_reaction_add(payload):
    # check if the user is not the bot
    guild = bot.get_guild(payload.guild_id)
    chan = bot.get_channel(payload.channel_id)
    team = db.teamdb[str(payload.guild_id)].find_one({"msg_id": payload.message_id})
    challenge = db.challdb[str(payload.guild_id)].find_one({"msg_id": payload.message_id})
    member = await guild.fetch_member(payload.user_id)

    if guild and member and chan and not member.bot:
        if team:
            role = guild.get_role(team["role_id"])
            if not role:
                logger.error(
                    f"Not adding role. Could not find role ID {team['role_id']} in Discord"
                )
                logger.error(team)
                return

            await member.add_roles(role, reason="User wanted to join team")
        elif challenge and config['react_for_challenge']:
            # logger.debug(f"Adding {member.name} to thread")
            thread = guild.get_thread(challenge['thread_id'])
            await thread.add_user(member)
            db.challdb[str(payload.guild_id)].update_one(
                {"msg_id": payload.message_id}, {"$push": {"working": member.id}}
            )
            # logger.debug(f"Added {member.name} to thread")
        else: 
            # logger.error(f"Not adding role. Could find team")
            return



@bot.event
async def on_raw_reaction_remove(payload):
    # check if the user is not the bot
    guild = bot.get_guild(payload.guild_id)
    team = db.teamdb[str(payload.guild_id)].find_one({"msg_id": payload.message_id})
    challenge = db.challdb[str(payload.guild_id)].find_one({"msg_id": payload.message_id})
    member = await guild.fetch_member(payload.user_id)
    
    if guild and member and not member.bot:
        # logger.debug(f"Removed reaction: {payload}")
        # logger.debug(f"Guild: {guild}, Team: {team}, Member: {member}")

        if team:
            role = guild.get_role(team["role_id"])
            if not role:
                logger.error(f"Not removing role. Could not find role ID {team['role_id']}")
                logger.error(team)
                return
            await member.remove_roles(role, reason="User wanted to leave team")
            # logger.debug(f"Removed role {role} from user {member}")
            
        elif challenge and config['react_for_challenge']:
            # logger.debug(f"Removing {member.name} to thread")
            thread = guild.get_thread(challenge['thread_id'])
            print(challenge)
            await thread.remove_user(member)
            db.challdb[str(payload.guild_id)].update_one(
                {"msg_id": payload.message_id}, {"$pull": {"working": member.id}}
            )
            # logger.debug(f"Removed {member.name} to thread")
        else: 
            # logger.error(f"Not removing role. Could find team")
            return
            
    
    
async def embed_help(chan, help_topic, help_text):
    emb = discord.Embed(description=help_text, colour=4387968)
    emb.set_author(name=help_topic)
    return await chan.send(embed=emb)


@bot.command()
async def source(ctx):
    await ctx.send(SOURCES_TEXT)


@bot.command()
async def help(ctx, category=None):
    helper = helpers["core"]
    if category:
        category = category.lower()
        if category[:3] == "ctf":
            helper = helpers["ctf"]
        elif category[:4] == "chal":
            helper = helpers["challenge"]
    await embed_help(ctx, helper["title"], helper["text"])


@bot.command()
async def request(ctx, feature):
    if config["maintainers"]:
        for cid in config["maintainers"]:
            creator = bot.get_user(cid)
            authors_name = str(ctx.author)
            await creator.send(f""":pencil: {authors_name}: {feature}""")
        await ctx.send(f""":pencil: Thanks, "{feature}" has been requested!""")
    else:
        await ctx.send(f""":pencil: No maintainers listed in config!""")


@bot.command()
async def report(ctx, error_report):
    if config["maintainers"]:
        for cid in config["maintainers"]:
            creator = bot.get_user(cid)
            authors_name = str(ctx.author)
            await creator.send(
                f""":triangular_flag_on_post: {authors_name}: {error_report}"""
            )
        await ctx.send(
            f""":triangular_flag_on_post: Thanks for the help, "{error_report}" has been reported!"""
        )
    else:
        await ctx.send(f""":pencil: No maintainers listed in config!""")
        
@bot.command()
async def setup(ctx):
    if ctx.author.id not in config["maintainers"]:
        return ctx.send("Only maintainers can run the setup process.")

    overwrites = {
        ctx.guild.default_role: ctf_model.basic_disallow,
        ctx.guild.me: ctf_model.basic_allow,
    }
    existing_categories = [category.name for category in ctx.guild.categories]
    for category in [config["categories"]["working"], config["categories"]["done"]]:
        if category not in existing_categories:
            await ctx.guild.create_category(category, overwrites=overwrites)

    await ctx.guild.create_role(
        name=ADMIN_ROLE_NAME,
        permissions=Permissions.all(),
        reason="tmp privesc role for some bot commands",
    )

    await ctx.guild.create_text_channel(
        config["channels"]["export"],
        overwrites={
            ctx.guild.default_role: only_read,
        },
    )

    await ctx.send("Setup successfull! :tada:")


@bot.command()
async def su(ctx):
    for role in ctx.guild.roles:
        if str(role) == ADMIN_ROLE_NAME:
            await ctx.author.add_roles(role)
            await asyncio.sleep(300)
            await exit(ctx)
    else:
        await ctx.send("Couldn't find temporary admin role, have you run !setup")


@bot.command()
async def exit(ctx):
    for role in ctx.guild.roles:
        if str(role) == ADMIN_ROLE_NAME:
            await ctx.author.remove_roles(role)


# -------------------

async def loadExtras(bot):
    await bot.load_extension("ctftime")
    await bot.load_extension("ctfs")

async def main():

    await loadExtras(bot)
    
    async with bot:
        await bot.start(config["token"])

    
if __name__ == "__main__":
    asyncio.run(main())