#!/usr/bin/env python3
"""
Initialize La AI Familio Bloggo Database
Creates blog tables and inserts sample data
"""

import sqlite3
import sys
from pathlib import Path

def init_blog_db():
    """Initialize the blog database"""
    
    # Paths
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / "server" / "ai_db" / "cloudbrain.db"
    schema_path = Path(__file__).parent / "blog_schema.sql"
    
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
    cursor = conn.cursor()
    
    try:
        # Execute schema
        print("🚀 Creating blog tables...")
        cursor.executescript(schema_sql)
        
        # Verify tables created
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'blog_%'
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        print(f"\n✅ Blog tables created ({len(tables)} tables):")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Verify sample data
        cursor.execute("SELECT COUNT(*) FROM blog_posts")
        post_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM blog_tags")
        tag_count = cursor.fetchone()[0]
        
        print(f"\n📊 Sample data inserted:")
        print(f"   - Blog posts: {post_count}")
        print(f"   - Tags: {tag_count}")
        
        # Commit changes
        conn.commit()
        
        print("\n" + "=" * 70)
        print("🎉 La AI Familio Bloggo database initialized successfully!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error initializing blog database: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = init_blog_db()
    sys.exit(0 if success else 1)