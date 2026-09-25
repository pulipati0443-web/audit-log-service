import sqlite3


connection = sqlite3.connect("data/audit.db")

connection.execute(
    """
    UPDATE audit_events
    SET payload = ?
    WHERE record_id = 1
    """,
    ('{"action":"TAMPERED"}',),
)

connection.commit()
connection.close()

print("Database record 1 modified directly.")