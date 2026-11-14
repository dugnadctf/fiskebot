import pathlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "bot"))
from logger import BotLogger, DiscordHandler, config  # noqa: E402


class LoggerTests(unittest.TestCase):
    def test_reconnect_replaces_discord_handler(self):
        logger = BotLogger("test_reconnect")
        bot = SimpleNamespace(get_channel=lambda channel_id: object())
        with patch.dict(config["channels"], {"logging": 123}):
            logger.add_discord_log_handler(bot)
            logger.add_discord_log_handler(bot)
        self.assertEqual(
            sum(isinstance(handler, DiscordHandler) for handler in logger.handlers), 1
        )
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    unittest.main()
