from cfut.commands import get_account

from .conftest import requires_aws


@requires_aws
def test_get_account():
    acc = get_account()
    assert acc
