#!/usr/bin/env python3
"""
Calculate average daily energy consumption during solar hours (9am - 4:30pm)
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

def get_solar_hours_consumption():
    """Calculate energy consumption during solar hours"""
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
        print("EKEDC Energy Consumption During Solar Hours (9:00 AM - 4:30 PM)")
        print("=" * 110)

        # EKEDC device ID
        device_id = 220

        # Calculate daily consumption during solar hours for each month
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
                        THEN kwh_import END) as max_kwh_solar,
                    COUNT(CASE WHEN EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos') >= 9 
                               AND (EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos') < 16 
                                    OR (EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos') = 16 
                                        AND EXTRACT(MINUTE FROM post_datetime AT TIME ZONE 'Africa/Lagos') <= 30))
                          THEN 1 END) as solar_readings
                FROM main_reading
                WHERE device_id = %s
                AND kwh_import IS NOT NULL
                GROUP BY DATE_TRUNC('month', post_datetime), DATE(post_datetime)
            )
            SELECT 
                month,
                COUNT(DISTINCT day) as days_with_data,
                AVG(max_kwh_solar - min_kwh_solar) as avg_daily_consumption,
                SUM(max_kwh_solar - min_kwh_solar) as total_monthly_consumption,
                SUM(solar_readings) as total_solar_readings
            FROM daily_solar_consumption
            WHERE min_kwh_solar IS NOT NULL AND max_kwh_solar IS NOT NULL
            GROUP BY month
            ORDER BY month DESC;
        """, (device_id,))

        monthly_data = cursor.fetchall()

        if monthly_data:
            print(f"\n{'Month':<20} {'Days':<8} {'Avg Daily (kWh)':<18} {'Monthly Total (kWh)':<22} {'Readings':<12}")
            print("-" * 110)
            
            total_avg = 0
            count = 0
            
            for month, days, avg_daily, monthly_total, readings in monthly_data:
                month_str = month.strftime('%B %Y')
                avg_daily_val = avg_daily if avg_daily else 0
                monthly_total_val = monthly_total if monthly_total else 0
                
                print(f"{month_str:<20} {days:<8} {avg_daily_val:<18,.2f} {monthly_total_val:<22,.2f} {readings:<12,}")
                
                if avg_daily:
                    total_avg += avg_daily
                    count += 1

            if count > 0:
                overall_avg = total_avg / count
                print("\n" + "=" * 110)
                print(f"\nOverall Average Daily Consumption (Solar Hours): {overall_avg:,.2f} kWh/day")
                print(f"Solar Hours: 9:00 AM - 4:30 PM (7.5 hours)")
                print(f"Average Hourly Consumption: {overall_avg/7.5:,.2f} kWh/hour")

        # Get more detailed breakdown for recent months
        print("\n\n" + "=" * 110)
        print("Detailed Analysis - Last 3 Months")
        print("=" * 110)

        cursor.execute("""
            WITH hourly_consumption AS (
                SELECT 
                    DATE_TRUNC('month', post_datetime) as month,
                    EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos') as hour,
                    AVG(total_kw) as avg_power_kw,
                    COUNT(*) as reading_count
                FROM main_reading
                WHERE device_id = %s
                AND kwh_import IS NOT NULL
                AND post_datetime >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '3 months'
                AND EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos') >= 9
                AND (EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos') < 17)
                GROUP BY DATE_TRUNC('month', post_datetime), EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos')
            )
            SELECT 
                month,
                hour,
                avg_power_kw,
                reading_count
            FROM hourly_consumption
            ORDER BY month DESC, hour;
        """, (device_id,))

        hourly_data = cursor.fetchall()

        if hourly_data:
            current_month = None
            for month, hour, avg_power, count in hourly_data:
                if month != current_month:
                    current_month = month
                    print(f"\n{month.strftime('%B %Y')}:")
                    print(f"  {'Hour':<10} {'Avg Power (kW)':<18} {'Readings':<12}")
                    print("  " + "-" * 50)
                
                hour_int = int(hour)
                if 9 <= hour_int <= 16:
                    hour_str = f"{hour_int:02d}:00"
                    avg_power_val = avg_power if avg_power else 0
                    print(f"  {hour_str:<10} {avg_power_val:<18,.2f} {count:<12,}")

        print("\n" + "=" * 110)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    get_solar_hours_consumption()

