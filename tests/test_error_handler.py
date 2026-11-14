import asyncio
import os
import pathlib
import sys
import unittest
from unittest.mock import patch

from discord.ext import commands

os.environ.setdefault("DISCORD_TOKEN", "dummy")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "bot"))
import bot  # noqa: E402


class Context:
    command = "invite"

    def __init__(self):
        self.messages = []

    async def send(self, message):
        self.messages.append(message)
        return self

    async def delete(self):
        pass


class ErrorHandlerTests(unittest.TestCase):
    def test_unknown_member_gets_input_error(self):
        context = Context()

        async def no_wait(seconds):
            pass

        with patch.object(bot.asyncio, "sleep", no_wait):
            asyncio.run(bot.on_command_error(context, commands.MemberNotFound("mattis")))

        self.assertEqual(context.messages, [':bangbang: Member "mattis" not found.'])


if __name__ == "__main__":
    unittest.main()
