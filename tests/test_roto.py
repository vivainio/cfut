"""Integration tests using a local Roto server and the real AWS CLI."""

import json
import shutil
import socket
import subprocess
import time

import pytest

from cfut import commands
from cfut.models import CfnTemplate, get_env


@pytest.fixture
def roto(tmp_path, monkeypatch):
    server = shutil.which("roto-server")
    if not server or not shutil.which("aws"):
        pytest.skip("requires roto-server and aws on PATH; see README.md")

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]

    monkeypatch.chdir(tmp_path)
    (tmp_path / "cfut.json").write_text(json.dumps({"templates": {}}))
    for key, value in {
        "AWS_ENDPOINT_URL": f"http://127.0.0.1:{port}",
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_DEFAULT_REGION": "eu-west-1",
        "AWS_CONFIG_FILE": str(tmp_path / "aws-config"),
        "AWS_SHARED_CREDENTIALS_FILE": str(tmp_path / "aws-credentials"),
        "AWS_EC2_METADATA_DISABLED": "true",
        "AWS_PAGER": "",
    }.items():
        monkeypatch.setenv(key, value)
    for key in (
        "AWS_PROFILE",
        "AWS_DEFAULT_PROFILE",
        "AWS_SESSION_TOKEN",
        "AWS_SECURITY_TOKEN",
        "AWS_ENDPOINT_URL_STS",
        "AWS_ENDPOINT_URL_CLOUDFORMATION",
        "AWS_IGNORE_CONFIGURED_ENDPOINT_URLS",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(commands, "current_profile", None)
    monkeypatch.setattr(commands, "current_config", None)
    commands.get_account.cache_clear()
    commands.get_region.cache_clear()
    get_env.cache_clear()

    with (tmp_path / "roto.log").open("w+") as log:
        process = subprocess.Popen(
            [server, "--host", "127.0.0.1", "--port", str(port), "--ephemeral"],
            stdout=log,
            stderr=log,
        )
        try:
            deadline = time.monotonic() + 10
            while True:
                if process.poll() is not None or time.monotonic() >= deadline:
                    log.seek(0)
                    pytest.fail(f"Roto did not start: {log.read()}")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                        break
                except OSError:
                    time.sleep(0.05)
            yield tmp_path
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            commands.get_account.cache_clear()
            commands.get_region.cache_clear()
            get_env.cache_clear()


def test_account_and_region(roto):
    assert commands.get_account() == "123456789012"
    assert commands.get_region() == "eu-west-1"


def test_stack_lifecycle(roto):
    template = roto / "stack.json"

    def write_template(value):
        template.write_text(
            json.dumps(
                {
                    "Resources": {"Queue": {"Type": "AWS::SQS::Queue"}},
                    "Outputs": {"Value": {"Value": value}},
                }
            )
        )

    stack = CfnTemplate(name="cfut-roto-test", path=str(template))
    assert commands.get_stack_status(stack.name) == "NOT_EXIST"
    write_template("first")
    commands.deploy_stack(stack)
    assert commands.get_stack_status(stack.name) == "CREATE_COMPLETE"

    write_template("second")
    commands.deploy_stack(stack)
    assert commands.get_stack_status(stack.name) == "UPDATE_COMPLETE"
    err, result = commands.run_cli_parsed_output(
        f"cloudformation describe-stacks --stack-name {stack.name}"
    )
    assert err is None
    assert result["Stacks"][0]["Outputs"] == [{"OutputKey": "Value", "OutputValue": "second"}]

    commands.run_cf(f"delete-stack --stack-name {stack.name}")
    commands.poll_until_status(stack.name, commands.STATUS_RULES_DELETE)
    assert commands.get_stack_status(stack.name) == "NOT_EXIST"
