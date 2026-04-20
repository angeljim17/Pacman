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

deltaX = 1
steps1 = 0
steps2 = 0
maxsteps = 50

def Axis():
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glShadeModel(GL_SMOOTH)
    glLineWidth(3.0)
    #X axis in red
    #glColor3f(1.0,0.0,0.0)
    glBegin(GL_LINES)
    glColor3f(1.0,0.0,0.0)
    glVertex2f(X_MIN,0.0)
    glColor3f(0.0,1.0,0.0)
    glVertex2f(X_MAX,0.0)
    glEnd()
    #Y axis in green
    glColor3f(0.0,1.0,0.0)
    glBegin(GL_LINES)
    glVertex2f(0.0,Y_MIN)
    glVertex2f(0.0,Y_MAX)
    glEnd()
    glLineWidth(1.0)

def display1():
    glPolygonMode(GL_BACK, GL_FILL)
    glShadeModel(GL_SMOOTH)  
    glBegin(GL_TRIANGLES)
    glColor3f(1.0, 0.0, 0.0)
    glVertex2iv(points[0])
    glColor3f(0.0, 1.0, 0.0)
    glVertex2iv(points[1])
    glColor3f(0.0, 0.0, 1.0)
    glVertex2iv(points[2])
    glEnd()
    

def display2():
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glShadeModel(GL_SMOOTH)
    glBegin(GL_TRIANGLES)
    glColor3f(1.0, 0.0, 0.0)
    glVertex2iv(points2[2])
    glColor3f(0.0, 0.0, 1.0)
    glVertex2iv(points2[0])
    glColor3f(0.0, 1.0, 0.0)
    glVertex2iv(points2[1])
    glEnd()

def setup():
    screen = pygame.display.set_mode((screen_width, screen_height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("OpenGL: ejes 2D")
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-450,450,-450,450)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glClearColor(0,0,0,0)


setup()
done = False
while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

    glClear(GL_COLOR_BUFFER_BIT)
    Axis()
    display1()
    update1()
    display2()
    
    pygame.display.flip()
    pygame.time.wait(100)

pygame.quit()