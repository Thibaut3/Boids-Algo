import pygame
import sys
import math
import random
import numpy as np
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# Paramètres de la simulation
WIDTH, HEIGHT = 1200, 800
BACKGROUND_COLOR = (0.1, 0.1, 0.2, 1.0)
BOID_COLOR = (1.0, 1.0, 1.0)
NUM_BOIDS = 100
BOID_SIZE = 0.2
MAX_SPEED = 0.3
MAX_FORCE = 0.07
MARGIN = 5

# Dimensions du monde 3D
WORLD_SIZE = 50

# Paramètres des règles
COHESION_RADIUS = 6.0
ALIGNMENT_RADIUS = 4.0
SEPARATION_RADIUS = 2.5

COHESION_FORCE = 0.015
ALIGNMENT_FORCE = 0.075
SEPARATION_FORCE = 0.075











###############
#    BOID     #
###############

class Boid:
    def __init__(self):
        self.position = np.array([
            random.uniform(-WORLD_SIZE/2, WORLD_SIZE/2),
            random.uniform(-WORLD_SIZE/2, WORLD_SIZE/2),
            random.uniform(-WORLD_SIZE/2, WORLD_SIZE/2)
        ], dtype=np.float32)
        
        angle_x = random.uniform(0, 2 * math.pi)
        angle_y = random.uniform(0, 2 * math.pi)
        self.velocity = np.array([
            math.cos(angle_x) * math.sin(angle_y),
            math.sin(angle_x) * math.sin(angle_y),
            math.cos(angle_y)
        ], dtype=np.float32)
        
        self.velocity = self.normalize(self.velocity) * MAX_SPEED
        self.acceleration = np.zeros(3, dtype=np.float32)
    
    def normalize(self, vector):
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm

    def update(self):
        self.velocity += self.acceleration
        speed = np.linalg.norm(self.velocity)
        if speed > MAX_SPEED:
            self.velocity = (self.velocity / speed) * MAX_SPEED
        
        self.position += self.velocity
        self.acceleration = np.zeros(3, dtype=np.float32)
    
    def apply_rules(self, boids):
        cohesion = np.zeros(3, dtype=np.float32)
        alignment = np.zeros(3, dtype=np.float32)
        separation = np.zeros(3, dtype=np.float32)
        
        cohesion_count = 0
        alignment_count = 0
        separation_count = 0
        
        for other in boids:
            if other is self:
                continue
                
            distance = np.linalg.norm(self.position - other.position)
            
            # Cohésion
            if distance < COHESION_RADIUS:
                cohesion += other.position
                cohesion_count += 1
            
            # Alignement
            if distance < ALIGNMENT_RADIUS:
                alignment += other.velocity
                alignment_count += 1
            
            # Séparation
            if distance < SEPARATION_RADIUS:
                diff = self.position - other.position
                if distance > 0:
                    diff /= distance  # Normaliser
                separation += diff
                separation_count += 1
        
        # Application des règles
        if cohesion_count > 0:
            cohesion /= cohesion_count
            cohesion -= self.position
            if np.linalg.norm(cohesion) > 0:
                cohesion = self.normalize(cohesion) * MAX_SPEED
            cohesion -= self.velocity
            if np.linalg.norm(cohesion) > MAX_FORCE:
                cohesion = self.normalize(cohesion) * MAX_FORCE
            cohesion *= COHESION_FORCE
        
        if alignment_count > 0:
            alignment /= alignment_count
            if np.linalg.norm(alignment) > 0:
                alignment = self.normalize(alignment) * MAX_SPEED
            alignment -= self.velocity
            if np.linalg.norm(alignment) > MAX_FORCE:
                alignment = self.normalize(alignment) * MAX_FORCE
            alignment *= ALIGNMENT_FORCE
        
        if separation_count > 0:
            separation /= separation_count
            if np.linalg.norm(separation) > 0:
                separation = self.normalize(separation) * MAX_SPEED
            separation -= self.velocity
            if np.linalg.norm(separation) > MAX_FORCE:
                separation = self.normalize(separation) * MAX_FORCE
            separation *= SEPARATION_FORCE
        
        # Ajout des forces à l'accélération
        self.acceleration += cohesion
        self.acceleration += alignment
        self.acceleration += separation
    
    def edges(self):
        # Rebond sur les bords
        for i in range(3):
            if abs(self.position[i]) > WORLD_SIZE/2:
                if self.position[i] > WORLD_SIZE/2:
                    self.velocity[i] = -abs(self.velocity[i])
                else:
                    self.velocity[i] = abs(self.velocity[i])
                
                # Limitation aux bords
                self.position[i] = max(-WORLD_SIZE/2, min(WORLD_SIZE/2, self.position[i]))
    
    def draw(self):
        glColor3f(*BOID_COLOR)
        
        # Direction du boid
        direction = self.normalize(self.velocity)
        up = np.array([0, 1, 0], dtype=np.float32)
        
        # Calcul de l'orientation
        right = np.cross(direction, up)
        up = np.cross(right, direction)
        
        # Points du triangle 3D
        nose = self.position + direction * BOID_SIZE * 2
        left_wing = self.position - direction * BOID_SIZE + right * BOID_SIZE
        right_wing = self.position - direction * BOID_SIZE - right * BOID_SIZE
        bottom = self.position - direction * BOID_SIZE + up * BOID_SIZE
        
        # Dessin du boid (pyramide)
        glBegin(GL_TRIANGLES)
        # Face avant
        glVertex3f(*nose)
        glVertex3f(*left_wing)
        glVertex3f(*right_wing)
        
        # Aile gauche
        glVertex3f(*nose)
        glVertex3f(*left_wing)
        glVertex3f(*bottom)
        
        # Aile droite
        glVertex3f(*nose)
        glVertex3f(*right_wing)
        glVertex3f(*bottom)
        
        # Base
        glVertex3f(*left_wing)
        glVertex3f(*right_wing)
        glVertex3f(*bottom)
        glEnd()

def draw_grid():
    glColor3f(0.3, 0.3, 0.4)
    glBegin(GL_LINES)
    size = WORLD_SIZE/2
    step = 2.0
    
    for x in np.arange(-size, size + step, step):
        glVertex3f(x, -size, -size)
        glVertex3f(x, -size, size)
        glVertex3f(x, size, -size)
        glVertex3f(x, size, size)
        
    for z in np.arange(-size, size + step, step):
        glVertex3f(-size, -size, z)
        glVertex3f(size, -size, z)
        glVertex3f(-size, size, z)
        glVertex3f(size, size, z)
        
    for y in np.arange(-size, size + step, step):
        glVertex3f(-size, y, -size)
        glVertex3f(-size, y, size)
        glVertex3f(size, y, -size)
        glVertex3f(size, y, size)
    glEnd()

def main():
    # Initialisation PyGame
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Simulation 3D de Boids")
    
    # Configuration OpenGL
    glEnable(GL_DEPTH_TEST)
    glClearColor(*BACKGROUND_COLOR)
    
    # Configuration de la perspective
    gluPerspective(45, (WIDTH/HEIGHT), 0.1, 100.0)
    glTranslatef(0.0, 0.0, -WORLD_SIZE * 2)
    
    # Rotation initiale
    glRotatef(30, 1, 0, 0)
    glRotatef(30, 0, 1, 0)
    
    # Création des boids
    boids = [Boid() for _ in range(NUM_BOIDS)]
    
    # Variables de contrôle de la caméra
    clock = pygame.time.Clock()
    mouse_dragging = False
    last_mouse_pos = (0, 0)
    rotation_x, rotation_y = 30, 30
    zoom = WORLD_SIZE * 2
    

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Clic gauche
                    mouse_dragging = True
                    last_mouse_pos = event.pos
                elif event.button == 4:  # Molette vers le haut
                    zoom = max(WORLD_SIZE, zoom - 1)
                elif event.button == 5:  # Molette vers le bas
                    zoom = min(WORLD_SIZE * 4, zoom + 1)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Relâchement clic gauche
                    mouse_dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if mouse_dragging:
                    dx = event.pos[0] - last_mouse_pos[0]
                    dy = event.pos[1] - last_mouse_pos[1]
                    rotation_y += dx * 0.5
                    rotation_x += dy * 0.5
                    last_mouse_pos = event.pos
        
        # Effacer les buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Positionner la caméra
        glLoadIdentity()
        gluPerspective(45, (WIDTH/HEIGHT), 0.1, 100.0)
        glTranslatef(0, 0, -zoom)
        glRotatef(rotation_x, 1, 0, 0)
        glRotatef(rotation_y, 0, 1, 0)
        
        # Dessiner la grille
        draw_grid()
        
        # Mettre à jour et dessiner les boids
        for boid in boids:
            boid.apply_rules(boids)
            boid.update()
            boid.edges()
            boid.draw()
        
        # Mettre à jour l'affichage
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()