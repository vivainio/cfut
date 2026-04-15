import json
import os
from dataclasses import asdict, dataclass, field, fields
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, List, Optional


class Capability(str, Enum):
    CAPABILITY_NAMED_IAM = "CAPABILITY_NAMED_IAM"
    CAPABILITY_IAM = "CAPABILITY_IAM"
    CAPABILITY_AUTO_EXPAND = "CAPABILITY_AUTO_EXPAND"


@dataclass
class CfnTemplate:
    name: str
    path: str
    capabilities: Optional[List[Capability]] = None
    parameters: Optional[Dict[str, Any]] = None


@dataclass
class EcrConfig:
    repo: str = field(
        metadata={"description": "ECR repository name, e.g. my-repo. Not the full URL!"}
    )
    account: Optional[str] = field(
        default=None,
        metadata={
            "description": "AWS account in which ECR repo is (may be different than current account)"
        },
    )
    region: Optional[str] = field(
        default=None, metadata={"description": "AWS region for the ECR repo"}
    )
    tag: str = field(
        default="dev",
        metadata={"description": "Tag to add in addition to git sha and 'latest'"},
    )
    src: str = field(
        default=".", metadata={"description": "Directory where Dockerfile is"}
    )


@dataclass
class EcsConfig:
    run_args: List[str] = field(default_factory=list)
    cluster: Optional[str] = None


@dataclass
class IniFile:
    templates: Dict[str, CfnTemplate]
    ecs: Optional[EcsConfig] = None
    ecr: Optional[EcrConfig] = None
    profile: Optional[str] = None
    logs: Optional[str] = None


@dataclass
class EnvVars:
    aws_default_region: Optional[str] = None


@dataclass
class StatusRules:
    in_progress: str
    success: str


@lru_cache()
def get_env() -> EnvVars:
    return EnvVars(aws_default_region=os.environ.get("AWS_DEFAULT_REGION"))


def _filter_kwargs(cls, data: Dict[str, Any]) -> Dict[str, Any]:
    """Drop keys not present on the dataclass (defensive for old configs)."""
    names = {f.name for f in fields(cls)}
    return {k: v for k, v in data.items() if k in names}


def load_inifile(raw: str) -> IniFile:
    data = json.loads(raw)
    templates = {
        k: CfnTemplate(
            name=v["name"],
            path=v["path"],
            capabilities=[Capability(c) for c in v["capabilities"]]
            if v.get("capabilities")
            else None,
            parameters=v.get("parameters"),
        )
        for k, v in data.get("templates", {}).items()
    }
    ecr = EcrConfig(**_filter_kwargs(EcrConfig, data["ecr"])) if data.get("ecr") else None
    ecs = EcsConfig(**_filter_kwargs(EcsConfig, data["ecs"])) if data.get("ecs") else None
    return IniFile(
        templates=templates,
        ecr=ecr,
        ecs=ecs,
        profile=data.get("profile"),
        logs=data.get("logs"),
    )


def dump_inifile(ini: IniFile, indent: int = 2) -> str:
    return json.dumps(asdict(ini), indent=indent)
