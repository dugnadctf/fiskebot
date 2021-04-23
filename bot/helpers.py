from config import config
from constants import SOURCE_FORK1, SOURCE_FORK2, SOURCE_FORK3

core = f"""
Fork from: {SOURCE_FORK3}
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

ctf = """
These commands are callable from a main CTF channel.

`!add <challenge name>`
Add a `challenge` and a respective channel. Challenge names may be altered to meet Discord restrictions.
(i.e. no special characters, less than 32 characters long, etc...)

`!delete <challenge name>`
Remove a challenge (this requires the bot has manage channels permissions).
This will **not** automatically delete the respective private channel. Server staff can remove manually if required.

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
""".replace(
    "!", config["prefix"]
)

# TODO: add export helper

challenge = """
These commands are callable from a CTF **challenge** environment.

`!done @user1 @user2 ...`
Marks this challenge as completed, and moves channel to "done" category. You may optionally include @'s of `users` that worked with you.
Once a challenge is completed, **no one** except you (and admins) can alter the done list or change reset the status to "undone".

`!undone`
Marks this challenge as **not** completed. This will move the channel back to the "working" category.
""".replace(
    "!", config["prefix"]
)

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
