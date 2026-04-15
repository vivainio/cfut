"""argparse integration for dataclass models

Usage: have a model class:

    @dataclass
    class MyModel:
        foo: str
        bar: str = field(metadata={"description": "what bar is for"})

    parser = ArgumentParser()
    add_overrider_args(parser, MyModel)
    ...

    parsed = parser.parse_args()
    model = read_model_from_config_somehow()
    assign_overrider_args(model, parsed)

    # ... use model
"""

import argparse
import dataclasses
import operator
from typing import Any, List


def add_overrider_args(parser: argparse.ArgumentParser, model_class) -> None:
    for f in dataclasses.fields(model_class):
        help_text = f.metadata.get("description")
        parser.add_argument("--" + f.name, help=help_text)


def assign_overrider_args(obj, ns: argparse.Namespace) -> None:
    for f in dataclasses.fields(obj):
        from_arg = getattr(ns, f.name, None)
        if from_arg:
            setattr(obj, f.name, from_arg)


def apply_config_overrides(config_obj: Any, overrides: List[str]) -> None:
    """Helper to apply set of config overrides from cli.

    Example use - this will allow you to do args like
        -d foo=12 -d my.deep.path=hello


    parser.add_argument("-d", "--define", type=str, action="append", help="Override configuration")
    parsed = parser.parse_args(sys.argv[1:])
    config = get_app_config()
    if parsed.define:
        apply_config_overrides(config, parsed.define)
    """
    for ov in overrides:
        name, value = ov.split("=", 1)
        assign_by_path(config_obj, name, value)


def assign_by_path(target_obj, path: str, value: Any) -> None:
    """assign 'deep' attribute within config model by path foo.bar.name"""
    parts = path.rsplit(".", 1)
    if len(parts) == 1:
        assign_to, name = target_obj, parts[0]
    else:
        assign_to, name = operator.attrgetter(parts[0])(target_obj), parts[1]
    setattr(assign_to, name, value)
