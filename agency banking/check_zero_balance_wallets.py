#!/usr/bin/env python3
"""
Check if wallets without transactions have zero balance
"""

import psycopg2

def check_zero_balance_wallets():
    """Check balance distribution for wallets without transactions"""

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

        # Query 1: Count wallets without transactions by balance
        print("Analyzing wallets WITHOUT transactions (before 2026-01-01)...")
        print("-" * 80)
        query_balance_distribution = """
        SELECT
            CASE
                WHEN ws.available_balance = 0 THEN 'Zero Balance'
                WHEN ws.available_balance > 0 THEN 'Positive Balance'
                WHEN ws.available_balance < 0 THEN 'Negative Balance'
                WHEN ws.available_balance IS NULL THEN 'NULL Balance'
            END as balance_category,
            COUNT(*) as wallet_count,
            MIN(ws.available_balance) as min_balance,
            MAX(ws.available_balance) as max_balance,
            AVG(ws.available_balance) as avg_balance,
            SUM(ws.available_balance) as total_balance
        FROM accounts_walletsystem ws
        WHERE NOT EXISTS (
            SELECT 1
            FROM accounts_transaction t
            WHERE t.source_wallet_id::uuid = ws.wallet_id
              AND t.date_created < '2026-01-01 00:00:00'
        )
        GROUP BY balance_category
        ORDER BY wallet_count DESC;
        """

        cursor.execute(query_balance_distribution)
        results = cursor.fetchall()

        print("\nBalance Distribution for Wallets WITHOUT Transactions:")
        print("=" * 80)
        print(f"{'Category':<20} {'Count':<10} {'Min':<15} {'Max':<15} {'Avg':<15} {'Total':<15}")
        print("-" * 80)

        total_wallets = 0
        for category, count, min_bal, max_bal, avg_bal, total_bal in results:
            total_wallets += count
            min_str = f"{min_bal:,.2f}" if min_bal is not None else "N/A"
            max_str = f"{max_bal:,.2f}" if max_bal is not None else "N/A"
            avg_str = f"{avg_bal:,.2f}" if avg_bal is not None else "N/A"
            total_str = f"{total_bal:,.2f}" if total_bal is not None else "N/A"
            print(f"{category:<20} {count:<10,} {min_str:<15} {max_str:<15} {avg_str:<15} {total_str:<15}")

        print("-" * 80)
        print(f"{'TOTAL':<20} {total_wallets:<10,}")
        print("=" * 80)

        # Query 2: Sample some non-zero balance wallets without transactions
        print("\n\nSample of wallets with NON-ZERO balance but NO transactions:")
        print("-" * 80)
        query_sample = """
        SELECT
            ws.wallet_id,
            ws.available_balance,
            ws.wallet_type,
            u.email,
            u.first_name,
            u.last_name
        FROM accounts_walletsystem ws
        LEFT JOIN main_user u ON ws.user_id = u.id
        WHERE ws.available_balance != 0
          AND ws.available_balance IS NOT NULL
          AND NOT EXISTS (
            SELECT 1
            FROM accounts_transaction t
            WHERE t.source_wallet_id::uuid = ws.wallet_id
              AND t.date_created < '2026-01-01 00:00:00'
        )
        ORDER BY ABS(ws.available_balance) DESC
        LIMIT 20;
        """

        cursor.execute(query_sample)
        samples = cursor.fetchall()

        if samples:
            print(f"\nFound {len(samples)} sample wallets (showing top 20 by absolute balance):\n")
            for wallet_id, balance, wallet_type, email, first_name, last_name in samples:
                print(f"Wallet ID: {wallet_id}")
                print(f"  Balance: ₦{balance:,.2f}")
                print(f"  Type: {wallet_type}")
                print(f"  User: {first_name} {last_name} ({email})")
                print()
        else:
            print("No wallets found with non-zero balance and no transactions.")

        cursor.close()
        conn.close()
        print("\nConnection closed.")

    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    print("=" * 80)
    print("Wallet Balance Analysis - Wallets Without Transactions")
    print("=" * 80)
    print()

    check_zero_balance_wallets()

