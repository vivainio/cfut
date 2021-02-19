from cfut.commands import get_account


def test_get_account():
    acc = get_account()
    assert acc
