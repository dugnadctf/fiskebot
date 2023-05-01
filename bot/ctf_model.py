import functools
import json
import os
import datetime
import asyncio

import bson
import db
# import ctfs
import discord
import discord.member
from config import config
from discord.ext import commands
from exceptions import ChannelDeleteFailedException, ChannelNotFoundException, ThreadNotFoundException

CATEGORY_CHANNEL_LIMIT = 50

# Globals
# > done_id
# > archive_id > working_id
# CtfTeam
# [gid...]
#   > challenges [array of thread IDs]
#   > name
#   > chan_id
#   > role_id
#
# Challenge
# [gid...]
#   > name
#   > ctf_id [int, thread ID]
#   > chan_id
#   > finished [bool]
#   > solvers (by id)
#
#
# GLOBAL
# ---
# create-ctf <name>
#
# CTF-specific channel
# ---
# ctf working <chal-name>
# ctf join
# ctf leave
# ctf add <chal-name>
# ctf del <chal-name>
# ctf archive
#
# CHALLENGE-specific channel
# ---
# chal done <with-list>
# chal undone


def _find_chan(chantype, group, name):
    name = name.casefold()
    for chan in getattr(group, chantype):
        if chan.name.casefold() == name:
            return chan

    raise ValueError(f"Cannot find category {name}")


def format_role_name(ctf_name):
    return f"{ctf_name}_team".lower()


async def _find_available_archive_category(guild, current_channel_count, start):
    archive_number = 0 
    
    for i in range(start, 15):
        year = str(datetime.date.today().year)

        category_name = f"{year}-{config['categories']['archive-prefix']}-{i}"
        archive_number = i
        try:
            category_archive = [
                category
                for category in guild.categories
                if category.name == category_name
            ][0]
            current_category_channels = len(category_archive.channels)
            if CATEGORY_CHANNEL_LIMIT - current_category_channels >= (
                current_channel_count
            ):
                break
        except IndexError:
            category_archive = await guild.create_category(category_name)
            break
    return category_archive, archive_number


find_category = functools.partial(_find_chan, "categories")
find_text_channel = functools.partial(_find_chan, "text_channels")


def load_category(guild, catg):
    # TODO: change name based on guild-local configs
    return find_category(guild, catg)



basic_read_send = discord.PermissionOverwrite(
    add_reactions=True,
    read_messages=True,
    send_messages=True,
    read_message_history=True,
)
basic_allow = discord.PermissionOverwrite(
    add_reactions=True,
    read_messages=True,
    send_messages=True,
    read_message_history=True,
    manage_channels=True,
)

basic_disallow = discord.PermissionOverwrite(
    add_reactions=False,
    read_messages=False,
    send_messages=False,
    read_message_history=False,
)

only_read = discord.PermissionOverwrite(
    add_reactions=False,
    read_messages=True,
    send_messages=False,
    read_message_history=True,
)


def chk_upd(ctx_name, update_res):
    if not update_res.matched_count:
        raise ValueError(f"{ctx_name}: Not matched on update")
    # if not update_res.modified_count:
    #    raise ValueError(f'{ctx_name}: Not modified on update')


def chk_del(ctx_name, delete_res):
    if not delete_res.deleted_count:
        raise ValueError(f"{ctx_name}: Not deleted")


def chk_get_role(guild, role_id):
    role = guild.get_role(role_id)
    if not role:
        raise ValueError(f"{role_id}: Invalid role ID")
    return role


def chk_archive(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.is_archived:
            raise TaskFailed("Cannot do that, this is archived")
        return func(self, *args, **kwargs)

    return wrapper


def user_to_dict(user):
    try:
        return {
            "id": user.id,
            "nick": user.nick,
            "user": user.name,
            "avatar": user.avatar,
            "bot": user.bot,
        }
    except AttributeError:
        return {
            "id": user.id,
            "nick": "<Unknown>",
            "user": user.name,
            "avatar": user.avatar,
            "bot": user.bot,
        }


class TaskFailed(commands.UserInputError):
    def __init__(self, msg):
        super().__init__(msg)


class CtfTeam:
    __teams__ = {}

    @staticmethod
    async def create(guild, name):
        names = [role.name for role in guild.roles] + [channel.name for channel in guild.channels]
        if name in names:
            return [(ValueError, f"`{name}` already exists as a role :grimacing:")]

        # Create role
        role_name = format_role_name(name)
        role = await guild.create_role(name=role_name, mentionable=True)

        # Create channel
        overwrites = {
            guild.default_role: basic_disallow,
            guild.me: basic_allow,
            role: basic_allow,
        }

        if discord.utils.get(guild.text_channels, name=name) is not None:
            return [(ValueError, f"`{name}` already exists as a channel :grimacing:")]
        
        #Becuase we use threads, it will be more clean to have a full category for ongoing ctfs
        workingCategoryName = config["categories"]["working"]
        workingCategoryId = False
        
        for category in guild.categories:
            if category.name == workingCategoryName:
                workingCategoryId = category
                
        if workingCategoryId:
            chan = await guild.create_text_channel(
                name=name,
                overwrites=overwrites,
                position=0,
                topic=f"Channel for {name} CTF event",
                category=workingCategoryId
            )
        else:
            existing_categories = [category.name for category in guild.categories]
            category = config["categories"]["working"]
            if category not in existing_categories:
                cat = await guild.create_category(category)
            chan = await guild.create_text_channel(
                name=name,
                overwrites=overwrites,
                category=cat,
                topic=f"Channel for {name} CTF event",
            )

        # Update database
        db.teamdb[str(guild.id)].insert_one(
            {
                "archived": False,
                "name": name,
                "chan_id": chan.id,
                "role_id": role.id,
                "msg_id": 0,
            }
        )
        CtfTeam.__teams__[chan.id] = CtfTeam(guild, chan.id)
        

        return [
            (
                None,
                f"<#{chan.id}> (`{name}`) has been created! :tada:! React to this message to join.",
            )
        ]

    @staticmethod
    def fetch(guild, chan_id):
        if chan_id not in CtfTeam.__teams__:
            if not db.teamdb[str(guild.id)].find_one({"chan_id": chan_id}):
                return None
            CtfTeam.__teams__[chan_id] = CtfTeam(guild, chan_id)
        else:
            CtfTeam.__teams__[chan_id].refresh()

        # TODO: check guild is same
        return CtfTeam.__teams__[chan_id]

    def __init__(self, guild, chan_id):
        self.__guild = guild
        self.__chan_id = chan_id
        self.__teams = db.teamdb[str(guild.id)]
        self.refresh()

    #Something weird with the 'chals' key here
    @property
    def challenges(self):
        # Temporary fix? Had a problem where ctfs with no challenges didn't archive correctly
        self.refresh()
        return [Challenge.fetch(self.__guild, cid) for cid in self.__teamdata["chals"]]

    @property
    def name(self):
        return self.__teamdata["name"]

    @property
    def chan_id(self):
        return self.__chan_id

    @property
    def guild(self):
        return self.__guild

    @property
    def is_archived(self):
        return self.__teamdata.get("archived", False)

    @property
    def mention(self):
        return f'<@&{self.__teamdata["role_id"]}>'

    @property
    def team_data(self):
        return self.__teamdata

    @chk_archive
    async def add_chal(self,name):
        cid = self.__chan_id
        guild = self.__guild
        teams = self.__teams
        team = self.__teamdata
        channel = guild.get_channel(cid)


        # catg_working = load_category(guild, config["categories"]["working"])
        if self.find_chal(name, False):
            raise TaskFailed(f'Challenge "{name}" already exists!')

        # Create a public thread, initially only with us added.
        fullname = f"❌ {name}"

        thread = await channel.create_thread(name=fullname,type=discord.ChannelType.public_thread)

        Challenge.create(guild=guild,ctf_id=cid,thread_id=thread.id,name=name)
        chk_upd(
            fullname, teams.update_one({"chan_id": cid}, {"$push": {"chals": thread.id}})
        )
        self.refresh()

        # Makes a lot of noise, but is needed to show challenges in channel-list. 
        # Added a feature request to allow the bot to silently add members to thread
        # Other methods is highly wanted
        try:
            team = db.teamdb[str(guild.id)].find_one({"chan_id": cid})
            role = guild.get_role(team["role_id"])
            
            threadMembers = [member for member in thread.members]
            teamMembers = [user for user in role.members]
            
            for user in teamMembers:
                if user not in threadMembers:
                    await thread.add_user(user)
        except:
            pass

        return [
            (
                None,
                f"<#{thread.id}> (`{name}`) has been added!",
            )
        ]


    @chk_archive
    async def archive(self):
        cid = self.__chan_id
        guild = self.__guild
        teams = self.__teams
        
        self.refresh()
        
        total_channels = 1
        category_archives = []
        previous_picked_archive = -1
        while total_channels != 0:
            channels_in_category = min(CATEGORY_CHANNEL_LIMIT, total_channels)
            category, previous_picked_archive = await _find_available_archive_category(
                guild, channels_in_category, previous_picked_archive + 1
            )
            category_archives.append(
                {
                    "channels": channels_in_category,
                    "category": category,
                }
            )
            total_channels -= channels_in_category

        
        # Archive all challenge threads

        main_chan = guild.get_channel(cid)
    
        category_archives[-1]["channels"] -= 1
        
        try:
            for thread in self.challenges:
                await thread._archive()
            self.refresh()
        except:
            #Failproof if challenge doesn't exist for some reason
            pass

        await main_chan.edit(category=category_archives[-1]["category"], position=0)
        
        # Update database
        chk_upd(
            self.name, teams.update_one({"chan_id": cid}, {"$set": {"archived": True}})
        )
        self.refresh()
        
        #Archive all threads
        channel = guild.get_channel(cid)
        for thread in channel.threads:
            await thread.edit(archived=True)
        
        if config["archive_access_to_all_users"]:
            # await asyncio.sleep(1) #Because the sync permissions was unstable
            test = main_chan.set_permissions(
                guild.default_role, overwrite=basic_read_send
            )

        return [(None, f"{self.name} CTF has been archived.")]

    
    async def unarchive(self):
        cid = self.__chan_id
        guild = self.__guild
        teams = self.__teams

        catg_working = load_category(guild, config["categories"]["working"])

        if not self.is_archived:
           raise TaskFailed('This is already not archived!')

        
        #chal = db.challdb[str(guild.id)].find_one({"thread_id": thread_id})
        team = db.teamdb[str(guild.id)].find_one({"chan_id": cid}) # May be able to use teams here
        role = guild.get_role(team["role_id"])
        
        
        # Update database
        chk_upd(
            self.name, teams.update_one({"chan_id": cid}, {"$set": {"role_id": role.id}})
        )
        
        # Unarchive challenge channel
        main_chan = guild.get_channel(cid)
        
        await main_chan.edit(category=catg_working, position=0)

        if config["archive_access_to_all_users"]:
            # await asyncio.sleep(1) #Because the sync permissions was unstable
            test = main_chan.set_permissions(
                guild.default_role, overwrite=basic_disallow
            )
        
        # Update database
        chk_upd(
            self.name, teams.update_one({"chan_id": cid}, {"$set": {"archived": False}})
        )
        self.refresh()
        
        
        # Unarchive all challenge threads
        # Same noise as in add challenge, fix this also if another method is preferred
        for thread in main_chan.threads:
            await thread.join()
            #Add all users with role to thread
            usersWithRole = [user for user in role.members]
            for user in usersWithRole:
                await thread.add_user(user)
                
            await thread.edit(archived=False)
            
        try:
            for thread in self.challenges:
                await thread._unarchive()
        except:
            #Failproof: If no challenges exists
            pass
        self.refresh()

        return [(cid, f"{self.name} CTF has been unarchived.")]
    
    @chk_archive
    async def del_chal(self, name):
        cid = self.__chan_id
        guild = self.__guild
        teams = self.__teams

        # Update database
        chal = self.find_chal(name)
        chk_upd(
            name,
            teams.update_one({"chan_id": cid}, {"$pull": {"chals": chal.thread_id}}),
        )
        await chal._delete(cid)
        self.refresh()

        return [(None, f'Challenge "{name}" is deleted, challenge thread deleted.')]

    def find_chal(self, name, err_on_fail=True):
        return Challenge.find(self.__guild, self.__chan_id, name, err_on_fail)

    @chk_archive
    async def invite(self, author, user):
        guild = self.__guild
        team = self.__teamdata
        cid = self.__chan_id

        # Add role for user
        role = chk_get_role(guild, team["role_id"])
        if role in user.roles:
            raise TaskFailed(f"{user.name} has already joined {self.name}")
        await user.add_roles(role)

        channel = guild.get_channel(cid)
        for thread in channel.threads:
            await thread.add_user(user)

        return [
            (None, f'{author.mention} invited {user.mention} to the "{self.name}" team')
        ]

    @chk_archive
    async def join(self, user):
        cid = self.__chan_id
        guild = self.__guild
        team = self.__teamdata

        # Add role for user
        role = chk_get_role(guild, team["role_id"])
        if role in user.roles:
            raise TaskFailed(f"{user.mention} has already joined {self.name}")
        await user.add_roles(role)

        channel = guild.get_channel(cid)
        for thread in channel.threads:
            await thread.add_user(user)

        return [(None, f"{user.mention} has joined the <#{cid}> team! :sparkles:")]

    @chk_archive
    async def leave(self, user):
        guild = self.__guild

        team = self.__teamdata

        # Remove role for user
        role = chk_get_role(guild, team["role_id"])
        if role not in user.roles:
            raise TaskFailed(f'{user.mention} is not in {team["name"]}')
        await user.remove_roles(role)

        return [(None, f'{user.mention} has left the {team["name"]} team...')]

    def refresh(self):
        team = self.__teams.find_one({"chan_id": self.__chan_id})
        if not team:
            raise ChannelNotFoundException(f"{self.__chan_id}: Invalid CTF channel ID")
        self.__teamdata = team


    async def deletectf(self, author, confirmation):
        if author.id not in config["maintainers"]:
            raise TaskFailed("Only maintainers can delete CTFs.")

        if not self.is_archived:
            raise TaskFailed("The CTF has to be archived before deleting!")

        if confirmation != self.name:
            raise TaskFailed(
                f"Confirmation does not equal the CTF name. Execute `!deletectf {self.name}`"
            )

        # There should be just one channel id?
        for c in [self.__chan_id]:
            try:
                await self.__guild.get_channel(c).delete(reason="Deleting CTF")
            except Exception as e:
                raise ChannelDeleteFailedException(
                    f"Deletion of channel {str(c)} failed: {str(e)}"
                )

        role = chk_get_role(self.__guild, self.__teamdata["role_id"])
        await role.delete(reason="Deleting CTF")


class Challenge:
    __chals__ = {}

    @staticmethod
    def create(guild, ctf_id, thread_id, name):
                
        chals = db.challdb[str(guild.id)]
        chals.insert_one(
            {
                "name": name,
                "ctf_id": ctf_id,
                "finished": False,
                "solvers": [],
                "thread_id": thread_id,
                "owner": 0,
            }
        )
        

        chal = Challenge(guild, thread_id)
        Challenge.__chals__[thread_id] = chal
        return chal

    @staticmethod
    def fetch(guild, thread_id):
        if thread_id not in Challenge.__chals__:
            chal = db.challdb[str(guild.id)].find_one({"thread_id": thread_id})
            if not chal:
                return None
            Challenge.__chals__[thread_id] = Challenge(guild, thread_id)
        chal = Challenge.__chals__[thread_id]
        chal.refresh()
        return chal

    @staticmethod
    def find(guild, ctfid, name, err_on_fail=True):
        chal = db.challdb[str(guild.id)].find_one({"name": name, "ctf_id": ctfid})
        if chal:
            return Challenge.fetch(guild, chal["thread_id"])
        elif err_on_fail:
            raise TaskFailed(f'Challenge "{name}" does not exist!')
        else:
            return None

    def __init__(self, guild, thread_id):
        self.__guild = guild
        self.__id = thread_id
        self.__chals = db.challdb[str(guild.id)]
        self.refresh()

    @property
    def thread_id(self):
        return self.__id

    @property
    def ctf_id(self):
        return self.__chalinfo["ctf_id"]

    @property
    def is_archived(self):
        return self.__chalinfo.get("archived", False)

    @property
    def is_finished(self):
        return self.__chalinfo["finished"]

    @property
    def name(self):
        return self.__chalinfo["name"]

    @property
    def owner(self):
        return self.__chalinfo["owner"]

    @property
    def solver_ids(self):
        if not self.is_finished:
            return
        return self.__chalinfo["solvers"]

    async def solver_users(self):
        if not self.is_finished:
            return
        return [await self.__guild.fetch_member(id) for id in self.solver_ids]

    async def status(self):
        if self.is_finished:
            solvers = ", ".join(user.name for user in await self.solver_users())
            return f"Solved by {solvers}"
        else:
            return "Unsolved"

    @property
    def team(self):
        return CtfTeam.fetch(self.__guild, self.ctf_id)

    async def _archive(self):
        thread_id = self.__id
        guild = self.__guild
        #Update db
        chk_upd(
            self.name,
            self.__chals.update_one({"thread_id": thread_id}, {"$set": {"archived": True}}),
        )
        self.refresh()
        
        # raise ThreadNotFoundException(f"Couldn't find thread {thread_id}")


    # async def _unarchive(self, catg_working, catg_done):
    async def _unarchive(self):
        cid = self.__id
        guild = self.__guild
        
        #Update db
        chk_upd(
            self.name,
            self.__chals.update_one({"thread_id": cid}, {"$set": {"archived": False}}),
        )
        self.refresh()
        
    def check_done(self, user):
        if not self.is_finished:# or Challenge._uid(user) == self.owner:
            return

        guild = self.__guild
        if not guild.get_channel(self.__id).permissions_for(user).manage_channels:
            raise commands.MissingPermissions("manage_channels")


    async def _delete(self, channelid):
        cid = self.__id

        # Delete entry
        chk_del(self.name, self.__chals.delete_one({"thread_id": self.__id}))
        del Challenge.__chals__[self.__id]

        # Delete thread
        channel = self.__guild.get_channel(channelid)
        await channel.get_thread(cid).edit(archived=True)

    @chk_archive
    async def done(self, owner, users):
        thread_id = self.__id
        guild = self.__guild

        # Create list of solvers
        owner = Challenge._uid(owner)
        users = [Challenge._uid(u) for u in users]
        users.append(owner)
        users = list(set(users))
        users.sort()
        mentions = [f"<@{uid}>" for uid in users]

        # Check if it is solved already
        if self.is_finished:
            old_solvers = self.solver_ids
            old_solvers.sort()
            if old_solvers == users:
                raise TaskFailed("This task is already solved with same users")

        # Mark thread as done
        thread = guild.get_channel(self.ctf_id).get_thread(thread_id)
        if thread is not None:
            newName = thread.name.replace("❌","✅")
            await thread.edit(name=newName)
            self.refresh()
        else:
            raise ThreadNotFoundException("The thread cannot be found!")

        mentions = " ".join(mentions)
        self.refresh()
        
        # Update database
        chk_upd(
            self.name,
            self.__chals.update_one(
                {"thread_id": thread_id},
                {"$set": {"finished": True, "owner": owner, "solvers": users}},
            ),
        )

        self.refresh()
        
        return [
            (
                self.ctf_id,
                f"{self.team.mention} :tada: <#{thread_id}> has been completed by {mentions}!",
            ),
            (None, "Challenge marked as complete!"),
        ]

    # #TODO Check if this is needed
    # @chk_archive
    # async def invite(self, author, user):
    #     ccid = self.team.chan_id
    #     guild = self.__guild
    #     chan = guild.get_channel(self.__id)

    #     if user in chan.overwrites:
    #         raise TaskFailed(f'{user.name} is already in the "{self.name}" challenge')

    #     await chan.set_permissions(
    #         user,
    #         overwrite=basic_allow,
    #         reason=f'{author.name} invited user to work on "{self.name}" challenge',
    #     )
    #     return [
    #         (
    #             ccid,
    #             f'{author.mention} invited {user.mention} to work on "{self.name}" challenge',
    #         )
    #     ]

    # #TODO Check if this is needed
    # @chk_archive
    # async def leave(self, user):
    #     ccid = self.team.chan_id
    #     guild = self.__guild
    #     chan = guild.get_channel(self.__id)
    #     await chan.set_permissions(
    #         user, overwrite=None, reason=f'Left "{self.name}" challenge'
    #     )
    #     return [(ccid, f'{user.mention} has left "{self.name}" challenge')]

    def refresh(self):
        cid = self.__id
        chal = self.__chals.find_one({"thread_id": cid})
        if not chal:
            raise ThreadNotFoundException(f"{cid}: Invalid challenge thread ID")
        self.__chalinfo = chal

    @chk_archive
    async def undone(self):
        thread_id = self.__id
        guild = self.__guild

        # catg_working = load_category(guild, config["categories"]["working"])

        if not self.is_finished:
            raise TaskFailed("This ctf challenge has not been completed yet")

        # Mark thread as undone
        thread = guild.get_thread(thread_id)
        if thread is not None:
            await thread.edit(name=thread.name.replace("✅","❌"))

            self.refresh()
        else:
            raise ThreadNotFoundException("The thread cannot be found!")
        
        # Update database
        chk_upd(
            self.name,
            self.__chals.update_one({"thread_id": thread_id}, {"$set": {"finished": False}}),
        )

        self.refresh()
        return [
            (None, f'Reopened "{self.name}" as not done'),
            (
                self.ctf_id,
                f"""{self.team.mention} <#{thread_id}> is now undone. :weary:""",
            ),
        ]

    # #TODO Check if this is needed
    # @chk_archive
    # async def working(self, user):
    #     ccid = self.team.chan_id
    #     guild = self.__guild
    #     chan = guild.get_channel(self.__id)
    #     if user in chan.overwrites:
    #         raise TaskFailed(f'{user.name} is already in the "{self.name}" challenge')
    #     await chan.set_permissions(
    #         user, overwrite=basic_allow, reason=f'Working on "{self.name}" challenge'
    #     )
    #     return [(ccid, f'{user.mention} is working on "{self.name}" challenge')]

    @staticmethod
    def _uid(user):
        if isinstance(user, str):
            return int(user)
        if isinstance(user, int):
            return user
        if isinstance(user, discord.member.Member):
            return user.id
        raise ValueError(f"Cannot convert to user: {user}")

#TODO fix export
async def export(ctx, author):
    guild = ctx.guild

    if author.id not in config["maintainers"]:
        return [(None, "Only maintainers can export CTFs.")]

    main_chan = ctx.channel

    channels = [main_chan]
    for chal in guild.text_channels:
        if f"{main_chan.name}-" in chal.name:
            channels.append(chal)

    CTF = await exportChannels(channels)

    return await save(guild, guild.name, main_chan.name, CTF)

#TODO fix export
async def exportChannels(channels):
    CTF = {"channels": []}
    for channel in channels:
        chan = {
            "name": channel.name,
            "topic": channel.topic,
            "messages": [],
            "pins": [m.id for m in await channel.pins()],
        }

        async for message in channel.history(limit=None, oldest_first=True):
            entry = {
                "id": message.id,
                "created_at": message.created_at.isoformat(),
                "content": message.clean_content,
            }
            entry["author"] = user_to_dict(message.author)
            entry["attachments"] = [
                {"filename": a.filename, "url": str(a.url)} for a in message.attachments
            ]
            entry["channel"] = {"name": message.channel.name}
            entry["edited_at"] = (
                message.edited_at.isoformat()
                if message.edited_at is not None
                else message.edited_at
            )
            # used for URLs
            entry["embeds"] = [e.to_dict() for e in message.embeds]
            entry["mentions"] = [user_to_dict(mention) for mention in message.mentions]
            entry["channel_mentions"] = [
                {"id": c.id, "name": c.name} for c in message.channel_mentions
            ]
            entry["mention_everyone"] = message.mention_everyone
            entry["reactions"] = [
                {
                    "count": r.count,
                    "emoji": r.emoji
                    if isinstance(r.emoji, str)
                    else {"name": r.emoji.name, "url": str(r.emoji.url)},
                }
                for r in message.reactions
            ]
            chan["messages"].append(entry)

        CTF["channels"].append(chan)
    return CTF


async def save(guild, guild_name, ctf_name, CTF):
    if not os.path.exists("backups"):
        os.mkdir("backups")

    json_file = f"backups/{guild_name} - {ctf_name}.json"
    with open(json_file, "w") as w:
        json.dump(CTF, w)

    bson_file = f"backups/{guild_name} - {ctf_name}.bson"
    with open(bson_file, "wb") as w:
        w.write(bson.BSON.encode(CTF))

    export_channel = config["channels"]["export"]
    for chn in guild.text_channels:
        if chn.name == export_channel:
            await chn.send(files=[discord.File(bson_file), discord.File(json_file)])
            break
    else:
        return [
            (
                None,
                f"Saved JSON, but couldn't find a bot channel `{export_channel}` to upload the CTF archive to",
            )
        ]

    return [
        (
            None,
            f"`{ctf_name}` CTF has been exported. Verify in <#{export_channel}> and execute `!deletectf {ctf_name}`",
        )
    ]


async def delete(guild, channels):
    # TODO: Dirty method to find the roles, we should rather use the role_id directly
    for role in guild.roles:
        role_name = format_role_name(channels[0].name)
        if role_name == role.name.lower():
            await role.delete(reason="exporting CTF")
            break
    for chn in channels:
        await chn.delete(reason="exporting CTF")
    return []
