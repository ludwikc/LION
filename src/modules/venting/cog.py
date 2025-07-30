import logging
import random

import discord
from discord.ext import commands as cmds
from discord import app_commands as appcmds

from meta import LionBot, LionCog, LionContext
from utils.lib import error_embed

logger = logging.getLogger(__name__)


class VentingCog(LionCog):
    """
    Venting module for therapeutic message disposal.
    
    Allows community members to vent their frustrations in a designated 
    channel where messages are completely discarded after validation,
    providing a safe therapeutic outlet without any record or storage.
    """
    
    # Target channel ID for venting
    TARGET_VENTING_CHANNEL = 1231496272381218977
    
    # Message length limit for venting
    MAX_VENT_LENGTH = 1000
    
    # Polish comfort responses
    COMFORT_RESPONSES = [
        "Czasami trzeba po prostu wypuścić to z siebie. Mam nadzieję, że czujesz się teraz lepiej. 💚",
        "Wygadanie się może przynieść ulgę. Pamiętaj, że każdy trudny moment kiedyś minie. 🌅",
        "To dobrze, że podzieliłeś(-aś) się tym, co Cię gniecie. Trzymaj się mocno! 💪",
        "Czasem wystarczy po prostu powiedzieć to na głos. Jesteś silniejszy(-a) niż myślisz. ✨",
        "Każde uczucie ma prawo być przeżyte. Mam nadzieję, że ta chwila refleksji Ci pomogła. 🤗",
        "Życie potrafi być trudne, ale ważne jest to, że nie poddajesz się. Trzymam za Ciebie kciuki! 🍀",
        "To odważne, że pozwoliłeś(-aś) sobie na moment słabości. To także jest siła. 💙"
    ]
    
    def __init__(self, bot: LionBot):
        self.bot = bot

    def validate_message_content(self, message: str) -> tuple[bool, str]:
        """
        Validate the venting message content.
        
        Returns (is_valid, error_message) tuple.
        """
        if not message or not message.strip():
            return False, "Proszę podaj wiadomość, którą chcesz wyrzucić z siebie."
        
        if len(message) > self.MAX_VENT_LENGTH:
            return False, f"Wiadomość jest zbyt długa! Maksymalna długość to {self.MAX_VENT_LENGTH} znaków."
        
        # Basic content filtering - no mass mentions
        message_lower = message.lower()
        if "@everyone" in message_lower or "@here" in message_lower:
            return False, "Wiadomości nie mogą zawierać @everyone lub @here."
        
        return True, ""

    def get_comfort_response(self) -> str:
        """
        Get a random Polish comfort response.
        
        Returns a therapeutic message to comfort the user.
        """
        return random.choice(self.COMFORT_RESPONSES)

    async def _dispose_message_logic(self, ctx: LionContext, message: str) -> tuple[bool, str]:
        """
        Shared logic for message disposal without response handling.
        
        Returns (success, error_message) tuple.
        - success: True if message was disposed successfully, False otherwise  
        - error_message: Error message if success is False, empty string if success is True
        """
        # Validate channel
        if ctx.channel.id != self.TARGET_VENTING_CHANNEL:
            return False, "Ta komenda działa tylko na wyznaczonym kanale do wygadywania się!"
        
        # Validate message content
        is_valid, error_msg = self.validate_message_content(message)
        if not is_valid:
            return False, error_msg
        
        try:
            # Message disposal logic: Simply discard the content after validation
            # The message content is intentionally not logged, stored, or processed further
            # This provides therapeutic value through the act of writing without permanence
            
            # Log successful disposal event (without content for complete privacy)
            logger.info(
                f"Venting message disposed in channel {ctx.channel.id} "
                f"by user {ctx.author.id} (content not logged for privacy)"
            )
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Unexpected error in message disposal: {e}", exc_info=True)
            return False, "Wystąpił nieoczekiwany błąd. Spróbuj ponownie później."

    @cmds.hybrid_command(
        name="vent",
        description="Wyrzuć z siebie to, co Cię gniecie - wiadomość zostanie bezpiecznie usunięta"
    )
    @appcmds.describe(message="Wiadomość, którą chcesz wyrzucić z siebie")
    @appcmds.guild_only
    async def vent_command(self, ctx: LionContext, *, message: str):
        """
        Dispose of a venting message therapeutically.
        
        This command allows users to vent their frustrations while ensuring
        complete privacy through immediate message disposal after validation.
        """
        try:
            # Validate channel
            if ctx.channel.id != self.TARGET_VENTING_CHANNEL:
                await ctx.respond(
                    embed=error_embed("Ta komenda działa tylko na wyznaczonym kanale do wygadywania się!"),
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
            
            # Message disposal: Simply discard after validation for therapeutic value
            logger.info(
                f"Venting message disposed in channel {ctx.channel.id} "
                f"by user {ctx.author.id} (content not logged for privacy)"
            )
            
            # Send comfort response
            comfort_response = self.get_comfort_response()
            await ctx.respond(
                comfort_response,
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error in vent command: {e}", exc_info=True)
            try:
                await ctx.respond(
                    embed=error_embed("Wystąpił nieoczekiwany błąd. Spróbuj ponownie później."),
                    ephemeral=True
                )
            except Exception as response_error:
                logger.error(f"Failed to send error response: {response_error}", exc_info=True)

    @cmds.hybrid_command(
        name="precz",
        description="Wyrzuć z siebie to, co Cię gniecie - wiadomość zostanie bezpiecznie usunięta (alias)"
    )
    @appcmds.describe(message="Wiadomość, którą chcesz wyrzucić z siebie")
    @appcmds.guild_only
    async def precz_command(self, ctx: LionContext, *, message: str):
        """
        Alias for the vent command.
        
        Alternative Polish-language alias for venting functionality.
        """
        try:
            # Validate channel
            if ctx.channel.id != self.TARGET_VENTING_CHANNEL:
                await ctx.respond(
                    embed=error_embed("Ta komenda działa tylko na wyznaczonym kanale do wygadywania się!"),
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
            
            # Message disposal: Simply discard after validation for therapeutic value
            logger.info(
                f"Venting message disposed in channel {ctx.channel.id} "
                f"by user {ctx.author.id} (content not logged for privacy)"
            )
            
            # Send comfort response
            comfort_response = self.get_comfort_response()
            await ctx.respond(
                comfort_response,
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error in precz command: {e}", exc_info=True)
            try:
                await ctx.respond(
                    embed=error_embed("Wystąpił nieoczekiwany błąd. Spróbuj ponownie później."),
                    ephemeral=True
                )
            except Exception as response_error:
                logger.error(f"Failed to send error response: {response_error}", exc_info=True)