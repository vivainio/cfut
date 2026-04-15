from cfut.cli import do_ecr_push

from .conftest import requires_aws


@requires_aws
def test_do_ecr_publish(init):
    do_ecr_push(None)
