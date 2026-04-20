import math
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *


def _mat_rotate(angle_deg: float) -> np.ndarray:
    """Matriz 3x3 de rotación 2D alrededor del origen."""
    theta = math.radians(angle_deg)
    c = math.cos(theta)
    s = math.sin(theta)
    return np.array([
        [c, -s, 0.0],
        [s,  c, 0.0],
        [0.0, 0.0, 1.0],
    ], dtype=float)


def _mat_translate(tx: float, ty: float) -> np.ndarray:
    """Matriz 3x3 de traslación 2D."""
    return np.array([
        [1.0, 0.0, tx],
        [0.0, 1.0, ty],
        [0.0, 0.0, 1.0],
    ], dtype=float)


def _transform_points(points: np.ndarray, M: np.ndarray) -> np.ndarray:
    """Aplica la transformación afín M (3x3) a puntos 2D (Nx2)."""
    ones = np.ones((points.shape[0], 1), dtype=float)
    pts_h = np.hstack([points, ones])
    res_h = (M @ pts_h.T).T
    return res_h[:, :2]


def vertices_equilatero(r: float) -> np.ndarray:
    """Vértices de un triángulo equilátero centrado en el origen."""
    rad = math.radians
    return np.array([
        [r * math.cos(rad(90)),  r * math.sin(rad(90))],
        [r * math.cos(rad(210)), r * math.sin(rad(210))],
        [r * math.cos(rad(330)), r * math.sin(rad(330))],
    ], dtype=float)


class EscenaTriangulos:

    X_MIN = -500
    X_MAX = 500
    Y_MIN = -500
    Y_MAX = 500

    def __init__(
        self,
        radio_centro: float = 100.0,
        radio_orbita_triangulo: float = 55.0,
        radio_orbita: float = 250.0,
        velocidad_centro: float = 1.0,
        velocidad_orbita: float = 0.5,
        velocidad_propio: float = 2.0,
    ):

        self.points_center = vertices_equilatero(radio_centro)
        self.points_orbit = vertices_equilatero(radio_orbita_triangulo)

        self.radio_orbita = radio_orbita

        self.velocidad_centro = velocidad_centro
        self.velocidad_orbita = velocidad_orbita
        self.velocidad_propio = velocidad_propio

        self.angulo_centro = 0.0
        self.angulo_orbita = 0.0
        self.angulo_propio = 0.0

    def draw_ejes(self) -> None:
        """Dibuja los ejes X e Y."""
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glShadeModel(GL_SMOOTH)
        glLineWidth(3.0)

        glBegin(GL_LINES)

        glColor3f(1.0, 0.0, 0.0)
        glVertex2f(self.X_MIN, 0.0)

        glColor3f(0.0, 1.0, 0.0)
        glVertex2f(self.X_MAX, 0.0)

        glEnd()

        glColor3f(0.0, 1.0, 0.0)

        glBegin(GL_LINES)

        glVertex2f(0.0, self.Y_MIN)
        glVertex2f(0.0, self.Y_MAX)

        glEnd()

        glLineWidth(1.0)

    def draw_triangulo_centro(self) -> None:
        """Dibuja el triángulo del centro girando sobre su propio eje."""

        M = _mat_rotate(self.angulo_centro)

        pts = _transform_points(self.points_center, M)

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

    def draw_triangulo_orbita(self) -> None:
        """Triángulo que orbita y gira sobre su propio eje."""

        T = _mat_translate(self.radio_orbita, 0.0)

        R_orbita = _mat_rotate(self.angulo_orbita)

        R_propio = _mat_rotate(self.angulo_propio)

        M = R_orbita @ T @ R_propio

        pts = _transform_points(self.points_orbit, M)

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

    def update(self) -> None:
        """Actualiza los ángulos de animación."""

        self.angulo_centro += self.velocidad_centro

        self.angulo_orbita += self.velocidad_orbita

        self.angulo_propio += self.velocidad_propio