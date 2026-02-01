# pycells_api/schemas.py

from pydantic import BaseModel


class RegisterSchema(BaseModel):
    username: str
    password: str
    email: str | None = None


class WriteCellSchema(BaseModel):
    table: str
    sheet: str
    cell: str
    cell_id: str | None = None
    data: str


class CursorUpdateSchema(BaseModel):
    cells: list[str]


class GroupSchema(BaseModel):
    name: str
    cells: list[str]
    style: str = ""
