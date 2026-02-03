#!/usr/bin/env python3
"""
Count the number of clients in the database
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

def count_clients():
    """Count clients in account_client table"""
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
        print("Client Count in Database")
        print("=" * 80)
        
        # Count total clients
        cursor.execute("SELECT COUNT(*) FROM account_client;")
        total_clients = cursor.fetchone()[0]
        
        print(f"\nTotal Clients: {total_clients:,}")
        
        # Get some additional info about clients
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns
            WHERE table_name = 'account_client'
            ORDER BY ordinal_position
            LIMIT 10;
        """)
        
        columns = cursor.fetchall()
        print(f"\nClient table has the following columns (first 10):")
        for col_name, data_type in columns:
            print(f"  - {col_name} ({data_type})")
        
        # Try to get a sample of client data
        cursor.execute("""
            SELECT * FROM account_client
            LIMIT 5;
        """)
        
        sample_data = cursor.fetchall()
        
        if sample_data:
            print(f"\nSample of {len(sample_data)} client(s):")
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'account_client' ORDER BY ordinal_position;")
            col_names = [row[0] for row in cursor.fetchall()]
            
            for row in sample_data:
                print("\n" + "-" * 80)
                for col_name, value in zip(col_names, row):
                    print(f"  {col_name}: {value}")
        
        print("\n" + "=" * 80)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    count_clients()

