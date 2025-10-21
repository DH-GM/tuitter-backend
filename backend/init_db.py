"""
Database initialization script for Railway deployment
Run this once after deploying PostgreSQL to initialize schema and seed data.

Usage:
    railway run python init_db.py
    
Or locally:
    export DATABASE_URL="your_database_url"
    python init_db.py
"""
import os
import sys
from pathlib import Path

try:
    import psycopg2
except ImportError:
    print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


def init_database():
    """Initialize database with schema and seed data"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    print(f"Connecting to database...")
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Get path to SQL files
        backend_dir = Path(__file__).parent
        project_root = backend_dir.parent
        schema_file = project_root / "database" / "schema.sql"
        seed_file = project_root / "database" / "seed_data.sql"
        
        # Execute schema
        print("Creating database schema...")
        if schema_file.exists():
            with open(schema_file, 'r') as f:
                cur.execute(f.read())
            print("✓ Schema created successfully")
        else:
            print(f"Warning: Schema file not found at {schema_file}")
        
        # Execute seed data
        print("Loading seed data...")
        if seed_file.exists():
            with open(seed_file, 'r') as f:
                cur.execute(f.read())
            print("✓ Seed data loaded successfully")
        else:
            print(f"Warning: Seed data file not found at {seed_file}")
        
        # Verify tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        
        print(f"\n✓ Database initialized successfully!")
        print(f"  Created {len(tables)} tables:")
        for table in tables:
            print(f"    - {table[0]}")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("Social.vim Database Initialization")
    print("=" * 60)
    init_database()
    print("=" * 60)

