import argparse

from cfut.commands import get_region, set_profile_from_config_or_parser

from .conftest import requires_aws


@requires_aws
def test_get_region(init):
    set_profile_from_config_or_parser(argparse.Namespace(profile=None))
    region = get_region()
    assert region == "eu-west-1"
