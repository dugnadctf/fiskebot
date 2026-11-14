import asyncio
import pathlib
import sys
import unittest
from types import SimpleNamespace

from discord.ext import commands

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "bot"))
from member_lookup import MemberArgument  # noqa: E402


class Guild:
    id = 42

    def __init__(self):
        self.fetched = []

    async def fetch_member(self, member_id):
        self.fetched.append(member_id)
        return SimpleNamespace(id=member_id)


class HTTP:
    def __init__(self, results):
        self.results = results
        self.params = []

    async def request(self, route, **kwargs):
        self.params.append(kwargs["params"])
        return self.results


def context(results):
    guild = Guild()
    http = HTTP(results)
    return SimpleNamespace(guild=guild, bot=SimpleNamespace(http=http)), http


def member(member_id, username, nick=None):
    return {"user": {"id": str(member_id), "username": username}, "nick": nick}


class MemberLookupTests(unittest.TestCase):
    def test_mention_resolves_by_id_without_search(self):
        ctx, http = context([])
        result = asyncio.run(MemberArgument().convert(ctx, "<@!123>"))
        self.assertEqual(result.id, 123)
        self.assertEqual(http.params, [])

    def test_plain_username_requires_exact_match(self):
        ctx, http = context([member(1, "alexander"), member(2, "alex")])
        result = asyncio.run(MemberArgument().convert(ctx, "alex"))
        self.assertEqual(result.id, 2)
        self.assertEqual(http.params, [{"query": "alex", "limit": 1000}])

    def test_plain_nickname_is_case_insensitive(self):
        ctx, _ = context([member(3, "othername", "Sam")])
        result = asyncio.run(MemberArgument().convert(ctx, "sam"))
        self.assertEqual(result.id, 3)

    def test_literal_at_username(self):
        ctx, _ = context([member(3, "sam")])
        result = asyncio.run(MemberArgument().convert(ctx, "@sam"))
        self.assertEqual(result.id, 3)

    def test_duplicate_name_asks_for_mention(self):
        ctx, _ = context([member(1, "alex"), member(2, "someone", "alex")])
        with self.assertRaisesRegex(commands.BadArgument, "@mention"):
            asyncio.run(MemberArgument().convert(ctx, "alex"))

    def test_unknown_name_raises_user_input_error(self):
        ctx, _ = context([member(1, "alexander")])
        with self.assertRaises(commands.BadArgument):
            asyncio.run(MemberArgument().convert(ctx, "alex"))


if __name__ == "__main__":
    unittest.main()
