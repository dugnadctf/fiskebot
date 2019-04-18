import enum
import discord, discord.member
from discord.ext import commands
from functools import partial

from trim import trim_nl
from .mongo import *

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

    raise ValueError(f'Cannot find {name}')

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

class TaskFailed(commands.UserInputError):
    def __init__(self, msg):
        super().__init__(msg)

class CtfTeam(object):
    __teams__ = {}

    @staticmethod
    async def create(guild, name, chan_id, role_id):
        teamdb[str(guild.id)].insert_one({ \
                'name': name, 
                'chan_id': chan_id, 
                'role_id': role_id,
                'chals': []})

        CtfTeam.__teams__[chan_id] = CtfTeam(guild,chan_id)
        return [(None, f'{name} ctf has been created! :tada:')]

    @staticmethod
    def fetch(guild, chan_id):
        if chan_id not in CtfTeam.__teams__:
            if not teamdb[str(guild.id)].find_one({'chan_id': chan_id}):
                return None
            CtfTeam.__teams__[chan_id] = CtfTeam(guild, chan_id)
        #TODO: check guild is same
        return CtfTeam.__teams__[chan_id] 

    def __init__(self, guild, chan_id):
        self.__guild = guild
        self.__chan_id = chan_id
        self.__chals = chaldb[str(guild.id)]
        self.__teams = teamdb[str(guild.id)]

    @property
    def challenges(self):
        return [Challenge.fetch(self.__guild, cid) for cid in self.team_data['chals']]

    @property
    def name(self):
        return self.team_data['name']

    @property
    def chan_id(self):
        return self.__chan_id

    @property
    def guild(self):
        return self.__guild
    
    @property
    def mention(self):
        return f'<@&{self.team_data["role_id"]}>'

    @property
    def team_data(self):
        team = self.__teams.find_one({'chan_id': self.__chan_id})
        if not team:
            raise ValueError(f'{cid}: Invalid CTF channel ID')
        return team

    async def add_chal(self, name):
        cid = self.__chan_id
        guild = self.__guild
        chals = self.__chals
        teams = self.__teams

        # Discord replaces spaces with dashes
        name = name.replace(' ', '-').lower()

        catg_working = load_category(guild, 'working')
        if chals.find_one({'name': name, 'ctf_id': cid}):
            raise TaskFailed(f'Challenge "{name}" already exists!')

        # Create a secret channel, initially only with us added.
        overwrites = {
            guild.default_role: basic_disallow,
            guild.me: basic_allow
        }
        fullname = f'{self.name}-{name}'
        chan = await catg_working.create_text_channel(name=fullname, overwrites=overwrites)
        chals.insert_one({'name': name, 'ctf_id': cid, 'finished': False,
            'solvers': [], 'chan_id': chan.id, 'owner': 0})
        chk_upd(f'{cid}/{name}', teams.update_one({'chan_id': cid}, 
            {'$push': {'chals': chan.id}}))

        return [(None, trim_nl(f'''Challenge "{name}" has been added! Run `!ctf
        working {name}` join this challenge channel!'''))]

    async def del_chal(self, name):
        cid = self.__chan_id
        guild = self.__guild
        chals = self.__chals
        teams = self.__teams

        catg_archive = load_category(guild, 'archive')

        filt = {'name': name, 'ctf_id': cid}
        chal = chals.find_one({'name': name, 'ctf_id': cid})
        if not chal:
            raise TaskFailed(f'Challenge "{name}" does not exist!')

        chk_upd(f'{cid}/{name}', teams.update_one({'chan_id': cid}, 
            {'$pull': {'chals': chal['chan_id']}}))
        chk_del(name, chals.delete_one(chal))
        
        # TODO: update name as well
        await guild.get_channel(chal['chan_id']).edit(category=catg_archive)

        return [(None, f'Challenge "{name}" is deleted, challenge channel archived.')]
    
    async def archive(self):
        # TODO:
        raise TaskFailed(f'TODO!!!')


    async def join(self, user):
        cid = self.__chan_id
        guild = self.__guild
        teams = self.__teams

        team = self.team_data

        # Then add role for user
        role = guild.get_role(team['role_id'])
        if not role:
            raise ValueError(f'{team["role_id"]}: Invalid role ID')
        if role in user.roles:
            raise TaskFailed(f'{user.mention} has already joined {team["name"]}')
        await user.add_roles(guild.get_role(team['role_id']))

        return [(None, f'{user.mention} has joined the {team["name"]} team! :sparkles:')]
    
    async def leave(self, user):
        cid = self.__chan_id
        guild = self.__guild
        teams = self.__teams

        team = self.team_data
        
        # Then remove role for user
        role = guild.get_role(team['role_id'])
        if not role:
            raise ValueError(f'{team["role_id"]}: Invalid role ID')
        if role not in user.roles:
            raise TaskFailed(f'{user.mention} is not in {team["name"]}')
        await user.remove_roles(guild.get_role(team['role_id']))

        return [(None, f'{user.mention} has left the {team["name"]} team...')]


    def find_chal(self, name):
        return Challenge.find(self.__guild, self.__chan_id, name)


class Challenge(object):
    __chals__ = {}

    @staticmethod
    def fetch(guild, chan_id):
        if chan_id not in Challenge.__chals__:
            chal = chaldb[str(guild.id)].find_one({'chan_id': chan_id})
            if not chal:
                return None
            Challenge.__chals__[chan_id] = Challenge(guild, chan_id)
        chal = Challenge.__chals__[chan_id]
        chal.refresh()
        return chal

    @staticmethod
    def find(guild, ctfid, name):
        chal = chaldb[str(guild.id)].find_one({'name': name, 'ctf_id': ctfid})
        if chal:
            return Challenge.fetch(guild, chal['chan_id'])
        else: 
            raise TaskFailed(f'Challenge "{name}" does not exist!')

    def __init__(self, guild, chan_id):
        self.__guild = guild
        self.__id = chan_id
        self.__chalinfo = None
        self.__chals = chaldb[str(guild.id)]

    @property
    def chan_id(self):
        return self.__id

    @property
    def ctf_id(self):
        return self.__chalinfo['ctf_id']

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

    def check_done(self, user):
        if not self.is_finished or Challenge._uid(user) == self.owner:
            return
        
        guild = self.__guild
        if not guild.get_channel(self.__id).permissions_for(user).manage_channels:
            raise commands.MissingPermissions('manage_channels')        


    async def working(self, user):
        ccid = self.team.chan_id
        cid = self.__id
        guild = self.__guild
        chan = guild.get_channel(self.__id)
        await chan.set_permissions(user, overwrite=basic_allow, 
                reason=f'Working on "{self.name}" challenge')
        return [(ccid, f'{user.mention} is working on "{self.name}" challenge')]

    async def leave(self, user):
        ccid = self.team.chan_id
        cid = self.__id
        guild = self.__guild
        chan = guild.get_channel(self.__id)
        await chan.set_permissions(user, overwrite=basic_disallow, 
                reason=f'Left "{self.name}" challenge')
        return [(ccid, f'{user.mention} has left "{self.name}" challenge')]


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

    def refresh(self):
        cid = self.__id
        chal = self.__chals.find_one({'chan_id': cid})
        if not chal:
            raise ValueError(f'{cid}: Invalid challenge channel ID')
        self.__chalinfo = chal

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

