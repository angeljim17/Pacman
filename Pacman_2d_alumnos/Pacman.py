import os
import math

import pygame
from pygame.locals import *

from OpenGL.GL import *

import numpy as np

from maze_utils import find_middle_tunnel_rows
# Pacman prueba de codigo

class Pacman:
    """Mapa lógico mapa[row, col]; tablero OpenGL view_size×view_size (p. ej. 400).
    Colisiones alineadas al mapa.csv generado desde mapa.bmp (misma rejilla)."""

    SPRITE_HALF = 12.0  # mitad del cuadrado texturizado (como el diseño original)
    COLLISION_COLOR_THRESHOLD = 16
    _COLLISION_MASKS = None

    def __init__(
        self,
        mapa,
        mc,
        x_mc,
        y_mc,
        view_size=400.0,
        spawn_exclude_rect=None,
        spawn_min_y=None,
        forbidden_rect=None,
    ):
        self.MC = mc
        self.XPxToMC = x_mc
        self.YPxToMC = y_mc
        self.mapa = mapa
        self.map_rows, self.map_cols = mapa.shape
        self.view_size = float(view_size)
        # (xmin, ymin, xmax, ymax) en coord. OpenGL: no spawear aquí (p. ej. casita de fantasmas)
        self._spawn_exclude_rect = spawn_exclude_rect
        # Si se define, el respawn busca primero celdas con py > spawn_min_y (p. ej. bajo la caja)
        self._spawn_min_y = None if spawn_min_y is None else float(spawn_min_y)
        # Si se define, Pacman no puede tener su centro dentro de este rectángulo
        # (p. ej. la casa de los fantasmas), aunque las celdas estén abiertas.
        self._forbidden_rect = forbidden_rect
        cw = self.view_size / self.map_cols
        ch = self.view_size / self.map_rows
        self._cell = min(cw, ch)
        # Mapa fino (rejilla alineada a la imagen): radio acorde al sprite 12
        if self.map_rows >= 50 or self.map_cols >= 50:
            self.radius = self.SPRITE_HALF * 0.5
            self.speed = 2.5
        else:
            # Mapa 10×10 de práctica: misma proporción que antes
            self.radius = 0.2 * self._cell
            self.speed = min(2.5, 0.45 * self._cell)
        self.collision_masks = self._get_collision_masks()
        self.tunnel_rows = set(find_middle_tunnel_rows(self.mapa))
        # 1 si el pacman está en el estado inicial del juego (reservado para lógica futura)
        self.start = 1
        self.angle = 0.0
        self.px, self.py = self._find_spawn()
        self.texturas = None
        self.Id = None

    def _gl_to_rc(self, x, y):
        """Coordenadas del tablero OpenGL → índices (fila, columna) en mapa."""
        c = int(x * self.map_cols / self.view_size)
        r = int(y * self.map_rows / self.view_size)
        c = min(max(c, 0), self.map_cols - 1)
        r = min(max(r, 0), self.map_rows - 1)
        return r, c

    def _rc_to_gl_center(self, r, c):
        """Centro de la celda (r, c) en coordenadas OpenGL."""
        px = (c + 0.5) * self.view_size / self.map_cols
        py = (r + 0.5) * self.view_size / self.map_rows
        return px, py

    @classmethod
    def _get_collision_masks(cls):
        if cls._COLLISION_MASKS is not None:
            return cls._COLLISION_MASKS

        sprite_size = int(cls.SPRITE_HALF * 2)
        sprite_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "pacman.bmp")
        image = pygame.image.load(sprite_path)
        sample = pygame.transform.scale(image, (sprite_size, sprite_size))

        base_points = []
        for y in range(sprite_size):
            for x in range(sprite_size):
                r, g, b, *_ = sample.get_at((x, y))
                if max(r, g, b) <= cls.COLLISION_COLOR_THRESHOLD:
                    continue
                base_points.append((x + 0.5 - cls.SPRITE_HALF, y + 0.5 - cls.SPRITE_HALF))

        if not base_points:
            # Fallback conservador si el sprite no se puede muestrear correctamente.
            base_points = [(0.0, 0.0)]

        cls._COLLISION_MASKS = {
            0: tuple(base_points),
            90: tuple((-y, x) for x, y in base_points),
            180: tuple((-x, -y) for x, y in base_points),
            270: tuple((y, -x) for x, y in base_points),
        }
        return cls._COLLISION_MASKS

    def _collision_points(self, angle=None):
        angle = self.angle if angle is None else angle
        return self.collision_masks[int(angle) % 360]

    def _is_tunnel_y(self, y):
        if not self.tunnel_rows or y < 0.0 or y >= self.view_size:
            return False
        r, _ = self._gl_to_rc(self.view_size * 0.5, y)
        return r in self.tunnel_rows

    def _pixel_walkable(self, x, y):
        if y < 0 or y >= self.view_size:
            return False
        if x < 0 or x >= self.view_size:
            if not self._is_tunnel_y(y):
                return False
            x %= self.view_size
        r, c = self._gl_to_rc(x, y)
        return self.mapa[r, c] == 0

    def _normalize_tunnel_x(self):
        if not self._is_tunnel_y(self.py):
            return
        if self.px < -self.SPRITE_HALF:
            self.px = self.view_size + self.SPRITE_HALF
        elif self.px > self.view_size + self.SPRITE_HALF:
            self.px = -self.SPRITE_HALF

    def _spawn_in_exclude_rect(self, px, py):
        if self._spawn_exclude_rect is None:
            return False
        x0, y0, x1, y1 = self._spawn_exclude_rect
        return x0 <= px <= x1 and y0 <= py <= y1

    def _spawn_seed_rc(self):
        """Elegir la celda más centrada en X (sobre el centro de la caja) en la franja de
        filas inmediatamente debajo de spawn_min_y. Prioriza centrado horizontal y
        cercanía al borde superior de la franja (tras el muro inferior de la caja)."""
        mid_c = self.map_cols // 2
        if self._spawn_exclude_rect is not None:
            x0, _, x1, _ = self._spawn_exclude_rect
            mid_c = int((x0 + x1) * 0.5 * self.map_cols / self.view_size)
            mid_c = min(max(mid_c, 0), self.map_cols - 1)
        if self._spawn_min_y is None:
            return self.map_rows // 2, mid_c
        # Recolectar todas las celdas walkable que pasen el filtro y elegir la mejor
        first_valid_r = None
        best = None
        best_score = float("inf")
        rows_after_first = 0
        SEARCH_ROWS = 24
        for r in range(self.map_rows):
            row_py = (r + 0.5) * self.view_size / self.map_rows
            if row_py <= self._spawn_min_y:
                continue
            if first_valid_r is None:
                first_valid_r = r
            rows_after_first = r - first_valid_r
            if rows_after_first > SEARCH_ROWS:
                break
            for c in range(self.map_cols):
                if self.mapa[r, c] != 0:
                    continue
                px, py = self._rc_to_gl_center(r, c)
                if self._spawn_in_exclude_rect(px, py):
                    continue
                if not self._walkable(px, py, 0.0):
                    continue
                # Penaliza fuertemente lejanía horizontal; pequeña preferencia por filas
                # cercanas al borde superior cuando el centrado es similar.
                score = (c - mid_c) * (c - mid_c) * 100 + rows_after_first
                if score < best_score:
                    best_score, best = score, (r, c)
        if best is not None:
            return best
        for r in range(self.map_rows):
            for c in range(self.map_cols):
                if self.mapa[r, c] != 0:
                    continue
                px, py = self._rc_to_gl_center(r, c)
                if py <= self._spawn_min_y or self._spawn_in_exclude_rect(px, py):
                    continue
                if self._walkable(px, py, 0.0):
                    return r, c
        return self.map_rows // 2, self.map_cols // 2

    def _iter_spawn_spiral(self, start_r, start_c, require_below, respect_exclude):
        for rad in range(max(self.map_rows, self.map_cols)):
            for dr in range(-rad, rad + 1):
                for dc in range(-rad, rad + 1):
                    r, c = start_r + dr, start_c + dc
                    if not (0 <= r < self.map_rows and 0 <= c < self.map_cols):
                        continue
                    if self.mapa[r, c] != 0:
                        continue
                    px, py = self._rc_to_gl_center(r, c)
                    if respect_exclude and self._spawn_in_exclude_rect(px, py):
                        continue
                    if require_below and self._spawn_min_y is not None and py <= self._spawn_min_y:
                        continue
                    if self._walkable(px, py, 0.0):
                        yield px, py

    def _find_spawn(self):
        need_below = self._spawn_min_y is not None
        seed_r, seed_c = self._spawn_seed_rc()
        for px, py in self._iter_spawn_spiral(
            seed_r, seed_c, require_below=need_below, respect_exclude=True
        ):
            return px, py
        for px, py in self._iter_spawn_spiral(
            self.map_rows // 2, self.map_cols // 2, require_below=need_below, respect_exclude=True
        ):
            return px, py
        for px, py in self._iter_spawn_spiral(
            self.map_rows // 2, self.map_cols // 2, require_below=False, respect_exclude=True
        ):
            return px, py
        for px, py in self._iter_spawn_spiral(
            self.map_rows // 2, self.map_cols // 2, require_below=False, respect_exclude=False
        ):
            return px, py
        vs = self.view_size
        return vs * 0.5, vs * 0.5

    def reset_spawn(self):
        """Para respawn o nueva vida: vuelve a buscar posición (respeta la exclusión)."""
        self.px, self.py = self._find_spawn()

    def _in_forbidden_rect(self, px, py):
        if self._forbidden_rect is None:
            return False
        x0, y0, x1, y1 = self._forbidden_rect
        return x0 <= px <= x1 and y0 <= py <= y1

    def _walkable(self, px, py, angle=None):
        if self._in_forbidden_rect(px, py):
            return False
        for ox, oy in self._collision_points(angle):
            if not self._pixel_walkable(px + ox, py + oy):
                return False
        return True

    def loadTextures(self, texturas, id):
        self.texturas = texturas
        self.Id = id

    def update(self, keys):
        dx, dy = 0.0, 0.0
        next_angle = self.angle
        if keys[K_LEFT]:
            dx, dy = -self.speed, 0.0
            next_angle = 180.0
        elif keys[K_RIGHT]:
            dx, dy = self.speed, 0.0
            next_angle = 0.0
        elif keys[K_UP]:
            dx, dy = 0.0, -self.speed
            next_angle = 270.0
        elif keys[K_DOWN]:
            dx, dy = 0.0, self.speed
            next_angle = 90.0

        if dx == 0.0 and dy == 0.0:
            return
        self.angle = next_angle
        # Micro-pasos para no saltar celdas finas con velocidad 2,5
        dist = math.hypot(dx, dy)
        n = max(1, min(16, int(math.ceil(dist / max(self._cell * 0.2, 0.05)))))
        for _ in range(n):
            nx = self.px + dx / n
            ny = self.py + dy / n
            if self._walkable(nx, ny, self.angle):
                self.px, self.py = nx, ny
                self._normalize_tunnel_x()
            else:
                break

    def _draw_sprite(self, px, py):
        s = self.SPRITE_HALF
        glPushMatrix()
        glTranslatef(px, py, 0.0)
        glRotatef(self.angle, 0.0, 0.0, 1.0)
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
        if self._is_tunnel_y(self.py):
            if self.px < self.SPRITE_HALF:
                self._draw_sprite(self.px + self.view_size, self.py)
            elif self.px > self.view_size - self.SPRITE_HALF:
                self._draw_sprite(self.px - self.view_size, self.py)
        glDisable(GL_TEXTURE_2D)


if __name__ == "__main__":
    print("Este archivo solo define la clase Pacman.")
    print("Para jugar, ejecuta: python main.py")
