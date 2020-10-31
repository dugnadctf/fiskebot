config = {
    # Connection to mongo backend database
    "db": "mongodb://mongo:27017",

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
    "token": "NzYxMjA4NDYXXXXXXXXXXXXX.J3XXXXXXXXXXXXXXXXXXXXXXXXXm0i4CDw",
    # To invite the bot, use a link similar to:
    # https://discord.com/oauth2/authorize?&client_id=000000000000000001&scope=bot&permissions=8
    # Replace the client_id with your client id. permissions=8 means the manage permission which this bot needs to manage the channels.

    # Prefix for all the bot commands
    "prefix": "!",

    # Profile ids of the maintainers of your installation. These will be messaged when running `!report "issue"` or `!request "feature"`
    # These people also have permission to export and delete ctfs.
    "maintainers": [
        111111111111111111,
        222222222222222222,
    ],

    "categories": {
        # Category where channels for challenges that are currently being worked on during a CTF
        "working": "working",
        # Category where channels for challenges that are marked as done during a CTF
        "done": "done",
        # Category to move channels to when the CTF is over. There is a max limit on 50 channels per category. The bot will automatically move channels to new categories when needed.
        "archive-prefix": "archive"
    },

    "channels": {
        # The channel to upload exports to
        "export": "export"
    },

    # CTFtime id for the default team to lookup using the `!ctftime team` command
    "team": {
        "id": 119480,
        "name": "EPT"
    },
}
