import networkx as nx
from PySide6.QtCore import QPointF

def apply_sugiyama_layout(graph_model):
    """
    Расставляет таблицы слоями (снизу вверх по зависимостям).
    """
    G = nx.DiGraph()
    for t in graph_model.tables:
        G.add_node(t.id)
    
    for r in graph_model.relationships:
        G.add_edge(r.src_table_id, r.dst_table_id) # От FK к PK
    
    # Используем dot layout (иерархический)
    # Примечание: Для работы нужен pygraphviz, но networkx имеет fallback или простой layout
    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
    except ImportError:
        # Если pygraphviz нет, используем простой layered layout от networkx
        # Или topological_sort + barycenter (упрощенная реализация ниже)
        layers = {}
        # Простая эвристика: FK-таблицы выше PK-таблиц? Нет, обычно FK указывает на PK.
        # По ТЗ: "выстраивающий зависимости сверху вниз".
        # Обычно PK-таблица (справочник) сверху, FK-таблица снизу.
        
        # Топологическая сортировка
        sorted_nodes = list(nx.topological_sort(G))
        
        # Присваиваем Y на основе "глубины"
        lengths = nx.shortest_path_length(G, source=sorted_nodes[0]) 
        # Это упрощение, лучше использовать layers
        
        # Для надежности без pygraphviz используем spring_layout с seed, 
        # но это не Sugiyama. Реализуем простой Sugiyama вручную.
        return _simple_sugiyama(G, graph_model)

    # Применяем координаты
    node_spacing_x = 250
    node_spacing_y = 150
    
    min_x = min(p[0] for p in pos.values())
    min_y = min(p[1] for p in pos.values())

    for node_id, (x, y) in pos.items():
        table = graph_model.get_table_by_id(node_id)
        if table:
            # Инвертируем Y, т.к. в QGraphicsScene Y растет вниз
            table.x = (x - min_x) * 2 
            table.y = -(y - min_y) * 2 + 100 # Отступ сверху

    return True

def _simple_sugiyama(G, graph_model):
    # Базовая реализация:
    # 1. Считаем входящие степени (in_degree) - это уровень
    # 2. Группируем по уровням
    # 3. Расставляем
    
    levels = {}
    for node in G.nodes():
        # Длина пути от источника (таблицы без входящих FK - это PK таблицы, "родители")
        # Но граф может быть лесом.
        pass
    
    # Временное решение: просто расставить сеткой, если нет graphviz
    x, y = 50, 50
    for table in graph_model.tables:
        table.x = x
        table.y = y
        x += 300
        if x > 2000:
            x = 50
            y += 300
    return True