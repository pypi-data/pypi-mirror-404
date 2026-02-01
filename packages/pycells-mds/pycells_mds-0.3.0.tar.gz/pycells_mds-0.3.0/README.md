<p align="center">
  <a href="https://pycells.com">
    <img src="https://pycells.com/assets/img/logo.png" width="600" alt="PyCells logo">
  </a>
</p>



# pycells_mds

**Multidimensional Data Structures**

---

## 🔍 Overview

PyCells MDS is a Python library for spreadsheet-like multidimensional data structures with hierarchical addressing.  
It supports Excel-style formulas, programmable cells, cell groups, hierarchical `cell_id`, JSON export, and a full Python API.

PyCells can be used to build accounting systems, warehouse structures, CRM/ERP modules, and dynamic spreadsheet engines.

---

## ✨ Features

- Tables and sheets
- Named cells (A1, B2, …)
- Hierarchical `cell_id` (e.g. `0000.0001.0001.0003`)
- Automatic recalculation engine
- Excel-style formulas
- Ranges (`A1:A10`)
- Built-in function set (`SUM`, `IF`, `UPPER`, etc.)
- Cell groups
- Notes and styles
- JSON / FLAT / TREE export
- Select queries
- Cursor manager (Redis + SQL optional)
- SQLite / PostgreSQL support

---

## 🛠 Installation

```bash
pip install pycells_mds
```

### Requirements

```bash
Python 3.9+

fastapi

SQLAlchemy

NumPy

Redis (optional, CursorManager)
```
---

## 🚀 Quick Start

### 1) Initialize database

```bash
from pycells_mds.session import init_db
from pycells_mds.core import PyCells

init_db({
    "engine": "sqlite",
    "path": "my_cells.db"
})

pc = PyCells()
print("Database connected.")
```

### 2) Register user

```bash
user = pc.safe_register_user("user1", "pw123", "user1@example.com")
user_id = user.id
```
### 3) Create table and sheet

```bash
tbl = pc.ctable("Finance", user_id)
sheet = pc.get_or_create_list("Finance", "Main", user_id)
```

### 🔢 Writing and Reading Cells

### New API (with hierarchical cell_id)

```bash
pc.write(
    table="Finance",
    sheet="Main",
    cell_name="A1",
    cell_id="0000.0001.0001.0001",
    data="100",
    user_id=user_id
)

pc.write("Finance", "Main", "A2", "0000.0001.0001.0002", "200", user_id)
pc.write("Finance", "Main", "A3", "0000.0001.0001.0003", "=A1+A2", user_id)

print(pc.read("Finance", "Main", "A3", user_id))


# → 300.0
```
### Read with full cell info

```bash
value = pc.read("Finance", "Main", "A1", user_id)

# returns dict:
# { "name": "A1", "value": "100", "data": "100", "cell_id": "0000.0001.0001.0001" }
```

### 📦 Export

### JSON export (dictionary)

```bash
json_data = pc.export("Finance", "Main", mode="json", user_id=user_id)

print(json_data)
```

### Result:

```bash
{
    "A1": {"id": 1, "name": "A1", "value": "100", "data": "100", "cell_id": "0000.0001.0001.0001"},
    "A2": {...}
}
```

### FLAT export (list)
```bash
flat = pc.export("Finance", "Main", mode="flat", user_id=user_id)
```

### Example:

```bash
[
    {"id": 1, "name": "A1", ...},
    {"id": 2, "name": "A2", ...}
]
```

### TREE export (hierarchical by cell_id)

```bash
tree = pc.export_tree("Finance", "Main", user_id)
```

### Example:

```bash
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
```

## 🔢 Formulas

### Supported operators
___
### ( + ) , ( - ) , ( * ) ,  ( / ) , ( ^ ) , ( % )
___

### Supported constructs


- #### ranges (A1:A10)

- #### nested formulas

- #### built-in functions

- #### SUM, MAX, MIN, AVERAGE

- #### ABS, ROUND, POWER

- #### INT, VALUE

- #### UPPER, LOWER, CONCAT, TEXTJOIN

- #### IF

- #### TODAY, NOW, DATE, YEAR, MONTH, DAY

- ### TEXT

- #### ETEXT — Exel notation text

- #### np.* — NumPy access for ranges

### Example:

```bash
pc.write("Finance", "Main", "B1", "=SUM(A1:A3)", user_id)
pc.write("Finance", "Main", "B2", "=A1^A2", user_id)
```

## 🎯 Groups

### Create group

```bash
sheet.add_group("Totals", ["A1", "A2", "A3"], style="color:red;")
```

### Get group cells

```bash
cells = sheet.get_group_cells("Totals")
print([c.name for c in cells])
```

### Update style

```bash
sheet.update_group_style("Totals", "background:yellow;")
```

### Delete group

```bash
sheet.delete_group("Totals")
```

## 🖱 CursorManager (optional)

```bash
from pycells_mds.managers import CursorManager

CursorManager.set_cursor(
    user_id=user_id,
    table_id=sheet.model.table_id,
    list_id=sheet.model.id,
    cells=["A1", "A2"]
)
```

### CursorManager.get_active(user_id)



## 🔄 Recalculation

```bash
pc.recalc("Finance", "Main", user_id)
📄 Select cells

result = pc.select("Finance", "Main", "A1", "A3", "C1", user_id=user_id)
```

### Returns:

```bash
{
  "A1": {"name": "A1", "value": "100", ...},
  "A3": {...},
  "C1": {...}
}
```

## 🌐 Backup / Restore

### Backup (JSON)

```bash
data = pc.export("Finance", "Main", "json", user_id)
```
### Restore

```bash
for name, c in data.items():
    pc.write("Finance", "Main", name, c["cell_id"], c["data"], user_id)
```

## 📡 FastAPI Integration

### Run API server

```bash
pip install pycells_mds
pycells_api
```

### Or manually:

```bash
uvicorn pycells_api.main:app --host 0.0.0.0 --port 8000
```


### PyCells works perfectly as a backend engine behind FastAPI.
### Typical endpoints:

- /write

- /read

- /export/json

- /export/tree

- /recalc

## 🧩 Use Cases

- Accounting structures (plan of accounts)

- Warehouse hierarchy

- Financial models

- CRM/ERP spreadsheets

- Document engines

- Structured multidimensional data

## Run demo (Tk)

```bash
pycells_demo_tk
```


## 📜 License

- Versions < 1.0.0 are licensed under the MIT License
- Versions >= 1.0.0 are distributed under a commercial license

## 📞 Contact

### Email: zhandos.mambetali@gmail.com
### WhatsApp: +7 701 457 7360

---