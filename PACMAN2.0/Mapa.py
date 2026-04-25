from __future__ import annotations

from collections import deque
from typing import Iterable, List, Optional, Tuple

from PIL import Image


Nodo = Tuple[int, int]
Direccion = Tuple[int, int]


class Mapa:
    _COLOR_PARED = (33, 33, 222)
    UMBRAL_CELDA_TRANSITABLE = 0.92
    RADIO_SEGURIDAD_ESQUINA = 1
    _FILAS_CAJA_FANTASMAS = (13, 14, 15)
    _COLUMNAS_CAJA_FANTASMAS = (11, 12, 13, 14, 15, 16)
    _PUERTA_INTERIOR_CAJA = ((13, 13), (13, 14))
    _PUERTA_EXTERIOR_CAJA = ((12, 13), (12, 14))
    NODOS_BLOQUEADOS_MANUALES = {
        (28, 2), (28, 11), (28, 13), (28, 14), (28, 16), (28, 25),
        (27, 2), (27, 11), (27, 13), (27, 14), (27, 16), (27, 25),
        (25, 2), (25, 4), (25, 5), (25, 10), (25, 17), (25, 22), (25, 23), (25, 25),
        (24, 2), (24, 7), (24, 8), (24, 10), (24, 17), (24, 19), (24, 20), (24, 25),
        (22, 2), (22, 11), (22, 13), (22, 14), (22, 16), (22, 20), (22, 25),
        (21, 2), (21, 5), (21, 7), (21, 11), (21, 16), (21, 20), (21, 22), (21, 25),
        (19, 5), (19, 7), (19, 8), (19, 10), (19, 17), (19, 19), (19, 20), (19, 22),
        (18, 10), (18, 17),
        (16, 10), (16, 17),
        (15, 5), (15, 7), (15, 8), (15, 19), (15, 20), (15, 22),
        (13, 5), (13, 7), (13, 8), (13, 19), (13, 20), (13, 22),
        (12, 10), (12, 17),
        (10, 11), (10, 13), (10, 14), (10, 16),
        (9, 5), (9, 11), (9, 16), (9, 22),
        (7, 2), (7, 5), (7, 10), (7, 17), (7, 22), (7, 25),
        (6, 2), (6, 5), (6, 7), (6, 8), (6, 10), (6, 17), (6, 19), (6, 20), (6, 22), (6, 25),
        (4, 2), (4, 5), (4, 7), (4, 11), (4, 13), (4, 14), (4, 16), (4, 20), (4, 22), (4, 25),
        (2, 2), (2, 5), (2, 7), (2, 11), (2, 16), (2, 20), (2, 22), (2, 25),
    }

    def __init__(
        self,
        ruta_bmp: str,
        ancho_vista: float = 400.0,
        alto_vista: Optional[float] = None,
        escala: int = 16,
    ) -> None:
        imagen = Image.open(ruta_bmp).convert("RGB")
        ancho_bmp, alto_bmp = imagen.size
        pixeles = imagen.load()

        self.ancho_bmp = ancho_bmp
        self.alto_bmp = alto_bmp
        self.escala = int(escala)
        self.columnas = ancho_bmp // self.escala
        self.filas = alto_bmp // self.escala

        self.ancho_vista = float(ancho_vista)
        if alto_vista is None:
            self.alto_vista = float(ancho_vista) * (alto_bmp / ancho_bmp)
        else:
            self.alto_vista = float(alto_vista)

        self._caminable = [[False] * ancho_bmp for _ in range(alto_bmp)]
        for y in range(alto_bmp):
            fila_pix = self._caminable[y]
            for x in range(ancho_bmp):
                fila_pix[x] = pixeles[x, y] != self._COLOR_PARED

        self._corredor = self._aislar_corredor_principal()

        self._adyacencia: dict = {}
        self._construir_grafo()

    def _aislar_corredor_principal(self) -> List[List[bool]]:
        ancho, alto = self.ancho_bmp, self.alto_bmp
        cy, cx = alto // 2, ancho // 2
        inicio = None
        for radio in range(0, max(ancho, alto)):
            if inicio is not None:
                break
            for dy in range(-radio, radio + 1):
                for dx in range(-radio, radio + 1):
                    yy, xx = cy + dy, cx + dx
                    if 0 <= yy < alto and 0 <= xx < ancho and self._caminable[yy][xx]:
                        inicio = (yy, xx)
                        break
                if inicio:
                    break

        corredor = [[False] * ancho for _ in range(alto)]
        if inicio is None:
            return corredor

        cola = deque([inicio])
        corredor[inicio[0]][inicio[1]] = True
        while cola:
            y, x = cola.popleft()
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = y + dy, x + dx
                if (
                    0 <= ny < alto
                    and 0 <= nx < ancho
                    and self._caminable[ny][nx]
                    and not corredor[ny][nx]
                ):
                    corredor[ny][nx] = True
                    cola.append((ny, nx))
        return corredor

    def _pixel_central(self, fila: int, columna: int) -> Tuple[int, int]:
        return (
            fila * self.escala + self.escala // 2,
            columna * self.escala + self.escala // 2,
        )

    def _celda_transitable(self, fila: int, columna: int) -> bool:
        if not (0 <= fila < self.filas and 0 <= columna < self.columnas):
            return False
        cy, cx = self._pixel_central(fila, columna)
        radio = 2
        total = 0
        validos = 0
        for y in range(cy - radio, cy + radio + 1):
            for x in range(cx - radio, cx + radio + 1):
                if 0 <= y < self.alto_bmp and 0 <= x < self.ancho_bmp:
                    total += 1
                    if self._corredor[y][x]:
                        validos += 1
        return total > 0 and validos / total > 0.7

    def _segmento_libre(self, n1: Nodo, n2: Nodo) -> bool:
        y1, x1 = self._pixel_central(*n1)
        y2, x2 = self._pixel_central(*n2)
        pasos = max(abs(y2 - y1), abs(x2 - x1))
        if pasos == 0:
            return True
        for t in range(pasos + 1):
            avance = t / pasos
            y = int(y1 + (y2 - y1) * avance)
            x = int(x1 + (x2 - x1) * avance)
            if not (0 <= y < self.alto_bmp and 0 <= x < self.ancho_bmp):
                return False
            if not self._corredor[y][x]:
                return False
        return True

    def _construir_grafo(self) -> None:
        nodos = [
            (f, c)
            for f in range(self.filas)
            for c in range(self.columnas)
            if self._celda_transitable(f, c)
            and (f, c) not in self.NODOS_BLOQUEADOS_MANUALES
        ]
        for nodo in nodos:
            self._adyacencia[nodo] = []
        for fila, col in nodos:
            for d_fila, d_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                vecino = (fila + d_fila, col + d_col)
                if vecino in self._adyacencia and self._segmento_libre((fila, col), vecino):
                    self._adyacencia[(fila, col)].append(vecino)

    def posicion(self, nodo: Nodo) -> Tuple[float, float]:
        fila, col = nodo
        cx = (col + 0.5) * self.ancho_vista / self.columnas
        cy = (fila + 0.5) * self.alto_vista / self.filas
        return cx, cy

    def nodo_mas_cercano(self, x: float, y: float) -> Optional[Nodo]:
        if not self._adyacencia:
            return None
        mejor = None
        mejor_dist = float("inf")
        for nodo in self._adyacencia:
            nx, ny = self.posicion(nodo)
            d = (nx - x) ** 2 + (ny - y) ** 2
            if d < mejor_dist:
                mejor_dist = d
                mejor = nodo
        return mejor

    def es_transitable(self, nodo: Nodo) -> bool:
        return nodo in self._adyacencia

    def vecinos(self, nodo: Nodo) -> List[Nodo]:
        return list(self._adyacencia.get(nodo, ()))

    def direccion_entre(self, n1: Nodo, n2: Nodo) -> Direccion:
        df = n2[0] - n1[0]
        dc = n2[1] - n1[1]
        return (1 if dc > 0 else -1 if dc < 0 else 0,
                1 if df > 0 else -1 if df < 0 else 0)

    def vecino_en_direccion(self, nodo: Nodo, direccion: Direccion) -> Optional[Nodo]:
        if direccion == (0, 0):
            return None
        candidato = (nodo[0] + direccion[1], nodo[1] + direccion[0])
        if candidato in self._adyacencia and candidato in self._adyacencia[nodo]:
            return candidato
        return None

    def es_interseccion(
        self, nodo: Nodo, direccion_actual: Optional[Direccion] = None
    ) -> bool:
        opciones = self.vecinos(nodo)
        if not opciones:
            return False
        if direccion_actual is None or direccion_actual == (0, 0):
            return len(opciones) >= 3
        opuesta = (-direccion_actual[0], -direccion_actual[1])
        no_opuestas = sum(
            1 for v in opciones
            if self.direccion_entre(nodo, v) != opuesta
        )
        return no_opuestas >= 2

    def es_nodo_caja_fantasmas(self, nodo: Nodo) -> bool:
        fila, col = nodo
        return (
            fila in self._FILAS_CAJA_FANTASMAS
            and col in self._COLUMNAS_CAJA_FANTASMAS
            and self.es_transitable(nodo)
        )

    def es_puerta_interior_caja_fantasmas(self, nodo: Nodo) -> bool:
        return nodo in self._PUERTA_INTERIOR_CAJA

    def es_puerta_exterior_caja_fantasmas(self, nodo: Nodo) -> bool:
        return nodo in self._PUERTA_EXTERIOR_CAJA

    def iterar_nodos(self) -> Iterable[Nodo]:
        return self._adyacencia.keys()

    def cantidad_nodos(self) -> int:
        return len(self._adyacencia)
