import os


def parse_variable(variable, default=None, valid=None):
    value = os.getenv(variable, None)
    if default and valid and variable not in valid:
        return default
    elif isinstance(default, int):
        return int(value) if value and value.isdigit() else default
    else:
        return value if value and value != "" else default


def parse_int_list(variable):
    return [
        int(item)
        for item in parse_variable(variable, "").replace(" ", "").split(",")
        if item.isdigit()
    ]


config = {
    # Connection to mongo backend database
    "db": parse_variable("MONGODB_URI", "mongodb://mongo:27017"),
    # Bot token.
    # Follow the wikihow guide for instructions:
    # https://www.wikihow.com/Create-a-Bot-in-Discord#Creating-the-Bot-on-Discord
    # -
    # Basically, go to https://discord.com/developers/applications/me
    # Register an application
    # Register a bot to the application
    # Click reveal token
    # On the same site you can change the name and profile picture of the bot
    # -
    # The token should have a similar format to the one bellow
    "token": parse_variable("DISCORD_TOKEN"),
    # To invite the bot, use a link similar to:
    # https://discord.com/oauth2/authorize?&client_id=000000000000000001&scope=bot&permissions=8
    # Replace the client_id with your client id. permissions=8 means the manage permission which this bot needs to manage the channels.
    #
    # The level of logging for alerting, etc. Uses the logging levels specified here: https://docs.python.org/3/library/logging.html
    "logging_level": parse_variable("LOGGING_LEVEL", "INFO"),
    # Logging format, see https://docs.python.org/3/library/logging.html#formatter-objects
    "logging_format": parse_variable(
        "LOGGING_FORMAT", "%(asctime)s:%(levelname)s:%(name)s: %(message)s"
    ),
    # If enabled, will send logging to this file
    "logging_file": parse_variable("LOGGING_FILE"),
    # The minimum level for logging into the logging channel (`CHANNEL_LOGGING_ID`)
    "logging_discord_level": parse_variable("LOGGING_DISCORD_LEVEL", "ERROR"),
    # Prefix for all the bot commands
    "prefix": parse_variable("COMMAND_PREFIX", "!"),
    # Profile ids of the maintainers of your installation. These will be messaged when running `!report "issue"` or `!request "feature"`
    # These people also have permission to export and delete ctfs.
    "maintainers": parse_int_list("MAINTAINERS"),
    # The guild IDs where the bot is running, used for executing CTF channel cleanup manually
    "guild_ids": parse_int_list("GUILD_IDS"),
    # Channel categories
    "categories": {
        # Category where channels for challenges that are currently being worked on during a CTF
        "working": parse_variable("CATEGORY_WORKING", "working"),
        # Category where channels for challenges that are marked as done during a CTF
        "done": parse_variable("CATEGORY_DONE", "done"),
        # Category to move channels to when the CTF is over. There is a max limit on 50 channels per category. The bot will automatically move channels to new categories when needed.
        "archive-prefix": parse_variable("CATEGORY_ARCHIVE_PREFIX", "archive"),
    },
    "channels": {
        # The channel to upload exports to
        "export": parse_variable("CHANNEL_EXPORT", "export"),
        # If enabled, will send logging to this channel, based on the `LOGGING_DISCORD_LEVEL` logging level
        "logging": parse_variable("CHANNEL_LOGGING_ID", 0),
    },
    # The delimiter for the channel names, must be one of "-" or "_". i.e. "-": "#ctf-challenge-name", "_": "#ctf_challenge_name"
    "challenge_name_delimiter": parse_variable(
        "CHALLENGE_NAME_DELIMITER", "-", valid=["-", "_"]
    ),
    # CTFtime id for the default team to lookup using the `!ctftime team` command
    "team": {
        "id": parse_variable("CTFTIME_TEAM_ID", -1),
        "name": parse_variable("CTFTIME_TEAM_NAME"),
    },
}
