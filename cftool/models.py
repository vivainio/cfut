from typing import Dict

from pydantic import BaseModel


class CfnTemplate(BaseModel):
    name: str
    path: str


class IniFile(BaseModel):
    profile: str
    templates: Dict[str, CfnTemplate]
