#!/usr/bin/env python3
"""
LION Bot Launcher Script

Manages the complete startup sequence:
1. Start LION-registry screen session and launch registry service
2. Wait 10 seconds for registry to initialize
3. Start LION-bot screen session and launch main bot
4. Report success status
"""

import subprocess
import time
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Execute a shell command and handle errors"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(f"✓ {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description}")
        print(f"Error: {e.stderr}")
        return False


def check_screen_session_exists(session_name):
    """Check if a screen session already exists"""
    try:
        result = subprocess.run(
            "screen -list",
            shell=True,
            capture_output=True,
            text=True
        )
        # screen -list returns 0 if sessions exist, 1 if no sessions
        if result.returncode == 1 and "No Sockets found" in result.stderr:
            return False
        # Screen sessions are listed as "PID.sessionname"
        # Look for ".sessionname" pattern to match our session
        return f".{session_name}" in result.stdout
    except subprocess.CalledProcessError:
        return False


def kill_existing_session(session_name):
    """Kill existing screen session if it exists"""
    if check_screen_session_exists(session_name):
        print(f"Found existing {session_name} session, terminating...")
        run_command(f"screen -S {session_name} -X quit", f"Terminated existing {session_name}")


def get_python_executable():
    """Get the correct Python executable, preferring venv if available"""
    script_dir = Path(__file__).parent
    
    # Check for common venv locations
    venv_paths = [
        script_dir / "venv" / "bin" / "python",
        script_dir / ".venv" / "bin" / "python", 
        script_dir / "env" / "bin" / "python"
    ]
    
    for venv_python in venv_paths:
        if venv_python.exists():
            print(f"✓ Found virtual environment: {venv_python}")
            return str(venv_python)
    
    print("⚠️  No virtual environment found, using system Python")
    return sys.executable


def main():
    print("🦁 LION Bot Launcher")
    print("=" * 50)
    
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print(f"Working directory: {os.getcwd()}")
    
    # Get the correct Python executable
    python_exe = get_python_executable()
    
    # Check if required scripts exist
    registry_script = "scripts/start_registry.py"
    bot_script = "scripts/start_leo.py"
    
    if not Path(registry_script).exists():
        print(f"✗ Registry script not found: {registry_script}")
        sys.exit(1)
        
    if not Path(bot_script).exists():
        print(f"✗ Bot script not found: {bot_script}")
        sys.exit(1)
    
    # Check if dependencies are installed
    print("🔍 Checking dependencies...")
    try:
        subprocess.run([python_exe, "-c", "import discord"], 
                      check=True, capture_output=True)
        print("✓ Discord.py dependency found")
    except subprocess.CalledProcessError:
        print("✗ Missing dependencies. Run: pip install -r requirements.txt")
        if "venv" in python_exe:
            print("   Make sure to activate venv first: source venv/bin/activate")
        sys.exit(1)
    
    # Kill any existing sessions
    kill_existing_session("LION-registry")
    kill_existing_session("LION-bot")
    
    print("\n🔧 Starting LION Registry...")
    
    # Start registry in screen session
    registry_command = f'screen -dmS LION-registry {python_exe} {registry_script}'
    if not run_command(registry_command, "Started LION-registry screen session"):
        print("Failed to start registry service")
        sys.exit(1)
    
    # Wait for registry to initialize
    print("⏳ Waiting 10 seconds for registry to initialize...")
    time.sleep(10)
    
    # Verify registry session is still running
    if not check_screen_session_exists("LION-registry"):
        print("✗ Registry session appears to have crashed")
        print("Debug: Current screen sessions:")
        subprocess.run("screen -list", shell=True)
        
        # Try to get the actual error from the registry
        print("\n📋 Testing registry startup manually...")
        try:
            result = subprocess.run([python_exe, registry_script], 
                                  capture_output=True, text=True, timeout=5)
            if result.stderr:
                print(f"Registry error: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("Registry seems to hang - may need configuration")
        except Exception as e:
            print(f"Registry test failed: {e}")
        
        sys.exit(1)
    
    print("\n🤖 Starting LION Bot...")
    
    # Start bot in screen session
    bot_command = f'screen -dmS LION-bot {python_exe} {bot_script}'
    if not run_command(bot_command, "Started LION-bot screen session"):
        print("Failed to start bot service")
        sys.exit(1)
    
    # Brief wait to ensure bot session starts properly
    time.sleep(2)
    
    # Verify bot session is running
    if not check_screen_session_exists("LION-bot"):
        print("✗ Bot session appears to have crashed")
        sys.exit(1)
    
    print("\n✅ SUCCESS: LION Bot launched successfully!")
    print("\nActive screen sessions:")
    subprocess.run("screen -list", shell=True)
    
    print("\n📋 Useful commands:")
    print("  screen -r LION-registry  # Attach to registry session")
    print("  screen -r LION-bot       # Attach to bot session")
    print("  screen -list             # List all sessions")
    print("  screen -S <session> -X quit  # Kill a session")


if __name__ == "__main__":
    main()