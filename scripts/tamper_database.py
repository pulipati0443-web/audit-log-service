import sqlite3


DATABASE_PATH = "data/audit.db"


connection = sqlite3.connect(DATABASE_PATH)

cursor = connection.execute(
    """
    UPDATE audit_events
    SET payload = ?
    WHERE record_id = 1
    """,
    ('{"action":"TAMPERED"}',),
)

connection.commit()
connection.close()

if cursor.rowcount != 1:
    raise RuntimeError(
        f"Expected to modify record 1, but modified {cursor.rowcount} records."
    )

print("Database record 1 modified directly.")
