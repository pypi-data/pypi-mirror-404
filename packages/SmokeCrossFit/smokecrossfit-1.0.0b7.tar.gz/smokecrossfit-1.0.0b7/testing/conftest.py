import logging
import sys
from pathlib import Path

import pytest

@pytest.fixture(scope="session")
def tests_dir_path() -> Path:
    return Path(__file__).resolve().parent

@pytest.fixture(scope="session")
def logger() -> logging.Logger:
    lg = logging.getLogger("testing")
    if not lg.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s"))
        lg.addHandler(handler)
    lg.setLevel(logging.DEBUG)
    return lg
