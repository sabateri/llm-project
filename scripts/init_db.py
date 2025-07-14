#!/usr/bin/env python3
"""
Database initialization script for RAG application
"""
import psycopg2
import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

POSTGRES_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "ragdb"),
    "user": os.getenv("POSTGRES_USER", "raguser"),
    "password": os.getenv("POSTGRES_PASSWORD", "ragpass"),
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": os.getenv("POSTGRES_PORT", 5432),
}

def wait_for_postgres(max_retries=30, delay=2):
    """Wait for PostgreSQL to be ready"""
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(**POSTGRES_CONFIG)
            conn.close()
            print("PostgreSQL is ready!")
            return True
        except psycopg2.OperationalError as e:
            print(f"Waiting for PostgreSQL... (attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
    
    print("Failed to connect to PostgreSQL after maximum retries")
    return False

def create_tables():
    """Create necessary database tables"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()
        
        # Create queries table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id SERIAL PRIMARY KEY,
                query TEXT NOT NULL,
                answer TEXT NOT NULL,
                relevance VARCHAR(20),
                relevance_explanation TEXT,
                confidence_score FLOAT,
                accuracy VARCHAR(20),
                completeness VARCHAR(20),
                clarity VARCHAR(20),
                evaluation_error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes for better performance
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_queries_created_at 
            ON queries(created_at);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_queries_query 
            ON queries USING gin(to_tsvector('english', query));
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database tables created successfully!")
        return True
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False

def main():
    """Main initialization function"""
    print("Starting database initialization...")
    
    # Wait for PostgreSQL to be ready
    if not wait_for_postgres():
        sys.exit(1)
    
    # Create tables
    if not create_tables():
        sys.exit(1)
    
    print("Database initialization completed successfully!")

if __name__ == "__main__":
    main()