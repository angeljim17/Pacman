import heapq
import math
import random

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
    glTexCoord2f,
    glTranslatef,
    glVertex2f,
)


def a_estrella(mapa, inicio, meta, nodos_evitar=None, penalizacion=4):
    if inicio is None or meta is None or inicio == meta:
        return []

    nodos_evitar = set(nodos_evitar or ())

    def heuristica(n):
        return abs(n[0] - meta[0]) + abs(n[1] - meta[1])

    nodos_abiertos = [(heuristica(inicio), 0, inicio)]
    procedencia = {}
    costo_acumulado = {inicio: 0}
    nodos_cerrados = set()
    contador = 0

    while nodos_abiertos:
        _, _, actual = heapq.heappop(nodos_abiertos)
        if actual in nodos_cerrados:
            continue
        if actual == meta:
            camino_resultante = []
            nodo = actual
            while nodo in procedencia:
                camino_resultante.append(nodo)
                nodo = procedencia[nodo]
            camino_resultante.reverse()
            return camino_resultante
        nodos_cerrados.add(actual)

        for vecino in mapa.vecinos(actual):
            extra = penalizacion if vecino in nodos_evitar and vecino != meta else 0
            nuevo_costo = costo_acumulado[actual] + 1 + extra
            if nuevo_costo >= costo_acumulado.get(vecino, math.inf):
                continue
            costo_acumulado[vecino] = nuevo_costo
            procedencia[vecino] = actual
            f = nuevo_costo + heuristica(vecino)
            contador += 1
            heapq.heappush(nodos_abiertos, (f, contador, vecino))

    return []


class Ghost:
    LADO_SPRITE = 6.5

    def __init__(
        self,
        mapa,
        fila_inicial,
        col_inicial,
        tipo,
        velocidad=1.8,
        semilla=None,
        frames_espera=0,
        lado_sprite=None,
    ):
        self.mapa = mapa
        self.tipo = tipo
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
        self.angulo = 0.0
        self.camino_resultante = []

        self.aleatorizador = random.Random(semilla)

        self.frames_espera = max(0, int(frames_espera))
        self.salio_de_caja = False

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

    def _opciones_validas(self):
        opciones = self.mapa.vecinos(self.nodo_actual)
        if self.salio_de_caja:
            opciones = [v for v in opciones if not self.mapa.es_nodo_caja_fantasmas(v)]
        if not opciones:
            return []
        if self.direccion_actual == (0, 0) or len(opciones) == 1:
            return opciones
        opuesta = (-self.direccion_actual[0], -self.direccion_actual[1])
        sin_reversa = [
            v for v in opciones
            if self.mapa.direccion_entre(self.nodo_actual, v) != opuesta
        ]
        return sin_reversa or opciones

    def _decidir_aleatorio(self):
        opciones = self._opciones_validas()
        if not opciones:
            return None
        return self.aleatorizador.choice(opciones)

    def _decidir_euclides(self, pacman):
        opciones = self._opciones_validas()
        if not opciones:
            return None

        def distancia_objetivo(nodo):
            nx, ny = self.mapa.posicion(nodo)
            return math.hypot(nx - pacman.px, ny - pacman.py)

        return min(opciones, key=distancia_objetivo)

    def _meta_lider(self, pacman):
        adelantamiento = 3
        dx, dy = pacman.direccion_actual if pacman.direccion_actual != (0, 0) else (1, 0)
        objetivo = (
            pacman.nodo_actual[0] + dy * adelantamiento,
            pacman.nodo_actual[1] + dx * adelantamiento,
        )
        if self.mapa.es_transitable(objetivo):
            return objetivo
        return pacman.nodo_actual

    def _meta_soporte(self, pacman, fantasmas):
        lider = next((f for f in fantasmas if f.tipo == "cooperativo_1"), None)
        adelantamiento = 2
        dx, dy = pacman.direccion_actual if pacman.direccion_actual != (0, 0) else (-1, 0)
        adelante_pacman = (
            pacman.nodo_actual[0] + dy * adelantamiento,
            pacman.nodo_actual[1] + dx * adelantamiento,
        )
        if lider is None:
            objetivo = adelante_pacman
        else:
            objetivo = (
                adelante_pacman[0] + (adelante_pacman[0] - lider.nodo_actual[0]),
                adelante_pacman[1] + (adelante_pacman[1] - lider.nodo_actual[1]),
            )
        if self.mapa.es_transitable(objetivo):
            return objetivo
        return self.mapa.nodo_mas_cercano(*self.mapa.posicion(adelante_pacman))

    def _decidir_cooperativo(self, pacman, fantasmas, lider):
        if lider:
            meta = self._meta_lider(pacman)
            ruta = a_estrella(self.mapa, self.nodo_actual, meta)
        else:
            meta = self._meta_soporte(pacman, fantasmas)
            ruta_lider_otros = []
            companero = next((f for f in fantasmas if f.tipo == "cooperativo_1"), None)
            if companero is not None:
                ruta_lider_otros = list(companero.camino_resultante[:6])
                if companero.nodo_objetivo:
                    ruta_lider_otros.append(companero.nodo_objetivo)
            ruta = a_estrella(
                self.mapa, self.nodo_actual, meta,
                nodos_evitar=ruta_lider_otros, penalizacion=3,
            )

        self.camino_resultante = ruta
        if not ruta:
            return None
        siguiente = ruta[0]
        if siguiente == self.nodo_anterior:
            opciones = self._opciones_validas()
            for opcion in opciones:
                if opcion != self.nodo_anterior:
                    return opcion
        return siguiente

    def _decidir(self, pacman, fantasmas):
        if self.tipo == "aleatorio":
            return self._decidir_aleatorio()
        if self.tipo == "euclides":
            return self._decidir_euclides(pacman)
        if self.tipo == "cooperativo_1":
            return self._decidir_cooperativo(pacman, fantasmas, lider=True)
        if self.tipo == "cooperativo_2":
            return self._decidir_cooperativo(pacman, fantasmas, lider=False)
        return self._decidir_aleatorio()

    def _decidir_salida_caja(self):
        if not self.mapa.es_nodo_caja_fantasmas(self.nodo_actual):
            return None

        if self.mapa.es_puerta_interior_caja_fantasmas(self.nodo_actual):
            destinos = [
                d for d in ((12, 13), (12, 14))
                if d in self.mapa.vecinos(self.nodo_actual)
            ]
            if destinos:
                return self.aleatorizador.choice(destinos)

        metas_interiores = ((13, 13), (13, 14))
        rutas = []
        for meta in metas_interiores:
            ruta = a_estrella(self.mapa, self.nodo_actual, meta)
            if ruta:
                rutas.append(ruta)
        if rutas:
            mejor_longitud = min(len(ruta) for ruta in rutas)
            candidatas = [ruta for ruta in rutas if len(ruta) == mejor_longitud]
            mejor = self.aleatorizador.choice(candidatas)
            self.camino_resultante = mejor
            return mejor[0]

        metas_exteriores = ((12, 13), (12, 14))
        rutas = []
        for meta in metas_exteriores:
            ruta = a_estrella(self.mapa, self.nodo_actual, meta)
            if ruta:
                rutas.append(ruta)
        if rutas:
            mejor_longitud = min(len(ruta) for ruta in rutas)
            candidatas = [ruta for ruta in rutas if len(ruta) == mejor_longitud]
            mejor = self.aleatorizador.choice(candidatas)
            self.camino_resultante = mejor
            return mejor[0]
        return None

    def _actualizar_estado_salida_caja(self):
        if self.mapa.es_puerta_exterior_caja_fantasmas(self.nodo_actual):
            self.salio_de_caja = True

    def _elegir_objetivo(self, pacman, fantasmas):
        opciones = self.mapa.vecinos(self.nodo_actual)
        if not opciones:
            return

        salida_forzada = self._decidir_salida_caja()
        if salida_forzada is not None:
            self.nodo_objetivo = salida_forzada
            self.direccion_actual = self.mapa.direccion_entre(
                self.nodo_actual, salida_forzada
            )
            self.angulo = self._angulo_direccion(self.direccion_actual)
            return

        if (
            self.direccion_actual != (0, 0)
            and not self.mapa.es_interseccion(self.nodo_actual, self.direccion_actual)
        ):
            siguiente = self.mapa.vecino_en_direccion(
                self.nodo_actual, self.direccion_actual
            )
            if siguiente is not None:
                self.nodo_objetivo = siguiente
                return

        siguiente = self._decidir(pacman, fantasmas)
        if siguiente is None:
            validas = self._opciones_validas()
            siguiente = validas[0] if validas else opciones[0]

        self.nodo_objetivo = siguiente
        self.direccion_actual = self.mapa.direccion_entre(self.nodo_actual, siguiente)
        self.angulo = self._angulo_direccion(self.direccion_actual)

    def actualizar(self, pacman, fantasmas=None):
        fantasmas = fantasmas or []

        if self.frames_espera > 0:
            self.frames_espera -= 1
            return

        if self.nodo_objetivo == self.nodo_actual:
            self._elegir_objetivo(pacman, fantasmas)

        objetivo_x, objetivo_y = self.mapa.posicion(self.nodo_objetivo)
        dx = objetivo_x - self.px
        dy = objetivo_y - self.py
        distancia = math.hypot(dx, dy)

        if distancia <= self.velocidad:
            self.px, self.py = objetivo_x, objetivo_y
            self.nodo_anterior = self.nodo_actual
            self.nodo_actual = self.nodo_objetivo
            self._actualizar_estado_salida_caja()
            self._elegir_objetivo(pacman, fantasmas)
        else:
            self.px += self.velocidad * dx / distancia
            self.py += self.velocidad * dy / distancia

    def update2(self, pacman, fantasmas=None):
        self.actualizar(pacman, fantasmas)

    def _dibujar_sprite(self):
        s = self.lado_sprite
        glPushMatrix()
        glTranslatef(self.px, self.py, 0.0)
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
