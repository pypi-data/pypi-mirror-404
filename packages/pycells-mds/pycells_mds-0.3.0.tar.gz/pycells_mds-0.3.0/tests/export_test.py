# tests/export_test.py

from pycells_mds.core import PyCells
from pycells_mds.session import init_db
import json
import os


def hr(msg):
    print(f"\n=== {msg} ===")


def main():

    # --------------------------------------------------------------
    # 0) RESET DATABASE
    # --------------------------------------------------------------
    if os.path.exists("test_pycells.db"):
        os.remove("test_pycells.db")

    hr("INIT DATABASE")

    init_db({
        "engine": "sqlite",
        "path": "test_pycells.db"
    })

    pc = PyCells()
    print("Database ready.")

    # --------------------------------------------------------------
    # 1) USER REGISTER / LOGIN
    # --------------------------------------------------------------
    hr("REGISTER USER")

    try:
        user = pc.register_user("zhandos", "0150", "z@cells.com")
        user_id = user.id
        print("New user created.")
    except Exception:
        print("User already exists → login")
        user_id = pc.login("zhandos", "0150")

    print("User ID:", user_id)

    # --------------------------------------------------------------
    # 2) CREATE TABLE + LIST
    # --------------------------------------------------------------
    hr("CREATE TABLE & LIST")

    tbl = pc.ctable("Finance", user_id)
    print("Table ID =", tbl.model.id)

    sheet = pc.get_or_create_list("Finance", "Main", user_id)
    print("List ID  =", sheet.model.id)
    print("List Name:", sheet.model.name)

    # --------------------------------------------------------------
    # 3) WRITE CELLS WITH HIERARCHICAL ID
    # --------------------------------------------------------------
    hr("WRITE CELLS WITH cell_id")

    pc.write("Finance", "Main", "A1", "0000.0001.0001.0001", "100", user_id)
    pc.write("Finance", "Main", "A2", "0000.0001.0001.0002", "200", user_id)
    pc.write("Finance", "Main", "A3", "0000.0001.0001.0003", "=A1+A2", user_id)

    print("Cells written.")

    # --------------------------------------------------------------
    # 4) CHECK READING
    # --------------------------------------------------------------
    hr("READ CELLS")

    print("A1 →", pc.read("Finance", "Main", "A1", user_id))
    print("A2 →", pc.read("Finance", "Main", "A2", user_id))
    print("A3 →", pc.read("Finance", "Main", "A3", user_id))

    # --------------------------------------------------------------
    # 5) EXPORT JSON
    # --------------------------------------------------------------
    hr("EXPORT JSON")

    json_data = pc.export("Finance", "Main", "json", user_id)
    print(json.dumps(json_data, indent=4, ensure_ascii=False))

    # --------------------------------------------------------------
    # 6) EXPORT FLAT
    # --------------------------------------------------------------
    hr("EXPORT FLAT")

    flat_data = pc.export("Finance", "Main", "flat", user_id)
    print(json.dumps(flat_data, indent=4, ensure_ascii=False))

    # --------------------------------------------------------------
    # 7) COUNT CELLS
    # --------------------------------------------------------------
    hr("COUNT CELLS")

    print("JSON cells:", len(json_data))
    print("FLAT cells:", len(flat_data))

    # --------------------------------------------------------------
    # 8) EXPORT TREE
    # --------------------------------------------------------------
    hr("EXPORT TREE")

    tree = pc.export_tree("Finance", "Main", user_id)

    print(json.dumps(tree, indent=4, ensure_ascii=False))

    # Final
    hr("DONE")


if __name__ == "__main__":
    main()
