async def setup(bot):
    """
    Setup function for the secrets module.
    
    Loads the SecretsCog for anonymous secret sharing functionality.
    """
    from .cog import SecretsCog
    
    await bot.add_cog(SecretsCog(bot))