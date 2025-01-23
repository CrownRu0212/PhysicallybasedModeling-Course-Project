import random
import numpy as np

class SmokeParticle3D:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z
        self.size = 0.1
        self.alpha = 1.0
        self.alpha_rate = 0.015
        self.vx = random.uniform(-0.01, 0.01)
        self.vy = 0.2 + random.random() * 0.1
        self.vz = random.uniform(-0.01, 0.01)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz
        self.alpha -= self.alpha_rate
        if self.alpha < 0:
            self.alpha = 0

class Smoke3D:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z
        self.particles = []

    def update(self):
        self.particles = [p for p in self.particles if p.alpha > 0]
        for _ in range(5):  # Add new particles
            self.particles.append(SmokeParticle3D(self.x, self.y, self.z))
        for p in self.particles:
            p.update()
