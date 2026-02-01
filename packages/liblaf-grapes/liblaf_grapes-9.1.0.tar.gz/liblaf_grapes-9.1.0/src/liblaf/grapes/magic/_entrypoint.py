import sys
from pathlib import Path


def entrypoint() -> Path:
    return Path(sys.argv[0])
