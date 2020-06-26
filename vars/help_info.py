import discord

src = "https://github.com/NullPxl/NullCTF"
src_fork = "https://gitlab.com/inequationgroup/igCTF"
creator_info = """https://blog.inequationgroup.com/
https://gitlab.com/inequationgroup
https://ctftime.org/team/59772"""

ctf_help_text = """
These commands are callable from a CTF **team** channel environment.

`!ctf add "<challenge>"`
Add a `challenge` and a respective private channel. Challenge names may be altered to meet Discord restrictions.
(i.e. no special characters, less than 32 characters long, etc...)

`!ctf invite <user>`
Invites a user to CTF team - `user` is granted the CTF role.

`!ctf delete "<challenge>"`
Remove a challenge (this requires the bot has manage channels permissions).
This will **not** automatically delete the respective private channel. Server staff can remove manually if required.

`!ctf archive`
Archives this ctf and all the respective challenges (this requires the bot has manage channels permissions).

`!ctf unarchive`
Unarchives this ctf and all the respective challenges (this requires the bot has manage channels permissions).

"""

chal_help_text = """
These commands are callable from a CTF **challenge** environment.

`!chal done [<users>]`
Marks this challenge as completed, and moves channel to "done" category. You may optionally include @'s of `users` that worked with you.
Once a challenge is completed, **no one** except you (and admins) can alter the done list or change reset the status to "undone".

`!chal invite <user>`
Invites a `user` to a challenge channel.

`!chal undone`
Marks this challenge as **not** completed. This will move the channel back to the "working" category.

"""

async def embed_help(chan, help_topic, help_text):
    emb = discord.Embed(description=help_text, colour=4387968)
    emb.set_author(name=help_topic)
    return await chan.send(embed=emb)