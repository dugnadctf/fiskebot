![UTCBot](/images/bot2.png |  width=100)

# UTCBot

>### A [discord.py](http://discordpy.readthedocs.io/en/latest/) bot focused on
 providing CTF tools for collaboration in Discord servers (ctftime.org commands,
 team setup, utilites, etc)!  If you have a feature request, make it a GitHub
 issue or use the !request "x" command.

This is a fork of the Nullctf Bot, as used by the recently created Texas-based
team: UTC!

[Invite to your server](https://discordapp.com/api/oauth2/authorize?client_id=565011034948239390&permissions=268548208&scope=bot) 

[Join the support server](https://discord.gg/x5TJTje)

# How to Use

>This bot has commands for encoding/decoding, ciphers, and other commonly
 accessed tools during CTFs.  But, the main use for NullCTF is to easily set up
 a CTF for your discord server to play as a team.  The following commands listed
 are probably going to be used the most.

* `!create_ctf "ctf name"`  This is the command you'll use when you want to
  begin a new CTF.  This command will make a text channel with your supplied
  name under the category 'CTF' (If the category doesn't exist it will be
  created). (The lather part is still a TODO...) In addition, the bot will also
  post and pin messages for help topics with the interaction between the bot.
  *Must have permissions to manage channels*

  ![Creating CTF](/images/create.png)

## CTF context-specific commands

Once a CTF has a been created, the following commands can be run on the
specifically created channel for that CTF. *This is to avoid clashes with
multiple ctfs going on in the same server.*

 * `!ctf join/leave` Using this command will either give or remove the role of a
   created ctf to/from you.
 
 ![Joining/leaving](/images/join.png)

 * `!ctf add/delete "challenge"` Allows users to add or remove challenges. This
   will also associate a respective private channel to that challenge.
   Challenges created will be defaulted into the `working` category. Use
   quotations for multi-word challenge names. *Must have permissions to manage
   channels in order to delete challenges!*

 ![Adding a challenge](/images/adding.png)
 
 * `!ctf invite <user>` Pings and invites a user to the CTF.

 * `!ctf working "challenge"` Marks the user as "working" on a particular
   challenge. This invites the user to the respective private channel for that
   challenge. (Without this, the user would not be able to see the challenge
   channel unless he/she is an admin).
 
 ![Working on a challenge](/images/working.png)
 
 * `!ctf challenge list` This is the list command that was previously mentioned,
   it displays the added challenges, who's working on what, and if a challenge
   is solved (and by who).

 ![List of challenges](/images/list.png)

 * `!ctf archive/unarchive` Archives all channels associated with the ctf or any
   of the challenges and moves them into the archive category. (Note that there
   is a 50 channel limit to a category, so once that is reached, the bot will
   just fail for now...) *Must have permissions to manage channels*

## Challenge context-specific commands

Once a challenge has been created for a CTF, the following commands can be run
on the specifically created channel for that challenge. 

 * `!chal done [with-users....]` Marks a challenge as finished. This will move
   the challenge into the `done` category. If multiple people worked together to
   complete a challenge, additional users can be tacked after the done command,
   separated by spaces. Only the user who marked it as done (or admins with
   manage channels permission) can modify dones. Here is how it is displayed on
   the challenge channel:

 ![Done with a challenge!](/images/done.png)

   And the CTF channel.

 ![Ctf channel --- done](/images/done2.png)

 * `!chal undone` Marks a finished challenge as not done. Again only the user
   who has marked it as done, or an admin can make this move.

 * `!chal invite <user>` Invites a user to join this challenge channel.

## CTFTime API

The following commands use the api from [ctftime](https://ctftime.org/api)

 * `!ctftime countdown/timeleft` Countdown will return when a selected CTF
   starts, and timeleft will return when any currently running CTFs end in the
   form of days hours minutes and seconds.

 ![enter image description here](https://i.imgur.com/LFSTr33.png)  

 ![enter image description here](https://i.imgur.com/AkBfp6E.png)

* `!ctftime upcoming <number>` Uses the api mentioned to return an embed up to 5
  upcoming CTFs.  If no number is provided the default is 3.

![enter image description here](https://i.imgur.com/UpouneO.png)

* `!ctftime current` Displays any currently running CTFs in the same embed as
  previously mentioned.

![enter image description here](https://i.imgur.com/RCh3xg6.png)

* `!ctftime top <year>`  Shows the ctftime leaderboards from a certain year
  *(dates back to 2011)*.

![enter image description here](https://i.imgur.com/2npW7gM.png)

## Utility commands

* `!magicb filetype` Returns the mime and magicbytes of your supplied filetype.
  Useful for stegonography challenges where a filetype is corrupt.

* `!rot  "a message" <right/left>` Returns all 25 possible rotations for a
  message with an optional direction (defaults to left).

* `!b64 encode/decode "message"`  Encode or decode in base64 *(at the time of
  writing this, if there are any unprintable characters this command will not
  work, this goes for all encoding/decoding commands).*

* `!binary encode/decode "message"` Encode or decode in binary.

* `!hex encode/decode "message"` Encode or decode in hex.

* `!url encode/decode "message"` Encode or decode with url parse.  This could be
  used for generating XSS payloads.

* `!reverse "message"` Reverse a message.

* `!counteach "message"` Count the occurrences of each character in the supplied
  message.

* `!characters "message"` Count the amount of characters in your message.

* `!wordcount a test` Counts the amount of words in  your message (don't use
  quotations).

* `!htb` Return when the next hackthebox machine is going live from
  @hackthebox_eu on twitter.

* `!cointoss` Get a 50/50 cointoss to make all your life's decisions.

* `!request/report "a feature"/"a bug"` Dm's the creator with your feature/bug
  request/report.

* `!help pagenumber` Returns the help page of your supplied number (currently
  there are 2 pages)

Have a feature request?  Make a GitHub issue or use the \>request command.


