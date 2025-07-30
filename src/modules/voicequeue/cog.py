import logging
import asyncio
import datetime as dt
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import discord
from discord.ext import commands as cmds
from discord import app_commands as appcmds

from meta import LionBot, LionCog, LionContext
from utils.lib import error_embed, utc_now

logger = logging.getLogger(__name__)


@dataclass
class QueueEntry:
    """Represents a user in a voice queue."""
    user_id: int
    position: int
    joined_at: dt.datetime = field(default_factory=utc_now)


@dataclass
class VoiceQueue:
    """Represents a voice queue for a specific channel."""
    channel_id: int
    entries: List[QueueEntry] = field(default_factory=list)
    current_speaker: Optional[int] = None
    last_updated: dt.datetime = field(default_factory=utc_now)
    display_message: Optional[discord.Message] = None

    def get_current_speaker(self) -> Optional[int]:
        """Get the current speaker (front of queue)."""
        if self.entries:
            return self.entries[0].user_id
        return None

    def add_user(self, user_id: int) -> bool:
        """Add user to queue if not already present. Returns True if added."""
        if any(entry.user_id == user_id for entry in self.entries):
            return False
        
        position = len(self.entries) + 1
        self.entries.append(QueueEntry(user_id=user_id, position=position))
        self.last_updated = utc_now()
        return True

    def remove_user(self, user_id: int) -> bool:
        """Remove user from queue. Returns True if removed."""
        for i, entry in enumerate(self.entries):
            if entry.user_id == user_id:
                self.entries.pop(i)
                # Reorder positions
                for j, remaining_entry in enumerate(self.entries[i:], start=i):
                    remaining_entry.position = j + 1
                self.last_updated = utc_now()
                return True
        return False

    def advance_queue(self) -> Optional[int]:
        """Remove current speaker and advance queue. Returns new current speaker."""
        if self.entries:
            removed = self.entries.pop(0)
            # Reorder positions
            for i, entry in enumerate(self.entries):
                entry.position = i + 1
            self.last_updated = utc_now()
            return self.get_current_speaker()
        return None


class QueueManager:
    """Manages voice queues across all channels."""
    
    def __init__(self):
        self.queues: Dict[int, VoiceQueue] = {}
        self.voice_timers: Dict[Tuple[int, int], asyncio.Task] = {}  # (channel_id, user_id) -> task

    def get_queue(self, channel_id: int) -> VoiceQueue:
        """Get or create queue for channel."""
        if channel_id not in self.queues:
            self.queues[channel_id] = VoiceQueue(channel_id=channel_id)
        return self.queues[channel_id]

    async def add_to_queue(self, channel_id: int, user_id: int) -> bool:
        """Add user to queue. Returns True if added."""
        queue = self.get_queue(channel_id)
        return queue.add_user(user_id)

    async def remove_from_queue(self, channel_id: int, user_id: int) -> bool:
        """Remove user from queue. Returns True if removed."""
        if channel_id in self.queues:
            return self.queues[channel_id].remove_user(user_id)
        return False

    async def advance_queue(self, channel_id: int) -> Optional[int]:
        """Advance queue by removing current speaker. Returns new current speaker."""
        if channel_id in self.queues:
            return self.queues[channel_id].advance_queue()
        return None

    async def get_queue_display_text(self, channel_id: int, guild: discord.Guild) -> str:
        """Generate queue display text."""
        if channel_id not in self.queues or not self.queues[channel_id].entries:
            return "🚂 **Kolejka do mówienia**\n\n📋 Kolejka jest pusta.\n\nUżyj `/kolejka` aby dołączyć!"

        queue = self.queues[channel_id]
        channel = guild.get_channel(channel_id)
        channel_name = channel.name if channel else "nieznany kanał"
        
        text = f"🚂 **Kolejka do mówienia w #{channel_name}**\n\n"
        
        if queue.entries:
            current_speaker = queue.get_current_speaker()
            if current_speaker:
                user = guild.get_member(current_speaker)
                user_name = user.display_name if user else f"<@{current_speaker}>"
                text += f"**🎤 Obecnie mówi:** {user_name}\n\n"
            
            if len(queue.entries) > 1:
                text += "📋 **W kolejce:**\n"
                for i, entry in enumerate(queue.entries[1:], start=2):
                    user = guild.get_member(entry.user_id)
                    user_name = user.display_name if user else f"<@{entry.user_id}>"
                    text += f"{i}. {user_name}\n"
            else:
                text += "📋 Kolejka jest pusta po obecnym mówcy.\n"
        
        text += f"\nUżyj `/kolejka` aby dołączyć!"
        return text

    def cancel_voice_timer(self, channel_id: int, user_id: int):
        """Cancel voice activity timer for user."""
        key = (channel_id, user_id)
        if key in self.voice_timers:
            self.voice_timers[key].cancel()
            del self.voice_timers[key]

    async def start_voice_timer(self, channel_id: int, user_id: int, callback):
        """Start 15-second voice activity timer."""
        key = (channel_id, user_id)
        self.cancel_voice_timer(channel_id, user_id)
        
        async def timer_callback():
            try:
                await asyncio.sleep(15)
                await callback(channel_id, user_id)
            except asyncio.CancelledError:
                pass
            finally:
                if key in self.voice_timers:
                    del self.voice_timers[key]
        
        self.voice_timers[key] = asyncio.create_task(timer_callback())


class VoiceQueueCog(LionCog):
    """
    Voice queue management for organized speaking in voice channels.
    
    Manages FIFO queues with automatic advancement based on voice activity,
    providing structured discussion flow for meetings and group conversations.
    """
    
    def __init__(self, bot: LionBot):
        self.bot = bot
        self.queue_manager = QueueManager()

    @cmds.hybrid_command(
        name="kolejka",
        description="Dołącz do kolejki do mówienia w kanale głosowym"
    )
    @appcmds.guild_only
    async def queue_command(self, ctx: LionContext):
        """
        Join the speaking queue for the voice channel.
        
        Users must be in a voice channel to join its speaking queue.
        Creates a new queue if one doesn't exist for the channel.
        """
        # Check if user is in voice channel
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.respond(
                embed=error_embed("Musisz być w kanale głosowym aby dołączyć do kolejki!"),
                ephemeral=True
            )
            return

        voice_channel = ctx.author.voice.channel
        channel_id = voice_channel.id
        user_id = ctx.author.id

        # Try to add user to queue
        added = await self.queue_manager.add_to_queue(channel_id, user_id)
        
        if not added:
            await ctx.respond(
                "Już jesteś w kolejce! 🚂",
                ephemeral=True
            )
            return

        # Generate queue display
        queue_text = await self.queue_manager.get_queue_display_text(channel_id, ctx.guild)
        
        # Get existing queue message or create new one
        queue = self.queue_manager.get_queue(channel_id)
        
        try:
            if queue.display_message:
                # Try to edit existing message
                try:
                    await queue.display_message.edit(content=queue_text)
                except discord.NotFound:
                    # Message was deleted, create new one
                    queue.display_message = await ctx.send(queue_text)
            else:
                # Create new queue display message
                queue.display_message = await ctx.send(queue_text)
            
            await ctx.respond(
                f"Dołączyłeś(-aś) do kolejki w #{voice_channel.name}! 🎤",
                ephemeral=True
            )
            
            logger.info(
                f"User {ctx.author.id} joined voice queue in channel {channel_id} "
                f"(guild {ctx.guild.id})"
            )
            
        except discord.HTTPException as e:
            logger.error(f"Failed to update queue display: {e}")
            await ctx.respond(
                embed=error_embed("Dołączyłeś(-aś) do kolejki, ale nie udało się zaktualizować wyświetlania."),
                ephemeral=True
            )

    @LionCog.listener('on_voice_state_update')
    async def voice_queue_tracker(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """
        Monitor voice state changes for queue management.
        
        Handles:
        - User leaving voice channel (remove from queue)
        - User muting/unmuting (start/cancel 15s timer)
        - Queue advancement based on voice activity
        """
        if member.bot:
            return

        # Handle user leaving voice channel
        if before.channel and not after.channel:
            await self._handle_user_left_voice(member, before.channel)
            return

        # Handle mute state changes
        if before.channel and after.channel and before.channel == after.channel:
            await self._handle_mute_state_change(member, before, after)

    async def _handle_user_left_voice(self, member: discord.Member, channel: discord.VoiceChannel):
        """Handle user leaving voice channel."""
        removed = await self.queue_manager.remove_from_queue(channel.id, member.id)
        
        if removed:
            # Cancel any pending voice timer
            self.queue_manager.cancel_voice_timer(channel.id, member.id)
            
            # Update queue display
            await self._update_queue_display(channel.id, member.guild)
            
            logger.info(
                f"User {member.id} removed from voice queue (left channel {channel.id})"
            )

    async def _handle_mute_state_change(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Handle user mute state changes."""
        channel_id = after.channel.id
        user_id = member.id
        
        # User muted - cancel timer if exists
        if not before.self_mute and after.self_mute:
            self.queue_manager.cancel_voice_timer(channel_id, user_id)
            return
        
        # User unmuted - start 15s timer
        if before.self_mute and not after.self_mute:
            await self.queue_manager.start_voice_timer(
                channel_id, 
                user_id, 
                self._handle_voice_activity_threshold
            )

    async def _handle_voice_activity_threshold(self, channel_id: int, user_id: int):
        """Handle voice activity after 15-second threshold."""
        queue = self.queue_manager.get_queue(channel_id)
        current_speaker = queue.get_current_speaker()
        
        if current_speaker == user_id:
            # Current speaker spoke for >15s - advance queue
            await self.queue_manager.advance_queue(channel_id)
            await self._update_queue_display(channel_id, self.bot.get_guild(queue.channel_id))
            
            logger.info(
                f"Voice queue advanced in channel {channel_id} (speaker {user_id} finished)"
            )
        else:
            # Non-current speaker spoke for >15s - send reminder
            guild = None
            for g in self.bot.guilds:
                if g.get_channel(channel_id):
                    guild = g
                    break
            
            if guild:
                member = guild.get_member(user_id)
                if member:
                    try:
                        await member.send("Pamiętaj o /kolejka 🚂")
                    except discord.Forbidden:
                        # Can't DM user, try to send ephemeral in a channel they can see
                        pass
                    
                    logger.info(
                        f"Voice queue reminder sent to user {user_id} in channel {channel_id}"
                    )

    async def _update_queue_display(self, channel_id: int, guild: discord.Guild):
        """Update the queue display message."""
        if channel_id not in self.queue_manager.queues:
            return
        
        queue = self.queue_manager.queues[channel_id]
        if not queue.display_message:
            return
        
        try:
            queue_text = await self.queue_manager.get_queue_display_text(channel_id, guild)
            await queue.display_message.edit(content=queue_text)
        except discord.NotFound:
            # Message was deleted
            queue.display_message = None
        except discord.HTTPException as e:
            logger.error(f"Failed to update queue display for channel {channel_id}: {e}")