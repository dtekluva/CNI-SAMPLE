#!/usr/bin/env python3
import psycopg2
import sys

wallet_id = "a20af24d-f588-41ff-a875-1c5ff9a8e696"

try:
    conn = psycopg2.connect(
        host='143.244.178.203',
        database='agency_banking_db',
        user='datauser',
        password='EiRXo6IfeHQuM3wcbZ67$LzwmVKCXhpUhWg',
        port='5432'
    )
    
    cursor = conn.cursor()
    
    # Get wallet info
    cursor.execute("""
        SELECT wallet_id, wallet_type, available_balance
        FROM accounts_walletsystem
        WHERE wallet_id = %s
    """, (wallet_id,))
    
    wallet = cursor.fetchone()
    print(f"Wallet: {wallet[0]}")
    print(f"Type: {wallet[1]}")
    print(f"Current Balance: ₦{wallet[2]:,.2f}")
    print()
    
    # Get last transaction
    cursor.execute("""
        SELECT balance_after, date_created
        FROM accounts_transaction
        WHERE source_wallet_id = %s
          AND date_created < '2026-01-01'
        ORDER BY date_created DESC
        LIMIT 1
    """, (wallet_id,))
    
    last_txn = cursor.fetchone()
    if last_txn:
        print(f"Last transaction balance_after: ₦{last_txn[0]:,.2f}")
        print(f"Last transaction date: {last_txn[1]}")
    else:
        print("No transactions found")
    print()
    
    # Get MAX balance_after
    cursor.execute("""
        SELECT balance_after, date_created
        FROM accounts_transaction
        WHERE source_wallet_id = %s
          AND date_created < '2026-01-01'
          AND balance_after IS NOT NULL
        ORDER BY balance_after DESC
        LIMIT 1
    """, (wallet_id,))
    
    max_txn = cursor.fetchone()
    if max_txn:
        print(f"MAX balance_after: ₦{max_txn[0]:,.2f}")
        print(f"Date of MAX: {max_txn[1]}")
        print()
        print(f"CSV shows: ₦32,721,591.73")
        print(f"Difference from MAX: ₦{abs(max_txn[0] - 32721591.73):,.2f}")
        
        if abs(max_txn[0] - 32721591.73) < 1:
            print("\n✓ CSV value matches MAX balance_after!")
        else:
            print("\n✗ CSV value does NOT match MAX balance_after")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

