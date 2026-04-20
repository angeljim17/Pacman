import pygame
from pygame.locals import *

# Cargamos las bibliotecas de OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import numpy as np

pygame.init()

screen_width = 900
screen_height = 900

#Variables para dibujar los ejes del sistema
X_MIN=-500
X_MAX=500
Y_MIN=-500
Y_MAX=500

#estructura de datos para las coord de los vertices del triangulo
points = np.array([[-300,0],[-150,300],[0,0]])
points2 = np.array([[300,0],[150,300],[0,0]])

def Axis():
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glShadeModel(GL_SMOOTH)
    glLineWidth(3.0)
    #X
    glBegin(GL_LINES)
    #color1
    glColor3f(1.0,0.0,0.0)
    glVertex2f(X_MIN,0.0)
    #color2
    glColor3f(0.0,1.0,0.0)
    glVertex2f(X_MAX,0.0)
    glEnd()
    #Y
    glBegin(GL_LINES)
    #color1
    glColor3f(0.0,1.0,1.0)
    glVertex2f(0.0,Y_MIN)
    #color2
    glColor3f(1.0,0.0,1.0)
    glVertex2f(0.0,Y_MAX)
    glEnd()
    glLineWidth(1.0)

def setup():
    screen = pygame.display.set_mode((screen_width, screen_height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("OpenGL: ejes 2D")
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    dimX = screen_width / 2
    dimY = screen_height / 2
    gluOrtho2D(-dimX,dimX,-dimY,dimY)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity() #e0
    glClearColor(0,0,0,0)

#------------------------ main -----------------------
setup()
done = False
while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

    glClear(GL_COLOR_BUFFER_BIT)
    Axis()
    
    pygame.display.flip()
    pygame.time.wait(100)

pygame.quit()