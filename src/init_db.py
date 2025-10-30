"""
Database initialization script
Run this to create the database tables
"""
import sys
import os
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.database import init_db

if __name__ == "__main__":
    print("Initializing database...")
    try:
        init_db()
        print("✅ Database initialized successfully!")
        print("Tables created: papers, queries")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
