import os
import sys
from typing import Optional

import argp

from pathlib import Path

from cfut import commands
from cfut.commands import CONFIG_FILE, get_config, run_cf, OutputFormat, DEFAULT_OUTPUT_FORMAT, run_cli, get_account, \
    get_region
from cfut.models import IniFile, CfnTemplate


def do_init(args):
    """ initialize cfut.json"""

    template_files = Path(".").glob("**/*.y*ml")
    templates = {
        t.stem: CfnTemplate(name=t.stem, path=str(t).replace("\\", "/"))
        for t in template_files
    }

    if len(templates) == 1:
        templates = {"default": list(templates.values())[0]}

    ini = IniFile(profile="default", templates=templates)
    cont = ini.json(indent=2)
    open(CONFIG_FILE, "w").write(cont)


def lint(args):
    config = get_config()
    for t in config.templates.values():
        os.system("cfn-lint " + t.path)


def add_any_alias(alias_name: str, family: str, subcommand: str, output: Optional[OutputFormat] = None):
    out = output if output else DEFAULT_OUTPUT_FORMAT

    def alias_handler(args):
        cmd = subcommand
        if args.other_args:
            cmd += " " + " ".join(args.other_args)
        run_cli(family, cmd, out)

    sp = argp.sub(alias_name, alias_handler, help="Alias: " + to)
    sp.add_argument("other_args", nargs="*")


def add_cloudformation_alias(fr: str, to: str, output: Optional[OutputFormat] = None):
    out = output if output else DEFAULT_OUTPUT_FORMAT

    def alias_handler(args):
        cmd = to
        if args.other_args:
            cmd += " " + " ".join(args.other_args)
        run_cf(cmd, out)

    sp = argp.sub(fr, alias_handler, help="Alias: " + to)
    sp.add_argument("other_args", nargs="*")


def add_id_cmd(fr: str, to: str, query: Optional[str] = None):
    output = None
    if query:
        output = OutputFormat("table", query)

    def id_cmd_handler(args):
        idd = args.id if args.id else "default"

        commands.run_command(idd, to, output)

    sp = argp.sub(fr, id_cmd_handler, help="Call: " + to)
    sp.add_argument("id", help="Nickname of stack", nargs="?")


def add_template_cmd(fr: str, to: str, with_params=False):
    def template_cmd_handler(args):
        idd = args.id if args.id else "default"
        commands.run_command_with_file(idd, to, with_params)

    sp = argp.sub(fr, template_cmd_handler, help=f"Call with template: {to}")
    sp.add_argument("id", help="Alias of stack", nargs="?")


def find_in_parents(fname: str) -> Optional[Path]:
    cur = Path(".").absolute()
    while 1:
        trie = cur / fname
        if trie.exists():
            return trie
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def change_to_root_dir():
    found = find_in_parents(commands.CONFIG_FILE)
    if found:
        os.chdir(found.parent)
        return
    resp = input(
        f"Config file {commands.CONFIG_FILE} not found, create it in {os.getcwd()} [y/n]? "
    )
    if resp.startswith("y"):
        do_init(None)


def print_stacks():
    config = get_config()
    for k, v in config.templates.items():
        print(f"{k}: {v.path} => {v.name}")


def c(s):
    print(">", s)
    os.system(s)


def do_ecr_push(args):
    """ push docker image to ecr"""
    config = get_config()
    acc = get_account()
    repo_name = config.ecr.repo
    tag = config.ecr.tag
    region = get_region()
    src_dir = config.ecr.src
    ecr_address = f"{acc}.dkr.ecr.{region}.amazonaws.com"
    remote_tag = f"{ecr_address}/{repo_name}:{tag}"

    c(f"docker build -t {remote_tag} {src_dir}")

    c(
        f'aws ecr --profile {config.profile} get-login-password | docker login  --password-stdin --username AWS  "{ecr_address}"')

    c(f"docker push {remote_tag}")


def main():
    os.environ["AWS_PAGER"] = "less"
    change_to_root_dir()
    if len(sys.argv) == 1:
        print("Run cfut -h to get help.")
        print("Workspace:", os.getcwd())
        print_stacks()
        return
    argp.init()
    argp.sub("init", do_init, help="Initialize working directory")
    argp.sub("lint", lint, help="Lint templates")

    add_template_cmd("update", "update-stack", True)
    add_template_cmd("create", "create-stack", True)
    add_id_cmd("describe", "describe-stacks")
    add_id_cmd("events", "describe-stack-events",
               'StackEvents[*].[LogicalResourceId,ResourceType,ResourceStatus,Timestamp,ResourceStatusReason]')
    add_id_cmd("res", "describe-stack-resources",
               'StackResources[*].[LogicalResourceId,ResourceType,PhysicalResourceId]')
    add_id_cmd("delete", "delete-stack")

    add_cloudformation_alias("ls", "describe-stacks",
                             OutputFormat("table", "Stacks[*].[StackName,StackStatus,CreationTime]"))

    argp.sub("ecrpush", do_ecr_push, help="Build and push to ECR repository")

    commands.set_profile_from_config()
    argp.parse()


if __name__ == "__main__":
    main()
