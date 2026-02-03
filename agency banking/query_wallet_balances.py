import psycopg2
from psycopg2 import Error
import pandas as pd

def run_wallet_balance_query():
    """
    Run query to get the latest balance for each source wallet
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

        # SQL Query
        query = """
        SELECT
            source_wallet_id,
            balance_after,
            date_created
        FROM (
            SELECT DISTINCT ON (source_wallet_id)
                source_wallet_id,
                balance_after,
                date_created
            FROM accounts_transaction
            ORDER BY source_wallet_id, date_created DESC
        ) t;
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

            # Save to CSV
            csv_filename = "wallet_balances.csv"
            df.to_csv(csv_filename, index=False)
            print(f"\n✓ Results saved to {csv_filename}")

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
    print("Wallet Balance Query - Latest Balance per Source Wallet")
    print("=" * 80)
    print()

    run_wallet_balance_query()

