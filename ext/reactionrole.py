import discord
from discord.ext import commands


class ReactionRole(commands.Cog):
    """Autorole configuration"""

    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @commands.group(invoke_without_command=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_guild=True)
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
    @commands.has_guild_permissions(manage_guild=True)
    async def autorole_set(
        self,
        ctx: commands.Context,
        message: commands.MessageConverter,
        emoji: commands.EmojiConverter,
        *,
        role: commands.RoleConverter = None,
    ):
        """Sets or unsets the role given to a member when they react to a message using an emoji"""

        config = self.bot.roles.get(ctx.guild.id, {})

        messages = config.get("reactionrole", {})
        if message.id not in messages:
            if len(messages) >= 15:
                raise commands.BadArgument(
                    message="Too many messages have reaction roles"
                )

            messages[message.id] = {"channel": message.channel.id}

        roles = messages[message.id]
        if role:
            roles[str(emoji)] = str(role.id)
        else:
            del roles[str(emoji)]

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
        config = self.bot.roles.get(event.guild_id, {})

        messages = config.get("reactionrole", {})
        roles = messages.get(str(event.message_id), {})

        if str(event.emoji) not in roles:
            return

        role = discord.Object(id=int(roles[str(event.emoji)]))
        await event.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, event: discord.RawReactionActionEvent):
        config = self.bot.roles.get(event.guild_id, {})

        messages = config.get("reactionrole", {})
        roles = messages.get(str(event.message_id), {})

        if str(event.emoji) not in roles:
            return

        guild = discord.utils.get(self.bot.guilds, id=event.guild_id)
        member = discord.utils.get(guild.members, id=event.user_id)
        if member is None:
            return

        role = discord.Object(id=int(roles[str(event.emoji)]))
        await member.remove_roles(role)


def setup(bot):
    bot.add_cog(ReactionRole(bot))
