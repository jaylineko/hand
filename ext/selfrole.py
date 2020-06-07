import discord
from discord.ext import commands

from .utils import converter


class SelfRole(commands.Cog):
    """Self-role configuration"""

    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @commands.group(invoke_without_command=True)
    @commands.cooldown(1, 3, commands.BucketType.channel)
    async def reactionrole(self, ctx: commands.Context):
        """Group of commands to manage reaction roles configuration in this server"""

        config = ctx.bot.roles.get(ctx.guild.id, {})

        embed = discord.Embed(
            title="Reaction role",
            description=f"Use `{ctx.prefix}help reactionrole` for more info"
            "\nCurrent configuration:",
        )

        for message_id, data in config.get("reactionrole", {}).items():
            data = data.copy()
            channel_id = data.pop("channel")

            message_link = (
                f"https://discord.com/channels/{ctx.guild.id}/{channel_id}/{message_id}"
            )

            channel = discord.utils.get(ctx.guild.channels, id=channel_id)

            embed.add_field(
                name=f"{len(data)} in #{channel.name}",
                value=f"[Go to message]({message_link})\n"
                + "\n".join(
                    [f"{emoji}: <@&{role_id}>" for emoji, role_id in data.items()]
                ),
            )

        await ctx.send(embed=embed)

    @reactionrole.command(name="set", aliases=["add"])
    @commands.cooldown(3, 30, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_guild=True, manage_roles=True)
    async def reactionrole_set(
        self,
        ctx: commands.Context,
        message: commands.MessageConverter,
        emoji: converter.EmojiConverter,
        *,
        role: commands.RoleConverter = None,
    ):
        """Sets or unsets the role given to a member when they react to a message using an emoji"""

        config = self.bot.roles.get(ctx.guild.id, {})

        messages = config.get("reactionrole", {})
        if str(message.id) not in messages:
            if len(messages) >= 15:
                raise commands.BadArgument(
                    message="Too many messages have reaction roles"
                )

            messages[str(message.id)] = {"channel": message.channel.id}

        roles = messages[str(message.id)]
        if role:
            roles[str(emoji)] = str(role.id)
        elif str(emoji) in roles:
            del roles[str(emoji)]

        if len(roles) == 0:
            del messages[str(message.id)]

        config["reactionrole"] = messages
        self.bot.roles.put(ctx.guild.id, config)

        if role:
            await message.add_reaction(emoji)
        else:
            await message.remove_reaction(emoji, ctx.me)

        description = (
            f"Members who react with {emoji} to [this message]"
            f"(https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}) "
        )
        if role:
            description += f"will now get {role.mention}"
        else:
            description += "will no longer get a role"

        await ctx.send(
            embed=discord.Embed(title="Reaction role", description=description)
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, event: discord.RawReactionActionEvent):
        if event.member.bot:
            return

        config = self.bot.roles.get(event.guild_id, {})

        messages = config.get("reactionrole", {})
        roles = messages.get(str(event.message_id), {})

        if str(event.emoji) not in roles:
            return

        role = discord.Object(id=int(roles[str(event.emoji)]))
        await event.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, event: discord.RawReactionActionEvent):
        guild = discord.utils.get(self.bot.guilds, id=event.guild_id)
        member = discord.utils.get(guild.members, id=event.user_id)
        if member is None or member.bot:
            return

        config = self.bot.roles.get(event.guild_id, {})

        messages = config.get("reactionrole", {})
        roles = messages.get(str(event.message_id), {})

        if str(event.emoji) not in roles:
            return

        role = discord.Object(id=int(roles[str(event.emoji)]))
        await member.remove_roles(role)

    @commands.group(aliases=["color"], invoke_without_command=True)
    @commands.cooldown(1, 3, commands.BucketType.channel)
    async def colour(self, ctx: commands.Context):
        """Group of commands to manage colour roles in this server"""

        config = ctx.bot.roles.get(ctx.guild.id, {})
        colour_config = config.get("colour", None)

        embed = discord.Embed(
            title="Colour role",
            description=f"Use `{ctx.prefix}help colour` for more info"
            "\nCurrent configuration:",
        )

        if colour_config is None:
            embed.add_field(name="Enabled", value="No")
            await ctx.send(embed=embed)
            return

        embed.add_field(name="Enabled", value="Yes")
        embed.add_field(
            name="Custom role names",
            value="Yes" if colour_config.get("custom-name", False) else "No",
        )

        await ctx.send(embed=embed)

    @colour.command(name="toggle")
    @commands.cooldown(3, 30, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def colour_toggle(self, ctx: commands.Context):
        """Enables or disables self colour roles"""

        config = ctx.bot.roles.get(ctx.guild.id, {})
        enabled = "colour" in config

        if enabled:
            del config["colour"]
        else:
            config["colour"] = {}

        ctx.bot.roles.put(ctx.guild.id, config)

        await ctx.send(
            embed=discord.Embed(
                title="Colour role",
                description=f"Colour roles are now {'disabled' if enabled else 'enabled'}",
            )
        )

    @colour.command(name="toggle-names")
    @commands.cooldown(3, 30, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def colour_toggle_names(self, ctx: commands.Context):
        """Enables or disables custom names for self colour roles"""

        config = ctx.bot.roles.get(ctx.guild.id, {})
        colour_config = config.get("colour", None)

        if colour_config is None:
            await ctx.send(
                embed=discord.Embed(
                    title="Colour role", description=f"Colour roles are disabled",
                )
            )
            return

        enabled = colour_config.get("custom-name", False)
        if enabled:
            del colour_config["custom-name"]
        else:
            colour_config["custom-name"] = True

        ctx.bot.roles.put(ctx.guild.id, config)

        await ctx.send(
            embed=discord.Embed(
                title="Colour role",
                description=f"Custom names are now {'disabled' if enabled else 'enabled'}",
            )
        )

    async def _clean_roles(self, guild: discord.Guild):
        guild_config = self.bot.roles.get(guild.id, {})
        managed_roles = guild_config.get("colour", {}).setdefault("roles", [])
        managed_roles = [
            str(role.id) for role in guild.roles if str(role.id) in managed_roles
        ]
        guild_config.get("colour", {})["roles"] = managed_roles

        for role in guild.roles:
            if str(role.id) not in managed_roles:
                continue
            if not any(role in member.roles for member in guild.members):
                guild_config.get("colour", {})["roles"] = [
                    r for r in managed_roles if r != str(role.id)
                ]
                await role.delete()

        self.bot.roles.put(guild.id, guild_config)

    async def _unset_colour(self, member: discord.Member):
        guild_config = self.bot.roles.get(member.guild.id, {})
        managed_roles = guild_config.get("colour", {}).setdefault("roles", [])

        for role in member.roles:
            if str(role.id) in managed_roles:
                await member.remove_roles(role)

        await self._clean_roles(member.guild)

    async def _set_colour(
        self, member: discord.Member, colour: discord.Colour, name: str
    ):
        guild_config = self.bot.roles.get(member.guild.id, {})
        managed_roles = guild_config.get("colour", {}).setdefault("roles", [])

        await self._unset_colour(member)

        role = discord.utils.get(
            (role for role in member.guild.roles if str(role.id) in managed_roles),
            name=name,
            colour=colour,
        )

        if role is None:
            role = await member.guild.create_role(name=name, colour=colour)
            guild_config.get("colour", {})["roles"] = [*managed_roles, str(role.id)]
            self.bot.roles.put(member.guild.id, guild_config)

        await member.add_roles(role)
        return role

    @colour.command(name="set")
    @commands.cooldown(3, 30, commands.BucketType.guild)
    @commands.bot_has_permissions(manage_roles=True)
    async def colour_set(
        self,
        ctx: commands.Context,
        colour: commands.ColourConverter = None,
        *,
        name: str = None,
    ):
        """Sets or unsets your current colour"""

        config = ctx.bot.roles.get(ctx.guild.id, {})
        colour_config = config.get("colour", None)

        if colour_config is None:
            await ctx.send(
                embed=discord.Embed(
                    title="Colour role", description=f"Colour roles are disabled",
                )
            )
            return

        custom_names_enabled = colour_config.get("custom-name", False)
        if not custom_names_enabled and name is not None:
            await ctx.send(
                embed=discord.Embed(
                    title="Colour role", description=f"Custom role names are disabled",
                )
            )
            return

        if colour is None:
            await self._unset_colour(ctx.author)
            await ctx.send(
                embed=discord.Embed(
                    title="Colour role", description="You no longer have a colour role",
                )
            )
            return

        if not name:
            name = str(colour)

        role = await self._set_colour(ctx.author, colour, name)

        await ctx.send(
            embed=discord.Embed(
                title="Colour role",
                description=f"You now have a colour role: {role.mention}",
            )
        )


def setup(bot):
    bot.add_cog(SelfRole(bot))
