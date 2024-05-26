import sqlite3

# TODO: make the addresses table more, and change sql handler functions accordingly
# TODO: change the addresses table to users table, and have the following fields:
# TODO: id (pk, ai, u), hostname, address, code
# ic(get_bare_hostname(addr[0]))

class SQLHandler:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.connection = None
        self.create_address_table()

    # Base functions
    def connect(self):
        self.connection = sqlite3.connect(self.db_name)
        print(f"Connected to {self.db_name}")

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            print(f"Disconnected from {self.db_name}")

    def execute_query(self, query: str, params=None):
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            self.connection.rollback()
            return None

    def fetchall(self, query: str, params=None):
        cursor = self.execute_query(query, params)
        if cursor:
            return cursor.fetchall()
        return []

    def fetchone(self, query: str, params=None):
        cursor = self.execute_query(query, params)
        if cursor:
            return cursor.fetchone()
        return None

    def insert(self, query: str, params: tuple):
        cursor = self.execute_query(query, params)
        if cursor:
            return cursor.lastrowid
        return None

    # Custom Functions

    def create_address_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS addresses (
        address TEXT PRIMARY KEY NOT NULL,
        code TEXT NOT NULL
        )
        """
        self.execute_query(query)

    # Checks if a value is in a specific column in a specific table, returns True or False
    def is_value_in(self, table_name: str, column_name: str, value: str) -> bool:
        query = f"SELECT 1 FROM {table_name} WHERE {column_name} = ?"
        exists = bool(self.fetchone(query, (value,)))
        return exists

    # With a given address, get the code
    def get_code_for_address(self, address: str):
        query = "SELECT code FROM addresses WHERE address = ?"
        row = self.fetchone(query, (address,))
        if row:
            return row[0]
        else:
            return None

    def insert_address_and_code(self, address: str, code: str):
        query = "INSERT INTO addresses (address, code) VALUES (?, ?)"
        self.insert(query, (address,code))


