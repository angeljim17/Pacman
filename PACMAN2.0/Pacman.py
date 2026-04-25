"""
Pacman.py
---------
Personaje controlado por el jugador. Movimiento estrictamente alineado
al grid del laberinto: avanza con velocidad constante entre centros de
celda y solo decide en intersecciones.

Reglas (rubrica):
  - Sin movimientos diagonales.
  - Cambio de direccion solo en intersecciones (con bufer de entrada
    para mantener control responsivo sin retraso).
  - Persistencia de la direccion hasta la siguiente decision valida.
  - Nunca atraviesa obstaculos: las direcciones invalidas se ignoran.
  - El juego nunca termina y la entidad nunca se queda detenida si hay
    al menos un vecino disponible.
"""

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
    """Pacman controlado por teclado, alineado al grid del laberinto."""

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

    # --- compatibilidad con la interfaz original ---
    def loadTextures(self, texturas, id_textura):
        self.cargar_texturas(texturas, id_textura)

    def cargar_texturas(self, texturas, id_textura):
        self.texturas = texturas
        self.id_textura = id_textura

    @property
    def position(self):
        """Posicion actual en coordenadas OpenGL (compatibilidad)."""
        return (self.px, self.py)

    # --- logica de movimiento ---
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
        """Lee SOLO el estado fisico actual de las flechas del teclado.

        Si no hay flecha presionada, la direccion solicitada se limpia
        a (0, 0) para que Pacman se detenga al llegar al siguiente nodo.
        Esto garantiza que el personaje solo se mueva mientras el
        jugador mantenga pulsada una flecha (control directo)."""
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
        """Politica de eleccion: control DIRECTO con las flechas fisicas.

        Pacman solo avanza mientras el jugador mantenga presionada una
        flecha en una direccion valida. Si la flecha apunta a una pared,
        o si no hay flecha pulsada, se queda parado en el nodo actual.
        No hay buffer ni continuacion automatica: el movimiento depende
        exclusivamente del input fisico del momento.
        """
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
        """Avanza un frame con velocidad constante.

        Garantiza ejecucion fluida (sin pausas) y evita vibraciones:
        las decisiones solo se toman cuando se llega exactamente al
        centro del nodo actual, y la posicion se ajusta al centro al
        cruzar el umbral de la velocidad."""
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
            # Encadenar nueva decision en el mismo frame para no detenerse
            self._elegir_objetivo()
        else:
            self.px += self.velocidad * dx / distancia
            self.py += self.velocidad * dy / distancia

    # --- compatibilidad con interfaz original ---
    def update(self, teclas):
        self.actualizar(teclas)

    # --- renderizado ---
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
