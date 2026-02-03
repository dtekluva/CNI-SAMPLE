#!/usr/bin/env python3
"""
List all clients in the database
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

def list_all_clients():
    """List all clients from account_client table"""
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

        print("=" * 100)
        print("All Clients in Database")
        print("=" * 100)

        # Get all clients
        cursor.execute("""
            SELECT id, name, client_type, email, phone_number, is_active
            FROM account_client
            ORDER BY id;
        """)

        clients = cursor.fetchall()

        print(f"\nTotal Clients: {len(clients)}\n")
        print(f"{'ID':<5} {'Name':<40} {'Type':<15} {'Active':<8} {'Email':<30}")
        print("-" * 100)

        active_count = 0
        inactive_count = 0
        standard_count = 0
        reseller_count = 0

        for client_id, name, client_type, email, phone, is_active in clients:
            active_status = "✓ Yes" if is_active else "✗ No"
            # Handle NULL values
            name = name or "N/A"
            client_type = client_type or "N/A"
            email = email or "N/A"

            print(f"{client_id:<5} {name:<40} {client_type:<15} {active_status:<8} {email:<30}")

            if is_active:
                active_count += 1
            else:
                inactive_count += 1

            if client_type == 'STANDARD':
                standard_count += 1
            elif client_type == 'RESELLER':
                reseller_count += 1

        print("\n" + "=" * 100)
        print(f"\nSummary:")
        print(f"  Total Clients: {len(clients)}")
        print(f"  Active: {active_count}")
        print(f"  Inactive: {inactive_count}")
        print(f"  Standard: {standard_count}")
        print(f"  Reseller: {reseller_count}")
        print("\n" + "=" * 100)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    list_all_clients()

