# igCTF

Copied with permission from nullpxl to make my own modifications. Also merged in changes from the UTCBot fork

[Original Project](https://github.com/NullPxl/NullCTF)

[Invite to your server](https://discordapp.com/oauth2/authorize?client_id=621367108063985667&scope=bot&permissions=268545136)
\
[Join the support server](https://discord.gg/yf8E2s8)

## Install

### develop

```bash
cd cloned-directory
virtualenv venv -p python3
source venv/bin/activate
pip install -r requirements.txt
```

### setup

```
docker volume create mdb
docker volume create mdb_config
```

### build

`docker-comopse up --build`

### start

`docker-compose up`

## How to Use
>### *A [discord.py](http://discordpy.readthedocs.io/en/latest/) bot focused on providing CTF tools for collaboration in Discord servers (ctftime.org commands, team setup + ctfd integration, utilites, etc)!  If you have a feature request, make it a GitHub issue or use the >request "x" command.*

[Invite to your server](https://discordapp.com/oauth2/authorize?client_id=455502163452362753&permissions=268528720&scope=bot)
\
[Join the support server](https://discord.gg/yf8E2s8)

#  How to Use
*If you ever forget a command, use `>help`!*

After inviting to your server, it is recommended that you first configure the categories you want active and archived CTF channels to go into.
* When you create a ctf, it will by default go into the "CTF" category (it will create one if it is not present), and when you archive a ctf it will go into the ARCHIVE category.
* You can configure this with `>config ctf_category "Category for CTFs"` and `>config archive_category "Category for Archived CTFs"` 
---

## CTF Commands

The following commands are the ones you will most likely want to pay attention to, although if you do not expect to use this bot to manage CTFs you can skip this category and go down to CTFTime commands.


> This bot has commands for encoding/decoding, ciphers, and other commonly accessed tools during CTFs. But, the main use for igCTF is to easily set up a CTF for your discord server to play as a team. The following commands listed are probably going to be used the most.

- `>create "ctf name"` This is the command you'll use when you want to begin a new CTF. This command will make a text channel with your supplied name under the category 'CTF' (If the category doesn't exist it will be created). _Must have permissions to manage channels_

_NOTE: the following ctf specific commands will only be accepted under the channel created for that ctf. This is to avoid clashes with multiple ctfs going on in the same server._

- `>ctf join/leave` Using this command will either give or remove the role of a created ctf to/from you.
    ![enter image description here](https://i.imgur.com/4QPUgvM.png)

- `>ctf challenge add/working/solved "challenge name"` Allows users to add challenges to a list, and then set the status of that challenge. _Use quotations_

- `>ctf challenge list` This is the list command that was previously mentioned, it displays the added challenges, who's working on what, and if a challenge is solved (and by who).
    ![enter image description here](https://i.imgur.com/KH5dYZr.png)

- `>ctf end` Delete the ctf info from the db, and remove the role from your server. _Must have permissions to manage channels_

---
 * `>ctf join/leave` Using this command will either give or remove the role of a created ctf to/from you.
 ![ctf join/leave](https://i.imgur.com/R1ktkMv.png)
 
 * `>ctf challenge add/working/solved/remove "challenge"` Allows users to add or remove challenges to a list, and then set the status of that challenge. *Use quotations*

  * `>ctf challenge list` This is the list command that was previously mentioned, it displays the added challenges, who's working on what, and if a challenge is solved (and by who).
 ![desc](https://i.imgur.com/l9jsuLz.png)

  > NOTE: There is shorthand!  challenge -> chal/chall, add -> a, working -> w, solved -> s, remove -> r
 
* `>ctf challenge pull "http(s)://ctfd.url"` Pull challenges and their solved states from a CTFd hosted CTF, and add them to your challenges list.  Requires the username and password to be set with `>ctf setcreds "username" "password"`

* `>ctf setcreds "ctfd username" "password"` Pin the message of ctf credentials, can be fetched by the bot later in order to use `>ctf challenge pull`.  Credentials are never stored outside of Discord.
![ctf pull and setcreds](https://i.imgur.com/Z3e0pE3.png)

* `>ctf creds` Gets the credentials from the pinned message.

> *IMPORTANT: credentials are never stored outside of the pinned message on Discord. They are needed to pull challenge data and solve state from the CTFd platform.*


* `>ctf archive` Move the CTF channel into the Archive category.  *Must have permissions to manage channels*

* `>ctf delete` Delete the CTF info from the database, and delete the role. *Must have permissions to manage channels*

---

## [CTFtime](https://ctftime.org) Commands

> The following commands use the api from [ctftime](https://ctftime.org/api)

- `>ctftime countdown/timeleft` Countdown will return when a selected CTF starts, and timeleft will return when any currently running CTFs end in the form of days hours minutes and seconds.
    ![enter image description here](https://i.imgur.com/LFSTr33.png)
    ![enter image description here](https://i.imgur.com/AkBfp6E.png)

- `>ctftime upcoming <number>` Uses the api mentioned to return an embed up to 5 upcoming CTFs. If no number is provided the default is 3.
    ![enter image description here](https://i.imgur.com/UpouneO.png)

- `>ctftime current` Displays any currently running CTFs in the same embed as previously mentioned.
    ![enter image description here](https://i.imgur.com/RCh3xg6.png)

- `>ctftime top <year>` Shows the ctftime leaderboards from a certain year _(dates back to 2011)_.
    ![enter image description here](https://i.imgur.com/2npW7gM.png)

---

> Utility commands
* `>ctftime top <year>`  Shows the ctftime leaderboards from a certain year *(dates back to 2011)*.
![enter image description here](https://i.imgur.com/jdPWmCV.png)

---
## Utility Commands
* `>help` Returns the help page

* `>magicb filetype` Returns the mime and magicbytes of your supplied filetype. Useful for stegonography challenges where a filetype is corrupt.

* `>rot  "a message"` Returns all 25 possible rotations for a message.

- `>magicb filetype` Returns the mime and magicbytes of your supplied filetype. Useful for stegonography challenges where a filetype is corrupt.

* `>b32 encode/decode "message"` Encode or decode in base32

* `>binary encode/decode "message"` Encode or decode in binary.

- `>b64 encode/decode "message"` Encode or decode in base64 _(at the time of writing this, if there are any unprintable characters this command will not work, this goes for all encoding/decoding commands)._

- `>binary encode/decode "message"` Encode or decode in binary.

- `>hex encode/decode "message"` Encode or decode in hex.

- `>url encode/decode "message"` Encode or decode with url parse. This could be used for generating XSS payloads.

- `>reverse "message"` Reverse a message.

- `>counteach "message"` Count the occurrences of each character in the supplied message.

- `>characters "message"` Count the amount of characters in your message.

- `>wordcount a test` Counts the amount of words in your message (don't use quotations).

- `>htb` Return when the next hackthebox machine is going live from @hackthebox_eu on twitter.

- `>cointoss` Get a 50/50 cointoss to make all your life's decisions.

- `>request/report "a feature"/"a bug"` Dm's the creator with your feature/bug request/report.

# Setup - General Overview
---
General guide for setup, not very detailed currently but I will expand in the future if people actually end up wanting to host locally :P 
* This may be necessary in the future because of Disord's recent [verification requirements](https://support.discordapp.com/hc/en-us/articles/360040720412-Bot-Verification-and-Data-Whitelisting) for bots in over 100 servers (which this bot is already over).  This rule, which will disallow users to invite bots that have not been verified by the owner (which requires photoid) will be enforced starting october 7th. 
```
Create a discord bot on discord's developer portal -> get the bot token -> clone this repo -> install discord.py >= 1.3.3 ->
Create mongodb account -> create project -> create cluster -> create db user -> 
add your ip to db whitelist access -> connect to cluster and select python as driver ->
get connection string and follow mongodb's steps with your password ->
pip install pymongo and dnspython -> use the following template for creating dbs and collections under the file config_vars.py
```
```
# config_vars.py
from pymongo import MongoClient

discord_token = ""
mongodb_connection = ""

client = MongoClient(mongodb_connection)

ctfdb = client['ctftime'] # Create ctftime database
ctfs = ctfdb['ctfs'] # Create ctfs collection

teamdb = client['ctfteams'] # Create ctf teams database

serverdb = client['serverinfo'] # configuration db
```
```
invite the bot to your server
```
