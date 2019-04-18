import requests
import re
import random
from string import *

help_page = '''
Adapted from: https://github.com/NullPxl/NullCTF

`!ctftime <upcoming/current> <number>`
return info on a number of upcoming ctfs, or currently running ctfs from ctftime.org (number param is just for upcoming)

`!ctftime <countdown/timeleft>`
return specific times for the time until a ctf begins, or until a currently running ctf ends.

`!ctftime top <year>`
display the leaderboards from ctftime from a certain year.

`!create_ctf "<ctf name>"`
create a text channel and role in the CTF category for a ctf (must have permissions to manage channels).

`!ctf <action>...`
Does various actions in a CTF team context. You can issue these commands in a channel that was created by the `!create_ctf` command. See `!ctf help` for more details.

`!chal <action>...`
Does various actions in a challenge context. You can issue these commands in a channel that was created by the `!ctf add` command. See `!chal help` for more details.

`!htb`
return the latest tweet from @hackthebox_eu that says when the next box will be released

*next page is utility commands*

**page: 1/2 - (!help 1)**
'''

help_page_2 = '''


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
count the occurences of each character in the supplied message - if message has spaces use quotations

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
'''

ctf_help_text = '''
These commands are callable from a CTF **team** channel environment.

`!ctf working <chal>`
Mark that you are working on this challenge. You will also be invited to the respective private channel 

`!ctf <join/leave>`
Gets/gets rid of the CTF role created with this CTF team.

`!ctf add "<chal>"`
Add a challenge and a respective private channel. There are certain restrictions on the challenge name (i.e. no special characters, less than 32 characters long, etc...)

`!ctf del "<chal>"`
Remove a challenge (must be able to manage channels). This will NOT automatically delete the respective private channel (if deemed necessary, an admin will manually delete it).

`!ctf archive`
Archives this ctf and all the respective challenges (must be able to manage channels)

'''

chal_help_text = '''
These commands are callable from a CTF **challenge** environment.

`!chal done [<with_users...>]`
Marks this challenge as completed. You may optionally include @'s of users that worked with you. Once a challenge is completed, **no** one except you (and admins) can tamper with the done list or change it to "undone". This will also move the channel to the "done" category.

`!chal undone`
Marks this challenge as **not** completed. This will move the channel back to the "working" category.

'''

# TODO: update it
src = "https://github.com/NullPxl/NullCTF"
creator_info = "https://youtube.com/nullpxl\nhttps://github.com/nullpxl\nhttps://twitter.com/nullpxl"
