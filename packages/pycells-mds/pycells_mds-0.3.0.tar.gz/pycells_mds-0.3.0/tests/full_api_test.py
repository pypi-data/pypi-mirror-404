# tests/full_api_test.py

from pycells_mds.core import PyCells
from pycells_mds.session import init_db
from redis import Redis
import json
import os


def hr(msg):
    print(f"\n=== {msg} ===")


def main():

    # --------------------------------------------------------------
    # 0) CLEAN PREVIOUS DATABASE
    # --------------------------------------------------------------
    if os.path.exists("full_test.db"):
        os.remove("full_test.db")

    hr("INIT DB")

    init_db({"engine": "sqlite", "path": "full_test.db"})
    pc = PyCells()

    print("DB OK.")

    # --------------------------------------------------------------
    # 1) USER REGISTRATION
    # --------------------------------------------------------------
    hr("USER REGISTER/LOGIN")

    user, user_id = pc.safe_register_user("tester", "pass", "")
    print("user_id =", user_id)

    # --------------------------------------------------------------
    # 2) CREATE TABLE AND LIST
    # --------------------------------------------------------------
    hr("TABLE & LIST")

    tbl = pc.ctable("Finance", user_id)
    sheet = pc.get_or_create_list("Finance", "Main", user_id)

    print("Table ID:", tbl.model.id)
    print("List ID:", sheet.model.id)

    # --------------------------------------------------------------
    # 3) CELLS & FORMULAS
    # --------------------------------------------------------------
    hr("CELLS & FORMULAS")

    pc.write("Finance", "Main", "A1", "0000.0001.0001.0001", "10", user_id)
    pc.write("Finance", "Main", "A2", "0000.0001.0001.0002", "20", user_id)
    pc.write("Finance", "Main", "A3", "0000.0001.0001.0003", "=A1+A2", user_id)

    print("A3 =", pc.read("Finance", "Main", "A3", user_id))

    # --------------------------------------------------------------
    # 4) GROUP RANGE TESTS
    # --------------------------------------------------------------
    hr("GROUPS")

    sheet.add_group("Totals", ["A1", "A2", "A3"], style="color:red;")
    totals = pc.get_group_cells("Finance", "Main", "Totals", user_id)
    print("Group Totals contains:", [c.name for c in totals])

    # --- 4.1 RANGE A1:C3 ---
    hr("GROUP RANGE A1:C3 TEST")

    for col in ["A", "B", "C"]:
        for row in range(1, 4):
            name = f"{col}{row}"
            if not sheet.get_cell(name):
                pc.write("Finance", "Main", name, None, f"{row}", user_id)

    sheet.add_group("Matrix", ["A1:C3"], style="background:blue;")

    matrix = pc.get_group_cells("Finance", "Main", "Matrix", user_id)
    actual = sorted([c.name for c in matrix])
    expected = sorted([f"{c}{r}" for c in "ABC" for r in [1, 2, 3]])

    print("Expected:", expected)
    print("Actual:", actual)
    assert actual == expected
    print("✔ RANGE expansion OK")

    # --- 4.2 MULTI RANGE ---
    hr("GROUP MULTI RANGE TEST")

    sheet.add_group("Many", ["A1:A3", "C1:C3", "B1:B2"], style="border:1px;")

    many = pc.get_group_cells("Finance", "Main", "Many", user_id)
    actual = sorted([c.name for c in many])
    expected = sorted(["A1", "A2", "A3", "B1", "B2", "C1", "C2", "C3"])

    print("Expected:", expected)
    print("Actual:", actual)
    assert actual == expected
    print("✔ MULTI RANGE expansion OK")

    # --- 4.3 LOWERCASE + SPACES + REVERSE ---
    hr("RANGE lowercase + spaces + reverse")

    sheet.add_group("Crazy", [" c3 : a1 "], style="x;")

    crazy = pc.get_group_cells("Finance", "Main", "Crazy", user_id)
    actual = sorted([c.name for c in crazy])
    expected = sorted([f"{col}{r}" for col in "ABC" for r in [1, 2, 3]])

    print("Expected:", expected)
    print("Actual:", actual)
    assert actual == expected
    print("✔ lowercase/space/reverse OK")

    # --------------------------------------------------------------
    # 5) EXPORT
    # --------------------------------------------------------------
    hr("EXPORT TESTS")

    print("JSON:", pc.export("Finance", "Main", "json", user_id))
    print("FLAT:", pc.export("Finance", "Main", "flat", user_id))

    print("TREE:", json.dumps(pc.export_tree("Finance", "Main", user_id), indent=4))

    # --------------------------------------------------------------
    # 6) CURSOR TESTS
    # --------------------------------------------------------------
    hr("CURSOR MANAGER")

    pc.set_active_cursor("Finance", "Main", ["A1", "A2"], user_id)
    print("ACTIVE:", pc.get_active_cursor(user_id))
    print("PREVIOUS:", pc.get_previous_cursor(user_id))

    # --------------------------------------------------------------
    # 6.1 RANGE CURSOR TEST !!!
    # --------------------------------------------------------------
    hr("CURSOR RANGE TEST")

    pc.set_active_cursor("Finance", "Main", ["a1 : a3", "C1:C2"], user_id)

    cursor = pc.get_active_cursor(user_id)
    actual = sorted(cursor["cells"])
    expected = sorted(["A1", "A2", "A3", "C1", "C2"])

    print("Cursor expanded:", actual)
    print("Expected:", expected)

    assert actual == expected
    print("✔ Cursor RANGE expansion OK")

    # --------------------------------------------------------------
    # 7) WRITE IN ACTIVE CURSOR
    # --------------------------------------------------------------
    hr("WRITE IN CURSOR")

    pc.write_in_active_cursor("style", "background:yellow", user_id)
    pc.write_in_active_cursor("note", "Edited by cursor", user_id)

    active = pc.get_active_cursor(user_id)
    cells = active["cells"]

    base = "9999.0001.0001"

    print("\nAssigning unique cell_id:")
    for i, cell in enumerate(cells, start=1):
        pc.set_active_cursor("Finance", "Main", [cell], user_id)
        new_id = f"{base}.{i:04d}"
        print(f" → {cell} = {new_id}")
        pc.write_in_active_cursor("cell_id", new_id, user_id)

    print("\nCursor-write result:")
    print("A1:", sheet.read("A1"))
    print("A2:", sheet.read("A2"))

    # --------------------------------------------------------------
    # 8) REDIS RAW TEST
    # --------------------------------------------------------------
    hr("REDIS RAW CHECK")

    redis = Redis(host="localhost", port=6379, decode_responses=True)
    raw = redis.get(f"cursor:{user_id}")

    print("RAW:", raw)
    print("TYPE:", type(raw))
    print("DECODED:", json.loads(raw))

    hr("FULL API TEST PASSED!")


if __name__ == "__main__":
    main()
