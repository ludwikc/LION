from babel.translator import LocalBabel

util_babel = LocalBabel('utils')

# Import interaction utilities for easy access
from .interaction import (
    safe_defer,
    safe_respond, 
    safe_edit_response,
    guaranteed_response,
    timeout_handler
)


async def setup(bot):
    from .cog import MetaUtils
    await bot.add_cog(MetaUtils(bot))
