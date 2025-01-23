import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import random

# Initialize Pygame and OpenGL
pygame.init()
screen_width, screen_height = 750, 650
screen = pygame.display.set_mode((screen_width, screen_height), DOUBLEBUF | OPENGL)
clock = pygame.time.Clock()
FPS = 60

# Set up the camera perspective
gluPerspective(45, (screen_width / screen_height), 0.1, 100.0)
glTranslatef(0.0, 0.0, -20)  # Move the camera back to see the smoke

# Enable blending for transparency
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

# Load texture (smoke image)
IMAGE = pygame.image.load('smoke.png').convert_alpha()

def load_texture(image_surface):
    texture_data = pygame.image.tostring(image_surface, "RGBA", True)
    width, height = image_surface.get_size()

    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)

    return texture_id

# Load the smoke texture
smoke_texture = load_texture(IMAGE)

# Helper function to draw a billboarded quad (2D plane that always faces the camera)
def draw_billboarded_quad(size, texture, x, y, z):
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture)

    # Get the current modelview matrix
    modelview = np.array(glGetFloatv(GL_MODELVIEW_MATRIX)).reshape((4, 4))

    # Extract the right and up vectors from the modelview matrix
    right = modelview[0][:3]
    up = modelview[1][:3]

    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex3f(x - right[0] * size - up[0] * size, y - right[1] * size - up[1] * size, z - right[2] * size - up[2] * size)
    
    glTexCoord2f(1, 0)
    glVertex3f(x + right[0] * size - up[0] * size, y + right[1] * size - up[1] * size, z + right[2] * size - up[2] * size)
    
    glTexCoord2f(1, 1)
    glVertex3f(x + right[0] * size + up[0] * size, y + right[1] * size + up[1] * size, z + right[2] * size + up[2] * size)
    
    glTexCoord2f(0, 1)
    glVertex3f(x - right[0] * size + up[0] * size, y - right[1] * size + up[1] * size, z - right[2] * size + up[2] * size)
    glEnd()

    glDisable(GL_TEXTURE_2D)

class SmokeParticle3D:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z
        self.size = 0.1  # Start even smaller for a tighter base
        self.alpha = 1.0
        self.alpha_rate = 0.015  # Slow down alpha fading for a longer smoke trail
        self.vx = random.uniform(-0.01, 0.01)  # Minimal horizontal movement at the start
        self.vy = 0.2 + random.random() * 0.1  # Faster vertical movement
        self.vz = random.uniform(-0.01, 0.01)
        self.dispersion_rate = 0.002  # Increased dispersion rate as particles rise

    def update(self):
        # Update position and simulate expansion as the particle moves upwards
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz

        # Increase size and horizontal velocity as the particle rises
        self.size += 0.01  # Grow faster for thicker smoke
        self.vx += self.dispersion_rate * random.choice([-1, 1])
        self.vz += self.dispersion_rate * random.choice([-1, 1])
        
        # Fade out the particle
        self.alpha -= self.alpha_rate
        if self.alpha <= 0:
            self.alpha = 0

    def draw(self):
        glColor4f(1, 1, 1, self.alpha)
        draw_billboarded_quad(self.size, smoke_texture, self.x, self.y, self.z)

class Smoke3D:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z
        self.particles = []

    def update(self):
        self.particles = [p for p in self.particles if p.alpha > 0]  # Remove dead particles
        for _ in range(5):  # Increase particle count for denser smoke
            self.particles.append(SmokeParticle3D(self.x, self.y, self.z))
        for particle in self.particles:
            particle.update()

    def draw(self):
        for particle in self.particles:
            particle.draw()

smoke3d = Smoke3D()

def main():
    rotate_x, rotate_y = 0, 0
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                quit()

        keys = pygame.key.get_pressed()
        if keys[K_LEFT]:
            rotate_y -= 1
        if keys[K_RIGHT]:
            rotate_y += 1
        if keys[K_UP]:
            rotate_x -= 1
        if keys[K_DOWN]:
            rotate_x += 1

        # Clear the screen and depth buffer
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Apply camera rotation
        glPushMatrix()
        glRotatef(rotate_x, 1, 0, 0)
        glRotatef(rotate_y, 0, 1, 0)

        # Update and draw the smoke particles
        smoke3d.update()
        smoke3d.draw()

        glPopMatrix()

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
