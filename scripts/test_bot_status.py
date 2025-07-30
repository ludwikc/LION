#!/usr/bin/env python3
"""
Bot status checker - verifies if LION bot is responsive and functioning.
"""

import asyncio
import sys
import os
import subprocess
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def check_processes():
    """Check if bot processes are running"""
    print("🔍 Checking LION processes...")
    
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
                    lion_processes.append(line.strip())
        
        if lion_processes:
            print(f"✅ Found {len(lion_processes)} LION processes:")
            for proc in lion_processes:
                print(f"  {proc}")
            return True
        else:
            print("❌ No LION processes found")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error checking processes: {e}")
        return False

def check_screen_sessions():
    """Check screen sessions"""
    print("\n🖥️  Checking screen sessions...")
    
    try:
        result = subprocess.run(
            "screen -list",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if "LION-registry" in result.stdout and "LION-bot" in result.stdout:
            print("✅ Both LION screen sessions are running")
            return True
        else:
            print("❌ Missing LION screen sessions")
            print("Screen output:", result.stdout)
            return False
            
    except Exception as e:
        print(f"❌ Error checking screen sessions: {e}")
        return False

def check_bot_logs():
    """Check recent bot logs for errors"""
    print("\n📋 Checking recent bot logs...")
    
    try:
        # Capture recent bot screen output
        subprocess.run(
            "screen -S LION-bot -X hardcopy /tmp/bot_check.log",
            shell=True,
            check=True
        )
        
        with open("/tmp/bot_check.log", "r", errors='ignore') as f:
            log_content = f.read()
        
        # Look for key indicators
        if "Ready" in log_content or "ready" in log_content:
            print("✅ Bot appears to be ready")
            
        if "Connected" in log_content or "connected" in log_content:
            print("✅ Bot appears to be connected")
            
        # Check for recent errors
        error_lines = []
        for line in log_content.split('\n')[-50:]:  # Check last 50 lines
            if any(keyword in line.lower() for keyword in ['error', 'exception', 'traceback', 'failed']):
                error_lines.append(line.strip())
        
        if error_lines:
            print(f"⚠️  Found {len(error_lines)} recent errors:")
            for line in error_lines[-5:]:  # Show last 5 errors
                print(f"    {line}")
        else:
            print("✅ No obvious errors in recent logs")
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking bot logs: {e}")
        return False

def check_database_connection():
    """Quick database connection check"""
    print("\n🐘 Quick database connection check...")
    
    try:
        result = subprocess.run(
            [sys.executable, "scripts/test_database.py"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            timeout=30
        )
        
        if "Database connection successful" in result.stdout:
            print("✅ Database connection working")
            return True
        else:
            print("⚠️  Database connection issues detected")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Database test timed out")
        return False
    except Exception as e:
        print(f"⚠️  Database test failed: {e}")
        return False

def main():
    """Run bot status checks"""
    print("🤖 LION Bot Status Check")
    print("=" * 40)
    
    checks = [
        ("Process Check", check_processes),
        ("Screen Sessions", check_screen_sessions), 
        ("Bot Logs", check_bot_logs),
        ("Database Connection", check_database_connection),
    ]
    
    results = {}
    for check_name, check_func in checks:
        print(f"\n{'='*15} {check_name} {'='*15}")
        results[check_name] = check_func()
    
    # Summary
    print(f"\n{'='*40}")
    print("📊 Status Summary:")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for check_name, passed_check in results.items():
        status = "✅ OK" if passed_check else "❌ ISSUE"
        print(f"  {check_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed >= 3:  # Allow for minor issues
        print("🎉 Bot appears to be running normally!")
        print("\n💡 Try testing these commands in Discord:")
        print("  - /vent (in venting channel)")
        print("  - /secret (in secrets channel)")
        print("  - /leaderboard (message activity)")
        return 0
    else:
        print("⚠️  Bot may have issues. Check the failed checks above.")
        return 1

if __name__ == "__main__":
    # Change to LION directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)
    
    sys.exit(main())