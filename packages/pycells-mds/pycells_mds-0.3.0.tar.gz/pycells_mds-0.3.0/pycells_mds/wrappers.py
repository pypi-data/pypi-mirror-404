# pycells_mds/wrappers.py

from .session import db, RANGE_RE, _expand_range
from .models import TableModel, ListModel, CellModel, GroupModel
import numpy as np
import datetime as dt
import re





def ETEXT(x, fmt: str = None):
    import re

  
    if isinstance(x, str):
        x = x.strip()
        
        if x.endswith("%"):
            try:
                x = float(x[:-1]) / 100
            except:
                pass
      
        elif "^" in x:
            try:
                base, exp = x.split("^")
                x = float(base) ** float(exp)
            except:
                pass
        else:
            try:
                x = float(x)
            except:
                pass

 
    if isinstance(x, (int, float)):
        if fmt == "0":          
            return f"{int(round(x))}"
        elif fmt == "0.0":      
            return f"{x:.1f}"
        elif fmt == "0.00":     
            return f"{x:.2f}"
        elif fmt == "0%":       
            return f"{round(x*100)}%"
        elif fmt == "0.0%":     
            return f"{x*100:.1f}%"
        elif fmt == "#,##0":    
            return f"{int(round(x)):,}"
        else:
            try:                
                return format(x, fmt)
            except:
                return str(x)

 
    elif isinstance(x, (dt.date, dt.datetime)):
        mapping = {
            "dd.mm.yyyy": "%d.%m.%Y",
            "dd/mm/yyyy": "%d/%m/%Y",
            "yyyy-mm-dd": "%Y-%m-%d",
            "yyyy/mm/dd": "%Y/%m/%d",
        }
        py_fmt = mapping.get(fmt.lower())
        if py_fmt:
            return x.strftime(py_fmt)
        else:
            return str(x)

 
    else:
        return str(x)





GLOBAL_NS = {
  
    "SUM": lambda lst: np.sum(lst) if isinstance(lst, (list, np.ndarray)) else lst,
    "MAX": lambda lst: np.max(lst) if isinstance(lst, (list, np.ndarray)) else lst,
    "MIN": lambda lst: np.min(lst) if isinstance(lst, (list, np.ndarray)) else lst,
    "AVERAGE": lambda lst: np.mean(lst) if isinstance(lst, (list, np.ndarray)) else lst,


    "ABS": np.abs,
    "ROUND": np.round,
    "POWER": lambda a, b: np.power(a, b),
    "PERCENT": lambda x: x / 100,
    "INT": lambda x: int(float(x)) if str(x).replace('.', '', 1).lstrip('-').isdigit() else 0,
    "VALUE": lambda x: float(x) if str(x).replace('.', '', 1).lstrip('-').isdigit() else 0.0,

  
    "IF": lambda cond, a, b: a if cond else b,

 
    "CONCAT": lambda *args: "".join(str(a) for a in args if a is not None),
    "TEXTJOIN": lambda sep, *args: sep.join(str(a) for a in args if a is not None),
    "LEFT": lambda text, n=1: str(text)[:int(n)],
    "RIGHT": lambda text, n=1: str(text)[-int(n):],
    "LEN": lambda text: len(str(text)),
    "LOWER": lambda text: str(text).lower(),
    "UPPER": lambda text: str(text).upper(),
    "TRIM": lambda text: str(text).strip(),

    "TEXT": lambda x, fmt=None: (
        x.strftime(fmt) if isinstance(x, (dt.date, dt.datetime)) and fmt else
        format(x, fmt) if fmt and isinstance(x, (int, float)) else
        str(x)
    ),
  
    "ETEXT": ETEXT,

    
    "TODAY": lambda: dt.date.today(),
    "NOW": lambda: dt.datetime.now(),
    "YEAR": lambda d: d.year if isinstance(d, (dt.date, dt.datetime)) else None,
    "MONTH": lambda d: d.month if isinstance(d, (dt.date, dt.datetime)) else None,
    "DAY": lambda d: d.day if isinstance(d, (dt.date, dt.datetime)) else None,
    "HOUR": lambda d: d.hour if isinstance(d, dt.datetime) else 0,
    "MINUTE": lambda d: d.minute if isinstance(d, dt.datetime) else 0,
    "SECOND": lambda d: d.second if isinstance(d, dt.datetime) else 0,
    "DATE": lambda y, m, d: dt.date(int(y), int(m), int(d)),
    "DATEDIF": lambda d1, d2: abs((d2 - d1).days) if all(isinstance(x, (dt.date, dt.datetime)) for x in (d1, d2)) else None,

    
    "np": np,
}


def register_func(name, func):
    GLOBAL_NS[name.upper()] = func








class CellWrapper:

    formula_pattern = re.compile(r"^=(.+)$") 

    def __init__(self, cell_model: CellModel):
        self.model = cell_model
        self.session = db.session

    # ----------------------------------------------------------
    # READ AND WRITE
    # ----------------------------------------------------------

    def read_data(self):
    
        return self.model.data or ""

    def write_data(self, value: str):
     
        self.model.data = value
        self.session.commit()

    # ----------------------------------------------------------
    # EVALUATE
    # ----------------------------------------------------------

    def evaluate(self):
   
        raw = self.read_data()

        # -----------------------------
        # 1) IF NOT FORMULA THEN TEXT
        # -----------------------------
        match = self.formula_pattern.match(raw)
        if not match:
            return raw or ""

        expr = match.group(1).strip()

        # -----------------------------
        # 2)IF THERE IS A FORMULA
        # -----------------------------
        return self._evaluate_formula(expr)

    # ----------------------------------------------------------
    # FORMULAS (minimal prototype)
    # ----------------------------------------------------------

    def _evaluate_formula(self, expr: str):
        import string

        # --- helper functions for ranges ---
        def col_to_index(col: str) -> int:
            # A -> 1, Z -> 26, AA -> 27
            col = col.upper()
            idx = 0
            for ch in col:
                if ch in string.ascii_uppercase:
                    idx = idx * 26 + (ord(ch) - ord("A") + 1)
            return idx

        def index_to_col(index: int) -> str:
            # 1 -> A, 27 -> AA
            result = ""
            while index > 0:
                index, rem = divmod(index - 1, 26)
                result = chr(rem + ord("A")) + result
            return result

        def split_cell(cell_name: str):
            m = re.match(r"^([A-Za-z]+)(\d+)$", cell_name)
            if not m:
                raise ValueError(f"Invalid cell name: {cell_name}")
            return m.group(1).upper(), int(m.group(2))

        def expand_range(a: str, b: str):
            # returns a list of cell names from a to b (incl.)
            col_a, row_a = split_cell(a)
            col_b, row_b = split_cell(b)

            c1 = col_to_index(col_a)
            c2 = col_to_index(col_b)
            r1 = row_a
            r2 = row_b

            cols = range(min(c1, c2), max(c1, c2) + 1)
            rows = range(min(r1, r2), max(r1, r2) + 1)

            cells = []
            for ci in cols:
                for ri in rows:
                    cells.append(f"{index_to_col(ci)}{ri}")
            return cells

        #--- 1) Processing ranges of the form A1:A3 ---
        # Find all occurrences of ranges and replace them with lists of values
        range_pattern = re.compile(r"([A-Za-z]+[0-9]+):([A-Za-z]+[0-9]+)")
        # make multiple passes to catch nested/multiple ranges
        while True:
            m = range_pattern.search(expr)
            if not m:
                break
            a, b = m.group(1), m.group(2)
            names = expand_range(a, b)

            vals = []
            for name in names:
                # find a cell, calculate it recursively
                cell = (
                    self.session.query(CellModel)
                    .filter_by(table_id=self.model.table_id,
                                list_id=self.model.list_id,
                                name=name)
                    .first()
                )
                if not cell:
                    vals.append(0)
                    continue
                wrap = CellWrapper(cell)
                v = wrap.evaluate()
                # attempt to cast to a number, otherwise leave it as a string
                try:
                    nv = float(v)
                except Exception:
                    # if the string is like a string (with quotes)
                    nv = v
                vals.append(nv)

            # We substitute the Python leaf into the expression:
            # strings should be reprs, numbers should be as is
            py_items = []
            for v in vals:
                if isinstance(v, (int, float)):
                    py_items.append(str(v))
                else:
                    # escape quotes correctly
                    py_items.append(repr(str(v)))
            list_literal = "[" + ",".join(py_items) + "]"

            # replace the first occurrence of the range with list_literal
            expr = expr[:m.start()] + list_literal + expr[m.end():]

        # --- 2) Now let's process simple links like A1, B2 ---
        tokens = re.findall(r"[A-Za-z]+[0-9]+", expr)

        # To avoid re-processing ranges and already substituted lists,
        # We use a dictionary, but do the replacement via regex with boundaries.
        values = {}

        for token in sorted(set(tokens), key=lambda s: -len(s)):
            # we skip cases where the token is already inside a list literal (for example [1,2,A1])
            if re.search(r"\[" + re.escape(token) + r"\]", expr):
                # already processed inside the list
                continue

            cell = (
                self.session.query(CellModel)
                .filter_by(table_id=self.model.table_id,
                            list_id=self.model.list_id,
                            name=token)
                .first()
            )

            if not cell:
                values[token] = 0
                continue

            wrap = CellWrapper(cell)
            val = wrap.evaluate()

            # if it’s a number, we’ll convert it to a float, otherwise we’ll leave it as a string
            try:
                numeric_val = float(val)
                values[token] = numeric_val
            except Exception:
                # string values ​​must be properly escaped when substituting
                values[token] = repr(str(val))

        # We carefully replace tokens (with boundaries) with their values
        expr_eval = expr
        for k, v in values.items():
            # if v is a number (int/float), insert it as is; if the string is v already repr
            if isinstance(v, (int, float)):
                repl = str(v)
            else:
                repl = v
            expr_eval = re.sub(rf"\b{re.escape(k)}\b", repl, expr_eval)

        # --- 3) Replace the operator ^ with ** (Excel power) ---
        # but we don’t change it inside the strings (simple approach - if there are quotes, leave the risk)
        expr_eval = expr_eval.replace("^", "**")

        # --- 4) Eval in a safe environment with GLOBAL_NS ---
        try:
            result = eval(expr_eval, {"__builtins__": {}}, GLOBAL_NS)
        except Exception:
            result = "#ERROR"

        return result







class ListWrapper:
    """
    Logical wrapper of the sheet.
    Works with models, recalculation, functions, reading/writing cells.
    """

    def __init__(self, list_model: ListModel):
        self.model = list_model
        self.session = db.session   #single session from session.py

    # ------------------------------------------
    # BASIC LIST OPERATIONS
    # ------------------------------------------

    def get_cell(self, name: str) -> CellModel | None:
        """Returns an ORM CellModel given the cell name."""
        return (
            self.session.query(CellModel)
            .filter_by(list_id=self.model.id, name=name)
            .first()
        )

    def read(self, name: str):
        """
        Returns the full contents of a cell:
        - value: calculated value
        - data: source text/formula
        - cell_id: hierarchical code (if any)
        - name: cell name (A1)
        """

        cell = self.get_cell(name)

        if not cell:
            return {
                "name": name,
                "value": "",
                "data": "",
                "cell_id": None
            }

        return {
            "name": cell.name,
            "value": cell.value if cell.value is not None else "",
            "data": cell.data if cell.data is not None else "",
            "cell_id": cell.cell_id
        }


    def write(self, cell_name: str, cell_id: str | None, data: str):
        """
        Record a cell with the ability to specify cell_id.
        If cell_id is not specified, the cell remains without a hierarchical code.
        """

        cell = self.get_cell(cell_name)

        # create if not
        if not cell:
            cell = CellModel(
                list_id=self.model.id,
                table_id=self.model.table_id,
                name=cell_name
            )
            self.session.add(cell)

        # the user wants to specify a hierarchical code
        if cell_id:
            cell.cell_id = cell_id

        # raw data (formula or text)
        cell.data = data

        #calculate value
        wrapper = CellWrapper(cell)
        try:
            cell.value = wrapper.evaluate()
        except:
            cell.value = "#ERROR"

        self.session.commit()
        return cell



    # ------------------------------------------
    # CALCULATION
    # ------------------------------------------

    def evaluate_cell(self, name: str):
        """Recalculate a specific cell."""
        cell = self.get_cell(name)
        if not cell:
            return None

        wrapper = CellWrapper(cell)
        try:
            result = wrapper.evaluate()
            cell.value = result
            self.session.commit()
            return result

        except Exception:
            cell.value = "#ERROR"
            self.session.commit()
            return "#ERROR"

    def recalc_all(self):
        """
        Recalculate all sheet cells.
        Complete replacement of the old recalc_all_safe().
        The logic now lies HERE, and not in the model.
        """
        for cell in self.model.cells:
            wrapper = CellWrapper(cell)
            try:
                value = wrapper.evaluate()
                cell.value = value
            except Exception:
                cell.value = "#ERROR"

        self.session.commit()

    # ------------------------------------------
    # STRATEGIC OPERATIONS
    # ------------------------------------------

    def get_all_cells(self):
        """Return all sheet cells (ORM objects)."""
        return self.model.cells

    def delete_cell(self, name: str):
        """Delete cell by name."""
        cell = self.get_cell(name)
        if cell:
            self.session.delete(cell)
            self.session.commit()

    def clear(self):
        """Delete all worksheet cells."""
        for cell in self.model.cells:
            self.session.delete(cell)
        self.session.commit()


    # ------------------------------------------
    #     GROUP OPERATIONS
    # ------------------------------------------


    def add_group(self, name: str, cell_names: list[str], style: str = ""):
        """
        Creates a group and adds to it:
        - single cells
        - ranges
        - ranges with spaces
        - reverse ranges
        """

        # 1) Create a group
        group = GroupModel(
            list_id=self.model.id,
            name=name,
            style=style,
        )
        db.session.add(group)
        db.session.commit()

        # 2) Many unique cells
        expanded = set()

        for expr in cell_names:
            expr = expr.strip()
            expanded.update(_expand_range(expr))

        # 3) Linking cells to a group
        if expanded:
            cells = (
                db.session.query(CellModel)
                .filter(
                    CellModel.list_id == self.model.id,
                    CellModel.name.in_(expanded)
                )
                .all()
            )

            for cell in cells:
                cell.group_id = group.id

            db.session.commit()

        return group


    


    def get_group(self, name: str):
        return (
            db.session.query(GroupModel)
            .filter_by(list_id=self.model.id, name=name)
            .first()
        )
    



    def update_group_style(self, name: str, style: str):
        group = self.get_group(name)
        if not group:
            return None

        group.style = style
        db.session.commit()

        for cell in group.cells:
            # if the cell does not have its own style
            if not cell.style:
                cell.style = style

        db.session.commit()
        return group
    


    def get_group_cells(self, name: str):
        group = self.get_group(name)
        if not group:
            return []

        return group.cells




    def delete_group(self, name: str):
        group = self.get_group(name)
        if not group:
            return None

        # clean bindings
        for cell in group.cells:
            cell.group_id = None

        db.delete(group)
        db.session.commit()
        return True
    



    

    # ------------------------------------------
    # CELL STYLE
    # ------------------------------------------


    def get_style(self, name: str) -> str:
        cell = self.get_cell(name)
        return cell.style if cell else ""
    


    def set_style(self, name: str, style: str):
        cell = self.get_cell(name)
        if not cell:
            return None
        cell.style = style
        self.session.commit()
        return cell
    


    def clear_style(self, name: str):
        cell = self.get_cell(name)
        if cell:
            cell.style = ""
            self.session.commit()
            

    # ------------------------------------------
    #     Note OPERATIONS
    # ------------------------------------------


    def get_note(self, name: str) -> str:
        cell = self.get_cell(name)
        return cell.note if cell else ""
    


    def set_note(self, name: str, note: str):
        cell = self.get_cell(name)
        if not cell:
            return None
        cell.note = note
        self.session.commit()
        return cell
    

    
    def clear_note(self, name: str):
        cell = self.get_cell(name)
        if cell:
            cell.note = None
            self.session.commit()

    

    # ------------------------------------------
    #     JSON OPERATIONS
    # ------------------------------------------


    def export_json(self):
        cells = (
            db.session.query(CellModel)
            .filter_by(list_id=self.model.id)
            .all()
        )

        result = {}

        for c in cells:
            result[c.name] = {
                "id": c.id,
                "name": c.name,
                "value": c.value,
                "data": c.data,
                "style": c.style or "",
                "note": c.note or "",
                "group": c.group_id,
                "cell_id": c.cell_id
            }

        return result
    


    def export_tree(self):
        """
        Иерархический JSON-экспорт на основе cell_id.
        Возвращает дерево вида:

        {
            "0000": {
                "0001": {
                    "0001": {
                        "0001": {...},
                        "0002": {...}
                    }
                }
            }
        }
        """

        cells = (
            db.session.query(CellModel)
            .filter_by(list_id=self.model.id)
            .all()
        )

        tree = {}

        for c in cells:

            # If the cell does not have a cell_id, skip it
            if not c.cell_id:
                continue

            levels = c.cell_id.split(".")  # ["0000","0001","0001","0003"]

            node = tree
            for lvl in levels[:-1]:
                if lvl not in node:
                    node[lvl] = {}
                node = node[lvl]

            # The last level is the cell itself
            last = levels[-1]
            node[last] = {
                "id": c.id,
                "name": c.name,
                "value": c.value,
                "data": c.data,
                "style": c.style or "",
                "note": c.note or "",
                "group": c.group_id,
                "cell_id": c.cell_id
            }

        # Sorting a tree by keys
        def sort_tree(node):
            if not isinstance(node, dict):
                return node
            return {
                key: sort_tree(node[key])
                for key in sorted(node.keys())
            }

        return sort_tree(tree)






    def export_flat(self):
        cells = (
            db.session.query(CellModel)
            .filter_by(list_id=self.model.id)
            .order_by(CellModel.id)
            .all()
        )

        return [
            {
                "id": c.id,
                "name": c.name,
                "value": c.value,
                "data": c.data,
                "style": c.style or "",
                "note": c.note or "",
                "group": c.group_id,
                "cell_id": c.cell_id
            }
            for c in cells
        ]


    def export(self, mode="json"):
        mode = mode.lower().strip()

        if mode == "json":
            return self.export_json()

        if mode == "flat":
            return self.export_flat()

        if mode == "tree":
            return self.export_tree()

        if mode == "all":
            return {
                "json": self.export_json(),
                "flat": self.export_flat(),
                "tree": self.export_tree(),
            }

        raise ValueError(f"Unknown export mode: {mode}")

    



class TableWrapper:
    """
    Wrapper around TableModel providing high-level list (sheet) operations.
    Clean, modern and SQLAlchemy-safe implementation.
    """

    def __init__(self, table_model: TableModel):
        self.model = table_model
        self.session = db.session

    # ==========================================================
    # INTERNAL UTILITIES
    # ==========================================================

    def _find_list(self, name: str) -> ListModel | None:
        """Return ListModel by name or None if not found."""
        return (
            self.session.query(ListModel)
            .filter_by(table_id=self.model.id, name=name)
            .first()
        )

    def _find_list_by_id(self, list_id: int) -> ListModel | None:
        """Return ListModel by primary key (safe SQLAlchemy 2.0)."""
        return self.session.get(ListModel, list_id)

    # ==========================================================
    # LIST ACCESSORS
    # ==========================================================

    def get_list(self, name: str) -> ListWrapper | None:
        """Return wrapper for existing sheet."""
        lst = self._find_list(name)
        return ListWrapper(lst) if lst else None

    def all_lists(self) -> list[ListWrapper]:
        """Return all sheets within this table."""
        return [ListWrapper(lst) for lst in self.model.lists]

    # ==========================================================
    # LIST CREATION / DELETION
    # ==========================================================

    def create_list(self, name: str, password: str | None = None) -> ListWrapper:
        """
        Create a new sheet if it doesn't exist.
        Password may be used later for protected sheets.
        """
        existing = self._find_list(name)
        if existing:
            return ListWrapper(existing)

        lst = ListModel(
            table_id=self.model.id,
            name=name,
            password=password
        )

        self.session.add(lst)
        self.session.commit()
        return ListWrapper(lst)

    def delete_list(self, name: str) -> bool:
        """Delete sheet by name. Returns True if removed."""
        lst = self._find_list(name)
        if not lst:
            return False

        self.session.delete(lst)
        self.session.commit()
        return True

    # ==========================================================
    # ACTIVE SHEET MANAGEMENT
    # ==========================================================

    def set_active_list(self, name: str) -> ListWrapper | None:
        """
        Set active sheet by name.
        The active sheet is stored inside the parent table model.
        """
        lst = self._find_list(name)
        if not lst:
            return None

        self.model.active_list_id = lst.id
        self.session.commit()

        return ListWrapper(lst)

    def get_active_list(self) -> ListWrapper | None:
        """Return wrapper for the currently active sheet."""
        if not self.model.active_list_id:
            return None

        lst = self._find_list_by_id(self.model.active_list_id)
        return ListWrapper(lst) if lst else None

    # ==========================================================
    # TABLE-LEVEL UTILITIES
    # ==========================================================

    def rename(self, new_name: str):
        """Rename the table."""
        self.model.name = new_name
        self.session.commit()

    def list_names(self) -> list[str]:
        """Return a list of all sheet names."""
        return [lst.name for lst in self.model.lists]

    def delete(self):
        """
        Delete this table entirely.
        Note: proper cascading requires SQLite foreign_keys=ON.
        """
        self.session.delete(self.model)
        self.session.commit()