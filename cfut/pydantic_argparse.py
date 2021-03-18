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


def add_overrider_args(parser: argparse.ArgumentParser, model_class):
    fields = model_class.__fields__
    for name, fieldinfo in fields.items():
        try:
            help_text = fieldinfo.field_info.description
        except AttributeError:
            help_text = None
        parser.add_argument("--" + name, help = help_text)


def assign_overrider_args(obj, ns: argparse.Namespace):
    # obj is pydantic BaseModel
    for k in obj.__fields__.keys():
        from_arg = getattr(ns, k)
        if from_arg:
            setattr(obj, k, from_arg)
