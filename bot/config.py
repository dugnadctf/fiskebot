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
    "token": os.getenv("DISCORD_TOKEN"),
    # To invite the bot, use a link similar to:
    # https://discord.com/oauth2/authorize?&client_id=000000000000000001&scope=bot&permissions=8
    # Replace the client_id with your client id. permissions=8 means the manage permission which this bot needs to manage the channels.
    # Prefix for all the bot commands
    "prefix": os.getenv("COMMAND_PREFIX", "!"),
    # Profile ids of the maintainers of your installation. These will be messaged when running `!report "issue"` or `!request "feature"`
    # These people also have permission to export and delete ctfs.
    "maintainers": [
        int(maintainer)
        for maintainer in os.getenv("MAINTAINERS", "").replace(" ", "").split(",")
        if maintainer.isdigit()
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
    },
    # CTFtime id for the default team to lookup using the `!ctftime team` command
    "team": {
        "id": os.getenv("CTFTIME_TEAM_ID", None),
        "name": os.getenv("CTFTIME_TEAM_NAME", None),
    },
}
