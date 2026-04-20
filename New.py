import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

import numpy as np
import math

pygame.init()

screen_width = 900
screen_height = 900

# Rango para dibujar los ejes (igual que en Ejemplo2D_triangulos.py)
X_MIN = -500
X_MAX = 500
Y_MIN = -500
Y_MAX = 500

# Triángulos equiláteros: r = distancia del centro al vértice.
# Vértices en ángulos 90°, 210°, 330° (uno arriba, dos abajo).
def vertices_equilatero(r: float) -> np.ndarray:
    rad = math.radians
    return np.array([
        [r * math.cos(rad(90)),  r * math.sin(rad(90))],   # arriba
        [r * math.cos(rad(210)), r * math.sin(rad(210))],  # abajo-izq
        [r * math.cos(rad(330)), r * math.sin(rad(330))],  # abajo-der
    ], dtype=float)

# Triángulo del centro 
points_center = vertices_equilatero(100.0)
# Triángulo que orbita 
points_orbit = vertices_equilatero(55.0)


def mat_rotate(angle_deg: float) -> np.ndarray:
    """Matriz 3x3 de rotación 2D alrededor del origen (columna: [x,y,1]^T)."""
    theta = math.radians(angle_deg)
    c = math.cos(theta)
    s = math.sin(theta)
    return np.array(
        [
            [c, -s, 0.0],
            [s,  c, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )


def mat_translate(tx: float, ty: float) -> np.ndarray:
    """Matriz 3x3 de traslación 2D."""
    return np.array(
        [
            [1.0, 0.0, tx],
            [0.0, 1.0, ty],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )


def transform_points(points: np.ndarray, M: np.ndarray) -> np.ndarray:
    """
    Aplica la transformación afín M (3x3) a una lista de puntos 2D.
    Cada punto se considera como vector columna [x,y,1]^T.
    """
    # Convertimos Nx2 -> Nx3 con coordenada homogénea 1
    ones = np.ones((points.shape[0], 1), dtype=float)
    pts_h = np.hstack([points, ones])          # Nx3
    # Usamos convención columna: resultado = M @ p
    res_h = (M @ pts_h.T).T                    # (3x3 * 3xN)^T -> Nx3
    return res_h[:, :2]                        # devolvemos solo (x,y)


def setup():
    """Configuración inicial de la ventana y la proyección 2D."""
    pygame.display.set_mode((screen_width, screen_height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("OpenGL: triángulos girando con matrices propias")

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # Proyección ortográfica 2D centrada en (0, 0)
    gluOrtho2D(-450, 450, -450, 450)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glClearColor(0.0, 0.0, 0.0, 1.0)


def Axis():
    """Dibuja los ejes X e Y, guiado por Ejemplo2D_triangulos.py."""
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glShadeModel(GL_SMOOTH)
    glLineWidth(3.0)

    # Eje X
    glBegin(GL_LINES)
    glColor3f(1.0, 0.0, 0.0)
    glVertex2f(X_MIN, 0.0)
    glColor3f(0.0, 1.0, 0.0)
    glVertex2f(X_MAX, 0.0)
    glEnd()

    # Eje Y
    glColor3f(0.0, 1.0, 0.0)
    glBegin(GL_LINES)
    glVertex2f(0.0, Y_MIN)
    glVertex2f(0.0, Y_MAX)
    glEnd()

    glLineWidth(1.0)


# Ángulos (en grados) para las animaciones
angulo_centro = 0.0       # Triángulo del centro gira sobre su propio eje
angulo_orbita = 0.0       # Triángulo exterior gira alrededor del centro


def dibujar_triangulo_centro():
    """Triángulo en el centro que gira sobre su propio eje usando matrices propias."""
    global angulo_centro

    # Matriz de rotación alrededor del origen
    M = mat_rotate(angulo_centro)
    pts = transform_points(points_center, M)

    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glShadeModel(GL_SMOOTH)

    glBegin(GL_TRIANGLES)
    glColor3f(1.0, 0.0, 0.0)
    glVertex2f(pts[0, 0], pts[0, 1])
    glColor3f(0.0, 1.0, 0.0)
    glVertex2f(pts[1, 0], pts[1, 1])
    glColor3f(0.0, 0.0, 1.0)
    glVertex2f(pts[2, 0], pts[2, 1])
    glEnd()


def dibujar_triangulo_orbita():
    """Triángulo que gira alrededor del triángulo del centro usando matrices propias."""
    global angulo_orbita

    # Órbita alrededor del centro (0,0): trasladamos al radio de la órbita
    # y luego rotamos ese radio. p' = R(ángulo) * T(radio, 0) * p
    radio_orbita = 250.0
    T = mat_translate(radio_orbita, 0.0)
    R = mat_rotate(angulo_orbita)
    M = R @ T

    pts = transform_points(points_orbit, M)

    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glShadeModel(GL_SMOOTH)

    glBegin(GL_TRIANGLES)
    glColor3f(1.0, 0.0, 0.0)
    glVertex2f(pts[0, 0], pts[0, 1])
    glColor3f(0.0, 0.0, 1.0)
    glVertex2f(pts[1, 0], pts[1, 1])
    glColor3f(0.0, 1.0, 0.0)
    glVertex2f(pts[2, 0], pts[2, 1])
    glEnd()


def main():
    global angulo_centro, angulo_orbita

    setup()

    clock = pygame.time.Clock()
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == QUIT:
                done = True

        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        # Dibujamos ejes y triángulos
        Axis()
        dibujar_triangulo_centro()
        dibujar_triangulo_orbita()

        pygame.display.flip()

        # Actualizamos los ángulos de giro
        angulo_centro += 1.0      # velocidad de rotación del triángulo central
        angulo_orbita += 0.5      # velocidad de órbita del triángulo exterior

        clock.tick(60)            # 60 FPS aprox.

    pygame.quit()


if __name__ == "__main__":
    main()
