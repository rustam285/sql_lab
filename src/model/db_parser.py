import re
import sqlite3
import logging
from typing import List, Tuple, Dict
from .entities import Table, Column, Relationship, Index

logger = logging.getLogger(__name__)

class SQLiteParser:
    SYSTEM_PREFIXES = ("sqlite_",)

    def parse(self, db_path: str) -> Tuple[List[Table], List[Relationship]]:
        tables: List[Table] = []
        relationships: List[Relationship] = []
        table_map: Dict[str, Table] = {}

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # 1. Получаем таблицы и Views (исключая системные)
            cursor.execute("""
                SELECT name, type FROM sqlite_master 
                WHERE type IN ('table', 'view') 
                AND name NOT LIKE 'sqlite_%'
                ORDER BY type, name
            """)
            entities = cursor.fetchall()

            for row in entities:
                table = self._parse_table(row["name"], row["type"] == "view", cursor)
                tables.append(table)

            table_map = {t.name: t for t in tables}

            # 2. Парсим внешние ключи
            for table in tables:
                if table.is_view:
                    continue  # Views не имеют FK в SQLite
                
                fks = cursor.execute(f"PRAGMA foreign_key_list('{table.name}')").fetchall()
                for fk in fks:
                    ref_table_name = fk["table"]
                    
                    # 2.1.b: Проверка на внешнюю БД или отсутствие таблицы
                    if ref_table_name not in table_map:
                        logger.warning(
                            f"[{table.name}] FK ссылается на отсутствующую/внешнюю таблицу: {ref_table_name}"
                        )
                        continue

                    relationships.append(Relationship(
                        id=f"{table.id}_{ref_table_name}_{fk['id']}_{fk['seq']}",
                        src_table_id=table.id,
                        src_col=fk["from"],
                        dst_table_id=table_map[ref_table_name].id,
                        dst_col=fk["to"],
                        on_delete=fk["on_delete"],
                        on_update=fk["on_update"]
                    ))
        finally:
            conn.close()

        return tables, relationships

    def _parse_table(self, name: str, is_view: bool, cursor: sqlite3.Cursor) -> Table:
        table = Table(name=name, is_view=is_view)
        
        # PRAGMA table_info: cid, name, type, notnull, dflt_value, pk
        pragma = cursor.execute(f"PRAGMA table_info('{name}')").fetchall()
        for col in pragma:
            # 2.1.c: Нетипизированные поля помечаем как (ANY)
            col_type = col["type"] if col["type"] else "(ANY)"
            table.columns.append(Column(
                name=col["name"],
                type=col_type,
                is_pk=bool(col["pk"]),
                is_not_null=bool(col["notnull"])
            ))
        return table