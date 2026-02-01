# tests/user_test.py — interactive CLI test for PyCells

from pycells_mds.core import PyCells
from pycells_mds.session import init_db, db, _expand_range
from pycells_mds.models import TableModel, CellModel
from pycells_mds.managers import CursorManager

import re

pc = PyCells()


# =====================================================
# AUTHENTICATION
# =====================================================
def auth_flow():
    while True:
        choice = input("Choose an action: [1] Login, [2] Register: ").strip()
        if choice not in ("1", "2"):
            print("Enter 1 or 2.")
            continue

        username = input("Username: ").strip()
        password = input("Password: ").strip()

        if choice == "2":
            email = input("Email (optional): ").strip() or None
            user = pc.register_user(username, password, email)
            print(f"User '{username}' registered.")
            return user.id

        # login
        user_id = pc.login(username, password)
        if not user_id:
            print("Invalid credentials. Try again.")
            continue

        print(f"Welcome, {username}!")
        return user_id


# =====================================================
# TABLE / SHEET SELECTION
# =====================================================
def choose_table(user_id):
    tables = db.session.query(TableModel).filter_by(author_id=user_id).all()
    print("\nYour tables:")

    for t in tables:
        print(f"{t.id}: {t.name}")

    inp = input("Enter table ID or a new table name: ").strip()

    # Existing table
    if inp.isdigit():
        table = (
            db.session.query(TableModel)
            .filter_by(id=int(inp), author_id=user_id)
            .first()
        )
        if not table:
            print("No such table.")
            return choose_table(user_id)
    else:
        # Create new table
        table = TableModel(name=inp, author_id=user_id)
        db.session.add(table)
        db.session.commit()
        print(f"Table '{inp}' created.")

    tbl = pc.ctable(table.name, user_id)

    # select or create sheet
    sheets = tbl.all_lists()
    if sheets:
        print("\nSheets:")
        for i, lst in enumerate(sheets, 1):
            print(f"{i}: {lst.model.name}")

        inp = input("Enter sheet number or press Enter to create new: ").strip()
        if inp.isdigit() and 1 <= int(inp) <= len(sheets):
            return sheets[int(inp) - 1]
        else:
            return tbl.create_list("MainSheet")

    else:
        return tbl.create_list("MainSheet")


# =====================================================
# CURSOR MODE
# =====================================================
def cursor_mode(sheet, user_id):
    while True:
        s = input("\nEnter cursor cells (A1,A2 or A1:C5 or mixed) or press Enter to exit cursor mode: ").strip()
        if not s:
            return

        # expand full range support using our global expand_range helper
        parts = [p.strip() for p in s.split(",") if p.strip()]
        expanded = []

        for p in parts:
            if ":" in p:
                try:
                    expanded.extend(_expand_range(p))
                except Exception as e:
                    print("Invalid range:", p, "→", str(e))
                    continue
            else:
                expanded.append(p)

        if not expanded:
            print("Empty selection.")
            continue

        # activate cursor
        CursorManager.set_cursor(
            user_id=user_id,
            table=sheet.model.table.name,
            list_name=sheet.model.name,     # IMPORTANT FIX
            cells=expanded
        )

        print("Cursor activated:", expanded)

        # write values into each cell
        for cell in expanded:
            val = input(f"{cell} = ").strip()
            sheet.write(cell, None, val)

        print("\nCurrent values:")
        for cell in expanded:
            r = sheet.read(cell)
            print(f"{cell} = {r['value']}")


# =====================================================
# DIRECT EDIT MODE
# =====================================================
def direct_edit(sheet):
    while True:
        line = input("\nEnter: A1=10 or A1 10 (or press Enter to exit): ").strip()
        if not line:
            return

        m = re.match(r"^([A-Za-z]+\d+)\s*=?\s*(.*)$", line)
        if not m:
            print("Invalid format.")
            continue

        cell_name, val = m.groups()
        sheet.write(cell_name, None, val)

        res = sheet.read(cell_name)
        print(f"{cell_name} = {res['value']}")


# =====================================================
# SHOW CELL IDS
# =====================================================
def show_cell_ids(sheet):
    print("\nCell IDs:")
    for name in ["A1", "A2", "A3", "B1", "C1"]:
        cell = (
            db.session.query(CellModel)
            .filter_by(
                table_id=sheet.model.table_id,
                list_id=sheet.model.id,
                name=name,
            )
            .first()
        )
        if cell:
            print(f"{name}: DB-ID={cell.id}, CELL-ID={cell.cell_id}")


# =====================================================
# MAIN
# =====================================================
def main():
    print("=== PyCells USER TEST ===\n")

    init_db({"engine": "sqlite", "path": "pycells_user_test.db"})
    print("Database initialized.")

    user_id = auth_flow()
    sheet = choose_table(user_id)

    print(f"\nWorking in table '{sheet.model.table.name}', sheet '{sheet.model.name}'")

    cursor_mode(sheet, user_id)
    direct_edit(sheet)
    show_cell_ids(sheet)

    print("\nTEST FINISHED.\n")


if __name__ == "__main__":
    main()
