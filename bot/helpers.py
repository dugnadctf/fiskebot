from config import config
from constants import SOURCE_FORK1, SOURCE_FORK2, SOURCE_FORK3, SOURCE_FORK4

core = f"""
Fork from: {SOURCE_FORK4}
Who again forked from {SOURCE_FORK3}
Who again forked from {SOURCE_FORK2}
Who again forked from {SOURCE_FORK1}

`!create <ctf name>`
Create a text channel and role in the CTF category for a specified `ctf name`.
(This requires the bot has manage channels permissions)

`!help ctf`
List CTF commands.

`!help challenges`
List CTF challenge specific commands.

`!ctftime`
List CTFtime commands.

`!source`
Display source information
""".replace(
    "!", config["prefix"]
)

# ctf = """
# These commands are callable from a main CTF channel.

# `!add <challenge name>`
# Add a `challenge` and a respective channel. Challenge names may be altered to meet Discord restrictions.
# (i.e. no special characters, less than 32 characters long, etc...)

# `!delete <challenge name>`
# Remove a challenge (this requires the bot has manage channels permissions).
# This will **not** automatically delete the respective private channel. Server staff can remove manually if required.

# `!join <ctf name>`
# Join a CTF by its name, can be used instead of reactions.

# `!leave`
# Leave the CTF team and all of the respective challenge channels.

# `!invite <user>`
# Invites a user to CTF team - `user` is granted the CTF role.

# `!archive`
# Archives this CTF and all the respective challenges (this requires the bot has manage channels permissions).

# `!unarchive`
# Unarchives this CTF and all the respective challenges (this requires the bot has manage channels permissions).

# `!status`
# Lists the status (unsolved, or solved and by whom) of each challenge in the CTF.

# `!deletectf <ctf name>`
# Deletes the CTF and it's challenge channels, provide the CTF name as an argument to this command
# """.replace(
#     "!", config["prefix"]
# )

ctf = """
These commands are callable from a CTF channel.

`!add <challenge name>`
Add a `challenge` and a respective thread.

`!delete <challenge name>`
Remove a challenge (this requires the bot has manage channels permissions).
This will **not** automatically delete the respective private thread. Server staff can remove manually if required.

`!join <ctf name>`
Join a CTF by its name, can be used instead of reactions.

`!leave`
Leave the CTF team and all of the respective challenge channels.

`!invite <user>`
Invites a user to CTF team - `user` is granted the CTF role.

`!archive`
Archives this CTF and all the respective challenges (this requires the bot has manage channels permissions).

`!unarchive`
Unarchives this CTF and all the respective challenges (this requires the bot has manage channels permissions).

`!status`
Lists the status (unsolved, or solved and by whom) of each challenge in the CTF.
Add unsolved as an argument to list only unsolved challenges

`!deletectf <ctf name>`
Deletes the CTF, provide the CTF name as an argument to this command

`!working`
Lists which team members are working which challenge. Only applicable if REACT_FOR_CHALLENGE is True.
""".replace(
    "!", config["prefix"]
)

challenge = """
These commands are callable from a CTF **challenge** environment.

`!done @user1 @user2 ...`
Marks this challenge as completed, and changes the thread emoji. You may optionally include @'s of `users` that worked with you.
Once a challenge is completed, **no one** except you (and admins) can alter the done list or change the status to "undone".

`!undone`
Marks this challenge as **not** completed. This will change the thread emoji.
""".replace(
    "!", config["prefix"]
)

# TODO: add export helper


helpers = {
    "core": {
        "title": "Help for core commands",
        "text": core,
    },
    "ctf": {
        "title": "Help for CTF main commands",
        "text": ctf,
    },
    "challenge": {
        "title": "Help for CTF challenge commands",
        "text": challenge,
    },
}
