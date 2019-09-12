import enum
import discord, discord.member
from discord.ext import commands
from functools import partial, wraps
from pprint import pprint

from vars.help_info import ctf_help_text, chal_help_text, embed_help
from util import trim_nl

from controllers.db import client, ctfdb, ctfs, teamdb, serverdb, challdb

# Globals
# > done_id
# > archive_id
# > working_id
#
# CtfTeam
# [gid...]
#   > challenges [array of chan IDs]
#   > name
#   > chan_id
#   > role_id
#
# Challenge
# [gid...]
#   > name
#   > ctf_id [int, channel ID]
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

    raise ValueError(f'Cannot find category {name}')

find_category = partial(_find_chan, 'categories')
find_text_channel = partial(_find_chan, 'text_channels')

def load_category(guild, catg):
    gid = guild.id
    # TODO: change name based on guild-local configs
    return find_category(guild, catg)

basic_allow = discord.PermissionOverwrite(add_reactions=True,
        read_messages=True, send_messages=True, read_message_history=True)
basic_disallow = discord.PermissionOverwrite(add_reactions=False,
        read_messages=False, send_messages=False, read_message_history=False)

def chk_upd(ctx_name, update_res):
    if not update_res.matched_count:
        raise ValueError(f'{ctx_name}: Not matched on update')
    if not update_res.modified_count:
        raise ValueError(f'{ctx_name}: Not modified on update')

def chk_del(ctx_name, delete_res):
    if not delete_res.deleted_count:
        raise ValueError(f'{ctx_name}: Not deleted')

def chk_get_role(guild, role_id):
    role = guild.get_role(role_id)
    if not role:
        raise ValueError(f'{role_id}: Invalid role ID')
    return role

def chk_archive(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.is_archived:
            raise TaskFailed('Cannot do that, this is archived')
        return func(self, *args, **kwargs)
    return wrapper


class TaskFailed(commands.UserInputError):
    def __init__(self, msg):
        super().__init__(msg)

class CtfTeam(object):
    __teams__ = {}

    @staticmethod
    async def create(guild, name):
        # Create role
        role = await guild.create_role(name=f'{name}_team', mentionable=True)

        # Create channel
        chan = await guild.create_text_channel(name=name, 
                topic=f'General talk for {name} CTF event.')
        await (await chan.send(trim_nl(f'''Welcome to {name}. Here you can do
        general discussion about this event. Also use this this place to type
        `ctf` related commands. Here is a list of commands just for
        reference:\n\n'''))).pin()
        await (await embed_help(chan, 'CTF team help topic', ctf_help_text)).pin()
        await (await embed_help(chan, 'Challenge help topic', chal_help_text)).pin()

        # Update database
        teamdb[str(guild.id)].insert_one({ \
                'archived': False,
                'name': name, 
                'chan_id': chan.id, 
                'role_id': role.id,
                'chals': []})
        CtfTeam.__teams__[chan.id] = CtfTeam(guild,chan.id)

        return [(None, f'{name} ctf has been created! :tada:')]

    @staticmethod
    def fetch(guild, chan_id):
        if chan_id not in CtfTeam.__teams__:
            if not teamdb[str(guild.id)].find_one({'chan_id': chan_id}):
                return None
            CtfTeam.__teams__[chan_id] = CtfTeam(guild, chan_id)
        else:
            CtfTeam.__teams__[chan_id].refresh()

        #TODO: check guild is same
        return CtfTeam.__teams__[chan_id] 

    def __init__(self, guild, chan_id):
        self.__guild = guild
        self.__chan_id = chan_id
        self.__teams = teamdb[str(guild.id)]
        self.refresh()

    @property
    def challenges(self):
        return [Challenge.fetch(self.__guild, cid) for cid in self.__teamdata['chals']]

    @property
    def name(self):
        return self.__teamdata['name']

    @property
    def chan_id(self):
        return self.__chan_id

    @property
    def guild(self):
        return self.__guild
    
    @property
    def is_archived(self):
        return self.__teamdata.get('archived', False)

    @property
    def mention(self):
        return f'<@&{self.__teamdata["role_id"]}>'

    @property
    def team_data(self):
        return self.__teamdata

    @chk_archive
    async def add_chal(self, name):
        cid = self.__chan_id
        guild = self.__guild
        teams = self.__teams

        catg_working = load_category(guild, 'working')
        if self.find_chal(name, False):
            raise TaskFailed(f'Challenge "{name}" already exists!')

        # Create a secret channel, initially only with us added.
        overwrites = {
            guild.default_role: basic_disallow,
            guild.me: basic_allow
        }
        fullname = f'{self.name}-{name}'
        chan = await catg_working.create_text_channel(name=fullname, overwrites=overwrites)
        Challenge.create(guild, cid, chan.id, name)
        chk_upd(fullname, teams.update_one({'chan_id': cid}, 
            {'$push': {'chals': chan.id}}))
        self.refresh()

        return [(None, trim_nl(f'''Challenge "{name}" has been added! Run `!ctf
        working {name}` join this challenge channel!'''))]
    
    @chk_archive
    async def archive(self):
        cid = self.__chan_id
        guild = self.__guild
        teams = self.__teams

        catg_archive = load_category(guild, 'archive')
        role = chk_get_role(guild, self.__teamdata['role_id'])

        # Update database
        chk_upd(self.name, teams.update_one({'chan_id': cid}, 
            {'$set': {'archived': True, 'role_id': 0}}))
        self.refresh()

        # Archive all challenge channels
        await guild.get_channel(cid).edit(category=catg_archive)
        for chal in self.challenges:
            await chal._archive(catg_archive)

        # Delete role
        await role.delete()

        return [(None, f'@here {self.name} CTF has been archived.')]

    async def unarchive(self):
        cid = self.__chan_id
        guild = self.__guild
        teams = self.__teams

        catg_working = load_category(guild, 'working')
        catg_done = load_category(guild, 'done')

        #if not self.is_archived:
        #    raise TaskFailed('This is already not archived!')

        # Create role
        role = await guild.create_role(name=f'{self.name}_team', mentionable=True)

        # Update database
        chk_upd(self.name, teams.update_one({'chan_id': cid}, 
            {'$set': {'archived': False, 'role_id': role.id}}))
        self.refresh()

        # Unarchive all challenge channels
        await guild.get_channel(cid).edit(category=None, position=0)
        for chal in self.challenges:
            await chal._unarchive(catg_working, catg_done)

        return [(cid, f'@here {self.name} CTF has been unarchived.')]


    @chk_archive
    async def del_chal(self, name):
        cid = self.__chan_id
        guild = self.__guild
        teams = self.__teams

        catg_archive = load_category(guild, 'archive')

        # Update database
        fullname = f'{self.name}-{name}'
        chal = self.find_chal(name)
        pprint(chal)
        chk_upd(fullname, teams.update_one({'chan_id': cid}, 
            {'$pull': {'chals': chal['chan_id']}}))
        await chal._delete(catg_archive)
        self.refresh()

        return [(None, f'Challenge "{name}" is deleted, challenge channel archived.')]

    def find_chal(self, name, err_on_fail=True):
         Challenge.find(self.__guild, self.__chan_id, name, err_on_fail)

    @chk_archive
    async def invite(self, author, user):
        cid = self.__chan_id
        guild = self.__guild
        teams = self.__teams
        team = self.__teamdata

        # Add role for user
        role = chk_get_role(guild, team['role_id'])
        if role in user.roles:
            raise TaskFailed(f'{user.mention} has already joined {self.name}')
        await user.add_roles(role)

        return [(None, f'{author.mention} invited {user.mention} to the "{self.name}" team')]

    @chk_archive
    async def join(self, user):
        cid = self.__chan_id
        guild = self.__guild
        teams = self.__teams
        team = self.__teamdata

        # Add role for user
        role = chk_get_role(guild, team['role_id'])
        if role in user.roles:
            raise TaskFailed(f'{user.mention} has already joined {self.name}')
        await user.add_roles(role)

        return [(None, f'{user.mention} has joined the {self.name} team! :sparkles:')]
    
    @chk_archive
    async def leave(self, user):
        cid = self.__chan_id
        guild = self.__guild
        teams = self.__teams

        team = self.__teamdata
        
        # Remove role for user
        role = chk_get_role(guild, team['role_id'])
        if role not in user.roles:
            raise TaskFailed(f'{user.mention} is not in {team["name"]}')
        await user.remove_roles(role)

        return [(None, f'{user.mention} has left the {team["name"]} team...')]

    def refresh(self):
        team = self.__teams.find_one({'chan_id': self.__chan_id})
        if not team:
            raise ValueError(f'{self.__chan_id}: Invalid CTF channel ID')
        self.__teamdata = team

class Challenge(object):
    __chals__ = {}

    @staticmethod
    def create(guild, ctf_id, chan_id, name):
        chals = challdb[str(guild.id)]
        chals.insert_one({'name': name, 'ctf_id': ctf_id, 'finished': False,
            'solvers': [], 'chan_id': chan_id, 'owner': 0})

        chal = Challenge(guild, chan_id)
        Challenge.__chals__[chan_id] = chal
        return chal

    @staticmethod
    def fetch(guild, chan_id):
        if chan_id not in Challenge.__chals__:
            chal = challdb[str(guild.id)].find_one({'chan_id': chan_id})
            if not chal:
                return None
            Challenge.__chals__[chan_id] = Challenge(guild, chan_id)
        chal = Challenge.__chals__[chan_id]
        chal.refresh()
        return chal

    @staticmethod
    def find(guild, ctfid, name, err_on_fail=True):
        chal = challdb[str(guild.id)].find_one({'name': name, 'ctf_id': ctfid})
        if chal:
            return Challenge.fetch(guild, chal['chan_id'])
        elif err_on_fail:
            raise TaskFailed(f'Challenge "{name}" does not exist!')
        else:
            return None

    def __init__(self, guild, chan_id):
        self.__guild = guild
        self.__id = chan_id
        self.__chals = challdb[str(guild.id)]
        self.refresh()

    @property
    def chan_id(self):
        return self.__id

    @property
    def ctf_id(self):
        return self.__chalinfo['ctf_id']

    @property
    def is_archived(self):
        return self.__chalinfo.get('archived', False)

    @property
    def is_finished(self):
        return self.__chalinfo['finished']

    @property
    def name(self):
        return self.__chalinfo['name']

    @property
    def owner(self):
        return self.__chalinfo['owner']

    @property
    def solver_ids(self):
        if not self.is_finished:
            return
        return self.__chalinfo['solvers']

    @property
    def solver_users(self):
        if not self.is_finished:
            return
        return list(map(self.__guild.get_member, self.solver_ids))

    @property
    def status(self):
        if self.is_finished:
            solvers = ', '.join(user.name for user in self.solver_users)
            return f'Solved by {solvers}'
        else:
            return 'Unsolved'

    @property
    def team(self):
        return CtfTeam.fetch(self.__guild, self.ctf_id)

    async def _archive(self, catg_archive):
        cid = self.__id
        guild = self.__guild
        chk_upd(self.name, self.__chals.update_one({'chan_id': cid}, {"$set": { \
                'archived': True}}))
        await guild.get_channel(cid).edit(category=catg_archive)
        self.refresh()

    async def _unarchive(self, catg_working, catg_done):
        cid = self.__id
        guild = self.__guild
        chk_upd(self.name, self.__chals.update_one({'chan_id': cid}, {"$set": { \
                'archived': False}}))
        await guild.get_channel(cid).edit(category=(catg_working,
            catg_done)[self.is_finished])
        self.refresh()

    def check_done(self, user):
        if not self.is_finished or Challenge._uid(user) == self.owner:
            return
        
        guild = self.__guild
        if not guild.get_channel(self.__id).permissions_for(user).manage_channels:
            raise commands.MissingPermissions('manage_channels')        

    async def _delete(self, catg_archive):
        cid = self.__id

        # Delete entry
        chk_del(self.name, self.__chals.delete_one({'chan_id': self.__id}))
        del Challenge.__chals__[self.__id]

        # Archive channel
        await self.__guild.get_channel(cid).edit(category=catg_archive)

    @chk_archive
    async def done(self, owner, users):
        cid = self.__id
        guild = self.__guild

        catg_done = load_category(guild, 'done')

        # Create list of solvers
        owner = Challenge._uid(owner)
        users = [Challenge._uid(u) for u in users]
        users.append(owner)
        users = list(set(users))
        users.sort()
        mentions = [f'<@{uid}>' for uid in users]
        
        # Check if it is solved already
        if self.is_finished:
            old_solvers = self.solver_ids
            old_solvers.sort()
            if old_solvers == users:
                raise TaskFailed('This task is already solved with same users')

        # Update database
        chk_upd(self.name, self.__chals.update_one({'chan_id': cid}, {"$set": { \
            'finished': True, 
            'owner': owner,
            'solvers': users }}))

        # Move channel to done
        await guild.get_channel(cid).edit(category=catg_done)

        mentions = ' '.join(mentions)
        self.refresh()
        return [ \
            (self.ctf_id, trim_nl(f'''{self.team.mention} :tada: "{self.name}" has
                been completed by {mentions}!''')), 
            (None, f'Challenge moved to done!')]

    @chk_archive
    async def invite(self, author, user):
        ccid = self.team.chan_id
        cid = self.__id
        guild = self.__guild
        chan = guild.get_channel(self.__id)
        
        if user in chan.overwrites:
            raise TaskFailed(f'{user.name} is already in the "{self.name}" challenge')

        await chan.set_permissions(user, overwrite=basic_allow, 
                reason=f'{author.name} invited user to work on "{self.name}" challenge')
        return [(ccid, f'{author.mention} invited {user.mention} to work on "{self.name}" challenge')]

    @chk_archive
    async def leave(self, user):
        ccid = self.team.chan_id
        cid = self.__id
        guild = self.__guild
        chan = guild.get_channel(self.__id)
        await chan.set_permissions(user, overwrite=None, 
                reason=f'Left "{self.name}" challenge')
        return [(ccid, f'{user.mention} has left "{self.name}" challenge')]

    def refresh(self):
        cid = self.__id
        chal = self.__chals.find_one({'chan_id': cid})
        if not chal:
            raise ValueError(f'{cid}: Invalid challenge channel ID')
        self.__chalinfo = chal

    @chk_archive
    async def undone(self):
        cid = self.__id
        guild = self.__guild

        catg_working = load_category(guild, 'working')

        if not self.is_finished:
            raise TaskFailed('This ctf challenge has not been completed yet')

        # Update database
        chk_upd(self.name, self.__chals.update_one({'chan_id': cid}, 
            {"$set": {'finished': False}}))

        # Move channel to working
        await guild.get_channel(cid).edit(category=catg_working)

        self.refresh()
        return [(None, f'Reopened "{self.name}" as not done'), 
                (self.ctf_id, trim_nl(f'''{self.team.mention} "{self.name}" is
                now undone. :weary:'''))]

    @chk_archive
    async def working(self, user):
        ccid = self.team.chan_id
        cid = self.__id
        guild = self.__guild
        chan = guild.get_channel(self.__id)
        if user in chan.overwrites:
            raise TaskFailed(f'{user.name} is already in the "{self.name}" challenge')
        await chan.set_permissions(user, overwrite=basic_allow, 
                reason=f'Working on "{self.name}" challenge')
        return [(ccid, f'{user.mention} is working on "{self.name}" challenge')]

    @staticmethod
    def _uid(user):
        if type(user) is str:
            return int(user)
        elif type(user) is int:
            return user
        elif type(user) is discord.member.Member:
            return user.id
        else:
            raise ValueError(f'Cannot convert to user: {user}')

