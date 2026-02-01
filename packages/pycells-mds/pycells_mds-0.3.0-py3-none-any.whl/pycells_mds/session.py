# pycells_mds/session.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import re

Base = declarative_base()



class DB:
    engine = None
    Session = None
    session = None


db = DB()   # ВСЕ модули будут использовать ОДИН ОБЪЕКТ


def init_db(cfg: dict):
    engine = cfg.get("engine", "sqlite")

    # --- SQLite ---
    if engine == "sqlite":
        path = cfg.get("path", "pycells.db")
        url = f"sqlite:///{path}"

    # --- Postgres ---
    elif engine == "postgres":
        user = cfg.get("user", "")
        password = cfg.get("password", "")
        host = cfg.get("host", "localhost")
        port = cfg.get("port", 5432)
        dbname = cfg.get("dbname", "postgres")
        url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"

    else:
        raise ValueError(f"Unsupported engine: {engine}")

    # создаём движок
    db.engine = create_engine(url, echo=False)

    # создаём таблицы
    Base.metadata.create_all(db.engine)

    # создаём фабрику сессий
    db.Session = sessionmaker(bind=db.engine)

    # создаём первую сессию
    db.session = db.Session()

    return db.session




RANGE_RE = re.compile(
    r"^\s*([A-Za-z]+)(\d+)\s*:\s*([A-Za-z]+)(\d+)\s*$"
)


def _col_to_int(col: str) -> int:
    """А → 1, Z → 26, AA → 27, AB → 28 ..."""
    col = col.upper()
    n = 0
    for c in col:
        n = n * 26 + (ord(c) - 64)
    return n


def _int_to_col(n: int) -> str:
    """1 → A, 26 → Z, 27 → AA, 28 → AB ..."""
    result = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result



def _expand_range(expr: str) -> list[str]:
    """
    Расширяет диапазон:
      'A1:C3' → ['A1','A2','A3','B1','B2','B3','C1','C2','C3']

    Поддержка:
      - пробелы: 'A1 : C5'
      - нижний регистр: 'a1:c3'
      - реверс: 'C5:A1'
      - мусор: '  a10 :   c2  '
    """

    expr = expr.strip()

    m = RANGE_RE.match(expr)
    if not m:
        # не диапазон — возможно одиночная ячейка
        expr = expr.replace(" ", "").upper()
        if re.fullmatch(r"[A-Z]+[0-9]+", expr):
            return [expr]
        return []   # мусор → пустой список

    col1, row1, col2, row2 = m.groups()

    col1 = col1.upper()
    col2 = col2.upper()

    row1 = int(row1)
    row2 = int(row2)

    c1 = _col_to_int(col1)
    c2 = _col_to_int(col2)

    # поддержка реверса (если C5:A1)
    col_start = min(c1, c2)
    col_end   = max(c1, c2)

    row_start = min(row1, row2)
    row_end   = max(row1, row2)

    result = []

    for c in range(col_start, col_end + 1):
        col_name = _int_to_col(c)
        for r in range(row_start, row_end + 1):
            result.append(f"{col_name}{r}")

    return result