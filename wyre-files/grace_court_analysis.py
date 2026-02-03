#!/usr/bin/env python3
"""
Analyze Grace Court energy consumption
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

def analyze_grace_court():
    """Analyze Grace Court client"""
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

        print("=" * 110)
        print("Grace Court Analysis")
        print("=" * 110)

        # Get Grace Court client info
        cursor.execute("""
            SELECT id, name, client_type, is_active
            FROM account_client
            WHERE name ILIKE '%grace court%'
            ORDER BY id;
        """)

        clients = cursor.fetchall()

        if not clients:
            print("\nGrace Court client not found!")
            return

        print(f"\nFound {len(clients)} Grace Court client(s):")
        for client_id, client_name, client_type, is_active in clients:
            print(f"  ID: {client_id}, Name: {client_name}, Type: {client_type}, Active: {'Yes' if is_active else 'No'}")

        # Use the first active Grace Court
        grace_court_id = None
        for client_id, client_name, client_type, is_active in clients:
            if is_active:
                grace_court_id = client_id
                grace_court_name = client_name
                break

        if not grace_court_id:
            grace_court_id = clients[0][0]
            grace_court_name = clients[0][1]

        print(f"\nAnalyzing: {grace_court_name} (ID: {grace_court_id})")
        print("-" * 110)

        # Get branches
        cursor.execute("""
            SELECT id, name, is_active
            FROM main_branch
            WHERE client_id = %s
            ORDER BY name;
        """, (grace_court_id,))

        branches = cursor.fetchall()
        print(f"\nBranches: {len(branches)}")
        for branch_id, branch_name, is_active in branches:
            print(f"  - {branch_name} (ID: {branch_id}, Active: {'Yes' if is_active else 'No'})")

        # Get devices
        cursor.execute("""
            SELECT d.id, d.name, d.fuel_type, d.is_active, b.name as branch_name
            FROM main_device d
            JOIN main_branch b ON d.branch_id = b.id
            WHERE b.client_id = %s
            ORDER BY b.name, d.name;
        """, (grace_court_id,))

        devices = cursor.fetchall()
        print(f"\nTotal Devices: {len(devices)}")
        print(f"\n{'Device ID':<12} {'Device Name':<35} {'Fuel Type':<15} {'Active':<8} {'Branch':<30}")
        print("-" * 110)
        
        utility_devices = []
        for dev_id, dev_name, fuel_type, is_active, branch_name in devices:
            dev_name = dev_name or "N/A"
            fuel_type = fuel_type or "N/A"
            branch_name = branch_name or "N/A"
            active_status = "✓ Yes" if is_active else "✗ No"
            print(f"{dev_id:<12} {dev_name:<35} {fuel_type:<15} {active_status:<8} {branch_name:<30}")
            
            # Identify utility meters (typically no fuel type or named with utility company)
            if fuel_type == "N/A" or "EKEDC" in dev_name.upper() or "IKEDC" in dev_name.upper() or "UTILITY" in dev_name.upper():
                utility_devices.append((dev_id, dev_name))

        print("\n" + "=" * 110)
        print("Energy Consumption Analysis - Solar Hours (9:00 AM - 4:30 PM)")
        print("=" * 110)

        # Analyze each utility device
        for dev_id, dev_name in utility_devices:
            print(f"\n\nDevice: {dev_name} (ID: {dev_id})")
            print("-" * 110)

            # Check if device has readings
            cursor.execute("""
                SELECT COUNT(*), MIN(post_datetime), MAX(post_datetime)
                FROM main_reading
                WHERE device_id = %s;
            """, (dev_id,))

            reading_info = cursor.fetchone()
            if reading_info[0] == 0:
                print("  No readings found for this device.")
                continue

            print(f"  Total Readings: {reading_info[0]:,}")
            print(f"  Period: {reading_info[1]} to {reading_info[2]}")

            # Calculate solar hours consumption
            cursor.execute("""
                WITH daily_solar_consumption AS (
                    SELECT 
                        DATE_TRUNC('month', post_datetime) as month,
                        DATE(post_datetime) as day,
                        MIN(CASE WHEN EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos') >= 9 
                                 AND (EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos') < 16 
                                      OR (EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos') = 16 
                                          AND EXTRACT(MINUTE FROM post_datetime AT TIME ZONE 'Africa/Lagos') <= 30))
                            THEN kwh_import END) as min_kwh_solar,
                        MAX(CASE WHEN EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos') >= 9 
                                 AND (EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos') < 16 
                                      OR (EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos') = 16 
                                          AND EXTRACT(MINUTE FROM post_datetime AT TIME ZONE 'Africa/Lagos') <= 30))
                            THEN kwh_import END) as max_kwh_solar
                    FROM main_reading
                    WHERE device_id = %s
                    AND kwh_import IS NOT NULL
                    GROUP BY DATE_TRUNC('month', post_datetime), DATE(post_datetime)
                )
                SELECT 
                    month,
                    COUNT(DISTINCT day) as days_with_data,
                    AVG(max_kwh_solar - min_kwh_solar) as avg_daily_consumption,
                    SUM(max_kwh_solar - min_kwh_solar) as total_monthly_consumption
                FROM daily_solar_consumption
                WHERE min_kwh_solar IS NOT NULL AND max_kwh_solar IS NOT NULL
                GROUP BY month
                ORDER BY month DESC
                LIMIT 12;
            """, (dev_id,))

            monthly_data = cursor.fetchall()

            if monthly_data:
                print(f"\n  {'Month':<20} {'Days':<8} {'Avg Daily (kWh)':<18} {'Monthly Total (kWh)':<22}")
                print("  " + "-" * 100)
                
                total_avg = 0
                count = 0
                
                for month, days, avg_daily, monthly_total in monthly_data:
                    month_str = month.strftime('%B %Y')
                    avg_daily_val = avg_daily if avg_daily else 0
                    monthly_total_val = monthly_total if monthly_total else 0
                    
                    print(f"  {month_str:<20} {days:<8} {avg_daily_val:<18,.2f} {monthly_total_val:<22,.2f}")
                    
                    if avg_daily:
                        total_avg += avg_daily
                        count += 1

                if count > 0:
                    overall_avg = total_avg / count
                    print(f"\n  Overall Average Daily Consumption (Solar Hours): {overall_avg:,.2f} kWh/day")
                    print(f"  Average Hourly Consumption: {overall_avg/7.5:,.2f} kWh/hour")

        print("\n" + "=" * 110)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_grace_court()

