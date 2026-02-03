import psycopg2
from psycopg2 import Error
import pandas as pd

def run_wallet_balance_query_with_user():
    """
    Run query to get the latest balance for each source wallet
    with wallet type and user email from wallet system
    """
    connection = None
    cursor = None

    try:
        # Database connection parameters
        connection_params = {
            'host': '143.244.178.203',
            'database': 'agency_banking_db',
            'user': 'datauser',
            'password': 'EiRXo6IfeHQuM3wcbZ67$LzwmVKCXhpUhWg',
            'port': '5432',
            'connect_timeout': 10
        }

        print("Connecting to the database...")
        connection = psycopg2.connect(**connection_params)
        cursor = connection.cursor()
        print("✓ Connected successfully!\n")

        # SQL Query with JOIN to wallet system and user tables
        # Note: source_wallet_id is varchar (UUID), ws.wallet_id is uuid
        # Filter: Only transactions up to January 1st, 2026 00:00:00
        query = """
        SELECT
            t.source_wallet_id,
            t.balance_after,
            t.date_created,
            ws.wallet_type,
            u.email as user_email,
            u.first_name,
            u.last_name
        FROM (
            SELECT DISTINCT ON (source_wallet_id)
                source_wallet_id,
                balance_after,
                date_created
            FROM accounts_transaction
            WHERE source_wallet_id IS NOT NULL
              AND date_created < '2026-01-01 00:00:00'
            ORDER BY source_wallet_id, date_created DESC
        ) t
        LEFT JOIN accounts_walletsystem ws ON t.source_wallet_id::uuid = ws.wallet_id
        LEFT JOIN main_user u ON ws.user_id = u.id
        ORDER BY t.source_wallet_id;
        """

        print("Executing query...")
        print("-" * 80)
        cursor.execute(query)

        # Fetch all results
        results = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]

        print(f"Query returned {len(results)} rows\n")

        if results:
            # Create DataFrame for better display
            df = pd.DataFrame(results, columns=column_names)

            print("Results:")
            print("=" * 80)
            print(df.to_string(index=False))
            print("=" * 80)

            # Summary statistics
            print(f"\nSummary:")
            print(f"  Total wallets: {len(results)}")
            print(f"  Total balance across all wallets: {df['balance_after'].sum():,.2f}")
            print(f"  Average balance: {df['balance_after'].mean():,.2f}")
            print(f"  Min balance: {df['balance_after'].min():,.2f}")
            print(f"  Max balance: {df['balance_after'].max():,.2f}")

            # Wallet type breakdown
            if 'wallet_type' in df.columns:
                print(f"\nWallet Type Breakdown:")
                wallet_type_summary = df.groupby('wallet_type').agg({
                    'source_wallet_id': 'count',
                    'balance_after': 'sum'
                }).rename(columns={'source_wallet_id': 'count', 'balance_after': 'total_balance'})
                print(wallet_type_summary.to_string())

            # Save to CSV
            csv_filename = "wallet_balances_as_at_2026_start.csv"
            df.to_csv(csv_filename, index=False)
            print(f"\n✓ Results saved to {csv_filename}")
            print(f"✓ Balances as at: January 1st, 2026 00:00:00")

        else:
            print("No results found.")

        return results

    except (Exception, Error) as error:
        print("✗ Error while executing query:")
        print(f"Error type: {type(error).__name__}")
        print(f"Error details: {error}")
        return None

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            print("\nConnection closed.")

if __name__ == "__main__":
    print("=" * 80)
    print("Wallet Balance Query - As at January 1st, 2026 00:00:00")
    print("With Wallet Type and User Email")
    print("=" * 80)
    print()

    run_wallet_balance_query_with_user()

