async def setup(bot):
    """
    Setup function for the reactions module.
    
    Loads the ReactionsCog into the bot.
    """
    from .cog import ReactionsCog
    
    await bot.add_cog(ReactionsCog(bot))