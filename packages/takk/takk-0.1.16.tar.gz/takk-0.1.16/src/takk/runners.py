import subprocess 
from typing import Callable


BashRunner = Callable[[list[str]], int]


def local_run(commands: list[str]) -> int:
    return subprocess.check_call(commands)


default_runner: BashRunner = local_run
