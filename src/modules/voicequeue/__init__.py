from .cog import VoiceQueueCog


async def setup(bot):
    await bot.add_cog(VoiceQueueCog(bot))