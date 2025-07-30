#!/usr/bin/env python3
"""
Database connectivity test script for LION bot.

Tests connection to external PostgreSQL database using configuration
from config/secrets.conf to validate connectivity before starting services.
"""

import sys
import os
import asyncio
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import psycopg
    import configparser
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the LION directory with venv activated")
    sys.exit(1)


def get_database_config():
    """Load database configuration from secrets.conf"""
    config = configparser.ConfigParser()
    config.read('config/secrets.conf')
    
    if 'DATA' not in config:
        raise ValueError("DATA section not found in secrets.conf")
    
    return config['DATA']['args']


async def test_basic_connection():
    """Test basic database connection"""
    print("🔍 Testing basic database connection...")
    
    try:
        # Get database connection string from config
        db_args = get_database_config()
        print(f"Database config: {db_args}")
        
        # Test connection
        start_time = time.time()
        async with await psycopg.AsyncConnection.connect(db_args) as conn:
            connect_time = time.time() - start_time
            print(f"✅ Database connection successful ({connect_time:.2f}s)")
            
            # Test basic query
            async with conn.cursor() as cur:
                await cur.execute("SELECT version();")
                version = await cur.fetchone()
                print(f"✅ PostgreSQL version: {version[0]}")
                
            return True
            
    except psycopg.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def test_lion_tables():
    """Test access to LION-specific tables"""
    print("\n🔍 Testing LION table access...")
    
    try:
        db_args = get_database_config()
        async with await psycopg.AsyncConnection.connect(db_args) as conn:
            async with conn.cursor() as cur:
                # Test core tables exist (PostgreSQL uses lowercase)
                test_tables = [
                    'versionhistory',
                    'user_config', 
                    'guild_config',
                    'members'
                ]
                
                for table in test_tables:
                    try:
                        await cur.execute(f"SELECT COUNT(*) FROM {table};")
                        count = await cur.fetchone()
                        print(f"✅ Table {table}: {count[0]} rows")
                    except psycopg.Error as e:
                        print(f"❌ Table {table} access failed: {e}")
                        return False
                        
                return True
                
    except Exception as e:
        print(f"❌ Table access test failed: {e}")
        return False


async def test_connection_pool():
    """Test multiple concurrent connections"""
    print("\n🔍 Testing connection pool...")
    
    try:
        db_args = get_database_config()
        connections = []
        
        # Create multiple connections
        for i in range(5):
            conn = await psycopg.AsyncConnection.connect(db_args)
            connections.append(conn)
            
        print(f"✅ Successfully created {len(connections)} concurrent connections")
        
        # Test queries on all connections
        tasks = []
        for i, conn in enumerate(connections):
            async def test_query(connection, conn_id):
                async with connection.cursor() as cur:
                    await cur.execute("SELECT current_timestamp;")
                    result = await cur.fetchone()
                    print(f"✅ Connection {conn_id}: {result[0]}")
            
            tasks.append(test_query(conn, i))
        
        await asyncio.gather(*tasks)
        
        # Close all connections
        for conn in connections:
            await conn.close()
            
        print("✅ Connection pool test successful")
        return True
        
    except Exception as e:
        print(f"❌ Connection pool test failed: {e}")
        return False


async def test_database_performance():
    """Test database response times"""
    print("\n🔍 Testing database performance...")
    
    try:
        db_args = get_database_config()
        
        # Test multiple queries and measure time
        times = []
        for i in range(10):
            start = time.time()
            async with await psycopg.AsyncConnection.connect(db_args) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT current_timestamp;")
                    await cur.fetchone()
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"✅ Average query time: {avg_time:.3f}s")
        print(f"   Min: {min_time:.3f}s, Max: {max_time:.3f}s")
        
        if avg_time > 2.0:
            print("⚠️  Warning: Database response times are slow")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False


async def main():
    """Run all database tests"""
    print("🐘 LION Database Connectivity Test")
    print("=" * 50)
    
    # Change to LION directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)
    print(f"Working directory: {os.getcwd()}")
    
    # Run tests
    tests = [
        ("Basic Connection", test_basic_connection),
        ("LION Tables", test_lion_tables),
        ("Connection Pool", test_connection_pool),
        ("Performance", test_database_performance),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 Test Summary:")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All database tests passed! Bot should be able to connect.")
        return 0
    else:
        print("⚠️  Some database tests failed. Check connectivity and configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))