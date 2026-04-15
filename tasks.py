"""Simple task runner. Prefer `uv run` directly; these are thin wrappers."""

import subprocess
import sys
import textwrap


def do_check(args):
    """type-check with mypy"""
    c("uv run mypy cfut")


def do_format(args):
    """ruff format"""
    c("uv run ruff format cfut")


def do_test(args):
    """run pytest"""
    c("uv run pytest tests/")


def do_publish(args):
    """Publishing is done by .github/workflows/publish.yml on GitHub release.

    To cut a release:
        gh release create v1.2.3 --notes "..."
    """
    print(do_publish.__doc__)


def c(cmd):
    print(">", cmd)
    subprocess.check_call(cmd, shell=True)


def show_help():
    g = globals()
    print(
        "Command not found, try",
        sys.argv[0],
        " | ".join([n[3:] for n in g if n.startswith("do_")]),
        "| <command> -h",
    )


def main():
    if len(sys.argv) < 2:
        show_help()
        return
    func = sys.argv[1]
    f = globals().get("do_" + func)
    if sys.argv[-1] == "-h":
        print(
            textwrap.dedent(f.__doc__).strip()
            if f and f.__doc__
            else "No documentation for this command"
        )
        return
    if not f:
        show_help()
        return
    f(sys.argv[2:])


if __name__ == "__main__":
    main()
