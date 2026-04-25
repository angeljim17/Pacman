import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, OPENGL

from OpenGL.GL import (
    GL_CLAMP,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_FILL,
    GL_FRONT_AND_BACK,
    GL_LINEAR,
    GL_MODELVIEW,
    GL_PROJECTION,
    GL_QUADS,
    GL_RGBA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindTexture,
    glClear,
    glClearColor,
    glColor3f,
    glDisable,
    glEnable,
    glEnd,
    glGenTextures,
    glGenerateMipmap,
    glLoadIdentity,
    glMatrixMode,
    glPolygonMode,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glVertex2d,
)
from OpenGL.GLU import gluOrtho2D

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from Mapa import Mapa
from Pacman import Pacman
from Ghost import Ghost


DIM_TABLERO = 400

RUTA_BASE = os.path.abspath(os.path.dirname(__file__))
archivo_mapa_textura = os.path.join(RUTA_BASE, "mapa.bmp")
archivo_pacman = os.path.join(RUTA_BASE, "pacman.bmp")
archivo_fantasma_1 = os.path.join(RUTA_BASE, "fantasma1.bmp")
archivo_fantasma_2 = os.path.join(RUTA_BASE, "fantasma2.bmp")
archivo_fantasma_3 = os.path.join(RUTA_BASE, "fantasma3.bmp")
archivo_fantasma_4 = os.path.join(RUTA_BASE, "fantasma4.bmp")

mapa_juego = Mapa(archivo_mapa_textura, ancho_vista=DIM_TABLERO)

ALTO_TABLERO = mapa_juego.alto_vista

ANCHO_CELDA_VISTA = DIM_TABLERO / mapa_juego.columnas
MARGEN_PIXELES_MURO = 1.8
LADO_SPRITE_ENTIDADES = max(3.8, ANCHO_CELDA_VISTA * 0.5 - MARGEN_PIXELES_MURO)

pacman = Pacman(
    mapa_juego,
    fila_inicial=17,
    col_inicial=13,
    velocidad=2.0,
    lado_sprite=LADO_SPRITE_ENTIDADES,
)

INTERVALO_SALIDA = 300
fantasmas = [
    Ghost(mapa_juego, 14, 12, tipo="aleatorio",
          velocidad=1.7, frames_espera=0 * INTERVALO_SALIDA,
          lado_sprite=LADO_SPRITE_ENTIDADES),
    Ghost(mapa_juego, 14, 13, tipo="euclides",
          velocidad=1.7, frames_espera=1 * INTERVALO_SALIDA,
          lado_sprite=LADO_SPRITE_ENTIDADES),
    Ghost(mapa_juego, 14, 14, tipo="cooperativo_1",
          velocidad=1.7, frames_espera=2 * INTERVALO_SALIDA,
          lado_sprite=LADO_SPRITE_ENTIDADES),
    Ghost(mapa_juego, 14, 15, tipo="cooperativo_2",
          velocidad=1.7, frames_espera=3 * INTERVALO_SALIDA,
          lado_sprite=LADO_SPRITE_ENTIDADES),
]

texturas = []


def cargar_textura(ruta_archivo):
    texturas.append(glGenTextures(1))
    indice = len(texturas) - 1
    glBindTexture(GL_TEXTURE_2D, texturas[indice])
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    imagen = pygame.image.load(ruta_archivo).convert()
    ancho, alto = imagen.get_rect().size
    datos_imagen = pygame.image.tostring(imagen, "RGBA")
    glTexImage2D(
        GL_TEXTURE_2D, 0, GL_RGBA, ancho, alto,
        0, GL_RGBA, GL_UNSIGNED_BYTE, datos_imagen,
    )
    glGenerateMipmap(GL_TEXTURE_2D)


def inicializar():
    pygame.display.set_mode((int(DIM_TABLERO), int(ALTO_TABLERO)), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Pacman IA - Rubrica Optimizada")
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, DIM_TABLERO, ALTO_TABLERO, 0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glClearColor(0, 0, 0, 0)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    cargar_textura(archivo_mapa_textura)   # 0: laberinto
    cargar_textura(archivo_pacman)         # 1: pacman
    cargar_textura(archivo_fantasma_1)     # 2: aleatorio
    cargar_textura(archivo_fantasma_2)     # 3: euclides
    cargar_textura(archivo_fantasma_3)     # 4: cooperativo_1
    cargar_textura(archivo_fantasma_4)     # 5: cooperativo_2

    pacman.cargar_texturas(texturas, 1)
    fantasmas[0].cargar_texturas(texturas, 2)
    fantasmas[1].cargar_texturas(texturas, 3)
    fantasmas[2].cargar_texturas(texturas, 4)
    fantasmas[3].cargar_texturas(texturas, 5)


def dibujar_plano():
    glColor3f(1.0, 1.0, 1.0)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texturas[0])
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex2d(0, 0)
    glTexCoord2f(0.0, 1.0)
    glVertex2d(0, ALTO_TABLERO)
    glTexCoord2f(1.0, 1.0)
    glVertex2d(DIM_TABLERO, ALTO_TABLERO)
    glTexCoord2f(1.0, 0.0)
    glVertex2d(DIM_TABLERO, 0)
    glEnd()
    glDisable(GL_TEXTURE_2D)


def dibujar_escena():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    dibujar_plano()
    pacman.dibujar()
    for fantasma in fantasmas:
        fantasma.dibujar()


pygame.init()
inicializar()

terminado = False
reloj = pygame.time.Clock()

while not terminado:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            terminado = True
        elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            terminado = True

    teclas = pygame.key.get_pressed()

    pacman.actualizar(teclas)
    for fantasma in fantasmas:
        fantasma.actualizar(pacman, fantasmas)

    dibujar_escena()
    pygame.display.flip()
    reloj.tick(60)

pygame.quit()
