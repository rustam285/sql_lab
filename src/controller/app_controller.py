import sqlite3
from PySide6.QtCore import QObject, QSize, QRectF, Slot
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtSvg import QSvgGenerator
from PySide6.QtGui import QPainter, QPixmap, QColor, QStandardItemModel, QStandardItem, QUndoStack, QUndoCommand
from pathlib import Path
import logging

from src.model.db_parser import SQLiteParser
from src.model.graph_model import GraphModel
from src.view.items.edge_item import EdgeItem
from src.utils.layout_engine import apply_sugiyama_layout

logger = logging.getLogger(__name__)

class AppController(QObject):
    def __init__(self, model: GraphModel, scene, window):
        super().__init__()
        self.model = model
        self.scene = scene
        self.window = window
        self.db_path = None
        self.undo_stack = QUndoStack(self)
        self.query_templates = [
            {"key": "a", "label": "a. Два поля", "cols": 2, "condition": False},
            {"key": "b", "label": "b. DISTINCT по одному полю", "cols": 1, "condition": False},
            {"key": "c", "label": "c. GROUP BY + HAVING", "cols": 1, "condition": False},
            {"key": "d", "label": "d. SUM по одному полю", "cols": 2, "condition": False},
            {"key": "e", "label": "e. Несколько полей, сортировка DESC", "cols": 3, "condition": False},
            {"key": "f", "label": "f. Арифметическое выражение", "cols": 2, "condition": False},
            {"key": "g", "label": "g. SUM + BETWEEN", "cols": 2, "condition": True},
            {"key": "h", "label": "h. AVG + WHERE", "cols": 2, "condition": True},
            {"key": "i", "label": "i. Три поля + вычисление + сортировка", "cols": 2, "condition": False},
            {"key": "j", "label": "j. LIKE", "cols": 1, "condition": True},
            {"key": "k", "label": "k. Условие + константа + сортировка", "cols": 2, "condition": True},
            {"key": "l", "label": "l. MIN и MAX", "cols": 1, "condition": False},
            {"key": "m", "label": "m. Сложное условие AND/OR", "cols": 3, "condition": True}
        ]
        
        self._wire_ui()

    def _wire_ui(self):
        # === ФАЙЛ ===
        act_open = self.window.menu_file.addAction("&Открыть БД...")
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self.open_db)

        act_save = self.window.menu_file.addAction("&Сохранить макет")
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self.save_layout)

        act_export = self.window.menu_file.addAction("&Экспорт PNG/SVG...")
        act_export.setShortcut("Ctrl+E")
        act_export.triggered.connect(self.export_diagram)

        self.window.menu_file.addSeparator()
        act_exit = self.window.menu_file.addAction("В&ыход")
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.window.close)

        # === ВИД ===
        act_zoom_in = self.window.menu_view.addAction("&Увеличить")
        act_zoom_in.setShortcut("Ctrl++")
        act_zoom_in.triggered.connect(self.zoom_in)

        act_zoom_out = self.window.menu_view.addAction("&Уменьшить")
        act_zoom_out.setShortcut("Ctrl+-")
        act_zoom_out.triggered.connect(self.zoom_out)

        act_fit = self.window.menu_view.addAction("&Вписать в окно")
        act_fit.setShortcut("Ctrl+0")
        act_fit.triggered.connect(self.fit_to_view)

        act_center = self.window.menu_view.addAction("Центрировать выделенное")
        act_center.setShortcut("Ctrl+Shift+C")
        act_center.triggered.connect(self.center_on_selected)

        act_layout = self.window.menu_view.addAction("&Авто-раскладка")
        act_layout.setShortcut("Ctrl+L")
        act_layout.triggered.connect(self.apply_layout)

        act_undo = self.window.menu_view.addAction("&Отменить")
        act_undo.setShortcut("Ctrl+Z")
        act_undo.triggered.connect(self.undo_stack.undo)

        act_redo = self.window.menu_view.addAction("&Вернуть")
        act_redo.setShortcut("Ctrl+Y")
        act_redo.triggered.connect(self.undo_stack.redo)

        act_grid = self.window.menu_view.addAction("Показывать &сетку")
        act_grid.setCheckable(True)
        act_grid.setChecked(True)
        act_grid.triggered.connect(self.scene.toggle_grid)

        # === ПОИСК ===
        self.window.search_box.returnPressed.connect(self.search_table)
        self.window.table_combo.currentTextChanged.connect(self.load_table_data)
        self.window.refresh_button.clicked.connect(self.load_table_data)
        self.window.query_table_combo.currentTextChanged.connect(self.on_query_table_changed)
        self.window.query_combo.currentTextChanged.connect(self.on_query_type_changed)
        self.window.query_col1.currentTextChanged.connect(self.update_query_preview)
        self.window.query_col2.currentTextChanged.connect(self.update_query_preview)
        self.window.query_col3.currentTextChanged.connect(self.update_query_preview)
        self.window.query_condition_edit.textChanged.connect(self.update_query_preview)
        self.window.run_query_button.clicked.connect(self.execute_fixed_query)
        
        # === СЦЕНА ===
        self.scene.tableMoved.connect(self.model.update_position)
        if hasattr(self.scene, 'positionMoveFinished'):
            self.scene.positionMoveFinished.connect(self.on_table_move_finished)
        if hasattr(self.window.view, 'viewportChanged'):
            self.window.view.viewportChanged.connect(self.window.minimap._update_viewport_rect)

    @Slot()
    def open_db(self):
        path, _ = QFileDialog.getOpenFileName(self.window, "Открыть SQLite БД", "", "SQLite (*.db *.sqlite)")
        if not path: return
        
        self.db_path = path
        self.scene.clear()
        self.scene.edges.clear()
        
        parser = SQLiteParser()
        tables, rels = parser.parse(path)
        self.model.load_data(tables, rels)
        
        if not self.model.load_layout(path):
            apply_sugiyama_layout(self.model)
            
        self._render_scene()
        self._populate_table_combo()
        self.model.save_layout(path)
        self.window.minimap._update_viewport_rect()
        self.window.status_label.setText(f"БД: {Path(path).name} | Таблиц: {len(tables)} | Связей: {len(rels)}")

    def _render_scene(self):
        item_map = {}
        for table in self.model.tables:
            item = self.scene.add_table(table)
            item_map[table.id] = item
            
        for rel in self.model.relationships:
            src = item_map.get(rel.src_table_id)
            dst = item_map.get(rel.dst_table_id)
            if src and dst:
                self.scene.add_edge(EdgeItem(rel, src, dst))

    def save_layout(self):
        if not self.db_path:
            QMessageBox.warning(self.window, "Внимание", "Сначала откройте базу данных.")
            return
        self.model.save_layout(self.db_path)
        self.window.status_label.setText("Макет сохранен.")

    def _populate_table_combo(self):
        self.window.table_combo.clear()
        self.window.query_table_combo.clear()
        for table in self.model.tables:
            self.window.table_combo.addItem(table.name)
            self.window.query_table_combo.addItem(table.name)
        if self.window.table_combo.count() > 0:
            self.window.table_combo.setCurrentIndex(0)
            self.load_table_data()
        if self.window.query_table_combo.count() > 0:
            self.window.query_table_combo.setCurrentIndex(0)
            self._populate_query_templates()
            self.on_query_table_changed(self.window.query_table_combo.currentText())

    def _populate_query_templates(self):
        self.window.query_combo.clear()
        for tmpl in self.query_templates:
            self.window.query_combo.addItem(tmpl["label"], tmpl["key"])

    def _populate_query_columns(self, table_name: str):
        self.window.query_col1.clear()
        self.window.query_col2.clear()
        self.window.query_col3.clear()
        table = self.model.get_table_by_name(table_name)
        if not table:
            return
        for col in table.columns:
            self.window.query_col1.addItem(col.name)
            self.window.query_col2.addItem(col.name)
            self.window.query_col3.addItem(col.name)
        self.update_query_preview()

    def on_query_table_changed(self, table_name: str):
        self._populate_query_columns(table_name)

    def on_query_type_changed(self, _text: str):
        self.update_query_preview()

    def update_query_preview(self):
        query = self._build_query(
            self.window.query_combo.currentData(),
            self.window.query_table_combo.currentText(),
            self.window.query_col1.currentText(),
            self.window.query_col2.currentText(),
            self.window.query_col3.currentText(),
            self.window.query_condition_edit.text().strip()
        )
        self.window.query_preview.setPlainText(query)

    def execute_fixed_query(self):
        if not self.db_path:
            QMessageBox.warning(self.window, "Ошибка", "Откройте базу данных перед выполнением запроса.")
            return
        query = self.window.query_preview.toPlainText().strip()
        if not query:
            QMessageBox.warning(self.window, "Ошибка", "Выберите запрос и заполните параметры.")
            return
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            headers = rows[0].keys() if rows else []
        except Exception as exc:
            QMessageBox.warning(self.window, "Ошибка", f"Ошибка при выполнении запроса: {exc}")
            return
        finally:
            conn.close()

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(list(headers))
        for row in rows:
            items = [QStandardItem(str(row[col])) for col in headers]
            model.appendRow(items)
        self.window.query_result_table.setModel(model)
        self.window.status_label.setText(f"Выполнен запрос: {self.window.query_combo.currentText()}")

    def _build_query(self, key, table, col1, col2, col3, cond):
        if not table:
            return ""
        safe = lambda s: s if s else ""
        c1 = safe(col1)
        c2 = safe(col2)
        c3 = safe(col3)
        condition = cond or ""
        if key == "a":
            return f"SELECT {c1}, {c2} FROM \"{table}\""
        if key == "b":
            return f"SELECT DISTINCT {c1} FROM \"{table}\""
        if key == "c":
            return f"SELECT {c1}, COUNT(*) AS count FROM \"{table}\" GROUP BY {c1} HAVING COUNT(*) > 1"
        if key == "d":
            return f"SELECT {c1}, SUM({c2}) AS total FROM \"{table}\" GROUP BY {c1}"
        if key == "e":
            return f"SELECT {c1}, {c2}, {c3} FROM \"{table}\" ORDER BY {c1} DESC"
        if key == "f":
            return f"SELECT {c1}, {c2}, CAST({c1} AS REAL) + CAST({c2} AS REAL) AS computed FROM \"{table}\""
        if key == "g":
            between = condition or "0 AND 100"
            return f"SELECT {c1}, SUM({c2}) AS total FROM \"{table}\" WHERE {c1} BETWEEN {between} GROUP BY {c1}"
        if key == "h":
            where = condition or "1=1"
            return f"SELECT {c1}, AVG({c2}) AS avg_val FROM \"{table}\" WHERE {where} GROUP BY {c1}"
        if key == "i":
            return f"SELECT {c1}, {c2}, CAST({c1} AS REAL) + CAST({c2} AS REAL) AS computed FROM \"{table}\" ORDER BY {c1} DESC, {c2} ASC, computed DESC"
        if key == "j":
            like = condition or "%"
            if not (like.startswith("%") or like.endswith("%")):
                like = f"%{like}%"
            return f"SELECT * FROM \"{table}\" WHERE {c1} LIKE '{like}'"
        if key == "k":
            value = condition or "value"
            return f"SELECT {c1}, {c2}, '{value}' AS note FROM \"{table}\" WHERE {c1} = '{value}' ORDER BY {c2} DESC"
        if key == "l":
            return f"SELECT MIN({c1}) AS min_value, MAX({c1}) AS max_value FROM \"{table}\""
        if key == "m":
            condition = condition or f"{c2} > 0 OR {c3} < 0"
            return f"SELECT * FROM \"{table}\" WHERE {c1} = 1 AND ({condition}) ORDER BY {c1} DESC, {c2} ASC"
        return ""

    def load_table_data(self):
        if not self.db_path:
            return
        table_name = self.window.table_combo.currentText()
        if not table_name:
            return

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            headers = [row["name"] for row in cursor.fetchall()]
            cursor.execute(f"SELECT * FROM \"{table_name}\" LIMIT 200")
            rows = cursor.fetchall()
        except Exception as exc:
            QMessageBox.warning(self.window, "Ошибка", f"Не удалось загрузить данные: {exc}")
            return
        finally:
            conn.close()

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(headers)
        for row in rows:
            items = [QStandardItem(str(row[column])) for column in headers]
            model.appendRow(items)
        self.window.data_table.setModel(model)
        self.window.status_label.setText(f"Показаны данные таблицы: {table_name} ({len(rows)} строк)")

    def apply_layout(self):
        if not self.model.tables: return
        apply_sugiyama_layout(self.model)
        self.scene.clear()
        self.scene.edges.clear()
        self._render_scene()
        self.model.save_layout(self.db_path)
        self.window.minimap._update_viewport_rect()
        self.window.status_label.setText("Авто-раскладка применена.")

    def on_table_move_finished(self, table_id, old_x, old_y, new_x, new_y):
        if old_x == new_x and old_y == new_y:
            return
        command = TableMoveCommand(
            table_id,
            old_x, old_y,
            new_x, new_y,
            self.scene,
            self.model
        )
        self.undo_stack.push(command)
        self.window.status_label.setText("Перемещение таблицы добавлено в историю.")

    def zoom_in(self):
        self.window.view.scale(1.25, 1.25)
        self.window.view.viewportChanged.emit()
        self.window.status_label.setText("Увеличено.")

    def zoom_out(self):
        self.window.view.scale(0.8, 0.8)
        self.window.view.viewportChanged.emit()
        self.window.status_label.setText("Уменьшено.")

    def fit_to_view(self):
        self.window.view.fit_to_view()
        self.window.status_label.setText("Вписано в окно.")

    def center_on_selected(self):
        selected = self.scene.selectedItems()
        if not selected:
            self.window.status_label.setText("Выделите таблицу для центрирования.")
            return
        item = selected[0]
        self.window.view.centerOn(item)
        self.window.status_label.setText("Центрировано выделенное.")

    def search_table(self):
        query = self.window.search_box.text().strip().lower()
        if not query:
            return
        for t in self.model.tables:
            if query in t.name.lower():
                item = self.scene.get_item(t.id)
                if item:
                    self.scene.clearSelection()
                    item.setSelected(True)
                    self.window.view.centerOn(item)
                    self.window.status_label.setText(f"Найдено: {t.name}")
                return
        self.window.status_label.setText("Таблица не найдена.")

    def export_diagram(self):
        if not self.scene.items():
            QMessageBox.information(self.window, "Экспорт", "Диаграмма пуста.")
            return

        path, _ = QFileDialog.getSaveFileName(self.window, "Экспорт диаграммы", "", "PNG (*.png);;SVG (*.svg)")
        if not path:
            return

        rect = self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50)
        if rect.isNull() or rect.width() <= 0 or rect.height() <= 0:
            QMessageBox.information(self.window, "Экспорт", "Нечего экспортировать.")
            return

        target_width = int(rect.width())
        target_height = int(rect.height())
        export_scale = max(1, min(4, 1200 // max(target_width, target_height)))
        if export_scale == 0:
            export_scale = 1
        output_size = QSize(int(target_width * export_scale), int(target_height * export_scale))

        if path.lower().endswith(".svg"):
            generator = QSvgGenerator()
            generator.setFileName(path)
            generator.setSize(output_size)
            generator.setViewBox(rect)
            painter = QPainter(generator)
            self.scene.render(painter, QRectF(0, 0, output_size.width(), output_size.height()), rect)
            painter.end()
        else:
            pix = QPixmap(output_size)
            pix.fill(QColor(255, 255, 255))
            painter = QPainter(pix)
            painter.setRenderHint(QPainter.Antialiasing)
            self.scene.render(painter, QRectF(0, 0, output_size.width(), output_size.height()), rect)
            painter.end()
            pix.save(path)

        self.window.status_label.setText(f"Экспортировано: {Path(path).name}")

class TableMoveCommand(QUndoCommand):
    def __init__(self, table_id, old_x, old_y, new_x, new_y, scene, model):
        super().__init__("Перемещение таблицы")
        self.table_id = table_id
        self.old_x = old_x
        self.old_y = old_y
        self.new_x = new_x
        self.new_y = new_y
        self.scene = scene
        self.model = model

    def undo(self):
        item = self.scene.get_item(self.table_id)
        if item:
            item.setPos(self.old_x, self.old_y)
            self.model.update_position(self.table_id, self.old_x, self.old_y)
            for edge in self.scene.edges:
                edge.rebuild_path()

    def redo(self):
        item = self.scene.get_item(self.table_id)
        if item:
            item.setPos(self.new_x, self.new_y)
            self.model.update_position(self.table_id, self.new_x, self.new_y)
            for edge in self.scene.edges:
                edge.rebuild_path()
