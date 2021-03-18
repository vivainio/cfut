from enum import Enum
from functools import lru_cache
from typing import Dict, Optional, List, Any

from pydantic import BaseModel, BaseSettings


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
    account: Optional[str]   # you can specify account if your ecr repo is in another account
    region: Optional[str]    # ditto
    repo: str
    tag = "dev"
    src = "."  # path to the directory with Dockerfile, e.g. "."


class IniFile(BaseModel):
    ecr: Optional[EcrConfig]
    profile: Optional[str]
    templates: Dict[str, CfnTemplate]


class EnvVars(BaseSettings):
    aws_default_region: Optional[str]


@lru_cache()
def get_env():
    return EnvVars()
