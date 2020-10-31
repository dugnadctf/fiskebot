# EPTbot

This bot is still work in process. It is a fork of [igCTF](https://gitlab.com/inequationgroup/igCTF), which is again a fork of [NullCTF](https://github.com/NullPxl/NullCTF).

## Install

Firstly, edit the `/bot/config.py`. Most important is to fill inn the bot token.

### develop

The `/bot` folder is mounted into the container, so you just need to restart to get your updated changes.
```bash
docker-compose build
docker-compose up # ctrl-c to stop and run up again to restart
```

### start

`docker-compose up --build -d`

## How to Use

> The main use for eptbot is to easily set up a CTF for your discord server to play as a team. The following commands listed are probably going to be used the most.

- `!help` Display the main help commands.

- `!create "ctf name"` This is the command you'll use when you want to begin a new CTF. This command will make a text channel with your supplied name. The bot will also send a message in chat where members can react to join the CTF.

- `!ctf add <challenge name>` This will create a new channel for a given challenge.

- `!chal done [users ...]` Mark a challenge as done. Needs to be done inside the challenge channel. Optionally specify other users who also contributed to solving the challenge, space separated without the @s.

- `!ctf archive` Mark the ctf as over and move it to the archive categories (specified in `/bot/config.py`).

---

> The following commands use the api from [ctftime](https://ctftime.org/api)

- `!ctftime countdown/timeleft` Countdown will return when a selected CTF starts, and timeleft will return when any currently running CTFs end in the form of days hours minutes and seconds.
    ![enter image description here](https://i.imgur.com/LFSTr33.png)
    ![enter image description here](https://i.imgur.com/AkBfp6E.png)

- `!ctftime upcoming <number>` Uses the api mentioned to return an embed up to 5 upcoming CTFs. If no number is provided the default is 3.
    ![enter image description here](https://i.imgur.com/UpouneO.png)

- `!ctftime current` Displays any currently running CTFs in the same embed as previously mentioned.
    ![enter image description here](https://i.imgur.com/RCh3xg6.png)

- `!ctftime top <year>` Shows the ctftime leaderboards from a certain year _(dates back to 2011)_.
    ![enter image description here](https://i.imgur.com/2npW7gM.png)

- `!ctftime team [team name/id]` Display the top 10 events a team have gotten points for this year.

> ### Have a feature request? Make a GitHub issue.
