import subprocess


def run(cmd: list[str]) -> int:
    return subprocess.call(cmd)
