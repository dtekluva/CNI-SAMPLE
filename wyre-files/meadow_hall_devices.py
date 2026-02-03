#!/usr/bin/env python3
"""
Count devices for Meadow Hall client
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

def get_meadow_hall_devices():
    """Get device count for Meadow Hall"""
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
        print("Meadow Hall Devices")
        print("=" * 100)

        # First, get Meadow Hall client ID
        cursor.execute("""
            SELECT id, name, client_type, is_active
            FROM account_client
            WHERE name ILIKE '%meadow hall%';
        """)

        client = cursor.fetchone()

        if not client:
            print("\nMeadow Hall client not found!")
            return

        client_id, client_name, client_type, is_active = client
        print(f"\nClient Found:")
        print(f"  ID: {client_id}")
        print(f"  Name: {client_name}")
        print(f"  Type: {client_type}")
        print(f"  Active: {'Yes' if is_active else 'No'}")
        print("-" * 100)

        # Check if there's a relationship between devices and clients
        # Let's first check the device table structure
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'main_device'
            ORDER BY ordinal_position;
        """)

        device_columns = cursor.fetchall()
        print(f"\nDevice table columns:")
        for col_name, data_type in device_columns:
            print(f"  - {col_name} ({data_type})")

        # Check if there's a branch table that links clients to devices
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'main_branch'
            ORDER BY ordinal_position;
        """)

        branch_columns = cursor.fetchall()
        print(f"\nBranch table columns:")
        for col_name, data_type in branch_columns:
            print(f"  - {col_name} ({data_type})")

        print("-" * 100)

        # Get devices for Meadow Hall through branches
        cursor.execute("""
            SELECT COUNT(DISTINCT d.id)
            FROM main_device d
            JOIN main_branch b ON d.branch_id = b.id
            WHERE b.client_id = %s;
        """, (client_id,))

        device_count = cursor.fetchone()[0]

        print(f"\nTotal Devices: {device_count}")

        # Get detailed device information
        cursor.execute("""
            SELECT d.id, d.name, d.type_id, d.fuel_type, d.is_active, b.name as branch_name
            FROM main_device d
            JOIN main_branch b ON d.branch_id = b.id
            WHERE b.client_id = %s
            ORDER BY b.name, d.name;
        """, (client_id,))

        devices = cursor.fetchall()

        if devices:
            print(f"\nDevice Details:")
            print(f"{'Device ID':<12} {'Device Name':<30} {'Fuel Type':<15} {'Active':<8} {'Branch':<30}")
            print("-" * 100)
            for dev_id, dev_name, dev_type_id, fuel_type, is_active, branch_name in devices:
                dev_name = dev_name or "N/A"
                branch_name = branch_name or "N/A"
                fuel_type = fuel_type or "N/A"
                active_status = "✓ Yes" if is_active else "✗ No"
                print(f"{dev_id:<12} {dev_name:<30} {fuel_type:<15} {active_status:<8} {branch_name:<30}")

        # Get branch count
        cursor.execute("""
            SELECT COUNT(*)
            FROM main_branch
            WHERE client_id = %s;
        """, (client_id,))

        branch_count = cursor.fetchone()[0]

        print("\n" + "=" * 100)
        print(f"\nSummary:")
        print(f"  Client: {client_name}")
        print(f"  Total Branches: {branch_count}")
        print(f"  Total Devices: {device_count}")
        print("\n" + "=" * 100)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    get_meadow_hall_devices()

