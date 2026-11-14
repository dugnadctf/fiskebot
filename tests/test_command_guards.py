import asyncio
import os
import pathlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DISCORD_TOKEN", "dummy")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "bot"))
from ctfs import Ctfs  # noqa: E402

import bot  # noqa: E402


class Context:
    def __init__(self, author_id=1):
        self.author = SimpleNamespace(id=author_id)
        self.messages = []

    async def send(self, message):
        self.messages.append(message)


class CommandGuardTests(unittest.TestCase):
    def test_join_without_name_stops_after_usage(self):
        ctx = Context()
        with patch("ctfs.chk_fetch_team_by_name") as fetch:
            asyncio.run(Ctfs.join.callback(None, ctx, None))
        fetch.assert_not_called()
        self.assertIn("Please specify a CTF", ctx.messages[0])

    def test_setup_rejects_nonmaintainer_with_message(self):
        ctx = Context()
        with patch.dict(bot.config, {"maintainers": [2]}):
            asyncio.run(bot.setup.callback(ctx))
        self.assertEqual(ctx.messages, ["Only maintainers can run the setup process."])

    def test_su_rejects_nonmaintainer(self):
        class Role:
            def __str__(self):
                return bot.ADMIN_ROLE_NAME

        role = Role()

        class Author:
            id = 1
            added = []

            async def add_roles(self, role):
                self.added.append(role)

        ctx = Context()
        ctx.author = Author()
        ctx.guild = SimpleNamespace(roles=[role])

        async def no_wait(seconds):
            pass

        with patch.dict(bot.config, {"maintainers": [2]}), patch.object(
            bot.asyncio, "sleep", no_wait
        ):
            asyncio.run(bot.su.callback(ctx))
        self.assertEqual(ctx.author.added, [])
        self.assertEqual(ctx.messages, ["Only maintainers can use this command."])

    def test_reaction_without_guild_is_ignored(self):
        payload = SimpleNamespace(guild_id=None, channel_id=2, message_id=3, user_id=4)
        with patch.object(bot.bot, "get_guild", return_value=None), patch.object(
            bot.db, "teamdb", {}
        ):
            asyncio.run(bot.on_raw_reaction_add(payload))
            asyncio.run(bot.on_raw_reaction_remove(payload))

    def test_bot_reaction_is_ignored(self):
        payload = SimpleNamespace(guild_id=1, channel_id=2, message_id=3, user_id=4)
        with patch.object(bot.bot, "get_guild", return_value=object()), patch.object(
            bot.bot, "_connection", SimpleNamespace(user=SimpleNamespace(id=4))
        ), patch.object(bot.db, "teamdb", {}):
            asyncio.run(bot.on_raw_reaction_add(payload))
            asyncio.run(bot.on_raw_reaction_remove(payload))


if __name__ == "__main__":
    unittest.main()
