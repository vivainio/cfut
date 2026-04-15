import os

import pytest

from cfut.cli import change_to_root_dir
from cfut.commands import get_config


# Tests that hit live AWS APIs are skipped by default. Set
# CFUT_RUN_AWS_TESTS=1 to opt in.
requires_aws = pytest.mark.skipif(
    not os.environ.get("CFUT_RUN_AWS_TESTS"),
    reason="requires AWS credentials and a configured cfut.json; "
    "set CFUT_RUN_AWS_TESTS=1 to run",
)


@pytest.fixture()
def init():
    orig_dir = os.getcwd()
    change_to_root_dir()
    get_config()
    yield
    os.chdir(orig_dir)
