from .cog import VentingCog


async def setup(bot):
    await bot.add_cog(VentingCog(bot))