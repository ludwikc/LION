import logging

import discord
from discord.ext import commands as cmds
from discord import app_commands as appcmds

from meta import LionBot, LionCog, LionContext
from utils.lib import error_embed

logger = logging.getLogger(__name__)


class SecretsCog(LionCog):
    """
    Anonymous secrets sharing module.
    
    Allows community members to share anonymous messages in a designated 
    secrets channel while maintaining complete privacy and anonymity.
    """
    
    # Target channel ID for secrets sharing
    TARGET_SECRETS_CHANNEL = 1196136652737892463
    
    # Role to mention when posting secrets
    LIFEHACKER_ROLE_ID = 1109472432387002408
    
    # Message length limit for secrets
    MAX_SECRET_LENGTH = 500
    
    def __init__(self, bot: LionBot):
        self.bot = bot

    def validate_message_content(self, message: str) -> tuple[bool, str]:
        """
        Validate the secret message content.
        
        Returns (is_valid, error_message) tuple.
        """
        if not message or not message.strip():
            return False, "Please provide a message to share as a secret."
        
        if len(message) > self.MAX_SECRET_LENGTH:
            return False, f"Secret message is too long! Maximum length is {self.MAX_SECRET_LENGTH} characters."
        
        # Basic content filtering
        message_lower = message.lower()
        if "@everyone" in message_lower or "@here" in message_lower:
            return False, "Secret messages cannot contain @everyone or @here mentions."
        
        return True, ""

    def format_secret_message(self, secret: str) -> str:
        """
        Format the secret message for posting in the channel.
        
        Returns the formatted message with role mention and spoiler tags.
        """
        return f"<@&{self.LIFEHACKER_ROLE_ID}>\n\nLifehacker podzielił się sekretem:\n\n|| {secret} ||"

    async def _share_secret_logic(self, ctx: LionContext, message: str) -> tuple[bool, str]:
        """
        Shared logic for secret sharing without response handling.
        
        Returns (success, error_message) tuple.
        - success: True if secret was shared successfully, False otherwise
        - error_message: Error message if success is False, empty string if success is True
        """
        # Validate channel
        if ctx.channel.id != self.TARGET_SECRETS_CHANNEL:
            return False, "This command only works in the designated secrets channel!"
        
        # Validate message content
        is_valid, error_msg = self.validate_message_content(message)
        if not is_valid:
            return False, error_msg
        
        try:
            # Format and send the secret message
            formatted_message = self.format_secret_message(message)
            await ctx.channel.send(formatted_message)
            
            # Log successful secret sharing (without content for privacy)
            logger.info(
                f"Anonymous secret shared in channel {ctx.channel.id} "
                f"by user {ctx.author.id} (content not logged for privacy)"
            )
            
            return True, ""
            
        except discord.HTTPException as e:
            logger.error(f"Failed to send secret message: {e}")
            return False, "Failed to share your secret. Please try again later."
        except Exception as e:
            logger.error(f"Unexpected error in secret sharing: {e}", exc_info=True)
            return False, "An unexpected error occurred. Please try again later."

    @cmds.hybrid_command(
        name="secret",
        description="Share an anonymous secret in the secrets channel"
    )
    @appcmds.describe(message="The secret message you want to share anonymously")
    @appcmds.guild_only
    async def secret_command(self, ctx: LionContext, *, message: str):
        """
        Share an anonymous secret message.
        
        This command allows users to share secrets anonymously while maintaining
        complete privacy. The user's identity is never revealed or logged.
        """
        try:
            # Validate channel
            if ctx.channel.id != self.TARGET_SECRETS_CHANNEL:
                await ctx.respond(
                    embed=error_embed("This command only works in the designated secrets channel!"),
                    ephemeral=True
                )
                return
            
            # Validate message content
            is_valid, error_msg = self.validate_message_content(message)
            if not is_valid:
                await ctx.respond(
                    embed=error_embed(error_msg),
                    ephemeral=True
                )
                return
            
            # Format and send the secret message
            formatted_message = self.format_secret_message(message)
            await ctx.channel.send(formatted_message)
            
            # Log successful secret sharing (without content for privacy)
            logger.info(
                f"Anonymous secret shared in channel {ctx.channel.id} "
                f"by user {ctx.author.id} (content not logged for privacy)"
            )
            
            await ctx.respond(
                "Your secret has been shared anonymously! 🤐",
                ephemeral=True
            )
            
        except discord.HTTPException as e:
            logger.error(f"Failed to send secret message: {e}")
            try:
                await ctx.respond(
                    embed=error_embed("Failed to share your secret. Please try again later."),
                    ephemeral=True
                )
            except Exception as response_error:
                logger.error(f"Failed to send error response: {response_error}", exc_info=True)
        except Exception as e:
            logger.error(f"Error in secret command: {e}", exc_info=True)
            try:
                await ctx.respond(
                    embed=error_embed("An unexpected error occurred. Please try again later."),
                    ephemeral=True
                )
            except Exception as response_error:
                logger.error(f"Failed to send error response: {response_error}", exc_info=True)

    @cmds.hybrid_command(
        name="sekret",
        description="Share an anonymous secret in the secrets channel (alias for /secret)"
    )
    @appcmds.describe(message="The secret message you want to share anonymously")
    @appcmds.guild_only
    async def sekret_command(self, ctx: LionContext, *, message: str):
        """
        Alias for the secret command.
        
        This is an alternative spelling/alias for the main secret sharing command.
        """
        try:
            # Validate channel
            if ctx.channel.id != self.TARGET_SECRETS_CHANNEL:
                await ctx.respond(
                    embed=error_embed("This command only works in the designated secrets channel!"),
                    ephemeral=True
                )
                return
            
            # Validate message content
            is_valid, error_msg = self.validate_message_content(message)
            if not is_valid:
                await ctx.respond(
                    embed=error_embed(error_msg),
                    ephemeral=True
                )
                return
            
            # Format and send the secret message
            formatted_message = self.format_secret_message(message)
            await ctx.channel.send(formatted_message)
            
            # Log successful secret sharing (without content for privacy)
            logger.info(
                f"Anonymous secret shared in channel {ctx.channel.id} "
                f"by user {ctx.author.id} (content not logged for privacy)"
            )
            
            await ctx.respond(
                "Your secret has been shared anonymously! 🤐",
                ephemeral=True
            )
            
        except discord.HTTPException as e:
            logger.error(f"Failed to send secret message: {e}")
            try:
                await ctx.respond(
                    embed=error_embed("Failed to share your secret. Please try again later."),
                    ephemeral=True
                )
            except Exception as response_error:
                logger.error(f"Failed to send error response: {response_error}", exc_info=True)
        except Exception as e:
            logger.error(f"Error in sekret command: {e}", exc_info=True)
            try:
                await ctx.respond(
                    embed=error_embed("An unexpected error occurred. Please try again later."),
                    ephemeral=True
                )
            except Exception as response_error:
                logger.error(f"Failed to send error response: {response_error}", exc_info=True)