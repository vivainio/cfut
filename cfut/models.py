from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Dict, Optional, List, Any

from pydantic import BaseModel, BaseSettings, Field


class Capability(str, Enum):
    CAPABILITY_NAMED_IAM = "CAPABILITY_NAMED_IAM"
    CAPABILITY_IAM = "CAPABILITY_IAM"
    CAPABILITY_AUTO_EXPAND = "CAPABILITY_AUTO_EXPAND"


class CfnTemplate(BaseModel):
    name: str
    path: str
    capabilities: Optional[List[Capability]]
    parameters: Optional[Dict[str, Any]]


class EcrConfig(BaseModel):
    account: Optional[str] = Field(
        description="AWS account in which ECR repo is (may be different than current account)")  # you can specify account if your ecr repo is in another account
    region: Optional[str] = Field(description="AWS region for the ECR repo")  # ditto
    repo: str = Field(description="ECR repository name, e.g. my-repo. Not the full URL!")
    tag: str = Field("dev", description="Tag to add in addition to git sha and 'latest'")
    src: str = Field(".", description="Directory where Dockerfile is")


class EcsConfig(BaseModel):
    run_args: Optional[List[str]] = []
    cluster: Optional[str] = Field(description="ECS cluster name")


class IniFile(BaseModel):
    ecs: Optional[EcsConfig]
    ecr: Optional[EcrConfig]
    profile: Optional[str]
    templates: Dict[str, CfnTemplate]


class EnvVars(BaseSettings):
    aws_default_region: Optional[str]


@dataclass
class StatusRules:
    in_progress: str
    success: str


@lru_cache()
def get_env():
    return EnvVars()
