import json
import logging
from pathlib import Path
from typing import List, Optional, Dict
from .entities import Table, Relationship

logger = logging.getLogger(__name__)

class GraphModel:
    def __init__(self):
        self.tables: List[Table] = []
        self.relationships: List[Relationship] = []
        self._index: Dict[str, Table] = {}

    def load_data(self, tables: List[Table], relationships: List[Relationship]):
        """Загрузка данных из парсера."""
        self.tables = tables
        self.relationships = relationships
        self._index = {t.id: t for t in self.tables}

    def get_table_by_id(self, table_id: str) -> Optional[Table]:
        return self._index.get(table_id)

    def get_table_by_name(self, name: str) -> Optional[Table]:
        for t in self.tables:
            if t.name == name:
                return t
        return None

    def update_position(self, table_id: str, x: float, y: float):
        """Обновление координат при Drag & Drop."""
        if table_id in self._index:
            self._index[table_id].x = x
            self._index[table_id].y = y

    def save_layout(self, db_path: str) -> Path:
        """Сохранение координат в JSON (п. 2.4.1)"""
        layout_path = Path(db_path).with_suffix(".layout.json")
        data = {t.id: {"x": t.x, "y": t.y} for t in self.tables}
        layout_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info(f"Макет сохранен: {layout_path.name}")
        return layout_path

    def load_layout(self, db_path: str) -> bool:
        """Восстановление координат из JSON."""
        layout_path = Path(db_path).with_suffix(".layout.json")
        if not layout_path.exists():
            return False
        
        try:
            data = json.loads(layout_path.read_text(encoding="utf-8"))
            for t in self.tables:
                if t.id in data:
                    t.x = float(data[t.id]["x"])
                    t.y = float(data[t.id]["y"])
            logger.info(f"Макет восстановлен: {layout_path.name}")
            return True
        except Exception as e:
            logger.error(f"Ошибка загрузки макета: {e}")
            return False

    def get_relationships_for_table(self, table_id: str):
        """Вспомогательный метод для подсветки связей."""
        incoming = [r for r in self.relationships if r.dst_table_id == table_id]
        outgoing = [r for r in self.relationships if r.src_table_id == table_id]
        return incoming, outgoing