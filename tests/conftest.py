import os

import pytest

from cfut.cli import change_to_root_dir
from cfut.commands import get_config


@pytest.fixture()
def init():
    orig_dir = os.getcwd()
    change_to_root_dir()
    get_config()
    yield
    os.chdir(orig_dir)

