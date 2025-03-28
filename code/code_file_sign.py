import datetime
import os.path
import sys
import glob

signatur = f"""#####
#
# Created by @MasterWoodie
# https://github.com/WoodieMaster
# {datetime.date.today()}
#
#####
"""

signatur_check = "#####"

def sign(file: str):
    with open(file, 'r') as f:
        content = f.read()

    if content.lstrip().startswith(signatur_check):
        return

    with open(file, 'w') as f:
        f.write(signatur)
        f.write(content)

def main():
    if len(sys.argv) < 2:
        print(f"Missing argument: path\nUsage: code_sign <path> [<pattern>]")
        exit(1)
    path = sys.argv[1]

    if os.path.isfile(path):
        sign(path)
    elif os.path.isdir(path):
        if len(sys.argv) != 3:
            print(f"Missing argument: pattern (Required when path is a folder)\nUsage: code_sign <path> [<pattern>]")
            return
        pattern = sys.argv[2]

        for p in glob.glob(pattern, root_dir=path, recursive=True):
            if os.path.isfile(os.path.join(path, p)):
                sign(p)

if __name__ == '__main__':
    main()