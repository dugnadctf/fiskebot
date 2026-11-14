import ast
import asyncio
import pathlib
import unittest
from types import SimpleNamespace


def load_delete(choose_archive):
    source = pathlib.Path(__file__).resolve().parents[1] / "bot" / "ctf_model.py"
    module = ast.parse(source.read_text())
    team = next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "CtfTeam"
    )
    delete = next(
        node
        for node in team.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "del_chal"
    )
    delete.decorator_list = []
    namespace = {
        "_find_available_archive_category": choose_archive,
        "chk_upd": lambda name, result: None,
    }
    executable = ast.fix_missing_locations(ast.Module(body=[delete], type_ignores=[]))
    exec(compile(executable, str(source), "exec"), namespace)
    return namespace["del_chal"]


class Challenge:
    def __init__(self):
        self.chan_id = 456
        self.archived_in = None

    async def _delete(self, category):
        self.archived_in = category


class Team:
    def __init__(self, challenge):
        self.guild = object()
        setattr(self, "__chan_id", 123)
        setattr(self, "__guild", self.guild)
        setattr(self, "__teams", SimpleNamespace(update_one=lambda *args: None))
        self.name = "ctf"
        self.challenges = [challenge, object()]
        self.challenge = challenge

    def find_chal(self, name):
        return self.challenge

    def refresh(self):
        pass


class DeleteTests(unittest.TestCase):
    def test_delete_archives_one_challenge_in_category(self):
        category = object()
        calls = []

        async def choose_archive(guild, count, start=0):
            calls.append((guild, count, start))
            return category, 0

        challenge = Challenge()
        team = Team(challenge)
        asyncio.run(load_delete(choose_archive)(team, "challenge"))
        self.assertEqual(calls, [(team.guild, 1, 0)])
        self.assertIs(challenge.archived_in, category)


if __name__ == "__main__":
    unittest.main()
