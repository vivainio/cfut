import json
import os
import pprint
import subprocess
import sys
from typing import Optional

from cftool.models import IniFile
import yaml

CONFIG_FILE = "cftool.json"


def run_cf(cmd: str):
    profile_arg = "--profile " + current_profile

    cmd = f"aws cloudformation --output yaml {profile_arg} {cmd}"
    print("> " + cmd)

    subprocess.call(cmd)


current_profile = "default"


def set_profile(profile: str):
    global current_profile
    current_profile = profile


def set_profile_from_config():
    config = get_config()
    set_profile(config.profile)


current_config: IniFile = None


def get_config():
    global current_config
    if current_config:
        return current_config
    if not os.path.isfile(CONFIG_FILE):
        print(f"Config file '{CONFIG_FILE}' not found, please run 'cftool init' to create it")
        sys.exit(1)

    current_config = IniFile.parse_raw(open(CONFIG_FILE).read())

    return current_config


def stack_args(stack_name: str, template_file: Optional[str]):
    parts = [f"--stack-name {stack_name}"]
    if template_file:
        parts.append(f"--template-body file://{template_file}")
    return " ".join(parts)


def base_command(command_name: str, stack_name: str, template_file: Optional[str]):
    return f"{command_name} " + stack_args(stack_name, template_file)


def run_command(stack_id: str, command_name: str):
    inifile = get_config()
    stack = inifile.templates[stack_id]
    cmd = base_command(command_name, stack.name, None)
    run_cf(cmd)


def run_command_with_file(stack_id: str, command_name: str):
    inifile = get_config()
    stack = inifile.templates[stack_id]
    cmd = base_command(command_name, stack.name, stack.path)
    if stack.capabilities:
        caps = " --capabilities "+ " ".join(c.name for c in stack.capabilities)
        cmd += caps
    run_cf(cmd)
