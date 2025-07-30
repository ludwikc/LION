#!/usr/bin/env python3
"""
Test bot Discord connection by checking if it can see guilds and channels.
"""

import sys
import os
import asyncio
import configparser
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import discord
    from discord.ext import commands
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the LION directory with venv activated")
    sys.exit(1)


def get_bot_token():
    """Load bot token from secrets.conf"""
    config = configparser.ConfigParser()
    config.read('config/secrets.conf')
    
    if 'STUDYLION' not in config:
        raise ValueError("STUDYLION section not found in secrets.conf")
    
    return config['STUDYLION']['token']


async def test_bot_connection():
    """Test if bot can connect to Discord and see guilds"""
    print("🤖 Testing Discord bot connection...")
    
    try:
        token = get_bot_token()
        
        # Create minimal bot instance
        intents = discord.Intents.default()
        intents.guilds = True
        intents.guild_messages = True
        intents.message_content = True
        
        bot = commands.Bot(command_prefix='!test!', intents=intents)
        
        @bot.event
        async def on_ready():
            print(f"✅ Bot connected as {bot.user}")
            print(f"📊 Bot is in {len(bot.guilds)} guilds:")
            
            for guild in bot.guilds:
                print(f"   - {guild.name} (id: {guild.id})")
                
                # Check if venting module commands are registered
                app_commands = await bot.tree.fetch_commands(guild=guild)
                vent_commands = [cmd for cmd in app_commands if 'vent' in cmd.name.lower()]
                secret_commands = [cmd for cmd in app_commands if 'secret' in cmd.name.lower()]
                
                print(f"     Vent commands: {[cmd.name for cmd in vent_commands]}")
                print(f"     Secret commands: {[cmd.name for cmd in secret_commands]}")
            
            await bot.close()
        
        # Start bot with timeout
        try:
            await asyncio.wait_for(bot.start(token), timeout=30.0)
        except asyncio.TimeoutError:
            print("❌ Bot connection timed out")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Bot connection failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_bot_connection())
    sys.exit(0 if success else 1)