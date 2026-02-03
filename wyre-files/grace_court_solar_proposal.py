#!/usr/bin/env python3
"""
Solar System Design and ROI Analysis for Grace Court
Target: 60% energy offset during solar hours
"""

import psycopg2
import os
from datetime import datetime

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

def solar_proposal_grace_court():
    """Generate solar proposal for Grace Court"""
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

        print("=" * 120)
        print("GRACE COURT - SOLAR SYSTEM DESIGN & ROI ANALYSIS")
        print("Target: 60% Energy Offset During Solar Hours")
        print("=" * 120)

        # Get Grace Court utility device data (excluding Jan 2026 anomaly)
        device_id = 60  # Utility meter

        # Get realistic consumption data (excluding anomalous Jan 2026)
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
                AND post_datetime >= '2024-01-01'
                AND post_datetime < '2026-01-01'  -- Exclude Jan 2026 anomaly
                GROUP BY DATE_TRUNC('month', post_datetime), DATE(post_datetime)
            )
            SELECT
                AVG(max_kwh_solar - min_kwh_solar) as avg_daily_consumption
            FROM daily_solar_consumption
            WHERE min_kwh_solar IS NOT NULL AND max_kwh_solar IS NOT NULL
            AND (max_kwh_solar - min_kwh_solar) > 0;
        """, (device_id,))

        result = cursor.fetchone()
        avg_daily_consumption = result[0] if result and result[0] else 100  # Default to 100 if no data

        # Get hourly power demand profile
        cursor.execute("""
            SELECT
                EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos') as hour,
                AVG(total_kw) as avg_power_kw,
                MAX(total_kw) as max_power_kw
            FROM main_reading
            WHERE device_id = %s
            AND total_kw IS NOT NULL
            AND post_datetime >= '2024-01-01'
            AND post_datetime < '2026-01-01'
            AND EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos') >= 9
            AND EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos') <= 16
            GROUP BY EXTRACT(HOUR FROM post_datetime AT TIME ZONE 'Africa/Lagos')
            ORDER BY hour;
        """, (device_id,))

        hourly_profile = cursor.fetchall()
        avg_power_demand = sum([row[1] for row in hourly_profile]) / len(hourly_profile) if hourly_profile else 50

        print(f"\n1. CURRENT ENERGY CONSUMPTION ANALYSIS")
        print("-" * 120)
        print(f"   Average Daily Consumption (Solar Hours 9am-4:30pm): {avg_daily_consumption:,.2f} kWh/day")
        print(f"   Average Power Demand (Solar Hours): {avg_power_demand:,.2f} kW")
        print(f"   Monthly Consumption (Solar Hours): {avg_daily_consumption * 30:,.2f} kWh/month")
        print(f"   Annual Consumption (Solar Hours): {avg_daily_consumption * 365:,.2f} kWh/year")

        # Solar system design parameters
        target_offset = 0.60  # 60% offset
        daily_solar_target = avg_daily_consumption * target_offset

        # Nigeria solar parameters - REALISTIC VALUES
        # Capacity factor accounts for: sun angle, cloud cover, temperature, dust, inverter losses, shading
        capacity_factor = 0.40  # 40% of rated capacity (realistic for Nigeria)
        # This means a 1kW system produces: 1kW * 24hrs * 0.40 = 9.6 kWh/day
        panel_degradation = 0.005  # 0.5% per year

        # Calculate required system size
        required_daily_generation = daily_solar_target
        hours_per_day = 24
        required_system_size_kw = required_daily_generation / (hours_per_day * capacity_factor)

        # Round up to nearest 5kW for practical installation
        system_size_kw = round(required_system_size_kw / 5) * 5
        if system_size_kw < required_system_size_kw:
            system_size_kw += 5

        # Actual generation with rounded system size
        actual_daily_generation = system_size_kw * hours_per_day * capacity_factor
        actual_offset_percentage = (actual_daily_generation / avg_daily_consumption) * 100

        print(f"\n2. SOLAR SYSTEM DESIGN")
        print("-" * 120)
        print(f"   Target Energy Offset: 60%")
        print(f"   Required Daily Generation: {required_daily_generation:,.2f} kWh/day")
        print(f"   Recommended System Size: {system_size_kw:,.0f} kWp (kilowatt-peak)")
        print(f"   Actual Daily Generation: {actual_daily_generation:,.2f} kWh/day")
        print(f"   Actual Energy Offset: {actual_offset_percentage:,.1f}%")

        # System components
        panel_wattage = 550  # Modern high-efficiency panels (550W)
        num_panels = int(system_size_kw * 1000 / panel_wattage)
        inverter_size_kw = system_size_kw * 1.2  # 20% oversizing for inverter

        print(f"\n   System Components:")
        print(f"   - Solar Panels: {num_panels} x {panel_wattage}W = {num_panels * panel_wattage / 1000:,.1f} kWp")
        print(f"   - Inverter Size: {inverter_size_kw:,.0f} kW (Hybrid/Grid-tied)")
        print(f"   - Mounting Structure: Rooftop/Ground mount")
        print(f"   - Monitoring System: IoT-enabled real-time monitoring")

        # Cost estimation (Nigeria market rates 2026)
        cost_per_watt = 0.85  # USD per watt installed (competitive rate for Nigeria)
        total_system_cost_usd = system_size_kw * 1000 * cost_per_watt

        # Convert to Naira (approximate rate)
        usd_to_ngn = 1500  # Approximate exchange rate
        total_system_cost_ngn = total_system_cost_usd * usd_to_ngn

        print(f"\n3. SYSTEM COST BREAKDOWN")
        print("-" * 120)
        print(f"   System Size: {system_size_kw:,.0f} kWp")
        print(f"   Cost per Watt: ${cost_per_watt:.2f} USD")
        print(f"   Total System Cost: ${total_system_cost_usd:,.2f} USD")
        print(f"   Total System Cost: ₦{total_system_cost_ngn:,.2f} NGN")
        print(f"\n   Cost Breakdown:")
        print(f"   - Solar Panels (40%): ₦{total_system_cost_ngn * 0.40:,.2f}")
        print(f"   - Inverter (25%): ₦{total_system_cost_ngn * 0.25:,.2f}")
        print(f"   - Mounting & BOS (20%): ₦{total_system_cost_ngn * 0.20:,.2f}")
        print(f"   - Installation & Labor (10%): ₦{total_system_cost_ngn * 0.10:,.2f}")
        print(f"   - Monitoring & Commissioning (5%): ₦{total_system_cost_ngn * 0.05:,.2f}")

        # Financial analysis
        # Electricity tariff (Nigeria Band A commercial rate)
        electricity_tariff_ngn = 226  # NGN per kWh (Band A tariff - 20+ hours supply)

        # Annual savings
        annual_generation_kwh = actual_daily_generation * 365
        annual_savings_ngn = annual_generation_kwh * electricity_tariff_ngn

        # O&M costs (1-2% of system cost per year)
        annual_om_cost_ngn = total_system_cost_ngn * 0.015

        # Net annual savings
        net_annual_savings_ngn = annual_savings_ngn - annual_om_cost_ngn

        print(f"\n4. FINANCIAL ANALYSIS")
        print("-" * 120)
        print(f"   Electricity Tariff: ₦{electricity_tariff_ngn:,.0f}/kWh")
        print(f"   Annual Solar Generation: {annual_generation_kwh:,.2f} kWh/year")
        print(f"   Annual Electricity Savings: ₦{annual_savings_ngn:,.2f}")
        print(f"   Annual O&M Costs (1.5%): ₦{annual_om_cost_ngn:,.2f}")
        print(f"   Net Annual Savings: ₦{net_annual_savings_ngn:,.2f}")

        # ROI calculations
        simple_payback_years = total_system_cost_ngn / net_annual_savings_ngn
        roi_percentage = (net_annual_savings_ngn / total_system_cost_ngn) * 100

        # 25-year lifetime analysis
        system_lifetime_years = 25
        total_lifetime_savings = 0

        for year in range(1, system_lifetime_years + 1):
            degradation_factor = (1 - panel_degradation) ** year
            year_generation = annual_generation_kwh * degradation_factor
            year_savings = year_generation * electricity_tariff_ngn - annual_om_cost_ngn
            total_lifetime_savings += year_savings

        net_lifetime_profit = total_lifetime_savings - total_system_cost_ngn

        print(f"\n5. RETURN ON INVESTMENT (ROI)")
        print("-" * 120)
        print(f"   Simple Payback Period: {simple_payback_years:.1f} years")
        print(f"   Annual ROI: {roi_percentage:.1f}%")
        print(f"   25-Year Total Savings: ₦{total_lifetime_savings:,.2f}")
        print(f"   25-Year Net Profit: ₦{net_lifetime_profit:,.2f}")
        print(f"   Lifetime ROI: {(net_lifetime_profit / total_system_cost_ngn) * 100:.0f}%")

        print(f"\n6. ENVIRONMENTAL IMPACT")
        print("-" * 120)
        co2_reduction_kg_per_kwh = 0.85  # kg CO2 per kWh (Nigeria grid average)
        annual_co2_reduction_kg = annual_generation_kwh * co2_reduction_kg_per_kwh
        lifetime_co2_reduction_kg = annual_co2_reduction_kg * system_lifetime_years

        print(f"   Annual CO2 Reduction: {annual_co2_reduction_kg:,.0f} kg ({annual_co2_reduction_kg/1000:,.1f} tonnes)")
        print(f"   25-Year CO2 Reduction: {lifetime_co2_reduction_kg:,.0f} kg ({lifetime_co2_reduction_kg/1000:,.1f} tonnes)")
        print(f"   Equivalent Trees Planted: {int(lifetime_co2_reduction_kg / 20):,} trees")

        print(f"\n7. RECOMMENDATION")
        print("-" * 120)
        print(f"   ✓ Install a {system_size_kw:,.0f} kWp solar PV system")
        print(f"   ✓ Expected to offset {actual_offset_percentage:.1f}% of daytime energy consumption")
        print(f"   ✓ Payback period of {simple_payback_years:.1f} years is excellent for commercial solar")
        print(f"   ✓ Annual ROI of {roi_percentage:.1f}% significantly outperforms traditional investments")
        print(f"   ✓ System will generate clean energy for 25+ years")
        print(f"   ✓ Protects against future electricity tariff increases")

        print(f"\n   FINANCING OPTIONS:")
        print(f"   1. Full Cash Payment: ₦{total_system_cost_ngn:,.2f}")
        print(f"   2. Bank Loan (5 years @ 15%): Monthly payment ~₦{(total_system_cost_ngn * 0.0238):,.2f}")
        print(f"   3. Solar Lease/PPA: Pay-as-you-save model available")

        print("\n" + "=" * 120)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    solar_proposal_grace_court()

