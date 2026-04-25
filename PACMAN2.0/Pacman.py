import math

import pygame
from pygame.locals import K_UP, K_DOWN, K_LEFT, K_RIGHT

from OpenGL.GL import (
    GL_QUADS,
    GL_TEXTURE_2D,
    glBegin,
    glBindTexture,
    glColor3f,
    glDisable,
    glEnable,
    glEnd,
    glPopMatrix,
    glPushMatrix,
    glRotatef,
    glTexCoord2f,
    glTranslatef,
    glVertex2f,
)


class Pacman:
    LADO_SPRITE = 5.5

    def __init__(self, mapa, fila_inicial, col_inicial, velocidad=2.0, lado_sprite=None):
        self.mapa = mapa
        self.velocidad = float(velocidad)
        self.lado_sprite = float(lado_sprite) if lado_sprite is not None else self.LADO_SPRITE

        nodo = (fila_inicial, col_inicial)
        if not self.mapa.es_transitable(nodo):
            nodo = self.mapa.nodo_mas_cercano(*self.mapa.posicion(nodo))
        self.nodo_actual = nodo
        self.nodo_objetivo = nodo
        self.nodo_anterior = None

        self.px, self.py = self.mapa.posicion(self.nodo_actual)

        self.direccion_actual = (0, 0)
        self.direccion_solicitada = (0, 0)
        self.angulo = 0.0

        self.texturas = None
        self.id_textura = None

    def loadTextures(self, texturas, id_textura):
        self.cargar_texturas(texturas, id_textura)

    def cargar_texturas(self, texturas, id_textura):
        self.texturas = texturas
        self.id_textura = id_textura

    @property
    def position(self):
        return (self.px, self.py)

    def _angulo_direccion(self, direccion):
        dx, dy = direccion
        if dx == 1:
            return 0.0
        if dx == -1:
            return 180.0
        if dy == 1:
            return 90.0
        if dy == -1:
            return 270.0
        return self.angulo

    def _leer_entrada(self, teclas):
        if teclas[K_RIGHT]:
            self.direccion_solicitada = (1, 0)
        elif teclas[K_LEFT]:
            self.direccion_solicitada = (-1, 0)
        elif teclas[K_DOWN]:
            self.direccion_solicitada = (0, 1)
        elif teclas[K_UP]:
            self.direccion_solicitada = (0, -1)
        else:
            self.direccion_solicitada = (0, 0)

    def _elegir_objetivo(self):
        nodo = self.nodo_actual
        candidato = self.mapa.vecino_en_direccion(nodo, self.direccion_solicitada)
        if candidato is not None and not self.mapa.es_nodo_caja_fantasmas(candidato):
            self.nodo_objetivo = candidato
            self.direccion_actual = self.direccion_solicitada
            self.angulo = self._angulo_direccion(self.direccion_actual)
            return

        self.nodo_objetivo = nodo
        self.direccion_actual = (0, 0)

    def actualizar(self, teclas):
        self._leer_entrada(teclas)

        if self.nodo_objetivo == self.nodo_actual:
            self._elegir_objetivo()

        objetivo_x, objetivo_y = self.mapa.posicion(self.nodo_objetivo)
        dx = objetivo_x - self.px
        dy = objetivo_y - self.py
        distancia = math.hypot(dx, dy)

        if distancia <= self.velocidad:
            self.px, self.py = objetivo_x, objetivo_y
            self.nodo_anterior = self.nodo_actual
            self.nodo_actual = self.nodo_objetivo
            self._elegir_objetivo()
        else:
            self.px += self.velocidad * dx / distancia
            self.py += self.velocidad * dy / distancia

    def update(self, teclas):
        self.actualizar(teclas)

    def _dibujar_sprite(self):
        s = self.lado_sprite
        glPushMatrix()
        glTranslatef(self.px, self.py, 0.0)
        glRotatef(self.angulo, 0.0, 0.0, 1.0)
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

    def dibujar(self):
        if self.texturas is None or self.id_textura is None:
            return
        glColor3f(1.0, 1.0, 1.0)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texturas[self.id_textura])
        self._dibujar_sprite()
        glDisable(GL_TEXTURE_2D)

    def draw(self):
        self.dibujar()
