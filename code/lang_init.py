import os
import pathlib
import shutil
import sys
from collections.abc import Callable

CMD = "langinit"


def add_file(path: str, filename: str, content: str):
    with open(os.path.join(path, filename), 'w') as f:
        f.write(content)


def add_gitignore(name: str):
    shutil.copyfile(
        os.path.join(
            pathlib.Path(
                os.path.realpath(__file__)
            ).parent.parent,
            "gitignore",
            name
        ),
        '.gitignore')


def python(path: str, _args: list[str]):
    add_file(path, 'requirements.txt', '')
    add_gitignore('python')
    os.system("git init")
    os.system("python -m venv .venv")
    os.system("pycharm .")


LANG_MAP: dict[str, Callable[[str, list[str]], None]] = {
    "python": python,
    "py": python,
}


def main():
    args = sys.argv[1:]

    try:
        pos = args.index("--")
        lang_args = args[pos + 1:]
        args = args[:pos]
    except ValueError:
        lang_args = []

    if len(sys.argv) < 2:
        print(f"Usage: {CMD} <lang>")
        return

    lang = args[1]
    path = args[2] if len(args) > 2 else os.getcwd()

    if lang not in LANG_MAP:
        print(f"Unknown language '{lang}'")

        lang_display = [f"\n{lang_option}" for lang_option in LANG_MAP.keys() if lang in lang_option]
        if len(lang_display) > 0:
            print(f"Similar languages: {"".join(lang_display)}")
        else:
            print("No similar languages found")
        return

    if path != os.getcwd():
        # save current directory
        curr_dir = os.getcwd()
        os.system(f"cd {path}")

        LANG_MAP[lang](path, lang_args)

        # return to original directory
        os.system(f"cd {curr_dir}")
    else:
        LANG_MAP[lang](path, lang_args)


if __name__ == '__main__':
    main()
