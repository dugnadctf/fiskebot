import discord


src = "https://github.com/NullPxl/NullCTF"
src_fork = "https://gitlab.com/inequationgroup/igCTF"
creator_info = """https://blog.inequationgroup.com/
https://gitlab.com/inequationgroup
https://ctftime.org/team/59772"""

help_page = f"""
Adapted from: https://github.com/NullPxl/NullCTF

`!ctftime <current/upcoming <number>>`
Returns info on ongoing CTFs from ctftime.org, or displays the `number` of upcoming events.

`!ctftime <countdown/timeleft>`
Returns remaining time until an upcoming CTF begins, or ongoing event ends.

`!ctftime top <year>`
Display the leader boards from ctftimeorg for a specified `year`.

`!create "<ctf name>"`
Create a text channel and role in the CTF category for a specified `ctf name`.
(This requires the bot has manage channels permissions)

`!ctf <action>...`
You can only issue these commands in a channel that was created by the `!create` command.
See `!ctf help` for more details.

`!chal <action>...`
You can only issue these commands in a channel that was created by the `!ctf add` command.
See `!chal help` for more details.

`!htb`
return the latest tweet from @hackthebox_eu that says when the next box will be released.

*next page is utility commands*

**page: 1/2 - (!help 1)**
"""

help_page_2 = """


`!rot <message> <direction(optional, will default to left)>`
return all 25 different possible combinations for the popular caesar cipher - use quotes for messages more than 1 word

`!magicb <filetype>`
return the magicbytes/file header of a supplied filetype.

`!b64 <encode/decode> <message>`
encode or decode in base64 - if message has spaces use quotations

`!binary <encode/decode> <message>`
encode or decode in binary - if message has spaces use quotations

`!hex <encode/decode> <message>`
encode or decode in hex - if message has spaces use quotations

`!url <encode/decode> <message>`
encode or decode based on url encoding - if message has spaces use quotations

`!reverse <message>`
reverse the supplied string - if message has spaces use quotations

`!counteach <message>`
count the occurrences of each character in the supplied message - if message has spaces use quotations

`!characters <message>`
count the amount of characters in your supplied message

`!wordcount <phrase>`
count the amount of words in your supplied message

`!atbash <message>`
encode or decode in the atbash cipher - if message has spaces use quotations (encode/decode do the same thing)

`!github <user>`
get a direct link to a github profile page with your supplied user

`!twitter <user>`
get a direct link to a twitter profile page with your supplied user

`!cointoss`
get a 50/50 cointoss to make all your life's decisions

`!amicool`
for the truth

`!report <"an issue">`
report an issue you found with the bot, if it is helpful your name will be added to the 'cool names' list!

**page: 2/2 - (!help 2)** ; more commands and documentation viewable on the github page (>source)
"""

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
