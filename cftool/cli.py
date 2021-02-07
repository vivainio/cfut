import os
import sys
import argp

from pathlib import Path

from cftool import commands
from cftool.commands import CONFIG_FILE, get_config, run_cf
from cftool.models import IniFile, CfnTemplate


def do_init(args):
    """ initialize cftool.json"""

    assert not os.path.isfile(CONFIG_FILE)
    template_files = Path(".").glob("**/*.y*ml")
    ini = IniFile(templates={
        t.stem: CfnTemplate(name=t.stem, path=str(t).replace('\\', '/')) for t in template_files})
    cont = ini.json(indent=2)
    open(CONFIG_FILE, "w").write(cont)


def lint(args):
    config = get_config()
    for t in config.templates.values():
        os.system("cfn-lint " + t.path)


def add_alias(fr: str, to: str):
    def alias_handler(args):
        cmd = to
        if args.other_args:
            cmd += " " + " ".join(args.other_args)
        run_cf(cmd)

    sp = argp.sub(fr, alias_handler, help="Alias: " + to)
    sp.add_argument("other_args", nargs="*")


def add_id_cmd(fr: str, to: str):
    def id_cmd_handler(args):
        commands.run_command(args.id, to)

    sp = argp.sub(fr, id_cmd_handler, help="Call: " + to)
    sp.add_argument("id", help="Nickname of stack")


def add_template_cmd(fr: str, to: str):
    def template_cmd_handler(args):
        commands.run_command_with_file(args.id, to)

    sp = argp.sub(fr, template_cmd_handler, help=f"Call with template: {to}")
    sp.add_argument("id", help="Alias of stack")


def main():
    argp.init()
    argp.sub("init", do_init, help="Initialize working directory")
    argp.sub("lint", lint, help="Lint templates")

    add_template_cmd("update", "update-stack")
    add_template_cmd("create", "create-stack")
    add_id_cmd("describe", "describe-stacks")
    add_id_cmd("delete", "delete-stack")

    add_alias("ls", "describe-stacks")
    commands.set_profile_from_config()
    argp.parse()


if __name__ == "__main__":
    main()
