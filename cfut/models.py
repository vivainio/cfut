from enum import Enum
from typing import Dict, Optional, List, Any

from pydantic import BaseModel


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
    repo: str
    tag = "dev"
    src = "."   # path to the directory with Dockerfile, e.g. "."


class IniFile(BaseModel):
    ecr: Optional[EcrConfig]
    profile: str
    templates: Dict[str, CfnTemplate]
