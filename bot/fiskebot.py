import asyncio
import logging
import os.path
import shutil
import traceback

import colorama
import ctf_model
import db
import discord
from config import config
from discord.ext import commands
from logger import BotLogger

logger = BotLogger("fiskebot")

if not config["token"]:
    logger.error("DISCORD_TOKEN has not been set")
    exit(1)

src_fork1 = "https://github.com/NullPxl/NullCTF"
src_fork2 = "https://gitlab.com/inequationgroup/igCTF"
src_fork3 = "https://github.com/ept-team/eptbot"

client = discord.Client()

bot = commands.Bot(command_prefix=config["prefix"])
bot.remove_command("help")

# -------------------


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
    logger.error(
        f"Ignoring exception in command {ctx.command}\n"
        + "".join(traceback.format_exception(type(err), err, err.__traceback__))
    )
    logger.info(
        colorama.Style.BRIGHT
        + colorama.Fore.RED
        + f"Error occured with: {ctx.command}\n{err}\n"
    )
    print(colorama.Style.RESET_ALL)
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
        msg = await ctx.send(f"An error has occurred... :disappointed: \n`{err}`\n")
        await asyncio.sleep(15)
        await msg.delete()


@bot.event
async def on_raw_reaction_add(payload):
    logger.debug("added reaction:", payload)
    # check if the user is not the bot
    guild = bot.get_guild(payload.guild_id)
    chan = bot.get_channel(payload.channel_id)
    team = db.teamdb[str(payload.guild_id)].find_one({"msg_id": payload.message_id})
    member = await guild.fetch_member(payload.user_id)
    logger.debug(f"guild: {guild}, chan: {chan}, team: {team}, member: {member}")
    if guild and member and chan:
        if team:
            role = guild.get_role(team["role_id"])
            await member.add_roles(role, reason="User wanted to join team")
            logger.debug(f"added role {role} to use {member}")


@bot.event
async def on_raw_reaction_remove(payload):
    logger.debug("removed reaction:", payload)
    # check if the user is not the bot
    guild = bot.get_guild(payload.guild_id)
    team = db.teamdb[str(payload.guild_id)].find_one({"msg_id": payload.message_id})
    member = await guild.fetch_member(payload.user_id)
    logger.debug(f"guild: {guild}, team: {team}, member: {member}")
    if guild and member:
        if team:
            role = guild.get_role(team["role_id"])
            await member.remove_roles(role, reason="User wanted to leave team")
            logger.debug(f"removed role {role} to use {member}")


async def embed_help(chan, help_topic, help_text):
    emb = discord.Embed(description=help_text, colour=4387968)
    emb.set_author(name=help_topic)
    return await chan.send(embed=emb)


@bot.command()
async def source(ctx):
    await ctx.send(
        f"Source: https://github.com/ekofiskctf/fiskebot\nForked from: {src_fork3}\nWho again forked from: {src_fork2}\nWho again forked from: {src_fork1}"
    )


@bot.command()
async def help(ctx, page=None):
    help = f"""
Fork from: {src_fork3}
Who again forked from {src_fork2}
Who again forked from {src_fork1}

`!create <ctf name>`
Create a text channel and role in the CTF category for a specified `ctf name`.
(This requires the bot has manage channels permissions)

`!ctf <action>...`
You can only issue these commands in a channel that was created by the `!create` command.
See `!ctf help` for more details.

`!chal <action>...`
You can only issue these commands in a channel that was created by the `!ctf add` command.
See `!chal help` for more details.

`!ctftime`
List CTFtime commands.

`!report <issue...>`
report an issue to the maintainers

`!request <request...>`
request a new feature from the maintainers

`!source`
display source information
""".replace(
        "!", config["prefix"]
    )
    await embed_help(ctx, "Help for core commands", help)


@bot.command()
async def request(ctx, feature):
    for cid in config["maintainers"]:
        creator = bot.get_user(cid)
        authors_name = str(ctx.author)
        await creator.send(f""":pencil: {authors_name}: {feature}""")
    await ctx.send(f""":pencil: Thanks, "{feature}" has been requested!""")


@bot.command()
async def report(ctx, error_report):
    for cid in config["maintainers"]:
        creator = bot.get_user(cid)
        authors_name = str(ctx.author)
        await creator.send(
            f""":triangular_flag_on_post: {authors_name}: {error_report}"""
        )
    await ctx.send(
        f""":triangular_flag_on_post: Thanks for the help, "{error_report}" has been reported!"""
    )


@bot.command()
async def setup(ctx):
    if ctx.author.id not in config["maintainers"]:
        return [(None, "Only maintainers can run the setup process.")]

    overwrites = {
        ctx.guild.default_role: ctf_model.basic_disallow,
        ctx.guild.me: ctf_model.basic_allow,
    }
    existing_categories = [category.name for category in ctx.guild.categories]
    for category in [config["categories"]["working"], config["categories"]["done"]]:
        if category not in existing_categories:
            await ctx.guild.create_category(category, overwrites=overwrites)

    await ctx.send("Setup successfull! :tada:")


# -------------------

if __name__ == "__main__":
    bot.load_extension("ctftime")
    bot.load_extension("ctfs")
    bot.run(config["token"])
