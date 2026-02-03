#!/usr/bin/env python3
"""
Check the structure of accounts_walletsystem table
"""

import psycopg2

def check_table_structure():
    """Check the columns in accounts_walletsystem table"""

    try:
        # Database connection parameters
        connection_params = {
            'host': '143.244.178.203',
            'database': 'agency_banking_db',
            'user': 'datauser',
            'password': 'EiRXo6IfeHQuM3wcbZ67$LzwmVKCXhpUhWg',
            'port': '5432'
        }

        print("Connecting to the database...")
        conn = psycopg2.connect(**connection_params)
        print("✓ Connected successfully!\n")

        cursor = conn.cursor()

        # Get table structure
        query = """
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'accounts_walletsystem'
        ORDER BY ordinal_position;
        """

        cursor.execute(query)
        columns = cursor.fetchall()

        print("Columns in accounts_walletsystem table:")
        print("-" * 80)
        for col_name, data_type, max_length in columns:
            length_info = f"({max_length})" if max_length else ""
            print(f"  {col_name:<30} {data_type}{length_info}")

        # Also get a sample row
        print("\n\nSample row from accounts_walletsystem:")
        print("-" * 80)
        cursor.execute("SELECT * FROM accounts_walletsystem LIMIT 1;")
        sample = cursor.fetchone()
        col_names = [desc[0] for desc in cursor.description]

        for col_name, value in zip(col_names, sample):
            print(f"  {col_name:<30} {value}")

        cursor.close()
        conn.close()
        print("\nConnection closed.")

    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    check_table_structure()

