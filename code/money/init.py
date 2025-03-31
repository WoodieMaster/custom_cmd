import os
import sqlite3
import sys

import utils

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


def init():
    print(utils.cyan("Initializing..."))
    print(utils.green("Creating database..."))
    conn = sqlite3.connect(os.path.dirname(sys.argv[0]) + "/money.db")
    cur = conn.cursor()

    for cmd in init_cmds:
        cur.execute(cmd)

    backup_path = utils.rel_path("bkp")
    if not os.path.exists(backup_path):
        print(utils.green("Creating backup folder..."))
        os.mkdir(utils.rel_path("bkp"))
    elif not os.path.isdir(backup_path):
        print(utils.red(f"Error: {backup_path} cannot be created as a folder. (It already exists as something else)"))
    else:
        print(utils.yellow(f"Skipping backup folder creation as it already exists"))

    print(utils.green("Initialization complete!"))


if __name__ == "__main__":
    init()
