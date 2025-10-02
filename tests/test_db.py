"""
Test script to verify PostgreSQL database connection.

This script tests:
1. Database connection establishment
2. Basic query execution with 'SELECT 1'

Before running:
- Ensure PostgreSQL is running and accessible
- Configure database credentials in .env.local

Usage:
    python tests/test_db.py
"""

import sys
import os

# Add src to path to import lib modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lib.db import open_connection, close_connection, execute_query


def test_connection():
    """Test database connection"""
    print("Testing database connection...")

    try:
        success = open_connection()
        if success:
            print("✓ Connection established successfully")
            return True
        else:
            print("✗ Connection failed")
            return False
    except Exception as e:
        print(f"✗ Connection failed with exception: {e}")
        return False


def test_select_query():
    """Test basic SELECT query"""
    print("\nTesting SELECT 1 query...")

    try:
        result = execute_query("SELECT 1", is_select_query=True)

        if result and len(result) > 0 and result[0][0] == 1:
            print(f"✓ Query executed successfully: result = {result[0][0]}")
            return True
        else:
            print(f"✗ Unexpected result: {result}")
            return False
    except Exception as e:
        print(f"✗ Query failed: {e}")
        return False


def main():
    """Run database tests"""
    print("=" * 50)
    print("PostgreSQL Database Connection Test")
    print("=" * 50)

    tests_passed = 0
    tests_total = 2
    connection_successful = False

    try:
        # Test 1: Connection
        if test_connection():
            tests_passed += 1
            connection_successful = True

        # Test 2: SELECT query (only if connection succeeded)
        if connection_successful:
            if test_select_query():
                tests_passed += 1
        else:
            print("\nSkipping SELECT query test (connection failed)")

    finally:
        # Always try to close connection
        try:
            close_connection()
        except:
            pass  # Ignore errors if connection was never established

    # Summary
    print("\n" + "=" * 50)
    print(f"Tests passed: {tests_passed}/{tests_total}")

    if tests_passed == tests_total:
        print("✓ All tests passed!")
        print("=" * 50)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 50)
        return 1


if __name__ == "__main__":
    exit(main())
