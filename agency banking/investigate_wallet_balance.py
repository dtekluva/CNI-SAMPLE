#!/usr/bin/env python3
"""
Investigate specific wallet balance discrepancy
"""

import psycopg2

def investigate_wallet(wallet_id):
    """Investigate transaction history for a specific wallet"""

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

        # Query 1: Get current wallet info
        print(f"Checking wallet: {wallet_id}")
        print("=" * 100)
        query_wallet = """
        SELECT
            wallet_id,
            wallet_type,
            available_balance,
            hold_balance,
            date_created,
            last_updated,
            user_id
        FROM accounts_walletsystem
        WHERE wallet_id = %s;
        """
        cursor.execute(query_wallet, (wallet_id,))
        wallet_info = cursor.fetchone()

        if wallet_info:
            print("\nCurrent Wallet Information:")
            print("-" * 100)
            print(f"Wallet ID:         {wallet_info[0]}")
            print(f"Wallet Type:       {wallet_info[1]}")
            print(f"Available Balance: ₦{wallet_info[2]:,.2f}")
            print(f"Hold Balance:      ₦{wallet_info[3]:,.2f}")
            print(f"Date Created:      {wallet_info[4]}")
            print(f"Last Updated:      {wallet_info[5]}")
            print(f"User ID:           {wallet_info[6]}")
        else:
            print("Wallet not found!")
            return

        # Query 2: Count total transactions
        query_count = """
        SELECT COUNT(*)
        FROM accounts_transaction
        WHERE source_wallet_id = %s
          AND date_created < '2026-01-01 00:00:00';
        """
        cursor.execute(query_count, (wallet_id,))
        total_count = cursor.fetchone()[0]
        print(f"\nTotal transactions for this wallet: {total_count:,}")

        # Query 3: Get the LAST transaction before 2026-01-01
        print("\n" + "=" * 100)
        print("LAST Transaction before 2026-01-01:")
        print("=" * 100)
        query_last_txn = """
        SELECT
            id,
            transaction_type,
            amount,
            balance_before,
            balance_after,
            date_created,
            status
        FROM accounts_transaction
        WHERE source_wallet_id = %s
          AND date_created < '2026-01-01 00:00:00'
        ORDER BY date_created DESC
        LIMIT 1;
        """
        cursor.execute(query_last_txn, (wallet_id,))
        last_txn = cursor.fetchone()

        if last_txn:
            print(f"\nTransaction ID:    {last_txn[0]}")
            print(f"Type:              {last_txn[1]}")
            print(f"Amount:            ₦{last_txn[2]:,.2f}")
            print(f"Balance Before:    ₦{last_txn[3]:,.2f}")
            print(f"Balance After:     ₦{last_txn[4]:,.2f}")
            print(f"Date:              {last_txn[5]}")
            print(f"Status:            {last_txn[6]}")

            print("\n" + "=" * 100)
            print("COMPARISON:")
            print("=" * 100)
            print(f"Balance from CSV:              ₦32,721,591.73")
            print(f"Last transaction balance_after: ₦{last_txn[4]:,.2f}")
            print(f"Current wallet balance:         ₦{wallet_info[2]:,.2f}")

            if abs(last_txn[4] - 32721591.73) > 0.01:
                print(f"\n⚠️  DISCREPANCY FOUND!")
                print(f"Difference: ₦{abs(last_txn[4] - 32721591.73):,.2f}")
        else:
            print("No transactions found!")

        # Query 4: Get MAX balance_after value
        print("\n" + "=" * 100)
        print("MAXIMUM balance_after value in all transactions:")
        print("=" * 100)
        query_max = """
        SELECT
            id,
            transaction_type,
            amount,
            balance_before,
            balance_after,
            date_created,
            status
        FROM accounts_transaction
        WHERE source_wallet_id = %s
          AND date_created < '2026-01-01 00:00:00'
          AND balance_after IS NOT NULL
        ORDER BY balance_after DESC
        LIMIT 1;
        """
        cursor.execute(query_max, (wallet_id,))
        max_txn = cursor.fetchone()

        if max_txn:
            print(f"\nTransaction ID:    {max_txn[0]}")
            print(f"Type:              {max_txn[1]}")
            print(f"Amount:            ₦{max_txn[2]:,.2f}" if max_txn[2] else "N/A")
            print(f"Balance Before:    ₦{max_txn[3]:,.2f}" if max_txn[3] else "N/A")
            print(f"Balance After:     ₦{max_txn[4]:,.2f}")
            print(f"Date:              {max_txn[5]}")
            print(f"Status:            {max_txn[6]}")

            print("\n" + "=" * 100)
            print("COMPARISON:")
            print("=" * 100)
            print(f"Balance from CSV:              ₦32,721,591.73")
            print(f"MAX balance_after in DB:       ₦{max_txn[4]:,.2f}")

            if abs(max_txn[4] - 32721591.73) < 0.01:
                print(f"\n✓ MATCH FOUND! The CSV value matches the MAXIMUM balance_after")
                print(f"  This suggests the CSV is using MAX(balance_after) instead of the LAST transaction")
            else:
                print(f"\n⚠️  NO MATCH - Difference: ₦{abs(max_txn[4] - 32721591.73):,.2f}")

        cursor.close()
        conn.close()
        print("\nConnection closed.")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    wallet_id = "a20af24d-f588-41ff-a875-1c5ff9a8e696"
    investigate_wallet(wallet_id)

