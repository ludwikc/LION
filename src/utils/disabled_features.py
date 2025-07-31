"""
Utilities for handling disabled features in Discord commands.
"""

import logging
from typing import Optional

import discord
from discord.ext import commands as cmds

from meta.errors import UserInputError
from meta.context import LionContext
from .interaction import safe_defer

logger = logging.getLogger(__name__)

__all__ = (
    'feature_disabled_response',
    'premium_disabled_decorator'
)


async def feature_disabled_response(
    ctx: LionContext, 
    feature_name: str, 
    reason: str = "This feature has been disabled.",
    *, 
    ephemeral: bool = True
) -> None:
    """
    Send a standardized "feature disabled" response to a Discord interaction.
    
    This function ensures proper deferring and consistent error messaging
    for disabled features across the bot.
    
    Args:
        ctx: The Lion context containing the interaction
        feature_name: Name of the disabled feature for logging
        reason: User-friendly reason why the feature is disabled
        ephemeral: Whether the response should be ephemeral
    """
    if not ctx.interaction:
        logger.warning(f"feature_disabled_response called without interaction for {feature_name}")
        return
    
    # Ensure we defer before sending error message
    await safe_defer(ctx.interaction, ephemeral=ephemeral)
    
    # Log the disabled feature access attempt
    logger.info(
        f"User {ctx.author.id} attempted to access disabled feature: {feature_name}",
        extra={'action': 'DisabledFeatureAccess', 'feature': feature_name}
    )
    
    # Send consistent error message
    raise UserInputError(reason)


def premium_disabled_decorator(feature_name: str, reason: Optional[str] = None):
    """
    Decorator for commands that have been disabled due to premium feature removal.
    
    Args:
        feature_name: Name of the disabled feature
        reason: Custom reason message (optional)
    
    Returns:
        Decorator function that handles the disabled feature response
    """
    default_reason = f"{feature_name} has been disabled. Premium features have been removed from this bot."
    final_reason = reason or default_reason
    
    def decorator(func):
        async def wrapper(self, ctx: LionContext, *args, **kwargs):
            await feature_disabled_response(ctx, feature_name, final_reason)
        
        # Preserve original function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__annotations__ = func.__annotations__
        
        return wrapper
    return decorator


def validation_with_defer(func):
    """
    Decorator that ensures interactions are deferred before validation that might raise UserInputError.
    
    This should be used on command functions that perform validation checks
    before the main command logic.
    """
    async def wrapper(self, ctx: LionContext, *args, **kwargs):
        # Defer immediately if we have an interaction
        if ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.interaction.response.defer()
        
        # Run the original command
        return await func(self, ctx, *args, **kwargs)
    
    # Preserve original function metadata
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__annotations__ = func.__annotations__
    
    return wrapper


# Standard disabled feature messages
DISABLED_FEATURE_MESSAGES = {
    'premium_removed': "This feature has been disabled. Premium features have been removed from this bot.",
    'temporarily_disabled': "This feature is temporarily disabled for maintenance.",
    'deprecated': "This feature has been deprecated and is no longer available.",
    'permissions_required': "This feature requires additional permissions that are not currently available.",
}


async def send_feature_disabled_embed(
    interaction: discord.Interaction,
    title: str,
    description: str,
    *,
    color: discord.Color = discord.Color.orange(),
    ephemeral: bool = True
) -> None:
    """
    Send a standardized disabled feature embed response.
    
    Args:
        interaction: The Discord interaction
        title: Embed title
        description: Embed description explaining why feature is disabled
        color: Embed color (default: orange)
        ephemeral: Whether response should be ephemeral
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
    except discord.HTTPException as e:
        logger.error(f"Failed to send disabled feature embed: {e}")