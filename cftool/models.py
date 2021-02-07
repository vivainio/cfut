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



class IniFile(BaseModel):
    profile: str
    templates: Dict[str, CfnTemplate]
