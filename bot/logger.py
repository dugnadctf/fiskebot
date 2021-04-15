import asyncio
import logging
import traceback

from config import config


class BotLogger(logging.getLoggerClass()):
    def __init__(self, name):
        super(BotLogger, self).__init__(name)

        # Setup standard logger
        self.setLevel(config["logging_level"])
        self.bot_formatter = logging.Formatter(config["logging_format"])

        # For console output
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(config["logging_level"])
        stream_handler.setFormatter(self.bot_formatter)
        self.addHandler(stream_handler)

        if not config["logging_file"]:
            self.debug("File for logging is not set, not enabling logging to file")
        else:
            # For file output
            self.debug(
                f"Setting up logging FileHandler with output to file: {config['logging_file']}"
            )
            file_handler = logging.FileHandler(
                config["logging_file"], encoding="utf-8", mode="w"
            )
            file_handler.setLevel(config["logging_level"])
            file_handler.setFormatter(self.bot_formatter)
            self.addHandler(file_handler)

    def add_discord_log_handler(self, bot):
        channel_name = config["channels"]["logging"]
        if not channel_name:
            self.debug(
                "Discord channel for logging is not set, not enabling logging to Discord"
            )
            return
        self.debug(
            f"Setting up logging DiscordHandler with output to channel name: {channel_name}"
        )

        # Find the channel for logging
        for channel in bot.get_all_channels():
            if channel_name == channel.name:
                logging_channel = channel
                break
        else:
            self.error(
                f"Discord logging will not be enabled even though it is set, could not find channel with name: {channel_name}"
            )
            return

        self.debug(f"Discord logging to channel: {repr(logging_channel)}")

        # Setup the custom Discord logging handler
        discord_handler = DiscordHandler(logging_channel)
        discord_handler.setLevel(config["logging_discord_level"])
        discord_handler.setFormatter(self.bot_formatter)
        self.addHandler(discord_handler)


class DiscordHandler(logging.Handler):
    def __init__(self, channel):
        super(DiscordHandler, self).__init__()
        self.channel = channel

    def emit(self, record):
        try:
            message = f"```\n{self.format(record)}\n```"
            loop = asyncio.get_event_loop()
            # needed for await
            loop.create_task(self.channel.send(message))
        except Exception as e:
            print("Unable to send log message to Discord")
            print(traceback.format_exc())
            print(e)
