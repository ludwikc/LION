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

# Import disabled feature utilities
from .disabled_features import (
    feature_disabled_response,
    premium_disabled_decorator,
    validation_with_defer,
    send_feature_disabled_embed,
    DISABLED_FEATURE_MESSAGES
)


async def setup(bot):
    from .cog import MetaUtils
    await bot.add_cog(MetaUtils(bot))
