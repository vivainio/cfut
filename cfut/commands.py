import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Dict, List, Tuple, Any, Union

from cfut.models import IniFile, get_env, CfnTemplate, StatusRules

CONFIG_FILE = "cfut.json"

ERROR_NO_UPDATES_TO_PERFORM = "No updates are to be performed"


@dataclass
class OutputFormat:
    style: str  # "yaml" | "table"
    query: Optional[str]

    def as_arg(self):
        parts = ["--output", str(self.style)]
        if self.query:
            parts.extend(["--query", self.query])
        return " ".join(parts)


DEFAULT_OUTPUT_FORMAT = OutputFormat("json", None)


def get_profile_arg():
    if current_profile:
        return ["--profile", current_profile]
    return []


def run_cli_parsed_output(cmd: str) -> Tuple[Optional[str], Any]:
    """ run command with right profile and json output, parse it

    return (err, object)
    """
    command = ["aws"] + get_profile_arg() + ["--output", "json", cmd]
    full_cmd = " ".join(command)
    p = subprocess.run(full_cmd, capture_output=True, text=True, shell=True)
    if p.returncode != 0:
        return p.stderr, None
    out = p.stdout

    parsed = json.loads(out)
    return None, parsed


def get_run_command(family: str, subcommand: str, output: Optional[OutputFormat] = None) -> str:
    out = (output if output else DEFAULT_OUTPUT_FORMAT).as_arg()
    profile_arg = " ".join(get_profile_arg())
    cmd = f"aws {family} {out} {profile_arg} {subcommand}"
    return cmd


def run_cli(family: str, subcommand: str, output: Optional[OutputFormat] = None):
    cmd = get_run_command(family, subcommand, output)
    print("> " + cmd)
    subprocess.check_call(cmd, shell=True)


def run_cli_safe(family: str, subcommand: str, allowed_errors=[], output: Optional[OutputFormat] = None):
    cmd = get_run_command(family, subcommand, output)
    print("> " + cmd)

    ret = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(ret.stdout)
    if ret.returncode == 0:
        return ""
    for err in allowed_errors:
        if err in ret.stderr:
            print("Allowed error:", err)
            return err

    raise Exception(f"Command '{cmd}' failed: {ret.stderr}")


def get_stack_status(stack_name: str) -> Union["NOT_EXIST"]:
    err, out = run_cli_parsed_output(f"cloudformation describe-stacks --stack-name={stack_name}")
    if err:
        if "does not exist" in err:
            return "NOT_EXIST"
        raise Exception(f"Unknown error: {err}")
    return out["Stacks"][0]["StackStatus"]


def poll_until_status(stack_name: str, statusrules: StatusRules):
    while 1:
        status = get_stack_status(stack_name)
        if status == statusrules.in_progress:
            print("Progress:", status)
            time.sleep(2)
            continue
        if status != statusrules.success:
            raise Exception(f"Polling expected status {statusrules.success}, got {status}")
        print("Complete:", status)
        break


def run_cf(cmd: str, output: Optional[OutputFormat] = None):
    return run_cli_safe("cloudformation", cmd, [ERROR_NO_UPDATES_TO_PERFORM], output)


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
    params = " ".join(f"ParameterKey={k},ParameterValue={v}" for (k, v) in d.items())
    return f"--parameters {params}"


def stack_args(stack_name: str, template_file: Optional[str]):
    parts = [f"--stack-name {stack_name}"]
    if template_file:
        parts.append(f"--template-body file://{template_file}")
    return " ".join(parts)


def base_command(command_name: str, stack_name: str, template_file: Optional[str]):
    return f"{command_name} " + stack_args(stack_name, template_file)


def run_command(stack_id: str, command_name: str, output: OutputFormat) -> str:
    """ returns stack name """
    inifile = get_config()
    # if no alias exists, just pass it through
    stack = inifile.templates.get(stack_id)
    stack_name = stack.name if stack else stack_id
    cmd = base_command(command_name, stack_name, None)
    run_cf(cmd, output)
    return stack_name


def run_stack(command_name: str, stack: CfnTemplate):
    cmd = base_command(command_name, stack.name, stack.path)
    if stack.capabilities:
        caps = " --capabilities " + " ".join(c.name for c in stack.capabilities)
        cmd += caps
    if stack.parameters:
        params = make_param_arg(stack.parameters)
        cmd += " " + params

    return run_cf(cmd)


def lookup_stack(stack_id: str) -> CfnTemplate:
    inifile = get_config()
    stack = inifile.templates[stack_id]
    return stack


def dispatch_stack_command(args: argparse.Namespace) -> CfnTemplate:
    """ looks up the stack from args, patches in params etc

    You should still call the right function with the stack
    """
    idd = args.id if args.id else "default"
    stack = lookup_stack(idd)
    params = [param.split("=", 1) for param in args.params or []]
    as_dict = {
        k: v for (k, v) in params
    }
    if not stack.parameters:
        stack.parameters = {}
    stack.parameters.update(as_dict)
    if args.name:
        stack.name = args.name
    return stack


def add_stack_command_args_to_parser(sp: argparse.ArgumentParser):
    sp.add_argument("id", help="Alias of stack", nargs="?")
    sp.add_argument("--params", nargs="+", help="Params as key1=value1 key2=value2")
    sp.add_argument("--name", type=str, help="Override name of the stack")


STATUS_RULES_CREATE = StatusRules("CREATE_IN_PROGRESS", "CREATE_COMPLETE")
STATUS_RULES_UPDATE = StatusRules("UPDATE_IN_PROGRESS", "UPDATE_COMPLETE")
STATUS_RULES_DELETE = StatusRules("DELETE_IN_PROGRESS", "NOT_EXIST")


def dump_stack_events(stack_name: str):
    run_command(stack_name, "describe-stack-events",
                OutputFormat(
                    "table",
                    "StackEvents[*].[LogicalResourceId,ResourceType,ResourceStatus,Timestamp,ResourceStatusReason]"))


class CfutError(Exception):
    ...


def raise_stack_failure(stack_name: str, error: str):
    print(f"ERROR: Stack '{stack_name}' failed: {error}")
    dump_stack_events(stack_name)
    raise CfutError(error)


def deploy_stack(stack: CfnTemplate):
    print("deploying", stack)
    status = get_stack_status(stack.name)
    if status == "NOT_EXIST":
        run_stack("create-stack", stack)
        poll_until_status(stack.name, STATUS_RULES_CREATE)
        return

    can_update = ["CREATE_UPDATE", "UPDATE_ROLLBACK_COMPLETE", "UPDATE_COMPLETE"]
    if status in can_update:
        update_ret = run_stack("update-stack", stack)
        if update_ret == ERROR_NO_UPDATES_TO_PERFORM:
            print("No updates to perform")
            return

        poll_until_status(stack.name, STATUS_RULES_UPDATE)
        return
    if "ROLLBACK" in status:
        raise_stack_failure(stack.name, f"Stack {stack.name} in rollback state, you have to repair (delete?) it manually!")

    print(status)


def run_command_with_file(stack_id: str, command_name: str):
    stack = lookup_stack(stack_id)
    run_stack(command_name, stack)


def ccap(cmd: List[str]):
    print(">", " ".join(cmd))
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return out


@lru_cache()
def get_account():
    get_config()
    out = ccap(
        ["aws", "sts", "get-caller-identity"]
        + get_profile_arg()
        + ["--query", "Account", "--output", "text"],
    ).strip()
    return out


@lru_cache()
def get_region() -> str:
    env = get_env()
    # aws_default_region overrides "profile"
    if env.aws_default_region:
        return env.aws_default_region

    ret = ccap(["aws", "configure"] + get_profile_arg() + ["get", "region"]).strip()
    return ret
