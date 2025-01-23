import random
import numpy as np

class SmokeParticle3D:
    def __init__(self, x=0, y=0, z=0, max_height=1.0):
        self.x = x
        self.y = y
        self.z = z
        self.size = 0.05   # Slightly larger to see better
        self.alpha = 1.0
        self.alpha_rate = 0.01
        self.vx = random.uniform(-0.005, 0.005)
        self.vy = 0.01 + random.random() * 0.01
        self.vz = random.uniform(-0.005, 0.005)
        self.max_height = max_height

    def update(self):
        # Move the particle
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz

        # If it reaches the max height, stop ascending
        if self.y > self.max_height:
            self.y = self.max_height
            self.vy = 0.0
            # Optionally reduce alpha decay to slow or stop fading
            self.alpha_rate = 0.005  # Fade slower at the top

        # Update alpha
        self.alpha -= self.alpha_rate
        if self.alpha < 0:
            self.alpha = 0

class Smoke3D:
    def __init__(self, x=0, y=0, z=0, max_height=1.0):
        self.x = x
        self.y = y
        self.z = z
        self.particles = []
        self.max_height = max_height

    def update(self):
        # Remove dead particles
        self.particles = [p for p in self.particles if p.alpha > 0]
        # Generate new particles
        for _ in range(20):
            self.particles.append(SmokeParticle3D(self.x, self.y, self.z, self.max_height))
        # Update all particles
        for p in self.particles:
            p.update()

    def draw(self, pos_field, color_field, index_field, max_particles, right, up):
        count = len(self.particles)
        count = min(count, max_particles)

        # Create arrays sized for max_particles
        pos_np = np.zeros((max_particles * 4, 3), dtype=np.float32)
        color_np = np.zeros((max_particles * 4, 4), dtype=np.float32)
        indices_np = np.zeros((max_particles * 6,), dtype=np.int32)  # full size

        for i, p in enumerate(self.particles[:count]):
            quad = compute_billboarded_quad(p.x, p.y, p.z, p.size, right, up)
            base = i * 4
            for v_idx, vpos in enumerate(quad):
                pos_np[base + v_idx] = vpos
                color_np[base + v_idx] = [1.0, 1.0, 1.0, p.alpha]

            tri_base = i * 6
            indices_np[tri_base:tri_base+6] = [base, base+1, base+2, base, base+2, base+3]

        pos_field.from_numpy(pos_np)
        color_field.from_numpy(color_np)
        index_field.from_numpy(indices_np)

        # Return the count so that the caller knows how many to draw
        return count



def compute_billboarded_quad(x, y, z, size, right, up):
    half = size
    v0 = [x - right[0]*half - up[0]*half,
          y - right[1]*half - up[1]*half,
          z - right[2]*half - up[2]*half]
    v1 = [x + right[0]*half - up[0]*half,
          y + right[1]*half - up[1]*half,
          z + right[2]*half - up[2]*half]
    v2 = [x + right[0]*half + up[0]*half,
          y + right[1]*half + up[1]*half,
          z + right[2]*half + up[2]*half]
    v3 = [x - right[0]*half + up[0]*half,
          y - right[1]*half + up[1]*half,
          z - right[2]*half + up[2]*half]
    return [v0, v1, v2, v3]
