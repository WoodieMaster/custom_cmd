import datetime
import os
import shutil
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
    """Convert ISO 8601
     datetime to datetime.datetime object."""
    return datetime.datetime.fromisoformat(val.decode())


def convert_timestamp(val):
    """Convert Unix epoch timestamp to datetime.datetime object."""
    return datetime.datetime.fromtimestamp(int(val))


sqlite3.register_converter("date", convert_date)
sqlite3.register_converter("datetime", convert_datetime)
sqlite3.register_converter("timestamp", convert_timestamp)

curr_path = os.path.dirname(sys.argv[0])


def rel_path(*parts: str) -> str:
    return os.path.join(curr_path, *parts)


def connect():
    _conn = sqlite3.connect(rel_path("money.db"))
    _cur = _conn.cursor()
    return _conn, _cur


conn, cur = connect()


def name_exists(name: str) -> bool:
    cur.execute("SELECT Count(*) FROM person WHERE name = ?", (name,))
    return cur.fetchone()[0] > 0


def create_person(name: str):
    if name_exists(name):
        raise Exception(f"Name '{name}' already exists")
    cur.execute("INSERT INTO person VALUES (?)", (name,))
    conn.commit()


def remove_person(name: str):
    if not name_exists(name):
        raise Exception(f"Name: {name} does not exist")

    cur.execute("DELETE FROM money WHERE name = ?", (name,))
    s = cur.execute("DELETE FROM person WHERE name = ?", (name,))

    if s.rowcount > 0:
        return conn.commit()


def get_entry_by_index(name: str, index: int) -> tuple[int, float, int, str]:
    s = cur.execute(
        "SELECT id, amount, created_at, reason FROM money WHERE name = ? ORDER BY created_at DESC LIMIT 1 OFFSET ?",
        (name, index))

    return s.fetchone()


def remove_money_entry(entry_id: int):
    cur.execute("DELETE FROM money WHERE id = ?", (entry_id,))
    cur.connection.commit()


def count_entries(name: str) -> int:
    cur.execute("SELECT Count(*) FROM money WHERE name = ?", (name,))
    return cur.fetchone()[0]


def create_money_entry(name: str, amount: float, reason: str, created_at: datetime.datetime):
    if not name_exists(name):
        raise Exception(f"Name: {name} does not exist")

    cur.execute("INSERT INTO money (name, amount, created_at, reason) VALUES (?, ?, ?, ?)",
                (name, amount, created_at, reason))
    conn.commit()


def get_current_balance(name: str) -> float:
    res = cur.execute("SELECT SUM(amount) FROM money WHERE name = ?", (name,))
    return res.fetchone()[0]


def get_balance_list(name: str) -> list[tuple[int, int, str]]:
    res = cur.execute("SELECT amount, created_at, reason FROM money WHERE name = ? ORDER BY created_at", (name,))
    return res.fetchall()


def get_overview() -> list[tuple[str, int]]:
    res = cur.execute(
        "SELECT p.name, ifnull(SUM(amount), 0) FROM person p LEFT JOIN money m on p.name = m.name GROUP BY p.name ORDER BY p.name")
    return res.fetchall()


def red(text: str) -> str:
    return "\033[31m" + text + "\033[0m"


def green(text: str) -> str:
    return "\033[32m" + text + "\033[0m"


def cyan(text: str) -> str:
    return "\033[36m" + text + "\033[0m"


def yellow(text: str) -> str:
    return "\033[33m" + text + "\033[0m"


def format_balance(value: float) -> str:
    fmt = f"{abs(value):.2f}"
    if value < 0:
        return red(f"-{fmt:>7}")

    if value == 0:
        return yellow(f"={fmt:>7}")

    return green(f"+{fmt:>7}")


def format_single_balance(value: float) -> str:
    fmt = f"{abs(value):.2f}"
    if value < 0:
        return red(f"-{fmt}")

    if value == 0:
        return yellow(f"={fmt}")

    return green(f"+{fmt}")


def format_timestamp(date: int) -> str:
    fmt = datetime.datetime.fromtimestamp(date).strftime("%Y-%m-%d %H:%M")
    return cyan(fmt)


def format_entry(name: str, entry: tuple[int, float, int, str]) -> str:
    return f"{cyan(name)} {format_single_balance(entry[1])} {format_timestamp(entry[2])} ({entry[3]})"


def format_person(name: str, money: float, entry_count) -> str:
    return f"{cyan(name)} ({format_single_balance(money)}, {entry_count} {"entries" if entry_count != 1 else "entry"})"


def print_overview(overview: list[tuple[str, int]]):
    for [name, amount] in overview:
        print(f"{name:10} {format_balance(amount)}")


def print_history(name: str, history: list[tuple[int, int, str]]):
    if not name_exists(name):
        raise Exception(f"Name '{name}' does not exist")
    print(name + ":")
    total = 0
    for (amount, created_at, reason) in history:
        total += amount
        print(
            f"{format_balance(amount)} {format_timestamp(created_at)} ({reason})")
    print("----------")
    print(f"{format_balance(total)}")


def print_help():
    cmds = [
        ("help", "Show this help message"),
        ("list", "Get the balance of all the people"),
        ("get <name>", "Get all entries with description of the give person"),
        ("add <name> <amount> <description>", "Create a new entry for the given person"),
        ("(add-p | add-person) <name>", "Register a new person"),
        ("rm <name> <idx>",
         "Remove entry with the given idx of the given person.\nThe idx is based on the entries timestamp (last made entry = 0)"),
        ("(rm-p | rm-person) <name>", "Remove the given person and all their entries"),
        ("run", "Create a new session for running multiple commands much easier\n(args from this command will be)"),
        ("exit", "Exit the session entered by the run command"),
        ("backup", "Create a backup of the database")
    ]

    print("Command list:")
    print("money")

    for cmd in cmds:
        fmt_code = cmd[0].ljust(40, " ")
        print(f"{" " * 6}{cyan(fmt_code)} {cmd[1].replace("\n", "\n" + (" " * 50))}")


def backup():
    global conn, cur
    conn.close()
    shutil.copyfile(rel_path("money.db"), rel_path("bkp", f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')}.db"))
    conn, cur = connect()


def print_error(e: BaseException):
    fmt = f"Error: {e}"
    print(red(fmt))


class Cmd:
    arg_list: dict[str, int] = {
        "date": 1
    }

    short_args: dict[str, str] = {
        "d": "date"
    }

    def __init__(self, args: list[str], base: Self = None):
        self.__input = args.__iter__()
        self.__flags: set[str] = base.__flags.copy() if base is not None else set()
        self.__vars: dict[str, list[str]] = base.__vars.copy() if base is not None else dict()
        self.__args: list[str] = list()

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
            elif n.startswith("-") and len(n) > 1 and not n[1].isdigit():
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
            print("Use command 'help' to show more info")
            return

        args: list[str]
        [cmd, *args] = self.__args

        match cmd:
            case "help":
                print_help()
            case "run":
                self.run()
            case "list":
                print_overview(get_overview())
            case "rm":
                if len(args) != 2:
                    raise Exception(f"Invalid arguments ({', '.join(args)}), requires: <name> <idx>")
                name = args[0]
                idx = int(args[1])
                entry = get_entry_by_index(name, idx)

                count = count_entries(name)

                print(count, count >= idx, idx)
                if count == 0:
                    raise Exception(f"{name} has no entries to delete!")
                if idx >= count or idx < 0:
                    raise Exception(f"{idx} is not a valid index for {name}. (valid: 0 - {count - 1})")

                if input(f"{format_entry(name, entry)}\nDelete this entry? (y/N)").lower() == "y":
                    remove_money_entry(entry[0])
                    print(green("Deleted entry"))
                else:
                    print(red("Deletion cancelled"))
            case "rm-p" | "rm-person":
                if len(args) != 1:
                    raise Exception(f"Invalid arguments ({', '.join(args)}), requires: <name>")
                name = args[0]
                entry_count = count_entries(name)
                if not name_exists(name):
                    raise Exception(f"Name: {name} does not exist")

                money = get_current_balance(name) or 0
                print(format_person(name, money, entry_count))
                if input(f"Delete person? (y/N)").lower() == "y":
                    remove_person(name)
                    print(green(f"Removed person {name}"))
                else:
                    print(red("Deletion cancelled!"))
            case "backup":
                backup()
            case "add":
                if len(args) != 3:
                    raise Exception(f"Invalid arguments ({", ".join(args)}), requires: <name> <amount> <reason>")

                [name, amount, reason] = self.__args[1:]
                created_at: datetime.datetime

                date_var = self.__vars.get("date", None)

                if date_var is not None:
                    date_str = date_var[0]
                    p_date = datetime.datetime.today().date()
                    p_time = datetime.time.min

                    v_date: str
                    if "_" in date_str:
                        [v_date, v_time] = date_str.split("_", 1)

                        if v_time != "":
                            p_time = datetime.datetime.strptime(v_time, "%H:%M").time()
                    else:
                        v_date = date_str

                    if v_date != "":
                        p_date = datetime.datetime.strptime(v_date, "%Y-%m-%d").date()

                    created_at = datetime.datetime.combine(p_date, p_time)
                else:
                    created_at = datetime.datetime.now()

                create_money_entry(name, float(amount), reason, created_at)
            case "add-person" | "add-p":
                if len(args) != 1:
                    raise Exception(f"Invalid arguments ({', '.join(args)}), requires: <name>")
                create_person(args[0])
                print(f"Added person {args[0]} successfully")
            case "exit":
                conn.close()
                exit(0)
            case "get":
                if len(args) != 1:
                    raise Exception(f"Invalid arguments ({', '.join(args)}), requires: <name>")
                name = self.__args[1]
                print_history(name, get_balance_list(name))
            case _:
                raise Exception(f"Unknown command: {cmd}")

    def run(self):
        while True:
            args = split(input("> "))
            cmd = Cmd(args, self)
            cmd.exec()

    def exec(self):
        try:
            self.__exec()
        except Exception as e:
            print_error(e)


def main():
    cmd = Cmd(sys.argv[1:])
    cmd.exec()
    conn.close()


if __name__ == "__main__":
    main()
