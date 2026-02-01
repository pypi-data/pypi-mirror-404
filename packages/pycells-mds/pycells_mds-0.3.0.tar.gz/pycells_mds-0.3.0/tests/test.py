# tests/test.py — full functional test of PyCells API

from pycells_mds.core import PyCells
from pycells_mds.session import init_db
import json
import os


def hr(msg):
    print(f"\n=== {msg} ===")


def main():

    # -------------------------------------------------------------
    # 0) RESET DATABASE
    # -------------------------------------------------------------
    if os.path.exists("test_pycells.db"):
        os.remove("test_pycells.db")

    hr("INITIALIZE DATABASE")

    init_db({
        "engine": "sqlite",
        "path": "test_pycells.db"
    })

    pc = PyCells()
    print("Database connected.")


    # -------------------------------------------------------------
    # 1) USER REGISTER / LOGIN
    # -------------------------------------------------------------
    hr("USER REGISTRATION")

    try:
        user = pc.register_user("default", "1234", "z@cells.com")
        user_id = user.id
        print("User created.")
    except Exception:
        print("User exists → login")
        user_id = pc.login("default", "1234")

    print("User ID =", user_id)


    # -------------------------------------------------------------
    # 2) TABLE + LIST
    # -------------------------------------------------------------
    hr("CREATE TABLE AND SHEET")

    tbl = pc.ctable("Finance", user_id)
    sheet = pc.get_or_create_list("Finance", "Main", user_id)

    print("Table:", tbl.model.name)
    print("Sheet:", sheet.model.name)


    # -------------------------------------------------------------
    # 3) WRITE CELLS
    # -------------------------------------------------------------
    hr("WRITE CELLS")

    pc.write("Finance", "Main", "A1", None, "10", user_id)
    pc.write("Finance", "Main", "A2", None, "20", user_id)
    pc.write("Finance", "Main", "A3", None, "=A1+A2", user_id)

    print("A1=10, A2=20, A3=A1+A2")


    # -------------------------------------------------------------
    # 4) READ CELLS
    # -------------------------------------------------------------
    hr("READ CELLS")

    print("A1:", pc.read("Finance", "Main", "A1", user_id)["value"])
    print("A2:", pc.read("Finance", "Main", "A2", user_id)["value"])
    print("A3:", pc.read("Finance", "Main", "A3", user_id)["value"])


    # -------------------------------------------------------------
    # 5) FORMULA TEST (POWER)
    # -------------------------------------------------------------
    hr("FORMULA POWER TEST")

    pc.write("Finance", "Main", "B1", None, "5", user_id)
    pc.write("Finance", "Main", "B2", None, "3", user_id)
    pc.write("Finance", "Main", "B3", None, "=B1^B2", user_id)  # 5^3 = 125

    print("B3 =", pc.read("Finance", "Main", "B3", user_id)["value"])


    # -------------------------------------------------------------
    # 6) GLOBAL FUNCTIONS
    # -------------------------------------------------------------
    hr("GLOBAL FUNCTIONS TEST")

    pc.write("Finance", "Main", "C1", None, "=SUM(A1:A3)", user_id)
    pc.write("Finance", "Main", "C2", None, "=IF(A1>5, 'OK', 'NO')", user_id)
    pc.write("Finance", "Main", "C3", None, "=UPPER('hello')", user_id)

    print("C1 SUM:", pc.read("Finance", "Main", "C1", user_id)["value"])
    print("C2 IF:", pc.read("Finance", "Main", "C2", user_id)["value"])
    print("C3 UPPER:", pc.read("Finance", "Main", "C3", user_id)["value"])


    # -------------------------------------------------------------
    # 7) GROUP TEST
    # -------------------------------------------------------------
    hr("GROUP TEST")

    sheet.add_group("Totals", ["A1", "A2", "A3"], style="color:red;")

    print("Group Totals:", [c.name for c in sheet.get_group_cells("Totals")])


    # -------------------------------------------------------------
    # 8) SELECT TEST
    # -------------------------------------------------------------
    hr("SELECT TEST")

    result = pc.select("Finance", "Main", "A1", "A3", "C1", user_id=user_id)
    print("Selected:", result)


    # -------------------------------------------------------------
    # 9) RECALC TEST
    # -------------------------------------------------------------
    hr("RECALC TEST")

    print("- Change A1 = 100")
    pc.write("Finance", "Main", "A1", None, "100", user_id)

    print("- Recalc...")
    pc.recalc("Finance", "Main", user_id)

    print("A3 =", pc.read("Finance", "Main", "A3", user_id)["value"])
    print("C1 =", pc.read("Finance", "Main", "C1", user_id)["value"])


    # -------------------------------------------------------------
    # DONE
    # -------------------------------------------------------------
    hr("TEST COMPLETED")


if __name__ == "__main__":
    main()
