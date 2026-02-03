#!/usr/bin/env python3
"""
Explore the wyre_db database structure and contents
"""

import psycopg2
from psycopg2 import Error
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

def explore_wyre_db():
    """
    Connect to wyre_db and explore its structure
    """
    connection = None
    cursor = None
    
    try:
        # Read credentials from file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        creds_path = os.path.join(script_dir, '.credentials')
        
        print("Reading credentials from .credentials file...")
        creds = read_credentials(creds_path)
        
        # Database connection parameters - connect to wyre_db
        connection_params = {
            'host': creds.get('host'),
            'database': 'wyre_db',
            'user': creds.get('user'),
            'password': creds.get('password'),
            'port': creds.get('port', '5432')
        }
        
        print("Connecting to wyre_db...")
        print(f"Host: {connection_params['host']}")
        print(f"Database: {connection_params['database']}")
        print(f"User: {connection_params['user']}")
        print("-" * 80)
        
        # Establish connection
        connection = psycopg2.connect(**connection_params)
        cursor = connection.cursor()
        
        print("✓ Successfully connected to wyre_db!")
        print("-" * 80)
        
        # List all schemas
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name;
        """)
        schemas = cursor.fetchall()
        
        if schemas:
            print(f"\nSchemas in database:")
            for schema in schemas:
                print(f"  - {schema[0]}")
        print("-" * 80)
        
        # List all tables with row counts
        cursor.execute("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            AND table_type = 'BASE TABLE'
            ORDER BY table_schema, table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"\nFound {len(tables)} table(s):")
            print("-" * 80)
            for schema, table in tables:
                # Get row count
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM "{schema}"."{table}";')
                    count = cursor.fetchone()[0]
                    print(f"  {schema}.{table}: {count:,} rows")
                except Exception as e:
                    print(f"  {schema}.{table}: (unable to count rows)")
        else:
            print("No user tables found in the database.")
        
        print("-" * 80)
        
        # For each table, show its structure
        if tables:
            print("\nTable Structures:")
            print("=" * 80)
            for schema, table in tables:
                print(f"\nTable: {schema}.{table}")
                print("-" * 80)
                
                # Get column information
                cursor.execute("""
                    SELECT 
                        column_name, 
                        data_type, 
                        character_maximum_length,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position;
                """, (schema, table))
                
                columns = cursor.fetchall()
                print(f"{'Column':<30} {'Type':<20} {'Nullable':<10} {'Default':<20}")
                print("-" * 80)
                for col_name, data_type, max_len, nullable, default in columns:
                    type_str = data_type
                    if max_len:
                        type_str = f"{data_type}({max_len})"
                    default_str = str(default)[:20] if default else ''
                    print(f"{col_name:<30} {type_str:<20} {nullable:<10} {default_str:<20}")
        
        print("\n" + "=" * 80)
        print("✓ Database exploration completed!")
        
        return connection
        
    except (Exception, Error) as error:
        print("✗ Error while exploring database:")
        print(f"Error type: {type(error).__name__}")
        print(f"Error details: {error}")
        return None
        
    finally:
        # Close cursor
        if cursor:
            cursor.close()

if __name__ == "__main__":
    print("=" * 80)
    print("Wyre Database Explorer")
    print("=" * 80)
    
    connection = explore_wyre_db()
    
    if connection:
        connection.close()
        print("Connection closed.")

