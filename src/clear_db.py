"""
Clear database script
Run this to drop all tables and recreate them
"""
import sys
import os
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.database import Base, engine, init_db

if __name__ == "__main__":
    print("⚠️  WARNING: This will delete all data from the database!")
    confirmation = input("Are you sure you want to continue? (yes/no): ")
    
    if confirmation.lower() == "yes":
        try:
            print("🗑️  Dropping all tables...")
            Base.metadata.drop_all(bind=engine)
            print("✅ All tables dropped successfully!")
            
            print("🔨 Creating fresh tables...")
            init_db()
            print("✅ Database cleared and reinitialized successfully!")
            print("Tables created: papers, queries")
        except Exception as e:
            print(f"❌ Error clearing database: {e}")
    else:
        print("❌ Operation cancelled.")
