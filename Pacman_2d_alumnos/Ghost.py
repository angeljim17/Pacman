import heapq
import math
import random
from collections import deque

import numpy as np

from OpenGL.GL import *

from maze_utils import angle_to_vector, find_middle_tunnel_rows, shortest_wrapped_delta


ANGLE_BY_VECTOR = {
    (-1, 0): 180.0,
    (1, 0): 0.0,
    (0, -1): 270.0,
    (0, 1): 90.0,
}


class NavigationGraph:
    def __init__(self, mapa, view_size=400.0, actor_radius=8.5, step=4.0):
        self.mapa = mapa
        self.view_size = float(view_size)
        self.actor_radius = float(actor_radius)
        self.step = float(step)
        self.offset = self.step * 0.5
        self.map_rows, self.map_cols = mapa.shape
        self.grid_cols = int(self.view_size // self.step)
        self.grid_rows = int(self.view_size // self.step)
        self.tunnel_rows = set(find_middle_tunnel_rows(mapa))
        self.tunnel_grid_rows = set()
        self.walkable = np.zeros((self.grid_rows, self.grid_cols), dtype=bool)

        for gy in range(self.grid_rows):
            py = self.node_to_world((0, gy))[1]
            if self._map_row(py) in self.tunnel_rows:
                self.tunnel_grid_rows.add(gy)
            for gx in range(self.grid_cols):
                px = self.node_to_world((gx, gy))[0]
                self.walkable[gy, gx] = self._position_walkable(px, py)

        self.nodes = [
            (gx, gy)
            for gy in range(self.grid_rows)
            for gx in range(self.grid_cols)
            if self.walkable[gy, gx]
        ]
        self._neighbors = {node: self._build_neighbors(node) for node in self.nodes}

    def _map_row(self, py):
        row = int(py * self.map_rows / self.view_size)
        return min(max(row, 0), self.map_rows - 1)

    def _map_col(self, px):
        col = int(px * self.map_cols / self.view_size)
        return min(max(col, 0), self.map_cols - 1)

    def _sample_point_open(self, px, py):
        if py < 0.0 or py >= self.view_size:
            return False
        if px < 0.0 or px >= self.view_size:
            if self._map_row(py) not in self.tunnel_rows:
                return False
            px %= self.view_size
        return self.mapa[self._map_row(py), self._map_col(px)] == 0

    def _position_walkable(self, px, py):
        samples = [(0.0, 0.0)]
        for idx in range(16):
            ang = (2.0 * math.pi * idx) / 16.0
            samples.append(
                (
                    self.actor_radius * math.cos(ang),
                    self.actor_radius * math.sin(ang),
                )
            )
        for ox, oy in samples:
            if not self._sample_point_open(px + ox, py + oy):
                return False
        return True

    def node_to_world(self, node):
        gx, gy = node
        return gx * self.step + self.offset, gy * self.step + self.offset

    def _snap_axis(self, value, limit):
        snapped = int(round((value - self.offset) / self.step))
        return min(max(snapped, 0), limit - 1)

    def nearest_node(self, px, py):
        px %= self.view_size
        py = min(max(py, self.offset), self.view_size - self.offset)
        gx0 = self._snap_axis(px, self.grid_cols)
        gy0 = self._snap_axis(py, self.grid_rows)

        if self.walkable[gy0, gx0]:
            return gx0, gy0

        max_radius = max(self.grid_cols, self.grid_rows)
        for radius in range(1, max_radius):
            candidates = []
            min_x = max(0, gx0 - radius)
            max_x = min(self.grid_cols - 1, gx0 + radius)
            min_y = max(0, gy0 - radius)
            max_y = min(self.grid_rows - 1, gy0 + radius)
            for gy in range(min_y, max_y + 1):
                for gx in range(min_x, max_x + 1):
                    if max(abs(gx - gx0), abs(gy - gy0)) != radius:
                        continue
                    if not self.walkable[gy, gx]:
                        continue
                    wx, wy = self.node_to_world((gx, gy))
                    dx = shortest_wrapped_delta(wx - px, self.view_size)
                    dy = wy - py
                    candidates.append((dx * dx + dy * dy, (gx, gy)))
            if candidates:
                candidates.sort(key=lambda item: item[0])
                return candidates[0][1]
        return None

    def _build_neighbors(self, node):
        gx, gy = node
        neighbors = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ngx = gx + dx
            ngy = gy + dy
            if 0 <= ngx < self.grid_cols and 0 <= ngy < self.grid_rows and self.walkable[ngy, ngx]:
                neighbors.append((ngx, ngy))

        if gy in self.tunnel_grid_rows:
            if gx == 0 and self.walkable[gy, self.grid_cols - 1]:
                neighbors.append((self.grid_cols - 1, gy))
            if gx == self.grid_cols - 1 and self.walkable[gy, 0]:
                neighbors.append((0, gy))
        return neighbors

    def neighbors(self, node):
        return self._neighbors.get(node, [])

    def astar(self, start, goal, avoid_nodes=None, avoid_penalty=0, forbidden_nodes=None):
        if start is None or goal is None:
            return []
        if start == goal:
            return []

        avoid_nodes = set(avoid_nodes or ())
        forbidden_nodes = set(forbidden_nodes or ())
        open_heap = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        seen = set()

        while open_heap:
            _, current = heapq.heappop(open_heap)
            if current in seen:
                continue
            if current == goal:
                return self._reconstruct_path(came_from, current)
            seen.add(current)

            for neighbor in self.neighbors(current):
                if neighbor in forbidden_nodes and neighbor != goal:
                    continue
                penalty = avoid_penalty if neighbor in avoid_nodes and neighbor != goal else 0
                tentative = g_score[current] + 1 + penalty
                if tentative >= g_score.get(neighbor, math.inf):
                    continue
                came_from[neighbor] = current
                g_score[neighbor] = tentative
                f_score = tentative + self._heuristic(neighbor, goal)
                heapq.heappush(open_heap, (f_score, neighbor))

        return []

    def nodes_in_rect(self, rect):
        x0, y0, x1, y1 = rect
        nodes = set()
        for gy in range(self.grid_rows):
            for gx in range(self.grid_cols):
                if not self.walkable[gy, gx]:
                    continue
                wx, wy = self.node_to_world((gx, gy))
                if x0 <= wx <= x1 and y0 <= wy <= y1:
                    nodes.add((gx, gy))
        return nodes

    def _heuristic(self, a, b):
        dx = abs(a[0] - b[0])
        dx = min(dx, self.grid_cols - dx)
        dy = abs(a[1] - b[1])
        return dx + dy

    def _reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path[1:]


class Ghost:
    SPRITE_HALF = 12.0
    NAV_RADIUS = 8.5
    NAV_STEP = 4.0
    REPLAN_INTERVAL = 10
    AVOID_PATH_STEPS = 10
    AVOID_PATH_PENALTY = 6

    def __init__(
        self,
        mapa,
        mc,
        x_mc,
        y_mc,
        xini,
        yini,
        dir,
        tipo,
        view_size=400.0,
        navigator=None,
        rng=None,
        release_delay_ms=0,
        house_exit_xy=None,
        house_rect=None,
    ):
        self.MC = mc
        self.XPxToMC = x_mc
        self.YPxToMC = y_mc
        self.mapa = mapa
        self.view_size = float(view_size)
        self.behavior = tipo
        self.speed = 1.7 if tipo == "random" else 1.9
        self.navigator = navigator or NavigationGraph(
            mapa,
            view_size=self.view_size,
            actor_radius=self.NAV_RADIUS,
            step=self.NAV_STEP,
        )
        self.current_node = self.navigator.nearest_node(xini, yini)
        self.px, self.py = self.navigator.node_to_world(self.current_node)
        self.previous_node = None
        self.recent_nodes = deque([self.current_node], maxlen=8)
        self.route = []
        self.replan_timer = 0
        self.angle = float(dir) % 360.0
        self.texturas = None
        self.Id = None
        self.rng = rng or random.Random()
        exit_xy = house_exit_xy or (self.view_size * 0.5, self.view_size * 0.405)
        self.house_exit_node = self.navigator.nearest_node(*exit_xy)
        # Una vez fuera, los nodos del interior de la caja están prohibidos
        self.house_rect = house_rect
        self.house_nodes = (
            self.navigator.nodes_in_rect(house_rect) if house_rect is not None else set()
        )
        self.release_delay_ms = max(0, int(release_delay_ms))
        self.state = "waiting" if self.release_delay_ms > 0 else "exiting"
        if self.current_node == self.house_exit_node:
            self.state = "chasing"

    def _forbidden_nodes(self):
        if self.state == "chasing":
            return self.house_nodes
        return set()

    def loadTextures(self, texturas, id):
        self.texturas = texturas
        self.Id = id

    def _filter_house(self, nodes):
        forbidden = self._forbidden_nodes()
        if not forbidden:
            return list(nodes)
        filtered = [n for n in nodes if n not in forbidden]
        return filtered or list(nodes)

    def _avoid_reverse(self, neighbors):
        nbrs = self._filter_house(neighbors)
        if self.previous_node is None or len(nbrs) <= 1:
            return nbrs
        filtered = [node for node in nbrs if node != self.previous_node]
        return filtered or nbrs

    def _distance_to(self, node, px, py):
        wx, wy = self.navigator.node_to_world(node)
        dx = shortest_wrapped_delta(wx - px, self.view_size)
        dy = wy - py
        return math.hypot(dx, dy)

    def _plan_random(self):
        options = self._avoid_reverse(self.navigator.neighbors(self.current_node))
        if not options:
            return []
        fresh_options = [node for node in options if node not in self.recent_nodes]
        pool = fresh_options or options
        return [self.rng.choice(pool)]

    def _plan_euclid(self, pacman):
        options = self._avoid_reverse(self.navigator.neighbors(self.current_node))
        if not options:
            return []
        best = min(options, key=lambda node: self._distance_to(node, pacman.px, pacman.py))
        return [best]

    def _project_target(self, px, py):
        return self.navigator.nearest_node(px % self.view_size, min(max(py, 0.0), self.view_size - 1.0))

    def _astar_goal(self, pacman, ghosts):
        dx, dy = angle_to_vector(pacman.angle)
        if self.behavior == "astar_lead":
            look_ahead = 36.0
            target_x = pacman.px + dx * look_ahead
            target_y = pacman.py + dy * look_ahead
        else:
            look_ahead = 28.0
            ahead_x = pacman.px + dx * look_ahead
            ahead_y = pacman.py + dy * look_ahead
            lead = next((ghost for ghost in ghosts if ghost.behavior == "astar_lead"), None)
            if lead is None:
                target_x, target_y = ahead_x, ahead_y
            else:
                target_x = ahead_x + (ahead_x - lead.px)
                target_y = ahead_y + (ahead_y - lead.py)
        return self._project_target(target_x, target_y)

    def _plan_astar(self, pacman, ghosts, avoid_nodes=None):
        goal = self._astar_goal(pacman, ghosts)
        route = self.navigator.astar(
            self.current_node,
            goal,
            avoid_nodes=avoid_nodes,
            avoid_penalty=self.AVOID_PATH_PENALTY,
            forbidden_nodes=self._forbidden_nodes(),
        )
        if route:
            return route
        return self._plan_euclid(pacman)

    def _plan_route(self, pacman, ghosts):
        if self.behavior == "random":
            return self._plan_random()
        if self.behavior == "euclid":
            return self._plan_euclid(pacman)
        avoid_nodes = None
        if self.behavior == "astar_support":
            lead = next((ghost for ghost in ghosts if ghost.behavior == "astar_lead"), None)
            if lead is not None:
                reserved = [lead.current_node]
                reserved.extend(lead.route[: self.AVOID_PATH_STEPS])
                avoid_nodes = reserved
        return self._plan_astar(pacman, ghosts, avoid_nodes=avoid_nodes)

    def _plan_house_exit(self):
        return self.navigator.astar(self.current_node, self.house_exit_node)

    def _set_angle_towards(self, target_node):
        tx, ty = self.navigator.node_to_world(target_node)
        dx = shortest_wrapped_delta(tx - self.px, self.view_size)
        dy = ty - self.py
        if abs(dx) >= abs(dy):
            self.angle = 0.0 if dx >= 0.0 else 180.0
        else:
            self.angle = 90.0 if dy >= 0.0 else 270.0

    def _move_towards(self, target_node):
        tx, ty = self.navigator.node_to_world(target_node)
        dx = shortest_wrapped_delta(tx - self.px, self.view_size)
        dy = ty - self.py
        dist = math.hypot(dx, dy)
        if dist <= self.speed:
            self.px = tx % self.view_size
            self.py = ty
            return True

        if dist > 0.0:
            self.px = (self.px + self.speed * dx / dist) % self.view_size
            self.py += self.speed * dy / dist
        return False

    def _tick_release(self, dt_ms):
        if self.state != "waiting":
            return
        self.release_delay_ms = max(0, self.release_delay_ms - int(dt_ms))
        if self.release_delay_ms == 0:
            self.state = "exiting"
            self.route = []

    def _maybe_refresh_route(self, pacman, ghosts):
        if self.state == "exiting":
            if not self.route:
                self.route = self._plan_house_exit()
            return

        if not self.route or (
            self.behavior.startswith("astar") and self.replan_timer <= 0
        ):
            self.route = self._plan_route(pacman, ghosts)
            self.replan_timer = self.REPLAN_INTERVAL
        else:
            self.replan_timer -= 1

    def update2(self, pacmanXY, ghosts=None, dt_ms=16):
        pacman = pacmanXY
        ghosts = ghosts or []
        if self.current_node is None:
            return
        self._tick_release(dt_ms)
        if self.state == "waiting":
            return

        self._maybe_refresh_route(pacman, ghosts)

        if not self.route:
            if self.state == "exiting" and self.current_node == self.house_exit_node:
                self.state = "chasing"
            return

        target_node = self.route[0]
        self._set_angle_towards(target_node)
        if self._move_towards(target_node):
            self.previous_node = self.current_node
            self.current_node = target_node
            self.recent_nodes.append(self.current_node)
            self.route.pop(0)
            if self.state == "exiting" and self.current_node == self.house_exit_node:
                self.state = "chasing"
                self.route = []

    def _draw_sprite(self, px, py):
        s = self.SPRITE_HALF
        glPushMatrix()
        glTranslatef(px, py, 0.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(-s, -s)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(-s, s)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(s, s)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(s, -s)
        glEnd()
        glPopMatrix()

    def draw(self):
        if self.texturas is None or self.Id is None:
            return
        glColor3f(1.0, 1.0, 1.0)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texturas[self.Id])
        self._draw_sprite(self.px, self.py)
        if self.px < self.SPRITE_HALF:
            self._draw_sprite(self.px + self.view_size, self.py)
        elif self.px > self.view_size - self.SPRITE_HALF:
            self._draw_sprite(self.px - self.view_size, self.py)
        glDisable(GL_TEXTURE_2D)
