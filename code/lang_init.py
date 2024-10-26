import os
import shutil
import sys
from collections.abc import Callable

CMD = "langinit"

def add_file(path: str, filename: str, content: str):
    with open(os.path.join(path, filename), 'w') as f:
        f.write(content)


def add_gitignore(path: str, name: str):
    shutil.copyfile(f'gitignore/{name}', os.path.join(path, '.gitignore'))

def run_cmd(path: str, cmd: str):
    os.system(f'cd {path} && {cmd}')

def python(path: str):
    add_file(path, 'requirements.txt', '')
    add_gitignore(path, 'python')
    run_cmd(path, "git init")
    run_cmd(path, "python -m venv .venv")


LANG_MAP: dict[str, Callable[str, None]] = {
    "python": python,
    "py": python,
}
def main():
    if len(sys.argv) < 2:
        print(f"Usage: {CMD} <lang>")
        return
    lang = sys.argv[1]
    path = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()



    if lang not in LANG_MAP:
        print(f"Unknown language: {lang}")
        return

    LANG_MAP[lang](path)

if __name__ == '__main__':
    main()