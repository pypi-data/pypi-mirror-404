# pycells_mds/models.py

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, ForeignKey,
    DateTime, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from .session import Base


# ========================== USERS ===========================

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    tables = relationship(
        "TableModel",
        back_populates="author",
        cascade="all, delete"
    )






# ============================ LISTS ============================

class ListModel(Base):
    __tablename__ = "pycells_lists"

    id = Column(Integer, primary_key=True)
    table_id = Column(Integer, ForeignKey("pycells_tables.id", ondelete="CASCADE"))
    name = Column(String(50))
    password = Column(String(255), nullable=True)
    style = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    table = relationship(
        "TableModel",
        back_populates="lists",
        foreign_keys=[table_id]   
    )

    cells = relationship(
        "CellModel",
        back_populates="list",
        cascade="all, delete"
    )

    groups = relationship(
        "GroupModel",
        back_populates="list",
        cascade="all, delete"
    )

    __table_args__ = (
        UniqueConstraint("table_id", "name", name="_list_name_uc"),
    )





# ============================ TABLES ============================

class TableModel(Base):
    __tablename__ = "pycells_tables"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    password = Column(String(255), nullable=True)
    style = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    visible_name_in_search = Column(Boolean, default=True)

    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("UserModel", back_populates="tables")

    # Активный лист
    active_list_id = Column(
        Integer,
        ForeignKey("pycells_lists.id", ondelete="SET NULL"),
        nullable=True
    )
    active_list = relationship(
        "ListModel",
        foreign_keys=[active_list_id]
    )

    # Все листы таблицы
    lists = relationship(
        "ListModel",
        back_populates="table",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys=[ListModel.table_id]
    )

    __table_args__ = (
        UniqueConstraint('author_id', 'name', name='uix_user_table_name'),
    )



# ============================ CELLS ============================

class CellModel(Base):
    __tablename__ = "pycells_cells"

    id = Column(Integer, primary_key=True)
    table_id = Column(Integer, ForeignKey("pycells_tables.id"))
    list_id = Column(Integer, ForeignKey("pycells_lists.id"))
    cell_id = Column(String(255), nullable=True, unique=True)
    name = Column(String(50), nullable=False)
    data = Column(Text, nullable=True)   # raw formula / text
    value = Column(Text, nullable=True)  # calculated value
    style = Column(Text, default="wrap:yes;")
    note = Column(Text, nullable=True)

    group_id = Column(Integer, ForeignKey("pyt_tab_groups.id"), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    list = relationship("ListModel", back_populates="cells")
    group = relationship("GroupModel", back_populates="cells")

    __table_args__ = (
        UniqueConstraint("list_id", "name", name="_cell_name_uc"),
    )


# ============================ GROUPS ============================

class GroupModel(Base):
    __tablename__ = "pyt_tab_groups"

    id = Column(Integer, primary_key=True)
    list_id = Column(Integer, ForeignKey("pycells_lists.id"))
    name = Column(String(50))
    style = Column(Text, default="")
    datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    list = relationship("ListModel", back_populates="groups")
    cells = relationship("CellModel", back_populates="group")


# ============================ CURSORS ============================

class CursorModel(Base):
    __tablename__ = "pyttabs_cursors"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    table_id = Column(Integer, ForeignKey("pycells_tables.id"))
    list_id = Column(Integer, ForeignKey("pycells_lists.id"))
    cells = Column(JSON)  # список выделенных ячеек
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    table = relationship("TableModel")
    list = relationship("ListModel")
