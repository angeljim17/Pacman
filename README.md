# Pacman 3D — Juego con OpenGL y Pygame

Implementación de **Pacman** en Python con renderizado **3D/OpenGL** y Pygame. Incluye mapa personalizable, fantasmas con IA y ejemplos de gráficos 2D/3D.

## Stack

- Python 3
- Pygame
- PyOpenGL
- NumPy

## Estructura

```
Pacman/
├── PACMAN2.0/
│   ├── main.py        # Punto de entrada del juego
│   ├── Pacman.py      # Lógica del jugador
│   ├── Ghost.py       # Lógica de fantasmas
│   ├── Mapa.py        # Carga y renderizado del mapa
│   └── mapa.csv       # Definición del laberinto
├── Ejemplo1 HolaMundo.py
├── Ejemplo2D_ejes.py
├── Ejemplo2D_triangulos.py
└── Ejemplo2 Ejes3D.py
```

## Funcionalidades

- Laberinto cargado desde CSV
- Pacman y fantasmas con movimiento en mapa 3D
- Renderizado con texturas OpenGL
- Ejemplos progresivos de gráficos 2D y 3D

## Cómo ejecutar

```bash
pip install pygame PyOpenGL numpy
cd PACMAN2.0
python main.py
```

## Autor

**Ángel Jiménez Morales** — [GitHub](https://github.com/angeljim17)
