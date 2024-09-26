import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('data/budgeting.db')

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# SQL commands to create the income and expense tables
create_income_table = """
CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    date TEXT NOT NULL
);
"""

create_expense_table = """
CREATE TABLE IF NOT EXISTS expense (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    date TEXT NOT NULL
);
"""

# Execute the SQL commands
cursor.execute(create_income_table)
cursor.execute(create_expense_table)

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database initialized successfully.")
