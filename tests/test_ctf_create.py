import ast
import asyncio
import pathlib
import unittest
from types import SimpleNamespace


class TaskFailed(Exception):
    pass


def load_create():
    source = pathlib.Path(__file__).resolve().parents[1] / "bot" / "ctf_model.py"
    module = ast.parse(source.read_text())
    team = next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "CtfTeam"
    )
    create = next(
        node
        for node in team.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "create"
    )
    create.decorator_list = []

    def get_channel(channels, name):
        return next((channel for channel in channels if channel.name == name), None)

    namespace = {
        "TaskFailed": TaskFailed,
        "format_role_name": lambda name: f"{name}_team".lower(),
        "discord": SimpleNamespace(utils=SimpleNamespace(get=get_channel)),
    }
    executable = ast.fix_missing_locations(ast.Module(body=[create], type_ignores=[]))
    exec(compile(executable, str(source), "exec"), namespace)
    return namespace["create"]


class Guild:
    def __init__(self, roles=(), channels=()):
        self.roles = [SimpleNamespace(name=name) for name in roles]
        self.channels = list(channels)
        self.text_channels = [SimpleNamespace(name=name) for name in channels]
        self.created_roles = []

    async def create_role(self, *, name, mentionable):
        self.created_roles.append(name)
        return SimpleNamespace(name=name)


class CreateTests(unittest.TestCase):
    def test_empty_name_does_not_create_role(self):
        guild = Guild()
        error = None
        try:
            asyncio.run(load_create()(guild, ""))
        except Exception as exc:
            error = exc
        self.assertEqual(guild.created_roles, [])
        self.assertIsInstance(error, TaskFailed)

    def test_existing_channel_does_not_create_role(self):
        guild = Guild(channels=["existing"])
        with self.assertRaises(TaskFailed):
            asyncio.run(load_create()(guild, "existing"))
        self.assertEqual(guild.created_roles, [])

    def test_existing_role_does_not_create_another(self):
        guild = Guild(roles=["existing"])
        with self.assertRaises(TaskFailed):
            asyncio.run(load_create()(guild, "existing"))
        self.assertEqual(guild.created_roles, [])


if __name__ == "__main__":
    unittest.main()
