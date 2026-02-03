#!/usr/bin/env python3
"""
Verify if wallet_balances_as_at_2026_start.csv contains wallets without transactions
"""

import psycopg2
import csv

def verify_csv_completeness():
    """Check if CSV includes wallets without transactions"""

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

        # Read wallet IDs from CSV
        print("Reading wallet_balances_as_at_2026_start.csv...")
        csv_wallet_ids = set()
        with open('wallet_balances_as_at_2026_start.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_wallet_ids.add(row['source_wallet_id'])

        print(f"✓ Found {len(csv_wallet_ids):,} wallets in CSV\n")

        # Query 1: Get all wallet IDs from database
        print("Querying all wallets from database...")
        query_all_wallets = """
        SELECT wallet_id::text
        FROM accounts_walletsystem;
        """
        cursor.execute(query_all_wallets)
        db_wallet_ids = set(row[0] for row in cursor.fetchall())
        print(f"✓ Found {len(db_wallet_ids):,} wallets in database\n")

        # Query 2: Get wallets WITHOUT transactions
        print("Querying wallets WITHOUT transactions...")
        query_no_txn = """
        SELECT ws.wallet_id::text
        FROM accounts_walletsystem ws
        WHERE NOT EXISTS (
            SELECT 1
            FROM accounts_transaction t
            WHERE t.source_wallet_id::uuid = ws.wallet_id
              AND t.date_created < '2026-01-01 00:00:00'
        );
        """
        cursor.execute(query_no_txn)
        no_txn_wallet_ids = set(row[0] for row in cursor.fetchall())
        print(f"✓ Found {len(no_txn_wallet_ids):,} wallets WITHOUT transactions\n")

        # Query 3: Get wallets WITHOUT transactions but WITH non-zero balance
        print("Querying wallets WITHOUT transactions but WITH non-zero balance...")
        query_no_txn_nonzero = """
        SELECT ws.wallet_id::text, ws.available_balance, ws.wallet_type
        FROM accounts_walletsystem ws
        WHERE ws.available_balance != 0
          AND ws.available_balance IS NOT NULL
          AND NOT EXISTS (
            SELECT 1
            FROM accounts_transaction t
            WHERE t.source_wallet_id::uuid = ws.wallet_id
              AND t.date_created < '2026-01-01 00:00:00'
        );
        """
        cursor.execute(query_no_txn_nonzero)
        no_txn_nonzero = cursor.fetchall()
        no_txn_nonzero_ids = set(row[0] for row in no_txn_nonzero)
        print(f"✓ Found {len(no_txn_nonzero_ids):,} wallets WITHOUT transactions but WITH non-zero balance\n")

        # Analysis
        print("=" * 80)
        print("ANALYSIS")
        print("=" * 80)

        # Check if CSV contains wallets without transactions
        no_txn_in_csv = csv_wallet_ids.intersection(no_txn_wallet_ids)
        no_txn_missing_from_csv = no_txn_wallet_ids - csv_wallet_ids

        print(f"\nWallets WITHOUT transactions:")
        print(f"  Total in database:                    {len(no_txn_wallet_ids):,}")
        print(f"  Present in CSV:                       {len(no_txn_in_csv):,}")
        print(f"  Missing from CSV:                     {len(no_txn_missing_from_csv):,}")

        # Check non-zero balance wallets
        no_txn_nonzero_in_csv = csv_wallet_ids.intersection(no_txn_nonzero_ids)
        no_txn_nonzero_missing = no_txn_nonzero_ids - csv_wallet_ids

        print(f"\nWallets WITHOUT transactions but WITH non-zero balance:")
        print(f"  Total in database:                    {len(no_txn_nonzero_ids):,}")
        print(f"  Present in CSV:                       {len(no_txn_nonzero_in_csv):,}")
        print(f"  Missing from CSV:                     {len(no_txn_nonzero_missing):,}")

        if no_txn_nonzero_missing:
            total_missing_balance = sum(row[1] for row in no_txn_nonzero if row[0] in no_txn_nonzero_missing)
            print(f"  Total balance MISSING from CSV:       ₦{total_missing_balance:,.2f}")

        # Check all wallets
        all_missing = db_wallet_ids - csv_wallet_ids
        print(f"\nAll wallets:")
        print(f"  Total in database:                    {len(db_wallet_ids):,}")
        print(f"  Present in CSV:                       {len(csv_wallet_ids):,}")
        print(f"  Missing from CSV:                     {len(all_missing):,}")

        # Show sample of missing non-zero balance wallets
        if no_txn_nonzero_missing:
            print("\n" + "=" * 80)
            print("SAMPLE OF MISSING WALLETS (Non-zero balance, no transactions)")
            print("=" * 80)
            sample_count = 0
            for wallet_id, balance, wallet_type in no_txn_nonzero:
                if wallet_id in no_txn_nonzero_missing and sample_count < 10:
                    print(f"\nWallet ID: {wallet_id}")
                    print(f"  Balance: ₦{balance:,.2f}")
                    print(f"  Type: {wallet_type}")
                    sample_count += 1

        print("\n" + "=" * 80)
        if no_txn_nonzero_missing:
            print("⚠️  WARNING: CSV is INCOMPLETE!")
            print(f"    Missing {len(no_txn_nonzero_missing):,} wallets with non-zero balances")
            print(f"    Total missing balance: ₦{total_missing_balance:,.2f}")
        else:
            print("✓ CSV is COMPLETE - includes all wallets with non-zero balances")
        print("=" * 80)

        cursor.close()
        conn.close()
        print("\nConnection closed.")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_csv_completeness()

