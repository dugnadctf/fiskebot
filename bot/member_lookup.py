import re

import discord
from discord.ext import commands
from discord.http import Route


class MemberArgument(commands.Converter):
    async def convert(self, ctx, argument):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()

        value = argument.strip()
        mention = re.fullmatch(r"<@!?(\d+)>", value)
        if mention or value.isdecimal():
            member_id = int(mention.group(1) if mention else value)
        else:
            name = value.removeprefix("@")
            if not name:
                raise commands.BadArgument("Specify a username or @mention.")

            route = Route(
                "GET", "/guilds/{guild_id}/members/search", guild_id=ctx.guild.id
            )
            results = await ctx.bot.http.request(
                route, params={"query": name, "limit": 1000}
            )
            exact_ids = {
                int(item["user"]["id"])
                for item in results
                if name.casefold()
                in {
                    item["user"]["username"].casefold(),
                    (item.get("nick") or "").casefold(),
                    (item["user"].get("global_name") or "").casefold(),
                }
            }
            if len(results) >= 1000 or len(exact_ids) > 1:
                raise commands.BadArgument(
                    f"Several members match `{name}`; use an @mention."
                )
            if not exact_ids:
                raise commands.BadArgument(
                    f"Member `{name}` not found; use an exact username or @mention."
                )
            member_id = exact_ids.pop()

        try:
            return await ctx.guild.fetch_member(member_id)
        except discord.NotFound as exc:
            raise commands.BadArgument("Member not found in this server.") from exc
