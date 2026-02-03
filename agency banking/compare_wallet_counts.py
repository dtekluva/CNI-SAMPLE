#!/usr/bin/env python3
"""
Compare wallet counts between wallet system table and transaction table
"""

import psycopg2

def compare_wallet_counts():
    """Compare total wallets in wallet system vs transaction table"""

    try:
        # Database connection parameters
        connection_params = {
            'host': '143.244.178.203',
            'database': 'agency_banking_db',
            'user': 'datauser',
            'password': 'EiRXo6IfeHQuM3wcbZ67$LzwmVKCXhpUhWg',
            'port': '5432'
        }

        # Connect to database
        print("Connecting to the database...")
        conn = psycopg2.connect(**connection_params)
        print("✓ Connected successfully!\n")

        cursor = conn.cursor()

        # Query 1: Total wallets in accounts_walletsystem table
        print("Querying accounts_walletsystem table...")
        query_wallet_system = """
        SELECT COUNT(*) as total_wallets
        FROM accounts_walletsystem;
        """
        cursor.execute(query_wallet_system)
        wallet_system_count = cursor.fetchone()[0]
        print(f"✓ Total wallets in accounts_walletsystem: {wallet_system_count:,}\n")

        # Query 2: Total unique wallets in accounts_transaction table (all time)
        print("Querying accounts_transaction table (all time)...")
        query_transaction_all = """
        SELECT COUNT(DISTINCT source_wallet_id) as unique_wallets
        FROM accounts_transaction
        WHERE source_wallet_id IS NOT NULL;
        """
        cursor.execute(query_transaction_all)
        transaction_all_count = cursor.fetchone()[0]
        print(f"✓ Unique wallets in accounts_transaction (all time): {transaction_all_count:,}\n")

        # Query 3: Total unique wallets in accounts_transaction table (before 2026-01-01)
        print("Querying accounts_transaction table (before 2026-01-01)...")
        query_transaction_2026 = """
        SELECT COUNT(DISTINCT source_wallet_id) as unique_wallets
        FROM accounts_transaction
        WHERE source_wallet_id IS NOT NULL
          AND date_created < '2026-01-01 00:00:00';
        """
        cursor.execute(query_transaction_2026)
        transaction_2026_count = cursor.fetchone()[0]
        print(f"✓ Unique wallets in accounts_transaction (before 2026-01-01): {transaction_2026_count:,}\n")

        # Query 4: Combined query for wallets without transactions and their balances
        print("Analyzing wallets without transactions (this may take a moment)...")
        query_combined = """
        WITH wallets_no_txn AS (
            SELECT
                ws.wallet_id,
                ws.wallet_type,
                ws.available_balance
            FROM accounts_walletsystem ws
            WHERE NOT EXISTS (
                SELECT 1
                FROM accounts_transaction t
                WHERE t.source_wallet_id::uuid = ws.wallet_id
                  AND t.date_created < '2026-01-01 00:00:00'
            )
        )
        SELECT
            COUNT(*) as total_count,
            SUM(CASE WHEN available_balance = 0 THEN 1 ELSE 0 END) as zero_balance_count,
            SUM(CASE WHEN available_balance > 0 THEN 1 ELSE 0 END) as positive_balance_count,
            SUM(CASE WHEN available_balance < 0 THEN 1 ELSE 0 END) as negative_balance_count,
            SUM(CASE WHEN available_balance IS NULL THEN 1 ELSE 0 END) as null_balance_count,
            COALESCE(SUM(available_balance), 0) as total_balance,
            COALESCE(SUM(CASE WHEN available_balance > 0 THEN available_balance ELSE 0 END), 0) as positive_total
        FROM wallets_no_txn;
        """
        cursor.execute(query_combined)
        result = cursor.fetchone()
        wallets_without_transactions = result[0]
        zero_bal_count = result[1]
        positive_bal_count = result[2]
        negative_bal_count = result[3]
        null_bal_count = result[4]
        total_balance_no_txn = result[5]
        positive_total = result[6]

        print(f"✓ Wallets in system but NO transactions (before 2026-01-01): {wallets_without_transactions:,}\n")

        # Display balance breakdown
        print("\nBalance Breakdown (wallets without transactions):")
        print("-" * 80)
        print(f"{'Category':<20} {'Count':<15} {'Total Balance':<20}")
        print("-" * 80)
        if zero_bal_count > 0:
            print(f"{'Zero Balance':<20} {zero_bal_count:<15,} {'₦0.00':<20}")
        if positive_bal_count > 0:
            print(f"{'Positive Balance':<20} {positive_bal_count:<15,} ₦{positive_total:,.2f}")
        if negative_bal_count > 0:
            negative_total = total_balance_no_txn - positive_total
            print(f"{'Negative Balance':<20} {negative_bal_count:<15,} ₦{negative_total:,.2f}")
        if null_bal_count > 0:
            print(f"{'NULL Balance':<20} {null_bal_count:<15,} {'N/A':<20}")
        print("-" * 80)
        print(f"{'TOTAL':<20} {wallets_without_transactions:<15,} ₦{total_balance_no_txn:,.2f}")
        print("-" * 80)

        # Query 5: Get wallet type breakdown for wallets without transactions
        print("\nGetting wallet type breakdown for wallets without transactions...")
        query_wallet_types = """
        SELECT
            ws.wallet_type,
            COUNT(*) as count,
            SUM(ws.available_balance) as total_balance,
            COUNT(CASE WHEN ws.available_balance > 0 THEN 1 END) as non_zero_count
        FROM accounts_walletsystem ws
        WHERE NOT EXISTS (
            SELECT 1
            FROM accounts_transaction t
            WHERE t.source_wallet_id::uuid = ws.wallet_id
              AND t.date_created < '2026-01-01 00:00:00'
        )
        GROUP BY ws.wallet_type
        ORDER BY total_balance DESC NULLS LAST;
        """
        cursor.execute(query_wallet_types)
        wallet_types = cursor.fetchall()

        print("\nWallet Type Breakdown (wallets without transactions):")
        print("-" * 100)
        print(f"{'Wallet Type':<25} {'Total Count':<15} {'Non-Zero Count':<18} {'Total Balance':<20}")
        print("-" * 100)
        for wallet_type, count, total_bal, non_zero_count in wallet_types:
            total_bal_str = f"₦{total_bal:,.2f}" if total_bal is not None else "₦0.00"
            print(f"{wallet_type:<25} {count:<15,} {non_zero_count:<18,} {total_bal_str:<20}")
        print("-" * 100)

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total wallets in wallet system:                    {wallet_system_count:,}")
        print(f"Unique wallets with transactions (all time):       {transaction_all_count:,}")
        print(f"Unique wallets with transactions (before 2026):    {transaction_2026_count:,}")
        print(f"Wallets WITHOUT transactions (before 2026):        {wallets_without_transactions:,}")
        print(f"\nPercentage with transactions (before 2026):        {(transaction_2026_count/wallet_system_count*100):.2f}%")
        print(f"Percentage WITHOUT transactions (before 2026):     {(wallets_without_transactions/wallet_system_count*100):.2f}%")
        print(f"\n⚠️  IMPORTANT: Wallets without transactions hold:   ₦{total_balance_no_txn:,.2f}")
        print(f"    These balances contribute to total system balance!")
        print("=" * 80)

        cursor.close()
        conn.close()
        print("\nConnection closed.")

    except psycopg2.Error as e:
        print(f"✗ Database error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    print("=" * 80)
    print("Wallet Count Comparison")
    print("Wallet System Table vs Transaction Table")
    print("=" * 80)
    print()

    compare_wallet_counts()

