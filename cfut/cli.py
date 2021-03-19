import itertools
import os
import sys
import argparse

from operator import itemgetter
from pathlib import Path
from typing import Optional, Tuple
import argp

from cfut import commands
from cfut.commands import (
    CONFIG_FILE,
    get_config,
    run_cf,
    OutputFormat,
    DEFAULT_OUTPUT_FORMAT,
    get_account,
    get_region,
    run_cli_parsed_output,
)
from cfut.models import IniFile, CfnTemplate, EcrConfig
from cfut.pydantic_argparse import add_overrider_args, assign_overrider_args, apply_config_overrides


def create_init_file(args):
    """ initialize cfut.json"""
    if os.path.isfile(CONFIG_FILE):
        print("Config already exist! Delete cfut.json if you want to run 'init' again")
        return

    def is_template(fname):
        return "AWSTemplateFormatVersion" in open(fname).read()

    template_files = [fname for fname in itertools.chain(
        Path(".").glob("**/*.y*ml"),
        Path(".").glob("**/*.json")) if is_template(fname)]

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


def add_template_cmd(fr: str, to: str):
    def template_cmd_handler(args):
        idd = args.id if args.id else "default"
        stack = commands.lookup_stack(idd)
        params = [param.split("=", 1) for param in args.params or []]
        as_dict = {
            k: v for (k, v) in params
        }
        if not stack.parameters:
            stack.parameters = {}
        stack.parameters.update(as_dict)
        if args.name:
            stack.name = args.name

        commands.run_stack(to, stack)

    sp = argp.sub(fr, template_cmd_handler, help=f"Call with template: {to}")
    sp.add_argument("id", help="Alias of stack", nargs="?")
    sp.add_argument("--params", nargs="+", help="Params as key1=value1 key2=value2")
    sp.add_argument("--name", type=str, help="Override name of the stack")


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
        create_init_file(None)


def print_stacks():
    config = get_config()
    for k, v in config.templates.items():
        print(f"{k}: {v.path} => {v.name}")


def c(s):
    print(">", s)
    ret = os.system(s)
    if ret:
        raise Exception("ERROR! Command failed: " + s)


def get_ecr_address(ecr: EcrConfig) -> Tuple[str, str]:
    """ address, region """
    region = ecr.region or get_region()
    acc = ecr.account or get_account()
    return f"{acc}.dkr.ecr.{region}.amazonaws.com", region


def get_ecr_config_for_command(parsed: argparse.Namespace):
    config = get_config()
    ecr = config.ecr.copy()
    assign_overrider_args(ecr, parsed)
    return ecr


def ecr_login(ecr: EcrConfig):
    ecr_address, region = get_ecr_address(ecr)
    profile_arg = " ".join(commands.get_profile_arg()).strip()
    c(
        f'aws ecr {profile_arg} get-login-password --region {region} | docker login --password-stdin --username AWS "{ecr_address}"'
    )


def do_ecr_push(args):
    """ push docker image to ecr"""
    ecr = get_ecr_config_for_command(args)
    ecr_login(ecr)

    repo_name = ecr.repo
    tag = ecr.tag
    src_dir = ecr.src
    ecr_address, _ = get_ecr_address(ecr)
    image_name = f"{ecr_address}/{repo_name}"
    rev = os.popen("git rev-parse HEAD").read().strip()[:8]

    rev_tag = f"{image_name}:{rev}" if rev else None
    config_tag = f"{image_name}:{tag}"
    latest_tag = f"{image_name}:latest"

    tags = [t for t in [rev_tag, config_tag, latest_tag] if t]
    tag_args = [f"-t " + tag for tag in tags]
    c(f"docker build " + " ".join(tag_args) + " " + src_dir)

    # agh, old docker client wants you to push every tag separately
    for t in tags:
        c(f"docker push -q {t}")


def do_ecr_ls(args):
    ecr = get_ecr_config_for_command(args)
    ecr_login(ecr)
    repo_name = ecr.repo
    parsed = run_cli_parsed_output(f"ecr describe-images --repository-name {repo_name}")
    lines = parsed["imageDetails"]
    lines.sort(key=itemgetter("imagePushedAt"))
    table = [
        [
            line["imagePushedAt"],
            "%d MB" % (int(line["imageSizeInBytes"]) / (1024 * 1024)),
            line["imageDigest"].split(":")[1],
            ",".join(line.get("imageTags", [])),
        ]
        for line in lines
    ]

    for line in table:
        print("\t".join(line))


def do_ecr_login(args):
    ecr = get_ecr_config_for_command(args)
    get_config()
    ecr_login(ecr)


def main():
    os.environ["AWS_PAGER"] = "less"
    change_to_root_dir()
    if len(sys.argv) == 1:
        print("Run cfut -h to get help.")
        print("Workspace:", os.getcwd())
        print_stacks()
        return
    parser = argparse.ArgumentParser()
    argp.init(parser)
    parser.add_argument("-p", "--profile", type=str, help="AWS profile to use")
    parser.add_argument("-d", "--define", type=str, action="append",
                        help="Override configuration, e.g. -d ecr.repo=my-repo")

    argp.sub("lint", lint, help="Lint templates")

    add_template_cmd("update", "update-stack")
    add_template_cmd("create", "create-stack")
    add_id_cmd("describe", "describe-stacks")
    add_id_cmd(
        "events",
        "describe-stack-events",
        "StackEvents[*].[LogicalResourceId,ResourceType,ResourceStatus,Timestamp,ResourceStatusReason]",
    )
    add_id_cmd(
        "res",
        "describe-stack-resources",
        "StackResources[*].[LogicalResourceId,ResourceType,PhysicalResourceId]",
    )
    add_id_cmd("delete", "delete-stack")

    add_cloudformation_alias(
        "ls",
        "describe-stacks",
        OutputFormat("table", "Stacks[*].[StackName,StackStatus,CreationTime]"),
    )

    push = argp.sub("ecrpush", do_ecr_push, help="Build and push to ECR repository")
    ecrls = argp.sub("ecrls", do_ecr_ls, help="List images in ECR repository")
    ecrlogin = argp.sub("ecrlogin", do_ecr_login, help="Do docker login to ECR")
    add_overrider_args(push, EcrConfig)
    add_overrider_args(ecrls, EcrConfig)
    add_overrider_args(ecrlogin, EcrConfig)

    parsed = parser.parse_args(sys.argv[1:])
    config = get_config()
    if parsed.define:
        apply_config_overrides(config, parsed.define)

    commands.set_profile_from_config_or_parser(parsed)

    argp.dispatch_parsed(parsed)


if __name__ == "__main__":
    main()
