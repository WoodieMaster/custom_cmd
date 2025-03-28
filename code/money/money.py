import datetime
import os
import sqlite3
import sys
from shlex import split
from typing import Self


def adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 date."""
    return val.isoformat()


def adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.isoformat()


def adapt_datetime_epoch(val):
    """Adapt datetime.datetime to Unix timestamp."""
    return int(val.timestamp())


sqlite3.register_adapter(datetime.date, adapt_date_iso)
sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)
sqlite3.register_adapter(datetime.datetime, adapt_datetime_epoch)


def convert_date(val):
    """Convert ISO 8601 date to datetime.date object."""
    return datetime.date.fromisoformat(val.decode())


def convert_datetime(val):
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return datetime.datetime.fromisoformat(val.decode())


def convert_timestamp(val):
    """Convert Unix epoch timestamp to datetime.datetime object."""
    return datetime.datetime.fromtimestamp(int(val))


sqlite3.register_converter("date", convert_date)
sqlite3.register_converter("datetime", convert_datetime)
sqlite3.register_converter("timestamp", convert_timestamp)

init_cmds = [
    """
    CREATE TABLE IF NOT EXISTS person (
        name Text PRIMARY KEY
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS money (
        name Text REFERENCES person(name),
        amount Number,
        created_at TIMESTAMP,
        reason Text
    )
    """
]

conn = sqlite3.connect(os.path.dirname(sys.argv[0]) + "/money.db")
cur = conn.cursor()


def init():
    for cmd in init_cmds:
        cur.execute(cmd)


def name_exists(name: str) -> bool:
    cur.execute("SELECT Count(*) FROM person WHERE name = ?", (name,))
    return cur.fetchone()[0] > 0


def create_person(name: str):
    if name_exists(name):
        raise Exception(f"Name '{name}' already exists")
    cur.execute("INSERT INTO person VALUES (?)", (name,))
    conn.commit()


def get_people() -> list[str]:
    cur.execute("SELECT name FROM person")
    return [name[0] for name in cur.fetchall()]


def remove_person(name: str) -> bool:
    if not name_exists(name):
        raise Exception(f"Name: {name} does not exist")
    s = cur.execute("DELETE FROM person WHERE name = ?", (name,))
    success = s.rowcount > 0
    if success:
        conn.commit()
    return success


def create_money_entry(name: str, amount: float, reason: str):
    if not name_exists(name):
        raise Exception(f"Name: {name} does not exist")

    cur.execute("INSERT INTO money (name, amount, created_at, reason) VALUES (?, ?, ?, ?)",
                (name, amount, datetime.datetime.now(), reason))
    conn.commit()


def get_current_balance(name: str) -> float:
    res = cur.execute("SELECT SUM(amount) FROM money WHERE name = ?", (name,))
    return res.fetchone()[0]


def red(text: str) -> str:
    return "\033[31m" + text + "\033[0m"


def green(text: str) -> str:
    return "\033[32m" + text + "\033[0m"


def get_balance_list(name: str) -> list[tuple[int, str]]:
    res = cur.execute("SELECT amount, reason FROM money WHERE name = ?", (name,))
    return res.fetchall()


def get_overview() -> list[tuple[str, int]]:
    res = cur.execute("SELECT name, SUM(amount) FROM money GROUP BY name")
    return res.fetchall()


class Cmd:
    arg_list: dict[str, int] = {
        "all": 0,
        "color": 0
    }

    short_args: dict[str, str] = {
        "a": "all",
        "c": "color"
    }

    def __init__(self, args: list[str], base: Self = None):
        self.__input = args.__iter__()
        self.__flags: set[str] = base.__flags.copy() if base is not None else set()
        self.__vars: dict[str, list[str]] = base.__vars.copy() if base is not None else dict()
        self.__args: list[str] = list()

    def __print_current_money(self, name: str, amount: float):
        print(f"{name}: {self.__format_balance(amount)}")

    def __format_balance(self, value: float) -> str:
        fmt = f"{value:.2f}"
        if "color" in self.__flags:
            if value < 0:
                return red(fmt)
            return green(fmt)
        else:
            return fmt

    def __print_overview(self, overview: list[tuple[str, int]]):
        for [name, amount] in overview:
            print(f"{name}: {self.__format_balance(amount)}")

    def __print_history(self, name: str, history: list[tuple[int, str]]):
        print(name + ":")
        total = 0
        for [amount, reason] in history:
            total += amount
            print(f"{self.__format_balance(amount)} ({reason})")
        print("----------")
        print(f"{self.__format_balance(total)}")

    def __parse_arg(self, arg: str):
        val = Cmd.arg_list.get(arg)

        if val is None:
            raise Exception(f"Unknown argument: --{arg}")

        if val == 0:
            if arg in self.__flags:
                raise Exception(f"Duplicate argument: --{arg}")
            self.__flags.add(arg)
        else:
            data = []
            for i in range(val):
                n = next(self.__input, None)
                if n is None:
                    raise Exception(f"Missing arguments for --{arg}")
                data.append(n)

            if arg in self.__vars:
                raise Exception(f"Duplicate argument: --{arg}")

            self.__vars[arg] = data

    def __parse(self):
        for n in self.__input:
            if n is None:
                return

            if n.startswith("--"):
                self.__parse_arg(n[2:])
            elif n.startswith("-"):
                for c in n[1:]:
                    name = Cmd.short_args.get(c)

                    if name is None:
                        raise Exception(f"Unknown argument: -{c}")

                    self.__parse_arg(name)
            else:
                self.__args.append(n)

    def __exec(self):
        self.__parse()
        if len(self.__args) == 0:
            print("Use --help to display info")
            return

        [cmd, *args] = self.__args

        match cmd:
            case "run":
                self.run()
            case "list":
                print("\n".join(get_people()))
            case "rm":
                if len(args) != 1:
                    raise Exception(f"Invalid arguments ({', '.join(args)}), requires: <name>")
                remove_person(args[0])
                print(f"Removed person {args[0]} successfully")
            case "add":
                if len(args) != 3:
                    raise Exception(f"Invalid arguments ({", ".join(args)}), requires: <name> <amount> <reason>")

                [name, amount, reason] = self.__args[1:]
                create_money_entry(name, float(amount), reason)
            case "add-person" | "add-p":
                if len(args) != 1:
                    raise Exception(f"Invalid arguments ({', '.join(args)}), requires: <name>")
                create_person(args[0])
                print(f"Added person {args[0]} successfully")
            case "exit":
                exit(0)
            case "get":
                if len(args) == 1:
                    name = self.__args[1]
                    if "all" in self.__flags:
                        self.__print_history(name, get_balance_list(name))
                    else:
                        self.__print_current_money(name, get_current_balance(name))
                elif len(args) == 0:
                    self.__print_overview(get_overview())
            case _:
                raise Exception(f"Unknown command: {cmd}")

    def run(self):
        while True:
            args = split(input(">>> "))
            cmd = Cmd(args, self)
            cmd.exec()

    def __print_error(self, e: BaseException):
        fmt = f"Error: {e}"

        if "color" in self.__flags:
            fmt = red(fmt)

        print(fmt)

    def exec(self):
        try:
            self.__exec()
        except Exception as e:
            self.__print_error(e)


def main():
    init()
    cmd = Cmd(sys.argv[1:])
    cmd.exec()
    conn.close()


if __name__ == "__main__":
    main()
