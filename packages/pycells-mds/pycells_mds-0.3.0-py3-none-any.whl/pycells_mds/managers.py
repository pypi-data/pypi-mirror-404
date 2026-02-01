# pycells_mds/managers.py

import json
from datetime import datetime, timezone
from redis import Redis

from pycells_mds.session import db, RANGE_RE, _expand_range
from pycells_mds.models import CursorModel, TableModel, ListModel
from pycells_mds.wrappers import ListWrapper

r = Redis(host="localhost", port=6379, decode_responses=True)




class CursorManager:
    """Hybrid cursor manager: Redis (active) + SQL (history)."""

    @staticmethod
    def _redis_key(user_id): return f"cursor:{user_id}"
    @staticmethod
    def _prec_redis_key(user_id): return f"prec_cursor:{user_id}"

    # ---------------------------------------------------------
    # RANGE EXPANSION FOR CURSORS
    # ---------------------------------------------------------

    @classmethod
    def _expand_cells(cls, cells):
        """Expand A1:A5 → ['A1','A2','A3','A4','A5']"""
        out = []
        for expr in cells:
            expr = expr.strip().upper().replace(" ", "")
            if RANGE_RE.match(expr):
                out.extend(_expand_range(expr))
            else:
                out.append(expr)
        return out

    # ---------------------------------------------------------
    # SET CURSOR
    # ---------------------------------------------------------

    @classmethod
    def set_cursor(cls, user_id: int, table: str, list_name: str, cells: list[str]):
        """
        Example:
            set_cursor(1, "Finance", "Main", ["A1","A2"])
            set_cursor(1, "Finance", "Main", ["A1:A10"])
        """

        table_obj = (
            db.session.query(TableModel)
            .filter_by(name=table, author_id=user_id)
            .first()
        )
        if not table_obj:
            raise ValueError("Table not found")

        list_obj = (
            db.session.query(ListModel)
            .filter_by(table_id=table_obj.id, name=list_name)
            .first()
        )
        if not list_obj:
            raise ValueError("List not found")

        # expand ranges
        cells = cls._expand_cells(cells)

        # shift active → previous
        current = cls.get_active(user_id)
        if current:
            r.set(cls._prec_redis_key(user_id), json.dumps(current))

        return cls.activate(
            user_id=user_id,
            table_id=table_obj.id,
            list_id=list_obj.id,
            table_name=table,
            list_name=list_name,
            cells=cells
        )

    # ---------------------------------------------------------
    # ACTIVATE CURSOR
    # ---------------------------------------------------------

    @classmethod
    def activate(cls, user_id, table_id, list_id, table_name, list_name, cells):
        now = datetime.now(timezone.utc)

        data = {
            "user_id": user_id,
            "table": table_name,
            "list": list_name,
            "table_id": table_id,
            "list_id": list_id,
            "cells": cells,
            "timestamp": now.isoformat()
        }

        r.set(cls._redis_key(user_id), json.dumps(data))

        # SQL history
        cursor = CursorModel(
            user_id=user_id,
            table_id=table_id,
            list_id=list_id,
            cells=cells,
            created_at=now
        )
        db.session.add(cursor)
        db.session.commit()

        return data

    # ---------------------------------------------------------
    # READ CURSOR
    # ---------------------------------------------------------

    @classmethod
    def get_active(cls, user_id: int):
        raw = r.get(cls._redis_key(user_id))
        return json.loads(raw) if raw else None

    @classmethod
    def get_prec_cursor(cls, user_id: int):
        raw = r.get(cls._prec_redis_key(user_id))
        return json.loads(raw) if raw else None

    @classmethod
    def get_previous(cls, user_id: int):
        cursors = (
            db.session.query(CursorModel)
            .filter(CursorModel.user_id == user_id)
            .order_by(CursorModel.id.desc())
            .limit(2)
            .all()
        )
        return cursors[1] if len(cursors) == 2 else None

    # ---------------------------------------------------------
    # CLEAN
    # ---------------------------------------------------------

    @classmethod
    def clear(cls, user_id: int):
        r.delete(cls._redis_key(user_id))
        r.delete(cls._prec_redis_key(user_id))
        db.session.query(CursorModel).filter_by(user_id=user_id).delete()
        db.session.commit()