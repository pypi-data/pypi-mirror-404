# pycells_api/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional, Any

from pycells_mds.core import PyCells

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import time







STARTED_AT = time.time()




# --------------------------------------------------------------
# SCHEMAS
# --------------------------------------------------------------

class CellData(BaseModel):
    cell: str
    data: str
    cell_id: Optional[str] = None


class MultiCellData(BaseModel):
    cells: List[str]


class GroupData(BaseModel):
    name: str
    cells: List[str]
    style: str = ""


class GroupStyle(BaseModel):
    style: str


class StyleData(BaseModel):
    value: str


class NoteData(BaseModel):
    note: str


class CursorWrite(BaseModel):
    path: str
    value: Any


pc = PyCells()


# --------------------------------------------------------------
# LIFESPAN
# --------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(">>> Initializing PyCells with quick_start()")
    pc.quick_start()
    print(">>> PyCells ready")
    yield
    print(">>> Shutdown")


app = FastAPI(title="PyCells REST API", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "assets"))


app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")




@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(ASSETS_DIR, "html", "index.html"))





@app.get("/health", include_in_schema=False)
def health():
    checks = {}

    # DB
    try:
        pc.read("Table1", "List1", "A1", 1)
        checks["db"] = "ok"
    except Exception:
        checks["db"] = "error"

    # Redis / cursor
    try:
        pc.get_active_cursor(1)
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"

    return {
        "status": status,
        "checks": checks,
        "started_at": int(STARTED_AT),
        "uptime_sec": int(time.time() - STARTED_AT),
    }





# ==============================================================
#   CELLS
# ==============================================================

@app.get("/tables/{table}/sheets/{sheet}/cells/{cell}")
def read_cell(table: str, sheet: str, cell: str, user_id: int = 1):
    return pc.read(table, sheet, cell, user_id)


@app.post("/tables/{table}/sheets/{sheet}/cells")
def write_cell(table: str, sheet: str, payload: CellData, user_id: int = 1):
    pc.write(table, sheet, payload.cell, payload.cell_id, payload.data, user_id)
    return {"status": "ok"}


@app.post("/tables/{table}/sheets/{sheet}/cells/select")
def select_cells(table: str, sheet: str, payload: MultiCellData, user_id: int = 1):
    return pc.select(table, sheet, *payload.cells, user_id=user_id)


@app.post("/tables/{table}/sheets/{sheet}/cells/recalc")
def recalc(table: str, sheet: str, user_id: int = 1):
    pc.recalc(table, sheet, user_id)
    return {"status": "recalculated"}


# ==============================================================
#   GROUPS
# ==============================================================

@app.get("/tables/{table}/sheets/{sheet}/groups/{group}")
def get_group(table: str, sheet: str, group: str, user_id: int = 1):
    return pc.get_group_cells(table, sheet, group, user_id)


@app.post("/tables/{table}/sheets/{sheet}/groups")
def create_group(table: str, sheet: str, payload: GroupData, user_id: int = 1):
    pc.create_group(table, sheet, payload.name, payload.cells, user_id, payload.style)
    return {"status": "created"}


@app.post("/tables/{table}/sheets/{sheet}/groups/{group}/style")
def update_group_style(table: str, sheet: str, group: str, payload: GroupStyle, user_id: int = 1):
    pc.update_group_style(table, sheet, group, payload.style, user_id)
    return {"status": "ok"}


@app.delete("/tables/{table}/sheets/{sheet}/groups/{group}")
def delete_group(table: str, sheet: str, group: str, user_id: int = 1):
    pc.delete_group(table, sheet, group, user_id)
    return {"status": "deleted"}


# ==============================================================
#   STYLE
# ==============================================================

@app.get("/tables/{table}/sheets/{sheet}/cells/{cell}/style")
def get_style(table: str, sheet: str, cell: str, user_id: int = 1):
    return pc.get_style(table, sheet, cell, user_id)


@app.post("/tables/{table}/sheets/{sheet}/cells/{cell}/style")
def set_style(table: str, sheet: str, cell: str, payload: StyleData, user_id: int = 1):
    pc.set_style(table, sheet, cell, payload.value, user_id)
    return {"status": "ok"}


@app.delete("/tables/{table}/sheets/{sheet}/cells/{cell}/style")
def clear_style(table: str, sheet: str, cell: str, user_id: int = 1):
    pc.clear_style(table, sheet, cell, user_id)
    return {"status": "cleared"}


# ==============================================================
#   NOTES
# ==============================================================

@app.get("/tables/{table}/sheets/{sheet}/cells/{cell}/note")
def get_note(table: str, sheet: str, cell: str, user_id: int = 1):
    return pc.get_note(table, sheet, cell, user_id)


@app.post("/tables/{table}/sheets/{sheet}/cells/{cell}/note")
def set_note(table: str, sheet: str, cell: str, payload: NoteData, user_id: int = 1):
    pc.set_note(table, sheet, cell, payload.note, user_id)
    return {"status": "ok"}


@app.delete("/tables/{table}/sheets/{sheet}/cells/{cell}/note")
def clear_note(table: str, sheet: str, cell: str, user_id: int = 1):
    pc.clear_note(table, sheet, cell, user_id)
    return {"status": "cleared"}


# ==============================================================
#   EXPORT
# ==============================================================

@app.get("/tables/{table}/sheets/{sheet}/export")
def export(table: str, sheet: str, mode: str = "json", user_id: int = 1):
    return pc.export(table, sheet, mode, user_id)


@app.get("/tables/{table}/sheets/{sheet}/export/tree")
def export_tree(table: str, sheet: str, user_id: int = 1):
    return pc.export_tree(table, sheet, user_id)


# ==============================================================
#   CURSOR
# ==============================================================

@app.get("/tables/{table}/sheets/{sheet}/cursor")
def get_cursor(table: str, sheet: str, user_id: int = 1):
    return pc.get_active_cursor(user_id)


@app.get("/tables/{table}/sheets/{sheet}/cursor/prev")
def previous_cursor(table: str, sheet: str, user_id: int = 1):
    return pc.get_previous_cursor(user_id)


@app.post("/tables/{table}/sheets/{sheet}/cursor")
def set_cursor(table: str, sheet: str, payload: MultiCellData, user_id: int = 1):
    return pc.set_active_cursor(table, sheet, payload.cells, user_id)


@app.post("/tables/{table}/sheets/{sheet}/cursor/write")
def cursor_write(table: str, sheet: str, payload: CursorWrite, user_id: int = 1):
    pc.write_in_active_cursor(payload.path, payload.value, user_id)
    return {"status": "ok"}
