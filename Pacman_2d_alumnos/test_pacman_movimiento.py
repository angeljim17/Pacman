"""
Pruebas del mapeo tablero 400×400 ↔ mapa 361×359 (filas × columnas) y colisiones.

Ejecutar: python -m pytest test_pacman_movimiento.py -v
"""
import os

import numpy as np
import pandas as pd
import pytest
from pygame.locals import K_LEFT, K_RIGHT

from Pacman import Pacman

BASE = os.path.abspath(os.path.dirname(__file__))
MAP_CSV = os.path.join(BASE, "mapa.csv")

MC = [[0] * 10 for _ in range(10)]
XPxToMC = np.zeros(359, dtype=int)
YPxToMC = np.zeros(361, dtype=int)
VIEW = 400.0


class _KeysRightOnly:
    def __getitem__(self, k):
        return k == K_RIGHT


class _KeysLeftOnly:
    def __getitem__(self, k):
        return k == K_LEFT


@pytest.fixture(scope="module")
def matrix():
    return np.array(pd.read_csv(MAP_CSV, header=None)).astype(int)


@pytest.fixture(scope="module")
def pac(matrix):
    return Pacman(matrix, MC, XPxToMC, YPxToMC, view_size=VIEW)


def test_mapa_shape_361_359(matrix):
    assert matrix.shape == (361, 359)


def test_spawn_sobre_celda_transitable(matrix, pac):
    r, c = pac._gl_to_rc(pac.px, pac.py)
    assert matrix[r, c] == 0


def test_spawn_respeta_mascara_de_colision(pac):
    assert pac._walkable(pac.px, pac.py, pac.angle)


def test_roundtrip_centro_celda(matrix):
    for r, c in [(50, 50), (180, 179), (100, 200)]:
        if matrix[r, c] != 0:
            continue
        px = (c + 0.5) * VIEW / matrix.shape[1]
        py = (r + 0.5) * VIEW / matrix.shape[0]
        p = Pacman(matrix, MC, XPxToMC, YPxToMC, view_size=VIEW)
        r2, c2 = p._gl_to_rc(px, py)
        assert (r2, c2) == (r, c)


def test_no_atraviesa_muro_vertical(matrix, pac):
    """Celda 0 con muro a la derecha: al pulsar derecha casi no avanza."""
    found = None
    for r in range(1, matrix.shape[0] - 1):
        for c in range(1, matrix.shape[1] - 2):
            if matrix[r, c] == 0 and matrix[r, c + 1] != 0:
                found = (r, c)
                break
        if found:
            break
    assert found is not None, "mapa sin patrón transitable|muro"
    r, c = found

    px, py = pac._rc_to_gl_center(r, c)
    pac.px, pac.py = px, py
    before_x = pac.px
    keys = _KeysRightOnly()
    for _ in range(80):
        pac.update(keys)
    assert pac.px - before_x < pac.speed * 3


def test_borde_fuera_no_es_transitable(pac):
    pac.px, pac.py = 5.0, 5.0
    assert not pac._walkable(-1.0, 5.0)
    assert not pac._walkable(5.0, -1.0)
    assert not pac._walkable(VIEW + 20.0, 5.0)


def test_celda_muro_no_transitable(matrix, pac):
    wall = np.argwhere(matrix != 0)
    assert wall.size > 0
    r, c = int(wall[0, 0]), int(wall[0, 1])
    px, py = pac._rc_to_gl_center(r, c)
    assert not pac._walkable(px, py)


def test_mapa_10x10_mantiene_radio_y_velocidad_clasicos():
    """Con 10×10, celda=40: radio 8 y speed 2.5 como en el diseño original."""
    m = np.zeros((10, 10), dtype=int)
    p = Pacman(m, MC, XPxToMC, YPxToMC, view_size=400.0)
    assert abs(p.radius - 8.0) < 1e-6
    assert abs(p.speed - 2.5) < 1e-6


def test_mascara_visible_se_detiene_justo_antes_del_muro():
    m = np.zeros((400, 400), dtype=int)
    m[:, 250:] = 1
    p = Pacman(m, MC, np.zeros(400, dtype=int), np.zeros(400, dtype=int), view_size=400.0)

    keys = _KeysRightOnly()
    for _ in range(120):
        before = p.px
        p.update(keys)
        if abs(p.px - before) < 1e-9:
            break

    front_x = p.px + max(x for x, _ in p._collision_points(0.0))
    assert abs(front_x - 250.0) <= 1.0
    assert p._walkable(p.px, p.py, 0.0)


def test_tunel_central_envuelve_de_izquierda_a_derecha(pac):
    assert pac.tunnel_rows, "el mapa no expone un túnel lateral central"
    tunnel_rows = sorted(pac.tunnel_rows)
    tunnel_row = tunnel_rows[len(tunnel_rows) // 2]
    py = (tunnel_row + 0.5) * VIEW / pac.map_rows

    start_x = None
    for px in np.linspace(8.0, 40.0, 33):
        if pac._walkable(float(px), py, 180.0):
            start_x = float(px)
            break

    assert start_x is not None, "no se encontró una entrada caminable al túnel"
    pac.px, pac.py = start_x, py
    pac.angle = 180.0

    keys = _KeysLeftOnly()
    left_exit = False
    right_reentry = False
    for _ in range(90):
        pac.update(keys)
        if pac.px < 0.0:
            left_exit = True
        if left_exit and pac.px > VIEW:
            right_reentry = True
            break

    assert left_exit, "Pacman no salió completamente por el lateral izquierdo"
    assert right_reentry, "Pacman no reapareció por fuera del lateral derecho"
