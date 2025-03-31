import os
import sys

curr_path = os.path.dirname(sys.argv[0])


def rel_path(*parts: str) -> str:
    """Create a path relative to the executing python script"""
    return os.path.join(curr_path, *parts)


def red(text: str) -> str:
    """Color text in red for terminal"""
    return "\033[31m" + text + "\033[0m"


def green(text: str) -> str:
    """Color text in green for terminal"""
    return "\033[32m" + text + "\033[0m"


def cyan(text: str) -> str:
    """Color text in cyan for terminal"""
    return "\033[36m" + text + "\033[0m"


def yellow(text: str) -> str:
    """Color text in yellow for terminal"""
    return "\033[33m" + text + "\033[0m"
