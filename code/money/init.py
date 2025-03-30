import os
import sqlite3
import sys

init_cmds = [
    """
    CREATE TABLE IF NOT EXISTS person (
        name Text PRIMARY KEY
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS money (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name Text REFERENCES person(name),
        amount Number,
        created_at TIMESTAMP,
        reason Text
    )
    """
]


def main():
    conn = sqlite3.connect(os.path.dirname(sys.argv[0]) + "/money.db")
    cur = conn.cursor()

    for cmd in init_cmds:
        cur.execute(cmd)


if __name__ == "__main__":
    main()
