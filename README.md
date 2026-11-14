# fiskebot
![](images/fiskebot_logo.png)

This bot is still work in process. It is a fork of [eptbot](https://github.com/ept-team/eptbot), which is again a fork of [igCTF](https://gitlab.com/inequationgroup/igCTF), which is again a fork of [NullCTF](https://github.com/NullPxl/NullCTF).

## Install

Configuration is done through environment variables. They can be defined in an `.env` file, or used directly, see [here](https://docs.docker.com/compose/environment-variables/) for more information.

The only required variable is `DISCORD_TOKEN`, the rest will use the default values as specified in the table below. See [`config.py`](./bot/config.py) for more information. 

| Name | Default | Comment |
| ---- | ------- | ------- |
| `DISCORD_TOKEN` |  | **Required!** Bot token, see [`config.py`](./bot/config.py) for more information |
| `MONGODB_URI` | `mongodb://mongo:27017` | URI for the MongoDB instance |
| `MONGO_HOST_PORT` | `27017` | Localhost port for MongoDB; set another port if multiple stacks share a host |
| `LOGGING_LEVEL` | `INFO` | The level of logging for alerting, etc. Uses the logging levels specified [here](https://docs.python.org/3/library/logging.html) |
| `LOGGING_FORMAT` | `%(asctime)s:%(levelname)s:%(name)s: %(message)s` | Logging format, see [here](https://docs.python.org/3/library/logging.html#formatter-objects) |
| `LOGGING_FILE` |  | If enabled, will send logging to this file |
| `LOGGING_DISCORD_LEVEL` | `ERROR` | The minimum level for logging into the logging channel (`CHANNEL_LOGGING_ID`) |
| `ARCHIVE_ACCESS_TO_ALL_USERS` | `false` | Should all the users in the Discord Server gain access to the CTF channels when the CTF is archived? Set to `true` if so. |
| `COMMAND_PREFIX` | `!` | Prefix for all the bot commands (i.e. `!done`) |
| `MAINTAINERS` |  | Comma-separated list of maintainer Discord IDs; these users can export and delete CTFs and use `!su` |
| `GUILD_IDS` |  | Comma-separated list with guild IDs of where the bot should run. Used for executing CTF channel cleanup manually |
| `CATEGORY_WORKING` | `working` | Category where channels for challenges that are currently being worked on during a CTF |
| `CATEGORY_DONE` | `done` | Category where channels for challenges that are marked as done during a CTF |
| `CATEGORY_ARCHIVE_PREFIX` | `archive` | Category to move channels to when the CTF is over. There is a max limit on 50 channels per category. The bot wil automatically move channels to new categories when needed |
| `CHANNEL_EXPORT` | `export` | The channel to upload exports to |
| `CHANNEL_LOGGING_ID` |  | If enabled, will send logging to this channel, based on the `LOGGING_DISCORD_LEVEL` logging level |
| `CHALLENGE_NAME_DELIMITER` | `-` | The delimiter for challenge channel names, either `-` or `_` |
| `CTFTIME_TEAM_ID` |  | CTFtime ID for the `!ctftime team` command |
| `CTFTIME_TEAM_NAME` |  | CTFtime name for the `!ctftime team` command |

### start from the published image

The [Bot image workflow](.github/workflows/image.yml) builds pull requests and publishes `ghcr.io/dugnadctf/fiskebot:latest` and `:sha-<full commit SHA>` after merges to `master`. Docker Compose pulls this image; a Git checkout is not needed on the server.

Create an empty deployment directory, download the Compose file, and create a `.env` file containing at least `DISCORD_TOKEN`. Set `MAINTAINERS` and `GUILD_IDS` to the appropriate Discord IDs for your server. Then run:

```shell
curl -fsSLo docker-compose.yml https://raw.githubusercontent.com/dugnadctf/fiskebot/master/docker-compose.yml
docker volume create mdb
docker volume create mdb_config
mkdir -p backups
sudo chown 1000:1000 backups
docker compose pull bot
docker compose up -d
```

The two MongoDB volumes are external so an existing installation keeps its data. Existing installations on MongoDB 4.4 must back up their data and upgrade through 5.0, 6.0, and 7.0, advancing the feature compatibility version at each step, before starting the 8.0 image on that volume. Follow [MongoDB's upgrade paths](https://www.mongodb.com/docs/mongodb-versions/) and the standalone procedure for each release.

To deploy a specific bot build, set `FISKEBOT_IMAGE_TAG=sha-<full commit SHA>` in `.env`, then run `docker compose pull bot && docker compose up -d --no-deps bot`. GitHub initially makes new container packages private; make the package public in GitHub Packages, or log in to `ghcr.io` with a token that has package read access before pulling it.

### develop

To build local changes instead of pulling the published image:
```bash
docker build -t ghcr.io/dugnadctf/fiskebot:dev .
FISKEBOT_IMAGE_TAG=dev docker compose up -d
```

For live editing during development, use a Compose override file with a source bind mount.

### linting

This codebase uses the PEP 8 code style. We enforce this with isort, black & flake8. In addition to the standards outlined in PEP 8, we have a few guidelines (see setup.cfg for more info):

First build the tester Docker image
```
$ make build
```

Format the code with black & isort

```shell
$ make fixme
```

To check if it is formatted properly, run:

```shell
$ make check
```

A git `pre-commit` hook for automatically linting before comitting can be found in [git-hook](./git-hook), to install it:
```shell
$ cp git-hook .git/hooks/pre-commit
```

## How to Use

> The main use for fiskebot is to easily set up a CTF for your discord server to play as a team. The following commands listed are probably going to be used the most.

- `!help` Display the main help commands.

- `!create "ctf name"` This is the command you'll use when you want to begin a new CTF. This command will make a text channel with your supplied name. The bot will also send a message in chat where members can react to join the CTF.
![enter image description here](images/ept-create.PNG)

- `!add <challenge name>` This will create a new channel for a given challenge.
![enter image description here](images/ept-add.PNG)
- `!done [users ...]` Mark a challenge as done inside its challenge channel. Other solvers can be given as @mentions, exact usernames, or nicknames. Quote nicknames containing spaces.
![enter image description here](images/ept-done.PNG)
- `!archive` Mark the CTF as over and move it to the archive categories (specified in `/bot/config.py`).

---

> The following commands use the api from [ctftime](https://ctftime.org/api)

- `!ctftime countdown/timeleft` Countdown will return when a selected CTF starts, and timeleft will return when any currently running CTFs end in the form of days hours minutes and seconds.
    ![countdown](images/ctftime-countdown.png)

- `!ctftime upcoming <number>` Uses the api mentioned to return an embed up to 5 upcoming CTFs. If no number is provided the default is 3.
    ![upcoming](images/ctftime-upcoming.png)

- `!ctftime current` Displays any currently running CTFs in the same embed as previously mentioned.

- `!ctftime top <year>` Shows the ctftime leaderboards from a certain year _(dates back to 2011)_.
    ![enter image description here](images/ctftime-top.png)

- `!ctftime team [team name/id]` Display the top 10 events a team have gotten points for this year.
![enter image description here](images/ctftime-team.png)

> ### Have a feature request? Make a GitHub issue.
