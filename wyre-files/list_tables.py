#!/usr/bin/env python3
"""
List tables in wyre_db database
"""

import psycopg2
import os

def read_credentials(filepath='.credentials'):
    """Read database credentials from file"""
    credentials = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                credentials[key] = value
    return credentials

def list_tables():
    """List all tables in wyre_db"""
    try:
        # Read credentials
        script_dir = os.path.dirname(os.path.abspath(__file__))
        creds_path = os.path.join(script_dir, '.credentials')
        creds = read_credentials(creds_path)
        
        # Connect to wyre_db
        conn = psycopg2.connect(
            host=creds.get('host'),
            database='wyre_db',
            user=creds.get('user'),
            password=creds.get('password'),
            port=creds.get('port', '5432')
        )
        
        cursor = conn.cursor()
        
        print("=" * 80)
        print("Tables in wyre_db")
        print("=" * 80)
        
        # List all tables
        cursor.execute("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            AND table_type = 'BASE TABLE'
            ORDER BY table_schema, table_name;
        """)
        
        tables = cursor.fetchall()
        
        if tables:
            print(f"\nFound {len(tables)} table(s):\n")
            for schema, table in tables:
                print(f"  {schema}.{table}")
        else:
            print("\nNo user tables found.")
        
        print("\n" + "=" * 80)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_tables()

