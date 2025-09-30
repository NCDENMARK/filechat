"""
Run this script to clear the ChromaDB database and start fresh.
This is useful when the database gets corrupted or you want to re-index everything.
"""

import shutil
from pathlib import Path
from config import DB_DIR

def clear_database():
    """Delete the entire ChromaDB database folder"""
    try:
        db_path = Path(DB_DIR)
        
        if db_path.exists():
            print(f"Deleting database at: {db_path}")
            shutil.rmtree(db_path)
            print("✓ Database deleted successfully!")
            
            # Recreate the empty directory
            db_path.mkdir(parents=True, exist_ok=True)
            print("✓ Fresh database directory created")
            print("\nYou can now restart your server and re-index your files.")
        else:
            print(f"Database directory not found at: {db_path}")
            print("Nothing to clear.")
    
    except Exception as e:
        print(f"✗ Error clearing database: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("FileChat Database Cleaner")
    print("=" * 50)
    print("\nThis will permanently delete all indexed documents.")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        clear_database()
    else:
        print("Operation cancelled.")