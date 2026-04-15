from dataclasses import dataclass, field
from typing import List, Optional
import uuid

@dataclass
class Column:
    name: str
    type: str
    is_pk: bool = False
    is_not_null: bool = False

@dataclass
class Index:
    name: str
    columns: List[str]
    is_unique: bool = False

@dataclass
class Table:
    name: str
    columns: List[Column] = field(default_factory=list)
    indexes: List[Index] = field(default_factory=list)
    checks: List[str] = field(default_factory=list)
    is_view: bool = False
    # Координаты на сцене (заполняются контроллером/алгоритмом)
    x: float = 0.0
    y: float = 0.0
    # Стабильный ID для привязки связей и JSON
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def get_column_index(self, col_name: str) -> Optional[int]:
        for i, col in enumerate(self.columns):
            if col.name == col_name:
                return i
        return None

@dataclass
class Relationship:
    """Связь между колонками таблиц."""
    id: str
    src_table_id: str   # Таблица, где объявлен FOREIGN KEY
    src_col: str        # Колонка FK
    dst_table_id: str   # Целевая таблица
    dst_col: str        # Целевая колонка (обычно PK)
    on_delete: Optional[str] = None
    on_update: Optional[str] = None