from cfut.commands import get_region, set_profile_from_config_or_parser, get_config


def test_get_region(init):
    set_profile_from_config_or_parser()
    region = get_region()
    assert region == "eu-west-1"
