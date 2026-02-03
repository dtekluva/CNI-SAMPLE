#!/usr/bin/env python3
"""
Connect to PostgreSQL database using credentials from .credentials file
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

def connect_to_database():
    """
    Attempt to connect to the PostgreSQL database using credentials from .credentials file
    """
    connection = None
    cursor = None

    try:
        # Read credentials from file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        creds_path = os.path.join(script_dir, '.credentials')

        print("Reading credentials from .credentials file...")
        creds = read_credentials(creds_path)

        # Database connection parameters
        # Try to connect to 'postgres' database first to list available databases
        connection_params = {
            'host': creds.get('host'),
            'database': creds.get('database', 'postgres'),  # Default to 'postgres' if not specified
            'user': creds.get('user'),
            'password': creds.get('password'),
            'port': creds.get('port', '5432')
        }

        print("Attempting to connect to the database...")
        print(f"Host: {connection_params['host']}")
        print(f"User: {connection_params['user']}")
        print(f"Port: {connection_params['port']}")
        print("-" * 50)

        # Establish connection
        connection = psycopg2.connect(**connection_params)

        # Create a cursor object
        cursor = connection.cursor()

        # Print PostgreSQL connection properties
        print("✓ Successfully connected to PostgreSQL database!")
        print("-" * 50)

        # Get PostgreSQL version
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"PostgreSQL version: {db_version[0]}")
        print("-" * 50)

        # Get current database name
        cursor.execute("SELECT current_database();")
        current_db = cursor.fetchone()
        print(f"Current database: {current_db[0]}")
        print("-" * 50)

        # List all databases
        cursor.execute("""
            SELECT datname
            FROM pg_database
            WHERE datistemplate = false
            ORDER BY datname;
        """)
        databases = cursor.fetchall()

        if databases:
            print(f"Found {len(databases)} database(s):")
            for db in databases:
                print(f"  - {db[0]}")
        print("-" * 50)

        # List all tables in the current database
        cursor.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name;
        """)
        tables = cursor.fetchall()

        if tables:
            print(f"Found {len(tables)} table(s) in the current database:")
            for schema, table in tables:
                print(f"  - {schema}.{table}")
        else:
            print("No user tables found in the database.")

        print("-" * 50)
        print("✓ Connection test completed successfully!")

        return connection

    except (Exception, Error) as error:
        print("✗ Error while connecting to PostgreSQL database:")
        print(f"Error type: {type(error).__name__}")
        print(f"Error details: {error}")
        return None

    finally:
        # Close cursor
        if cursor:
            cursor.close()

        # Note: We return the connection, so we don't close it here
        # The caller should close it when done

if __name__ == "__main__":
    print("=" * 50)
    print("PostgreSQL Database Connection Test")
    print("=" * 50)

    connection = connect_to_database()

    if connection:
        print("\n" + "=" * 50)
        print("Connection object is available for use")
        print("=" * 50)
        # Close the connection when done
        connection.close()
        print("Connection closed.")
    else:
        print("\n" + "=" * 50)
        print("Failed to establish connection")
        print("=" * 50)

