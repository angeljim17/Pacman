import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

from triangulos_opengl import EscenaTriangulos


deg = 0
delta_deg = 1


def setup(ancho: int, alto: int) -> None:

    pygame.display.set_mode((ancho, alto), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("OpenGL: triángulos con pila de estados")

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    medio_x = ancho / 2
    medio_y = alto / 2

    gluOrtho2D(-medio_x, medio_x, -medio_y, medio_y)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glClearColor(0.0, 0.0, 0.0, 1.0)


def main() -> None:

    global deg

    pygame.init()

    screen_width = 900
    screen_height = 900

    setup(screen_width, screen_height)

    escena = EscenaTriangulos()

    clock = pygame.time.Clock()
    done = False

    while not done:

        for event in pygame.event.get():
            if event.type == QUIT:
                done = True

        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        escena.draw_ejes()

        # TRIANGULO CENTRAL
        glPushMatrix()

        glRotatef(deg, 0, 0, 1)

        escena.draw_triangulo_centro()

        glPopMatrix()


        # TRIANGULO SATELITE
        glPushMatrix()

        # rotacion de la orbita
        glRotatef(deg, 0, 0, 1)

        # mover a la orbita
        glTranslatef(250, 0, 0)

        # rotacion sobre su propio eje
        glRotatef(deg * 3, 0, 0, 1)

        escena.draw_triangulo_orbita()

        glPopMatrix()


        deg += delta_deg
        deg = deg % 360

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()