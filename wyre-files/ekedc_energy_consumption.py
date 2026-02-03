#!/usr/bin/env python3
"""
Calculate total energy consumption from EKEDC device for Meadow Hall
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

def get_ekedc_energy():
    """Get total energy consumption from EKEDC device"""
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
        print("EKEDC Energy Consumption Analysis")
        print("=" * 100)

        # First, let's check the structure of the readings table
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'main_reading'
            ORDER BY ordinal_position;
        """)

        reading_columns = cursor.fetchall()
        print(f"\nReading table columns:")
        for col_name, data_type in reading_columns:
            print(f"  - {col_name} ({data_type})")
        print("-" * 100)

        # Get EKEDC device ID (we know it's 220 from previous query)
        device_id = 220

        # Get total count of readings
        cursor.execute("""
            SELECT COUNT(*)
            FROM main_reading
            WHERE device_id = %s;
        """, (device_id,))

        reading_count = cursor.fetchone()[0]
        print(f"\nTotal readings for EKEDC device: {reading_count:,}")

        # Get date range of readings
        cursor.execute("""
            SELECT MIN(post_datetime), MAX(post_datetime)
            FROM main_reading
            WHERE device_id = %s;
        """, (device_id,))

        date_range = cursor.fetchone()
        if date_range[0]:
            print(f"First reading: {date_range[0]}")
            print(f"Last reading: {date_range[1]}")

        print("-" * 100)

        # Get total energy consumption (sum of kwh_import field)
        cursor.execute("""
            SELECT
                SUM(kwh_import) as total_energy,
                MIN(kwh_import) as min_energy,
                MAX(kwh_import) as max_energy,
                AVG(kwh_import) as avg_energy
            FROM main_reading
            WHERE device_id = %s
            AND kwh_import IS NOT NULL;
        """, (device_id,))

        energy_stats = cursor.fetchone()

        if energy_stats and energy_stats[0] is not None:
            total_energy, min_energy, max_energy, avg_energy = energy_stats
            print(f"\nEnergy Statistics (kwh_import):")
            print(f"  Total Energy (Sum): {total_energy:,.2f} kWh")
            print(f"  Minimum Reading: {min_energy:,.2f} kWh")
            print(f"  Maximum Reading: {max_energy:,.2f} kWh")
            print(f"  Average Reading: {avg_energy:,.2f} kWh")
        else:
            print("\nNo energy data found in readings.")

        # Get latest reading value
        cursor.execute("""
            SELECT kwh_import, post_datetime, voltage_l1_l12, current_l1, total_kw
            FROM main_reading
            WHERE device_id = %s
            AND kwh_import IS NOT NULL
            ORDER BY post_datetime DESC
            LIMIT 1;
        """, (device_id,))

        latest = cursor.fetchone()
        if latest:
            print(f"\nLatest Reading:")
            print(f"  Energy (kwh_import): {latest[0]:,.2f} kWh")
            print(f"  Date: {latest[1]}")
            if latest[2]:
                print(f"  Voltage L1: {latest[2]:.2f} V")
            if latest[3]:
                print(f"  Current L1: {latest[3]:.2f} A")
            if latest[4]:
                print(f"  Total Power: {latest[4]:.2f} kW")

        # Get first reading value
        cursor.execute("""
            SELECT kwh_import, post_datetime
            FROM main_reading
            WHERE device_id = %s
            AND kwh_import IS NOT NULL
            ORDER BY post_datetime ASC
            LIMIT 1;
        """, (device_id,))

        first = cursor.fetchone()
        if first and latest:
            print(f"\nFirst Reading:")
            print(f"  Energy (kwh_import): {first[0]:,.2f} kWh")
            print(f"  Date: {first[1]}")

            # Calculate cumulative consumption (difference between latest and first)
            cumulative = latest[0] - first[0]
            print(f"\nCumulative Energy Consumption:")
            print(f"  Total consumed: {cumulative:,.2f} kWh")
            print(f"  (From {first[1]} to {latest[1]})")

        # Get monthly breakdown
        cursor.execute("""
            SELECT
                DATE_TRUNC('month', post_datetime) as month,
                COUNT(*) as reading_count,
                MIN(kwh_import) as min_energy,
                MAX(kwh_import) as max_energy
            FROM main_reading
            WHERE device_id = %s
            AND kwh_import IS NOT NULL
            GROUP BY DATE_TRUNC('month', post_datetime)
            ORDER BY month DESC
            LIMIT 12;
        """, (device_id,))

        monthly_data = cursor.fetchall()
        if monthly_data:
            print(f"\n\nMonthly Breakdown (Last 12 months):")
            print(f"{'Month':<20} {'Readings':<12} {'Min (kWh)':<15} {'Max (kWh)':<15} {'Consumption':<15}")
            print("-" * 100)
            for month, count, min_val, max_val in monthly_data:
                consumption = max_val - min_val if max_val and min_val else 0
                print(f"{str(month):<20} {count:<12,} {min_val:<15,.2f} {max_val:<15,.2f} {consumption:<15,.2f}")

        print("\n" + "=" * 100)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    get_ekedc_energy()

