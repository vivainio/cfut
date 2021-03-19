""" argparse integration for pydantic models

Usage: have a model class:

class MyModel(BaseModel):
    foo: str
    bar: str


parser = ArgumentParser()
add_overrider_args(parser, MyModel)
...

parsed = parser.parse_args()
model = read_model_from_config_somehow().copy()
assign_overrider_args(model, parsed)

# ... use model

"""

import argparse
import operator
import pprint
from typing import Any, List


def add_overrider_args(parser: argparse.ArgumentParser, model_class):
    fields = model_class.__fields__
    for name, fieldinfo in fields.items():
        try:
            help_text = fieldinfo.field_info.description
        except AttributeError:
            help_text = None
        parser.add_argument("--" + name, help=help_text)


def assign_overrider_args(obj, ns: argparse.Namespace):
    # obj is pydantic BaseModel
    for k in obj.__fields__.keys():
        from_arg = getattr(ns, k)
        if from_arg:
            setattr(obj, k, from_arg)


def apply_config_overrides(config_obj: Any, overrides: List[str]):
    """ Helper to apply set of config overrides from cli

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


def assign_by_path(target_obj, path: str, value: Any):
    """ assign 'deep' object within config model or whatever, by path foo.bar.name """
    parts = path.rsplit(".", 1)
    if len(parts) == 1:
        assign_to, name = target_obj, parts[0]
    else:
        assign_to, name = operator.attrgetter(parts[0])(target_obj), parts[1]
    setattr(assign_to, name, value)
