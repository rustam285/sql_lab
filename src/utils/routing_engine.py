import heapq
from PySide6.QtCore import QPointF, QRectF

class OrthogonalRouter:
    def __init__(self, grid_size=20):
        self.grid_size = grid_size
        self.penalty_turn = 50   # Штраф за поворот
        self.penalty_obs = 10000 # Штраф за пересечение препятствий

    def _grid_pos(self, pos):
        return (int(pos.x() // self.grid_size), int(pos.y() // self.grid_size))

    def _world_pos(self, gx, gy):
        return QPointF(gx * self.grid_size + self.grid_size/2, gy * self.grid_size + self.grid_size/2)

    def route(self, start, end, obstacles):
        start_g = self._grid_pos(start)
        end_g = self._grid_pos(end)

        if start_g == end_g:
            return [start, end]

        # Расширяем границы поиска для надежности
        min_x = min(start_g[0], end_g[0]) - 15
        max_x = max(start_g[0], end_g[0]) + 15
        min_y = min(start_g[1], end_g[1]) - 15
        max_y = max(start_g[1], end_g[1]) + 15

        # PQ: (f_score, counter, node, g_score, direction)
        open_set = []
        heapq.heappush(open_set, (0, 0, start_g, 0, 0))

        came_from = {}
        g_score = {start_g: 0}
        f_score = {start_g: self._heuristic(start_g, end_g)}

        counter = 1

        while open_set:
            current = heapq.heappop(open_set)[2]

            if current == end_g:
                return self._reconstruct_path(came_from, current)

            neighbors = [
                (current[0], current[1] - 1, 2), # Up
                (current[0], current[1] + 1, 2), # Down
                (current[0] - 1, current[1], 1), # Left
                (current[0] + 1, current[1], 1)  # Right
            ]

            for nx, ny, ndir in neighbors:
                if not (min_x <= nx <= max_x and min_y <= ny <= max_y):
                    continue

                neighbor = (nx, ny)
                if self._is_obstacle(neighbor, obstacles):
                    continue

                tentative_g = g_score[current] + self.grid_size

                # Штраф за поворот
                came_from_node = came_from.get(current)
                if came_from_node:
                    # 🔑 ИСПРАВЛЕНО: было [2], теперь [1] (направление хранится во втором элементе)
                    prev_dir = came_from_node[1] 
                    if prev_dir != ndir and prev_dir != 0:
                        tentative_g += self.penalty_turn

                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = (current, ndir)
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, end_g)
                    heapq.heappush(open_set, (f_score[neighbor], counter, neighbor, tentative_g, ndir))
                    counter += 1

        return [] # Путь не найден

    def _is_obstacle(self, grid_pos, obstacles):
        rect = QRectF(grid_pos[0] * self.grid_size, grid_pos[1] * self.grid_size,
                      self.grid_size, self.grid_size)
        for obs in obstacles:
            if rect.intersects(obs):
                return True
        return False

    def _heuristic(self, a, b):
        return self.grid_size * (abs(a[0] - b[0]) + abs(a[1] - b[1]))

    def _reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current][0]
            path.append(current)
        path.reverse()
        return [self._world_pos(p[0], p[1]) for p in path]