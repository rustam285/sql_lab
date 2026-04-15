from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QStatusBar, QLabel, QToolBar, QTabWidget, QTableView, QComboBox, QPushButton, QPlainTextEdit
from PySide6.QtCore import Qt
from .diagram_scene import DiagramScene
from .diagram_view import DiagramView
from .widgets.minimap import Minimap

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ER Diagrammer for SQLite")
        self.resize(1200, 800)

        # Инициализация компонентов
        self.scene = DiagramScene()
        self.view = DiagramView(self.scene)
        self.minimap = Minimap(self.scene)
        self.minimap.set_main_view(self.view)

        self.table_combo = QComboBox()
        self.refresh_button = QPushButton("Обновить")
        self.data_table = QTableView()
        self.data_table.setEditTriggers(QTableView.NoEditTriggers)

        self.query_table_combo = QComboBox()
        self.query_combo = QComboBox()
        self.query_col1 = QComboBox()
        self.query_col2 = QComboBox()
        self.query_col3 = QComboBox()
        self.query_condition_edit = QLineEdit()
        self.query_preview = QPlainTextEdit()
        self.query_preview.setReadOnly(True)
        self.run_query_button = QPushButton("Выполнить запрос")
        self.query_result_table = QTableView()
        self.query_result_table.setEditTriggers(QTableView.NoEditTriggers)

        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Вкладка диаграммы
        diagram_tab = QWidget()
        diagram_layout = QHBoxLayout(diagram_tab)
        diagram_layout.setContentsMargins(0, 0, 0, 0)
        diagram_layout.addWidget(self.view, 1)

        mm_container = QWidget()
        mm_layout = QVBoxLayout(mm_container)
        mm_layout.setContentsMargins(0, 0, 0, 0)
        mm_layout.addWidget(self.minimap)
        mm_layout.addStretch()
        diagram_layout.addWidget(mm_container)

        self.tabs.addTab(diagram_tab, "Диаграмма")

        # Вкладка данных
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        data_layout.setContentsMargins(0, 0, 0, 0)

        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.addWidget(QLabel("Таблица:"))
        controls_layout.addWidget(self.table_combo)
        controls_layout.addWidget(self.refresh_button)
        controls_layout.addStretch()
        data_layout.addWidget(controls)
        data_layout.addWidget(self.data_table)

        self.tabs.addTab(data_tab, "Данные")

        # Вкладка запросов
        query_tab = QWidget()
        query_layout = QVBoxLayout(query_tab)
        query_layout.setContentsMargins(0, 0, 0, 0)

        query_controls = QWidget()
        query_controls_layout = QHBoxLayout(query_controls)
        query_controls_layout.setContentsMargins(0, 0, 0, 0)
        query_controls_layout.addWidget(QLabel("Таблица:"))
        query_controls_layout.addWidget(self.query_table_combo)
        query_controls_layout.addWidget(QLabel("Запрос:"))
        query_controls_layout.addWidget(self.query_combo)
        query_controls_layout.addWidget(QLabel("Поле 1:"))
        query_controls_layout.addWidget(self.query_col1)
        query_controls_layout.addWidget(QLabel("Поле 2:"))
        query_controls_layout.addWidget(self.query_col2)
        query_controls_layout.addWidget(QLabel("Поле 3:"))
        query_controls_layout.addWidget(self.query_col3)
        query_controls_layout.addWidget(QLabel("Условие:"))
        query_controls_layout.addWidget(self.query_condition_edit)
        query_controls_layout.addWidget(self.run_query_button)

        query_layout.addWidget(query_controls)
        query_layout.addWidget(QLabel("SQL-запрос:"))
        query_layout.addWidget(self.query_preview)
        query_layout.addWidget(self.query_result_table)

        self.tabs.addTab(query_tab, "Запросы")

        # Тулбар и поиск
        self.toolbar = self.addToolBar("Main")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Поиск таблицы (Enter)...")
        self.search_box.setFixedWidth(220)
        self.toolbar.addWidget(self.search_box)

        # Статус-бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Готово")
        self.status_bar.addPermanentWidget(self.status_label)

        # Пустые меню (заполнит Controller)
        self.menu_file = self.menuBar().addMenu("&Файл")
        self.menu_view = self.menuBar().addMenu("&Вид")