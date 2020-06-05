import discord
from discord.ext import commands


class Autorole(commands.Cog):
    """Autorole configuration"""

    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @commands.group(invoke_without_command=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_guild=True)
    async def autorole(self, ctx: commands.Context):
        """Group of commands to manage autoroles configuration in this server"""

        config = ctx.bot.roles.get(ctx.guild.id, {})

        embed = discord.Embed(
            title="Autorole",
            description=f"Use `{ctx.prefix}help autorole` for more info"
            "\nCurrent configuration:",
        )
        embed.add_field(
            name="Default member role",
            value=f"<@&{config['autorole']}>" if "autorole" in config else "None",
        )

        await ctx.send(embed=embed)

    @autorole.command(name="set")
    @commands.cooldown(3, 30, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_guild=True)
    async def autorole_set(self, ctx: commands.Context, role: commands.RoleConverter):
        """Sets the role given to all members on join"""

        config = ctx.bot.roles.get(ctx.guild.id, {})
        config["autorole"] = str(role.id)
        ctx.bot.roles.put(ctx.guild.id, config)

        await ctx.send(
            embed=discord.Embed(
                title="Autorole",
                description=f"All members will now get {role.mention} on join",
            )
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = self.bot.roles.get(member.guild.id, {})

        autorole = config.get("autorole", None)

        if autorole:
            await member.add_roles(discord.Object(id=int(autorole)))


def setup(bot):
    bot.add_cog(Autorole(bot))
