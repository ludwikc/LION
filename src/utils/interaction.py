"""
Utilities for guaranteed Discord interaction responses to prevent timeout errors.
"""

import logging
import asyncio
from typing import Optional

import discord

logger = logging.getLogger(__name__)

__all__ = (
    'safe_defer',
    'safe_respond',
    'safe_edit_response',
    'guaranteed_response'
)


async def safe_defer(interaction: discord.Interaction, *, thinking: bool = True, ephemeral: bool = False) -> bool:
    """
    Safely defer an interaction response, returning True if successful.
    
    Args:
        interaction: The Discord interaction to defer
        thinking: Whether to show the "thinking" indicator
        ephemeral: Whether the eventual response should be ephemeral
    
    Returns:
        bool: True if defer was successful, False otherwise
    """
    if interaction.response.is_done() or interaction.is_expired():
        return False
    
    try:
        await interaction.response.defer(thinking=thinking, ephemeral=ephemeral)
        return True
    except discord.HTTPException as e:
        logger.warning(f"Failed to defer interaction {interaction.id}: {e}")
        return False


async def safe_respond(interaction: discord.Interaction, content: str = None, *, 
                      embed: discord.Embed = None, ephemeral: bool = False, **kwargs) -> bool:
    """
    Safely respond to an interaction, handling both initial and followup responses.
    
    Args:
        interaction: The Discord interaction to respond to
        content: Message content
        embed: Embed to send
        ephemeral: Whether response should be ephemeral
        **kwargs: Additional keyword arguments for the response
    
    Returns:
        bool: True if response was successful, False otherwise
    """
    if interaction.is_expired():
        logger.warning(f"Attempted to respond to expired interaction {interaction.id}")
        return False
    
    try:
        if interaction.response.is_done():
            await interaction.followup.send(content=content, embed=embed, ephemeral=ephemeral, **kwargs)
        else:
            await interaction.response.send_message(content=content, embed=embed, ephemeral=ephemeral, **kwargs)
        return True
    except discord.HTTPException as e:
        logger.error(f"Failed to respond to interaction {interaction.id}: {e}")
        return False


async def safe_edit_response(interaction: discord.Interaction, content: str = None, *,
                           embed: discord.Embed = None, **kwargs) -> bool:
    """
    Safely edit the original interaction response.
    
    Args:
        interaction: The Discord interaction
        content: New message content
        embed: New embed
        **kwargs: Additional keyword arguments
    
    Returns:
        bool: True if edit was successful, False otherwise
    """
    if interaction.is_expired():
        logger.warning(f"Attempted to edit expired interaction {interaction.id}")
        return False
    
    if not interaction.response.is_done():
        logger.warning(f"Attempted to edit response for interaction {interaction.id} that hasn't been responded to")
        return False
    
    try:
        await interaction.edit_original_response(content=content, embed=embed, **kwargs)
        return True
    except discord.HTTPException as e:
        logger.error(f"Failed to edit interaction response {interaction.id}: {e}")
        return False


async def guaranteed_response(interaction: discord.Interaction, success_content: str = None,
                            error_content: str = "An error occurred. Please try again.",
                            *, success_embed: discord.Embed = None,
                            error_embed: discord.Embed = None,
                            ephemeral: bool = True) -> bool:
    """
    Guarantee that an interaction receives some response, even if the main operation fails.
    
    This function ensures that Discord interactions always receive a response within the timeout window,
    preventing "The application did not respond" errors.
    
    Args:
        interaction: The Discord interaction
        success_content: Content to send on success
        error_content: Fallback content to send on error
        success_embed: Embed to send on success
        error_embed: Fallback embed to send on error
        ephemeral: Whether responses should be ephemeral
    
    Returns:
        bool: True if any response was sent, False if all attempts failed
    """
    if interaction.is_expired():
        return False
    
    # First attempt: send success response
    if success_content or success_embed:
        if await safe_respond(interaction, success_content, embed=success_embed, ephemeral=ephemeral):
            return True
    
    # Fallback attempt: send error response
    if await safe_respond(interaction, error_content, embed=error_embed, ephemeral=ephemeral):
        return True
    
    # Last resort: try a simple text response
    return await safe_respond(interaction, "Operation completed.", ephemeral=True)


def timeout_handler(timeout_seconds: float = 2.5):
    """
    Decorator to automatically handle command timeouts by deferring interactions.
    
    Args:
        timeout_seconds: Maximum time to wait before auto-deferring (default 2.5s)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Find the interaction in the arguments
            interaction = None
            if args and hasattr(args[0], 'interaction'):
                interaction = args[0].interaction  # LionContext
            elif args and isinstance(args[1], discord.Interaction):
                interaction = args[1]
            elif 'interaction' in kwargs:
                interaction = kwargs['interaction']
            
            if not interaction:
                # No interaction found, run normally
                return await func(*args, **kwargs)
            
            try:
                # Try to complete within timeout window
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                # Auto-defer and retry
                logger.warning(f"Function {func.__name__} timed out, auto-deferring interaction")
                if await safe_defer(interaction):
                    return await func(*args, **kwargs)
                else:
                    # Defer failed, try to send error response
                    await guaranteed_response(
                        interaction, 
                        error_content="Operation is taking longer than expected. Please try again."
                    )
                    return None
        
        return wrapper
    return decorator