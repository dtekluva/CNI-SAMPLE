import psycopg2
from psycopg2 import Error

def connect_to_database():
    """
    Attempt to connect to the PostgreSQL database
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
            'port': '5432'
        }
        
        print("Attempting to connect to the database...")
        print(f"Host: {connection_params['host']}")
        print(f"Database: {connection_params['database']}")
        print(f"User: {connection_params['user']}")
        print(f"Port: {connection_params['port']}")
        print("-" * 50)
        
        # Establish connection
        connection = psycopg2.connect(**connection_params)
        
        # Create a cursor object
        cursor = connection.cursor()
        
        # Print PostgreSQL connection properties
        print("✓ Successfully connected to PostgreSQL database!")
        print("-" * 50)
        
        # Get PostgreSQL version
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"PostgreSQL version: {db_version[0]}")
        print("-" * 50)
        
        # Get current database name
        cursor.execute("SELECT current_database();")
        current_db = cursor.fetchone()
        print(f"Current database: {current_db[0]}")
        print("-" * 50)
        
        # List all tables in the database
        cursor.execute("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"Found {len(tables)} table(s) in the database:")
            for schema, table in tables:
                print(f"  - {schema}.{table}")
        else:
            print("No user tables found in the database.")
        
        print("-" * 50)
        print("✓ Connection test completed successfully!")
        
        return connection
        
    except (Exception, Error) as error:
        print("✗ Error while connecting to PostgreSQL database:")
        print(f"Error type: {type(error).__name__}")
        print(f"Error details: {error}")
        return None
        
    finally:
        # Close cursor
        if cursor:
            cursor.close()
            
        # Note: We return the connection, so we don't close it here
        # The caller should close it when done

if __name__ == "__main__":
    print("=" * 50)
    print("PostgreSQL Database Connection Test")
    print("=" * 50)
    
    connection = connect_to_database()
    
    if connection:
        print("\n" + "=" * 50)
        print("Connection object is available for use")
        print("=" * 50)
        # Close the connection when done
        connection.close()
        print("Connection closed.")
    else:
        print("\n" + "=" * 50)
        print("Failed to establish connection")
        print("=" * 50)

