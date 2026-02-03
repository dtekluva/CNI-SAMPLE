import psycopg2
from psycopg2 import Error

def check_table_structure():
    """
    Check the structure of accounts_transaction and accounts_walletsystem tables
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

        # Check accounts_transaction table structure
        print("=" * 80)
        print("ACCOUNTS_TRANSACTION TABLE STRUCTURE")
        print("=" * 80)
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'accounts_transaction'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[0]:<30} {col[1]:<20} {col[2] if col[2] else ''}")

        # Check accounts_walletsystem table structure
        print("\n" + "=" * 80)
        print("ACCOUNTS_WALLETSYSTEM TABLE STRUCTURE")
        print("=" * 80)
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'accounts_walletsystem'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[0]:<30} {col[1]:<20} {col[2] if col[2] else ''}")

        # Check main_user table structure
        print("\n" + "=" * 80)
        print("MAIN_USER TABLE STRUCTURE")
        print("=" * 80)
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'main_user'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[0]:<30} {col[1]:<20} {col[2] if col[2] else ''}")

        # Sample data from accounts_transaction
        print("\n" + "=" * 80)
        print("SAMPLE DATA FROM ACCOUNTS_TRANSACTION (first 3 rows)")
        print("=" * 80)
        cursor.execute("""
            SELECT source_wallet_id, balance_after, date_created
            FROM accounts_transaction
            LIMIT 3;
        """)
        rows = cursor.fetchall()
        for row in rows:
            print(f"  source_wallet_id: {row[0]}, balance_after: {row[1]}, date_created: {row[2]}")

        # Sample data from accounts_walletsystem
        print("\n" + "=" * 80)
        print("SAMPLE DATA FROM ACCOUNTS_WALLETSYSTEM (first 3 rows)")
        print("=" * 80)
        cursor.execute("""
            SELECT id, wallet_type, user_id
            FROM accounts_walletsystem
            LIMIT 3;
        """)
        rows = cursor.fetchall()
        for row in rows:
            print(f"  id: {row[0]}, wallet_type: {row[1]}, user_id: {row[2]}")

    except (Exception, Error) as error:
        print("✗ Error:")
        print(f"Error type: {type(error).__name__}")
        print(f"Error details: {error}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            print("\nConnection closed.")

if __name__ == "__main__":
    check_table_structure()

