import logging

import discord

from meta import LionBot, LionCog

logger = logging.getLogger(__name__)


class ReactionsCog(LionCog):
    """
    Simple reactions module for automated message reactions.
    
    Currently handles GM/DD reactions with sun emoji in a specific channel.
    """
    
    # Target channel ID for GM/DD reactions
    TARGET_CHANNEL_ID = 1021389566445375558
    
    def __init__(self, bot: LionBot):
        self.bot = bot

    @LionCog.listener('on_message')
    async def handle_gm_dd_reactions(self, message: discord.Message):
        """
        React with sun emoji to GM or DD messages in the target channel.
        
        Listens for 'GM' or 'DD' messages (case insensitive) from anyone
        (including bots) in the specified channel and reacts with ☀️.
        """
        # Filter for specific channel only
        if message.channel.id != self.TARGET_CHANNEL_ID:
            return
        
        # Check message content (case insensitive, strip whitespace)
        content = message.content.strip().upper()
        if content in ['GM', 'DD']:
            try:
                await message.add_reaction('☀️')
                logger.debug(
                    f"Added sun reaction to message '{message.content}' from {message.author} "
                    f"in channel {message.channel.id}"
                )
            except discord.HTTPException as e:
                # Log but don't crash if reaction fails (permissions, rate limits, etc.)
                logger.warning(
                    f"Failed to add sun reaction to message {message.id} "
                    f"in channel {message.channel.id}: {e}"
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error adding reaction to message {message.id}: {e}",
                    exc_info=True
                )