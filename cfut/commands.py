import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Dict, List

from cfut.models import IniFile, get_env

CONFIG_FILE = "cfut.json"


@dataclass
class OutputFormat:
    style: str  # "yaml" | "table"
    query: Optional[str]

    def as_arg(self):
        parts = ["--output", str(self.style)]
        if self.query:
            parts.extend(["--query", self.query])
        return " ".join(parts)


DEFAULT_OUTPUT_FORMAT = OutputFormat("yaml", None)


def get_profile_arg():
    if current_profile:
        return ["--profile", current_profile]
    return []


def run_cli_parsed_output(cmd: str):
    """ run command with right profile and json output, parse it """
    command = ["aws"] + get_profile_arg() + ["--output", "json", cmd]
    full_cmd = " ".join(command)
    print("> " + full_cmd)
    out = subprocess.run(full_cmd, capture_output=True, text=True).stdout
    parsed = json.loads(out)
    return parsed


def run_cli(family: str, subcommand: str, output: Optional[OutputFormat] = None):
    out = (output if output else DEFAULT_OUTPUT_FORMAT).as_arg()
    profile_arg = " ".join(get_profile_arg())
    cmd = f"aws {family} {out} {profile_arg} {subcommand}"
    print("> " + cmd)
    subprocess.call(cmd, shell=True)


def run_cf(cmd: str, output: Optional[OutputFormat] = None):
    run_cli("cloudformation", cmd, output)


current_profile = "default"


def set_profile(profile: str):
    global current_profile
    current_profile = profile


def set_profile_from_config_or_parser(parser: argparse.Namespace):
    from_cmd = parser.profile
    if from_cmd:
        set_profile(from_cmd)
        return

    config = get_config()
    set_profile(config.profile)


current_config: Optional[IniFile] = None


def get_config():
    global current_config
    if current_config:
        return current_config
    if not os.path.isfile(CONFIG_FILE):
        print(
            f"Config file '{CONFIG_FILE}' not found, please run 'cfut init' to create it"
        )
        sys.exit(1)

    current_config = IniFile.parse_raw(open(CONFIG_FILE).read())

    return current_config


def make_param_arg(d: Dict[str, str]):
    params = " ".join(
        f"ParameterKey={k},ParameterValue={v}" for (k, v) in d.items()
    )
    return f'--parameters {params}'


def stack_args(stack_name: str, template_file: Optional[str]):
    parts = [f"--stack-name {stack_name}"]
    if template_file:
        parts.append(f"--template-body file://{template_file}")
    return " ".join(parts)


def base_command(command_name: str, stack_name: str, template_file: Optional[str]):
    return f"{command_name} " + stack_args(stack_name, template_file)


def run_command(stack_id: str, command_name: str, output: OutputFormat):
    inifile = get_config()
    # if no alias exists, just pass it through
    stack = inifile.templates.get(stack_id)
    stack_name = stack.name if stack else stack_id
    cmd = base_command(command_name, stack_name, None)
    run_cf(cmd, output)


def run_command_with_file(stack_id: str, command_name: str, with_params: bool):
    inifile = get_config()
    stack = inifile.templates[stack_id]
    cmd = base_command(command_name, stack.name, stack.path)
    if stack.capabilities:
        caps = " --capabilities " + " ".join(c.name for c in stack.capabilities)
        cmd += caps
    if with_params and stack.parameters:
        params = make_param_arg(stack.parameters)
        cmd += " " + params

    run_cf(cmd)


def ccap(cmd: List[str]):
    print(">", " ".join(cmd))
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return out


@lru_cache()
def get_account():
    get_config()
    out = ccap(
        ["aws", "sts", "get-caller-identity"] + get_profile_arg() + ["--query", "Account", "--output", "text"],
    ).strip()
    return out


@lru_cache()
def get_region() -> object:
    env = get_env()
    # aws_default_region overrides "profile"
    if env.aws_default_region:
        return env.aws_default_region

    ret = ccap(["aws", "configure"] + get_profile_arg() + ["get", "region"]).strip()
    return ret
