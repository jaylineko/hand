import re

import discord
from discord.ext import commands

from .emoji import is_emoji


class EmojiConverter(commands.IDConverter):
    """Converts to a :class:`discord.Emoji`.
    All lookups are done for the local guild, if available.
    The lookup strategy is as follows (in order):
    1. Lookup by ID.
    2. Lookup by extracting ID from the emoji.
    3. Lookup by name
    """

    async def convert(self, ctx, argument):
        if not ctx.guild:
            raise commands.NoPrivateMessage()

        match = self._get_id_match(argument) or re.match(
            r"<a?:[a-zA-Z0-9\_]+:([0-9]+)>$", argument
        )
        result = None

        if match is None:
            result = discord.utils.get(ctx.guild.emojis, name=argument)
        else:
            emoji_id = int(match.group(1))
            result = discord.utils.get(ctx.guild.emojis, id=emoji_id)

        if result is None:
            if is_emoji(argument):
                return argument
            else:
                raise commands.BadArgument(f'Emoji "{argument}" not found')

        return result
