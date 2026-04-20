import pygame
from pygame.locals import *

# Cargamos las bibliotecas de OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import math
import os
import numpy as np
import pandas as pd

from Pacman import Pacman
from Ghost import Ghost, NavigationGraph

screen_width = 800
screen_height = 800

#Variables para dibujar los ejes del sistema
X_MIN=-500
X_MAX=500
Y_MIN=-500
Y_MAX=500
#Dimension del plano
DimBoard = 400

#Arreglo para el manejo de texturas
textures = []
#Nombre de los archivos a usar
BASE_PATH = os.path.abspath(os.path.dirname(__file__))
file_1 = os.path.join(BASE_PATH, 'mapa.bmp')
img_pacman = os.path.join(BASE_PATH, 'pacman.bmp')
img_ghost1 = os.path.join(BASE_PATH, 'fantasma1.bmp')
img_ghost2 = os.path.join(BASE_PATH, 'fantasma2.bmp')
img_ghost3 = os.path.join(BASE_PATH, 'fantasma3.bmp')
img_ghost4 = os.path.join(BASE_PATH, 'fantasma4.bmp')


file_csv = os.path.join(BASE_PATH, 'mapa.csv')
matrix = np.array(pd.io.parsers.read_csv(file_csv, header=None)).astype("int")

#Matriz de Control para mapeo entre pixeles <-> coord donde se localizan esquinas
MC = [
    [10,0,21,0,11,10,0,21,0,11],
    [24,0,25,21,23,23,21,25,0,22],
    [12,0,22,12,11,10,13,24,0,13],
    [0,0,0,10,23,23,11,0,0,0],
    [26,0,25,22,0,0,24,25,0,27],
    [0,0,0,24,0,0,22,0,0,0],
    [10,0,25,23,11,10,23,25,0,11],
    [12,11,24,21,23,23,21,22,10,13],
    [10,23,13,12,11,10,13,12,23,11],
    [12,0,0,0,23,23,0,0,0,13]
]

xMC = [0,30,71,114,156,199,242,286,328,358]

XPxToMC = np.full(359, -1, dtype=int)
XPxToMC[0] = 0
XPxToMC[30] = 1
XPxToMC[71] = 2
XPxToMC[114] = 3
XPxToMC[156] = 4
XPxToMC[199] = 5
XPxToMC[242] = 6
XPxToMC[286] = 7
XPxToMC[328] = 8
XPxToMC[358] = 9
 
yMC = [0,51,90,130,168,208,244,282,320,360]
#YPxToMC = np.zeros((361,), dtype=int)
YPxToMC = np.full(361, -1, dtype=int)
YPxToMC[0] = 0
YPxToMC[51] = 1
YPxToMC[90] = 2
YPxToMC[130] = 3
YPxToMC[168] = 4
YPxToMC[208] = 5
YPxToMC[244] = 6
YPxToMC[282] = 7
YPxToMC[320] = 8
YPxToMC[360] = 9

#pathfinding variables
path = []
grid = []

pc = Pacman(matrix, MC, XPxToMC, YPxToMC, view_size=float(DimBoard))
ghost_nav = NavigationGraph(matrix, view_size=float(DimBoard), actor_radius=Ghost.NAV_RADIUS, step=Ghost.NAV_STEP)
ghost_house_exit = (200.0, 150.0)
ghosts = [
    Ghost(matrix, MC, XPxToMC, YPxToMC, 186.0, 186.0, 180.0, "random", view_size=float(DimBoard), navigator=ghost_nav, release_delay_ms=0, house_exit_xy=ghost_house_exit),
    Ghost(matrix, MC, XPxToMC, YPxToMC, 202.0, 186.0, 0.0, "euclid", view_size=float(DimBoard), navigator=ghost_nav, release_delay_ms=3000, house_exit_xy=ghost_house_exit),
    Ghost(matrix, MC, XPxToMC, YPxToMC, 218.0, 186.0, 270.0, "astar_lead", view_size=float(DimBoard), navigator=ghost_nav, release_delay_ms=6000, house_exit_xy=ghost_house_exit),
    Ghost(matrix, MC, XPxToMC, YPxToMC, 202.0, 222.0, 90.0, "astar_support", view_size=float(DimBoard), navigator=ghost_nav, release_delay_ms=9000, house_exit_xy=ghost_house_exit),
]


pygame.init()

def Axis():
    glShadeModel(GL_FLAT)
    glLineWidth(3.0)
    #X axis in red
    glColor3f(1.0,0.0,0.0)
    glBegin(GL_LINES)
    glVertex3f(X_MIN,0.0,0.0)
    glVertex3f(X_MAX,0.0,0.0)
    glEnd()
    #Y axis in green
    glColor3f(0.0,1.0,0.0)
    glBegin(GL_LINES)
    glVertex3f(0.0,Y_MIN,0.0)
    glVertex3f(0.0,Y_MAX,0.0)
    glEnd()
    glLineWidth(1.0)

def Texturas(filepath):
    textures.append(glGenTextures(1))
    id = len(textures) - 1
    glBindTexture(GL_TEXTURE_2D, textures[id])
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T, GL_CLAMP)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    image = pygame.image.load(filepath).convert()
    w, h = image.get_rect().size
    image_data = pygame.image.tostring(image,"RGBA")
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
    glGenerateMipmap(GL_TEXTURE_2D) 
    
def Init():
    screen = pygame.display.set_mode(
        (400, 400), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("OpenGL: cubos")
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0,400,400,0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glClearColor(0,0,0,0)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    #textures[0]: plano
    Texturas(file_1)
    #textures[1]: pacman
    Texturas(img_pacman)
    #textures[2]: fantasma1
    Texturas(img_ghost1)
    #textures[3]: fantasma2
    Texturas(img_ghost2)
    #textures[4]: fantasma3
    Texturas(img_ghost3)
    #textures[5]: fantasma4
    Texturas(img_ghost4)
    pc.loadTextures(textures, 1)
    ghosts[0].loadTextures(textures, 2)
    ghosts[1].loadTextures(textures, 3)
    ghosts[2].loadTextures(textures, 4)
    ghosts[3].loadTextures(textures, 5)
    
def PlanoTexturizado():
    #Activate textures
    glColor3f(1.0,1.0,1.0)
    glEnable(GL_TEXTURE_2D)
    #front face
    glBindTexture(GL_TEXTURE_2D, textures[0])    
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex2d(0, 0)
    glTexCoord2f(0.0, 1.0)
    glVertex2d(0, DimBoard)
    glTexCoord2f(1.0, 1.0)
    glVertex2d(DimBoard, DimBoard)
    glTexCoord2f(1.0, 0.0)
    glVertex2d(DimBoard, 0)
    glEnd()              
    glDisable(GL_TEXTURE_2D)
    
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    Axis()
    PlanoTexturizado()
    pc.draw()
    for ghost in ghosts:
        ghost.draw()
    
done = False
Init()
clock = pygame.time.Clock()

while not done:
    dt_ms = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                done = True
    
    keys = pygame.key.get_pressed()
    pc.update(keys)
    for ghost in ghosts:
        ghost.update2(pc, ghosts, dt_ms=dt_ms)

    display()
    pygame.display.flip()

pygame.quit()
    

