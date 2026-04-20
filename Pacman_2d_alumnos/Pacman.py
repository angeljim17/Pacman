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

    def __init__(self, mapa, mc, x_mc, y_mc, view_size=400.0):
        self.MC = mc
        self.XPxToMC = x_mc
        self.YPxToMC = y_mc
        self.mapa = mapa
        self.map_rows, self.map_cols = mapa.shape
        self.view_size = float(view_size)
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

    def _find_spawn(self):
        mid_r, mid_c = self.map_rows // 2, self.map_cols // 2
        for rad in range(max(self.map_rows, self.map_cols)):
            for dr in range(-rad, rad + 1):
                for dc in range(-rad, rad + 1):
                    r, c = mid_r + dr, mid_c + dc
                    if (
                        0 <= r < self.map_rows
                        and 0 <= c < self.map_cols
                        and self.mapa[r, c] == 0
                    ):
                        px, py = self._rc_to_gl_center(r, c)
                        if self._walkable(px, py, 0.0):
                            return px, py
        vs = self.view_size
        return vs * 0.5, vs * 0.5

    def _walkable(self, px, py, angle=None):
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
