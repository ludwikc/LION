#!/usr/bin/env python3
"""
LION Service Manager

Manages LION bot services (registry and bot) with proper dependency handling,
health checks, and recovery procedures.
"""

import subprocess
import time
import sys
import os
import signal
from pathlib import Path


class ServiceManager:
    def __init__(self):
        self.script_dir = Path(__file__).parent.parent
        os.chdir(self.script_dir)
        self.python_exe = self.get_python_executable()
        
    def get_python_executable(self):
        """Get the correct Python executable, preferring venv if available"""
        venv_paths = [
            self.script_dir / "venv" / "bin" / "python",
            self.script_dir / ".venv" / "bin" / "python", 
            self.script_dir / "env" / "bin" / "python"
        ]
        
        for venv_python in venv_paths:
            if venv_python.exists():
                print(f"✓ Using virtual environment: {venv_python}")
                return str(venv_python)
        
        print("⚠️  No virtual environment found, using system Python")
        return sys.executable

    def run_command(self, command, description, check=True):
        """Execute a shell command and handle errors"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                check=check, 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                print(f"✓ {description}")
            return result
        except subprocess.CalledProcessError as e:
            print(f"✗ {description}")
            if e.stderr:
                print(f"Error: {e.stderr}")
            return e

    def check_screen_session_exists(self, session_name):
        """Check if a screen session exists"""
        try:
            result = subprocess.run(
                "screen -list",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 1 and "No Sockets found" in result.stderr:
                return False
            return f".{session_name}" in result.stdout
        except subprocess.CalledProcessError:
            return False

    def kill_screen_session(self, session_name):
        """Kill a screen session if it exists"""
        if self.check_screen_session_exists(session_name):
            print(f"Found existing {session_name} session, terminating...")
            self.run_command(f"screen -S {session_name} -X quit", f"Killed {session_name} session")
            time.sleep(2)  # Give it time to terminate

    def get_lion_processes(self):
        """Get all LION-related processes"""
        try:
            result = subprocess.run(
                ["ps", "aux"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            lion_processes = []
            for line in result.stdout.split('\n'):
                if any(keyword in line.lower() for keyword in ['lion', 'start_leo', 'start_registry']):
                    if 'grep' not in line and line.strip():
                        lion_processes.append(line)
            
            return lion_processes
        except subprocess.CalledProcessError:
            return []

    def kill_all_lion_processes(self):
        """Kill all LION-related processes"""
        print("🔍 Checking for LION processes...")
        processes = self.get_lion_processes()
        
        if not processes:
            print("✓ No LION processes found")
            return
        
        print(f"Found {len(processes)} LION processes:")
        for proc in processes:
            print(f"  {proc}")
        
        # Kill screen sessions first
        self.kill_screen_session("LION-registry")
        self.kill_screen_session("LION-bot")
        
        # Wait a bit for graceful shutdown
        time.sleep(3)
        
        # Check for remaining processes
        remaining = self.get_lion_processes()
        if remaining:
            print("⚠️  Forcing termination of remaining processes...")
            for proc in remaining:
                try:
                    pid = proc.split()[1]
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"✓ Sent SIGTERM to PID {pid}")
                except (ValueError, ProcessLookupError, PermissionError) as e:
                    print(f"✗ Could not kill PID {pid}: {e}")
        
        time.sleep(2)
        final_check = self.get_lion_processes()
        if not final_check:
            print("✅ All LION processes terminated")
        else:
            print("⚠️  Some processes may still be running:")
            for proc in final_check:
                print(f"  {proc}")

    def test_database_connectivity(self):
        """Test database connectivity before starting services"""
        print("🔍 Testing database connectivity...")
        
        test_result = self.run_command(
            f"{self.python_exe} scripts/test_database.py",
            "Database connectivity test",
            check=False
        )
        
        if test_result.returncode == 0:
            print("✅ Database connectivity verified")
            return True
        else:
            print("❌ Database connectivity failed")
            print("Output:", test_result.stdout if test_result.stdout else "No output")
            print("Error:", test_result.stderr if test_result.stderr else "No error")
            return False

    def start_registry(self):
        """Start the registry service"""
        print("🔧 Starting LION Registry...")
        
        if self.check_screen_session_exists("LION-registry"):
            print("⚠️  Registry session already exists")
            return False
        
        command = f'screen -dmS LION-registry {self.python_exe} scripts/start_registry.py'
        result = self.run_command(command, "Started LION-registry screen session")
        
        if isinstance(result, subprocess.CalledProcessError):
            return False
        
        # Wait for registry to initialize
        print("⏳ Waiting for registry to initialize...")
        for i in range(15):  # Wait up to 15 seconds
            time.sleep(1)
            if not self.check_screen_session_exists("LION-registry"):
                print("❌ Registry session terminated unexpectedly")
                return False
            print(f"   Registry initializing... ({i+1}/15)")
        
        print("✅ Registry service started")
        return True

    def start_bot(self):
        """Start the bot service"""
        print("🤖 Starting LION Bot...")
        
        if self.check_screen_session_exists("LION-bot"):
            print("⚠️  Bot session already exists")
            return False
        
        command = f'screen -dmS LION-bot {self.python_exe} scripts/start_leo.py'
        result = self.run_command(command, "Started LION-bot screen session")
        
        if isinstance(result, subprocess.CalledProcessError):
            return False
        
        # Wait for bot to initialize
        print("⏳ Waiting for bot to initialize...")
        for i in range(10):  # Wait up to 10 seconds
            time.sleep(1)
            if not self.check_screen_session_exists("LION-bot"):
                print("❌ Bot session terminated unexpectedly")
                return False
            print(f"   Bot initializing... ({i+1}/10)")
        
        print("✅ Bot service started")
        return True

    def show_status(self):
        """Show current service status"""
        print("\n📊 Service Status:")
        print("=" * 40)
        
        # Check screen sessions
        registry_running = self.check_screen_session_exists("LION-registry")
        bot_running = self.check_screen_session_exists("LION-bot")
        
        print(f"Registry: {'✅ Running' if registry_running else '❌ Stopped'}")
        print(f"Bot:      {'✅ Running' if bot_running else '❌ Stopped'}")
        
        # Show all screen sessions
        print("\nActive screen sessions:")
        subprocess.run("screen -list", shell=True)
        
        # Show LION processes
        processes = self.get_lion_processes()
        if processes:
            print(f"\nLION processes ({len(processes)}):")
            for proc in processes:
                print(f"  {proc}")

    def restart_services(self, test_db=True):
        """Complete service restart"""
        print("🔄 LION Service Recovery")
        print("=" * 50)
        
        # Phase 1: Clean termination
        print("\n📝 Phase 1: Clean Service Termination")
        self.kill_all_lion_processes()
        
        # Phase 2: Database validation (optional)
        if test_db:
            print("\n📝 Phase 2: Database Connectivity Test")
            if not self.test_database_connectivity():
                print("⚠️  Database connectivity failed. Continuing anyway...")
                response = input("Continue with service restart? (y/N): ")
                if response.lower() != 'y':
                    print("Service restart cancelled")
                    return False
        
        # Phase 3: Staged restart
        print("\n📝 Phase 3: Staged Service Restart")
        
        # Start registry first
        if not self.start_registry():
            print("❌ Registry startup failed")
            return False
        
        # Start bot
        if not self.start_bot():
            print("❌ Bot startup failed")
            return False
        
        # Phase 4: Validation
        print("\n📝 Phase 4: Service Validation")
        time.sleep(3)  # Let services settle
        
        registry_ok = self.check_screen_session_exists("LION-registry")
        bot_ok = self.check_screen_session_exists("LION-bot")
        
        if registry_ok and bot_ok:
            print("🎉 Service restart successful!")
            self.show_status()
            return True
        else:
            print("❌ Service restart failed - some services not running")
            self.show_status()
            return False


def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python service_manager.py <command>")
        print("Commands:")
        print("  restart    - Full service restart with database test")
        print("  restart-force - Restart without database test")
        print("  stop       - Stop all services")
        print("  start      - Start services (registry then bot)")
        print("  status     - Show service status")
        print("  test-db    - Test database connectivity only")
        sys.exit(1)
    
    manager = ServiceManager()
    command = sys.argv[1].lower()
    
    if command == "restart":
        success = manager.restart_services(test_db=True)
        sys.exit(0 if success else 1)
    elif command == "restart-force":
        success = manager.restart_services(test_db=False)
        sys.exit(0 if success else 1)
    elif command == "stop":
        manager.kill_all_lion_processes()
    elif command == "start":
        success = manager.start_registry() and manager.start_bot()
        sys.exit(0 if success else 1)
    elif command == "status":
        manager.show_status()
    elif command == "test-db":
        success = manager.test_database_connectivity()
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()