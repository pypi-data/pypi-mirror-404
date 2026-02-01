# pycells_mds/core.py

from .session import db, init_db
from .models import TableModel, ListModel
from pycells_mds.wrappers import TableWrapper, ListWrapper, CellWrapper
from pycells_mds.managers import CursorManager

from pycells_mds.users import (
    register_user,
    login_user,
    safe_register_user
)





class PyCells:

    # =========================================================
    # USER API (PUBLIC)
    # =========================================================

    def register_user(self, username: str, password: str, email: str | None = None):
        return register_user(username, password, email)

    def login(self, username: str, password: str) -> int | None:
        return login_user(username, password)

    def safe_register_user(self, username: str, password: str, email: str | None = None):
        return safe_register_user(username, password, email)

    # ---------------------------------------------------------
    # TABLE OPERATIONS
    # ---------------------------------------------------------

    def ctable(self, name: str, user_id: int) -> TableWrapper:
        table = (
            db.session.query(TableModel)
            .filter_by(name=name, author_id=user_id)
            .first()
        )

        if not table:
            table = TableModel(name=name, author_id=user_id)
            db.session.add(table)
            db.session.commit()

        return TableWrapper(table)

    def get_table(self, name: str, user_id: int) -> TableWrapper | None:
        table = (
            db.session.query(TableModel)
            .filter_by(name=name, author_id=user_id)
            .first()
        )
        return TableWrapper(table) if table else None

    # ---------------------------------------------------------
    # LIST OPERATIONS
    # ---------------------------------------------------------

    def get_list(self, table_name: str, list_name: str, user_id: int) -> ListWrapper | None:
        tbl = self.get_table(table_name, user_id)
        if not tbl:
            return None

        lst = (
            db.session.query(ListModel)
            .filter_by(table_id=tbl.model.id, name=list_name)
            .first()
        )
        return ListWrapper(lst) if lst else None

    def get_or_create_list(self, table_name: str, list_name: str, user_id: int) -> ListWrapper:
        tbl = self.ctable(table_name, user_id)
        return tbl.create_list(list_name)

    # ---------------------------------------------------------
    # QUICK START
    # ---------------------------------------------------------

    def quick_start(self):

        init_db({
            "engine": "sqlite",
            "path": "default.db"
        })

        print("DB connected.")

        user, user_id = self.safe_register_user("default", "1234", "")

        print(f"User ID = {user_id}")

      
        tbl = self.ctable("Table1", user_id)

   
        sheet = self.get_or_create_list("Table1", "List1", user_id)

        print("Table: Table1, Sheet: List1 ready.")

        return user_id, tbl, sheet




    def write(self, table: str, sheet: str, cell_name: str, cell_id: str | None, data: str, user_id: int):
        
        lst = self.get_or_create_list(table, sheet, user_id)
        return lst.write(cell_name, cell_id, data)


    def read(self, table: str, sheet: str, cell_name: str, user_id: int):
        lst = self.get_or_create_list(table, sheet, user_id)
        return lst.read(cell_name)


    def select(self, table: str, sheet: str, *cells, user_id: int):
        
        lst = self.get_or_create_list(table, sheet, user_id)
        return {name: lst.read(name) for name in cells}

    # ---------------------------------------------------------
    # RE-CALC
    # ---------------------------------------------------------

    def recalc(self, table: str, sheet: str, user_id: int):
      
        lst = self.get_or_create_list(table, sheet, user_id)
        lst.recalc_all()
        return True
    


    # GROUP OPERATIONS
# ----------------------------------------------------------

    def create_group(self, table: str, sheet: str, name: str, cells: list[str], user_id: int, style: str = ""):
    
        lst = self.get_or_create_list(table, sheet, user_id)
        return lst.add_group(name, cells, style)

    def update_group_style(self, table: str, sheet: str, name: str, style: str, user_id: int):
        
        lst = self.get_or_create_list(table, sheet, user_id)
        return lst.update_group_style(name, style)

    def get_group_cells(self, table: str, sheet: str, name: str, user_id: int):
   
        lst = self.get_or_create_list(table, sheet, user_id)
        return lst.get_group_cells(name)

    def delete_group(self, table: str, sheet: str, name: str, user_id: int):
       
        lst = self.get_or_create_list(table, sheet, user_id)
        return lst.delete_group(name)
    


    # Notes and Style
# ----------------------------------------------------------

    def set_style(self, table, sheet, cell, style, user_id):
        lst = self.get_or_create_list(table, sheet, user_id)
        return lst.set_style(cell, style)

    def get_style(self, table, sheet, cell, user_id):
        lst = self.get_or_create_list(table, sheet, user_id)
        return lst.get_style(cell)

    def set_note(self, table, sheet, cell, note, user_id):
        lst = self.get_or_create_list(table, sheet, user_id)
        return lst.set_note(cell, note)

    def get_note(self, table, sheet, cell, user_id):
        lst = self.get_or_create_list(table, sheet, user_id)
        return lst.get_note(cell)

    def clear_style(self, table, sheet, cell, user_id):
        lst = self.get_or_create_list(table, sheet, user_id)
        return lst.clear_style(cell)

    def clear_note(self, table, sheet, cell, user_id):
        lst = self.get_or_create_list(table, sheet, user_id)
        return lst.clear_note(cell)
    

    def update_group_style(self, table, sheet, group, style, user_id):
        lst = self.get_or_create_list(table, sheet, user_id)
        return lst.update_group_style(group, style)
    

    def export(self, table: str, sheet: str, mode: str, user_id: int):
        lst = self.get_or_create_list(table, sheet, user_id)
        return lst.export(mode)
    


    def export_tree(self, table: str, sheet: str, user_id: int):
        lst = self.get_or_create_list(table, sheet, user_id)
        return lst.export_tree()
    


     # ---------------------------------------------------------
    # CURSOR API
    # ---------------------------------------------------------

    def set_active_cursor(self, table: str, sheet: str, cells: list[str], user_id: int):
        return CursorManager.set_cursor(user_id, table, sheet, cells)

    def get_active_cursor(self, user_id: int):
        return CursorManager.get_active(user_id)

    def get_previous_cursor(self, user_id: int):
        return CursorManager.get_prec_cursor(user_id)

    def write_in_active_cursor(self, path: str, value, user_id: int):
        cursor = CursorManager.get_active(user_id)
        if not cursor:
            raise ValueError("No active cursor")

        table = cursor["table"]
        sheet = cursor["list"]
        cells = cursor["cells"]

        lst = self.get_or_create_list(table, sheet, user_id)

        for cell_name in cells:
            cell = lst.get_cell(cell_name)
            if not cell:
                continue

            if path == "data":
                cell.data = value
                wrapper = CellWrapper(cell)
                try:
                    cell.value = wrapper.evaluate()
                except Exception:
                    cell.value = "#ERROR"

            elif path == "style":
                cell.style = value

            elif path == "note":
                cell.note = value

            elif path == "cell_id":
                cell.cell_id = value

            elif path == "group":
                cell.group_id = int(value) if value else None

            else:
                raise ValueError(f"Unknown path: {path}")

        db.session.commit()
        return True




