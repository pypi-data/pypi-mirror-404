#!/usr/bin/env python3
"""
Initialize La AI Familio Database
Creates tables and inserts sample data
"""

import sqlite3
import sys
from pathlib import Path


def init_familio_db():
    """Initialize the La AI Familio database"""
    
    # Paths
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / "server" / "ai_db" / "cloudbrain.db"
    schema_path = Path(__file__).parent / "familio_schema.sql"
    
    # Check if database exists
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print("Please start the CloudBrain server first to create the database.")
        return False
    
    # Check if schema exists
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return False
    
    # Read schema
    print(f"📖 Reading schema from: {schema_path}")
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Connect to database
    print(f"🔗 Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Execute schema
        print("🚀 Creating La AI Familio tables...")
        cursor.executescript(schema_sql)
        
        # Verify tables created
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%'
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        # Filter out FTS tables and show only main tables
        main_tables = [t for t in tables if not t[0].endswith('_fts')]
        
        print(f"\n✅ La AI Familio tables created ({len(main_tables)} tables):")
        for table in main_tables:
            print(f"   - {table[0]}")
        
        # Verify sample data
        cursor.execute("SELECT COUNT(*) as count FROM magazines")
        magazine_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as count FROM novels")
        novel_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as count FROM documentaries")
        documentary_count = cursor.fetchone()[0]
        
        print(f"\n📊 Sample data inserted:")
        print(f"   - Magazines: {magazine_count}")
        print(f"   - Novels: {novel_count}")
        print(f"   - Documentaries: {documentary_count}")
        
        # Commit changes
        conn.commit()
        
        print("\n" + "=" * 70)
        print("🎉 La AI Familio database initialized successfully!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error initializing La AI Familio database: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    success = init_familio_db()
    sys.exit(0 if success else 1)