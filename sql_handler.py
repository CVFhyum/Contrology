"""
Consider changing the logs table such that only the user id is stored, as that is the only option that matters.
In the code, add the possibility to display the hostname, address, and code as well.
Fetch these from the users table.
"""

import sqlite3
import time
from icecream import ic


class SQLHandler:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.connection = None
        self.create_users_table()
        self.create_logs_table()

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
            self.connection.rollback()
            raise Exception(f"An SQL Error occurred: {e}")

    def fetch_data_generator(self,query: str,params=None,chunk_size=100):
        cursor = self.execute_query(query,params)
        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break
            yield rows

    def fetchall(self, query: str, params=None, chunk_size=100):
        for rows in self.fetch_data_generator(query, params, chunk_size):
            yield rows

    def fetchone(self, query: str, params=None):
        cursor = self.execute_query(query, params)
        if cursor:
            return cursor.fetchone()
        return None

    # Custom Functions
    def create_users_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostname TEXT NOT NULL,
            address TEXT NOT NULL,
            code TEXT NOT NULL,
            is_connected INTEGER NOT NULL CHECK (is_connected IN (0, 1))
        )
        """
        self.execute_query(query)

    def create_logs_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            user_id INTEGER NOT NULL,
            user_hostname TEXT NOT NULL,
            action TEXT NOT NULL,
            target_user_id INTEGER,
            target_user_hostname TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (target_user_id) REFERENCES users(id)
        )
        """
        self.execute_query(query)

    # Checks if a value is in a specific column in a specific table, returns True or False
    def is_value_in(self, table_name: str, column_name: str, value: str) -> bool:
        query = f"SELECT 1 FROM {table_name} WHERE {column_name} = ?"
        exists = bool(self.fetchone(query, (value,)))
        return exists

    # Return the values of a user
    def get_user_info(self,*,user_id=None,ip_addr=None,code=None):
        if sum(arg is not None for arg in (user_id,ip_addr,code)) != 1:
            raise ValueError("Exactly one identifying argument (ip_addr, user_id, code) must be provided")

        if user_id is not None:
            query = "SELECT * FROM users WHERE id = ?"
            params = (user_id,)
        elif ip_addr is not None:
            query = "SELECT * FROM users WHERE address = ?"
            params = (ip_addr,)
        elif code is not None:
            query = "SELECT * FROM users WHERE code = ?"
            params = (code,)
        else:
            return None

        cursor = self.execute_query(query,params)
        result = cursor.fetchone()

        if result:
            # Getting column names from the cursor description
            column_names = [description[0] for description in cursor.description]
            # Creating a dictionary from column names and result values
            result_dict = dict(zip(column_names,result))
            return result_dict
        return None

    def code_exists(self, code) -> bool:
        query = "SELECT 1 FROM users WHERE code = ?"
        result = self.fetchone(query,(code,))
        return bool(result)

    # Adds a user with given information and returns their new id
    def add_user(self,*,hostname: str,address: str,code: str,is_connected: int) -> int:
        query = "INSERT INTO users (hostname, address, code, is_connected) VALUES (?, ?, ?, ?)"
        cursor = self.execute_query(query,(hostname,address,code,is_connected))
        return cursor.lastrowid if cursor else None

    def set_user_connection_status(self,user_id: int, new_status: bool) -> None:
        query = "UPDATE users SET is_connected = ? WHERE id = ?"
        self.execute_query(query,(1 if new_status else 0,user_id))

    def set_all_users_disconnected(self):
        query = "UPDATE users SET is_connected = 0"
        self.execute_query(query)

    def log(self,*,user_id,user_hostname,action,target_user_id=None,target_user_hostname=None):
        timestamp = time.time()  # Get current time as float
        query = """
        INSERT INTO logs (timestamp, user_id, user_hostname, action, target_user_id, target_user_hostname)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (timestamp,user_id,user_hostname,action,target_user_id,target_user_hostname)
        self.execute_query(query,params)

    def get_all_logs(self):
        query = "SELECT * FROM logs"
        return self.fetchall(query)

    def get_last_log(self):
        query = "SELECT * FROM logs ORDER BY id DESC LIMIT 1"
        return self.fetchone(query)



