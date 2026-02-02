#!/usr/bin/env python3
"""
GFRAM Basic Usage Example
=========================

This example shows the simplest way to use GFRAM for face recognition.

Usage:
    python basic_usage.py

Requirements:
    pip install gfram
"""

import gfram

def main():
    print("=" * 50)
    print("🎯 GFRAM Basic Usage Example")
    print("=" * 50)
    
    # Check version
    print(f"\n📦 GFRAM Version: {gfram.__version__}")
    
    # Get statistics
    stats = gfram.stats()
    print(f"📊 Initial stats: {stats}")
    
    # Clear database (fresh start)
    gfram.clear()
    print("\n✅ Database cleared")
    
    # List persons (should be empty)
    persons = gfram.list_persons()
    print(f"👥 Persons in database: {persons}")
    
    print("\n" + "=" * 50)
    print("To add a real person, use:")
    print("  gfram.add('John', 'path/to/john.jpg')")
    print("")
    print("To recognize:")
    print("  result = gfram.recognize('path/to/test.jpg')")
    print("  print(result)")
    print("=" * 50)


if __name__ == '__main__':
    main()
