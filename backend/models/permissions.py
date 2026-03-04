# Permission-related Pydantic models
from pydantic import BaseModel


class PermissionUpdate(BaseModel):
    chapter: str
    title: str
    permission_key: str
    value: bool


class BulkPermissionUpdate(BaseModel):
    chapter: str
    title: str
    permissions: dict
