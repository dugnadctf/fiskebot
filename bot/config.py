import os

config = {
    # Connection to mongo backend database
    "db": os.getenv("MONGODB_URI", "mongodb://mongo:27017"),
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
    "token": "NjM3NTU5ODU2NTA4OTYwODA2.XbP77Q.WOqjqQsMH8El_8peRQq4izdnI3A",
    # To invite the bot, use a link similar to:
    # https://discord.com/oauth2/authorize?&client_id=000000000000000001&scope=bot&permissions=8
    # Replace the client_id with your client id. permissions=8 means the manage permission which this bot needs to manage the channels.
    #
    # The level of logging for alerting, etc. Uses the logging levels specified here: https://docs.python.org/3/library/logging.html
    "logging_level": os.getenv("LOGGING_LEVEL", "INFO"),
    # Logging format, see https://docs.python.org/3/library/logging.html#formatter-objects
    "logging_format": os.getenv(
        "LOGGING_FORMAT", "%(asctime)s:%(levelname)s:%(name)s: %(message)s"
    ),
    # If enabled, will send logging to this file
    "logging_file": os.getenv("LOGGING_FILE", None),
    # The minimum level for logging into the logging channel (`CHANNEL_LOGGING`)
    "logging_discord_level": os.getenv("LOGGING_DISCORD_LEVEL", "ERROR"),
    # Prefix for all the bot commands
    "prefix": os.getenv("COMMAND_PREFIX", "!"),
    # Profile ids of the maintainers of your installation. These will be messaged when running `!report "issue"` or `!request "feature"`
    # These people also have permission to export and delete ctfs.
    "maintainers": [
        int(maintainer)
        for maintainer in os.getenv("MAINTAINERS", "").replace(" ", "").split(",")
        if maintainer.isdigit()
    ],
    "guild_ids": [
        int(guild_id)
        for guild_id in os.getenv("GUILD_IDS","").replace(" ", "").split(",")
        if guild_id.isdigit()
    ],
    "categories": {
        # Category where channels for challenges that are currently being worked on during a CTF
        "working": os.getenv("CATEGORY_WORKING", "working"),
        # Category where channels for challenges that are marked as done during a CTF
        "done": os.getenv("CATEGORY_DONE", "done"),
        # Category to move channels to when the CTF is over. There is a max limit on 50 channels per category. The bot will automatically move channels to new categories when needed.
        "archive-prefix": os.getenv("CATEGORY_ARCHIVE_PREFIX", "archive"),
    },
    "channels": {
        # The channel to upload exports to
        "export": os.getenv("CHANNEL_EXPORT", "export"),
        # If enabled, will send logging to this channel, based on the `LOGGING_DISCORD_LEVEL` logging level
        "logging": os.getenv("CHANNEL_LOGGING", None),
    },
    # CTFtime id for the default team to lookup using the `!ctftime team` command
    "team": {
        "id": os.getenv("CTFTIME_TEAM_ID", -1),
        "name": os.getenv("CTFTIME_TEAM_NAME", None),
    },
}