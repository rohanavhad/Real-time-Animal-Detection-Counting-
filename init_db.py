import mysql.connector
from mysql.connector import errorcode

# Database configuration
DB_CONFIG = {
    'user': 'your_username',        # Replace with your MySQL username
    'password': 'your_password',    # Replace with your MySQL password
    'host': 'localhost',            # Database host
    'database': 'animal_detection'   # Name of the database to be created
}

def init_db():
    try:
        # Connect to MySQL server
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        print(f"Database '{DB_CONFIG['database']}' created or already exists.")

        # Use the created database
        cursor.execute(f"USE {DB_CONFIG['database']}")

        # Create the 'detections' table if it doesn't already exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INT AUTO_INCREMENT PRIMARY KEY,
                object VARCHAR(255) NOT NULL,
                confidence FLOAT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                count INT NOT NULL
            )
        ''')

        # Commit changes and close the connection
        conn.commit()
        print("Table 'detections' created or already exists.")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Access denied: Invalid username or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    init_db()  # Call the function to initialize the database
