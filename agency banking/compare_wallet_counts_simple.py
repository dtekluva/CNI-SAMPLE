#!/usr/bin/env python3
"""
Compare wallet counts - Simple version
"""

import psycopg2

def run_query(query_name, query):
    """Run a single query and return result"""
    try:
        # Database connection parameters
        connection_params = {
            'host': '143.244.178.203',
            'database': 'agency_banking_db',
            'user': 'datauser',
            'password': 'EiRXo6IfeHQuM3wcbZ67$LzwmVKCXhpUhWg',
            'port': '5432'
        }
        
        print(f"\n{query_name}")
        print("-" * 80)
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
        
        cursor.execute(query)
        result = cursor.fetchone()[0]
        
        print(f"Result: {result:,}")
        
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

if __name__ == "__main__":
    print("=" * 80)
    print("Wallet Count Comparison")
    print("=" * 80)
    
    # Query 1: Total wallets in wallet system
    q1 = """
    SELECT COUNT(*) 
    FROM accounts_walletsystem;
    """
    wallet_system_count = run_query("1. Total wallets in accounts_walletsystem", q1)
    
    # Query 2: Unique wallets in transactions (before 2026)
    q2 = """
    SELECT COUNT(DISTINCT source_wallet_id)
    FROM accounts_transaction
    WHERE source_wallet_id IS NOT NULL
      AND date_created < '2026-01-01 00:00:00';
    """
    transaction_count = run_query("2. Unique wallets in transactions (before 2026-01-01)", q2)
    
    # Summary
    if wallet_system_count and transaction_count:
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total wallets in wallet system:              {wallet_system_count:,}")
        print(f"Wallets with transactions (before 2026):     {transaction_count:,}")
        print(f"Wallets WITHOUT transactions (before 2026):  {wallet_system_count - transaction_count:,}")
        print(f"\nPercentage with transactions:                {(transaction_count/wallet_system_count*100):.2f}%")
        print(f"Percentage WITHOUT transactions:             {((wallet_system_count - transaction_count)/wallet_system_count*100):.2f}%")
        print("=" * 80)

