#WSCPH.py
import taichi as ti
import sph_base
import math

class WCSPHSolver(sph_base.SPHBase):
    def __init__(self, particle_system):
        super().__init__(particle_system)
        self.gamma = self.ps.config['gamma']
        self.B = self.ps.config['B']
        self.surface_tension = ti.field(ti.f32, shape=())
        self.surface_tension[None] = self.ps.config['surfaceTension']

        # Define crater parameters and an upward eruption force.
        # Adjust these values as needed.
        self.crater_position = ti.Vector([0.85, 0.15, 0.85])   # example crater position
        self.crater_radius = 0.15                           # radius of crater influence
        self.lava_force_magnitude = 20.0                    # upward force magnitude

        self.time_step = ti.field(ti.i32, shape=())
        self.time_step[None] = 0
        self.period = 2000  # number of steps for a full sine cycle
        self.horizontal_force_magnitude = 5.0


    @ti.func
    def update_density_task(self, p_i, p_j, density: ti.template()):
        if self.ps.material[p_j] == self.ps.material_fluid:
            density += self.ps.mass[p_i] * self.cubic_spline_kernel(
                (self.ps.position[p_i] - self.ps.position[p_j]).norm())
        elif self.ps.material[p_j] == self.ps.material_rigid:
            density += self.ps.density0 * self.ps.volume[p_j] * self.cubic_spline_kernel(
                (self.ps.position[p_i] - self.ps.position[p_j]).norm())

    @ti.kernel
    def update_density(self):
        for i in range(self.ps.total_particle_num):
            if self.ps.material[i] == self.ps.material_fluid:
                density = self.ps.mass[i] * self.cubic_spline_kernel(0.0)
                self.ps.for_all_neighbors(i, self.update_density_task, density)
                self.ps.density[i] = density

    @ti.kernel
    def update_pressure(self):
        for i in range(self.ps.total_particle_num):
            if self.ps.material[i] == self.ps.material_fluid:
                self.ps.density[i] = ti.max(self.ps.density[i], self.ps.density0)
                self.ps.pressure[i] = self.B * ((self.ps.density[i] / self.ps.density0) ** self.gamma - 1)

    @ti.func
    def compute_pressure_force_task(self, p_i, p_j, acc: ti.template()):
        gradW = self.cubic_spline_kernel_derivative((self.ps.position[p_i] - self.ps.position[p_j]))
        p_rho_i = self.ps.pressure[p_i] / (self.ps.density[p_i] ** 2)
        if self.ps.material[p_j] == self.ps.material_fluid:
            m_j = self.ps.mass[p_j]
            p_rho_j = self.ps.pressure[p_j] / (self.ps.density[p_j] ** 2)
            acc -= m_j * (p_rho_i + p_rho_j) * gradW
        else:
            psi = self.ps.density0 * self.ps.volume[p_j]
            acc_tmp = -psi * p_rho_i * gradW
            acc += acc_tmp
            if self.ps.is_dynamic_rigid_body(p_j):
                self.ps.acceleration[p_j] -= acc_tmp * self.ps.mass[p_i] / self.ps.mass[p_j]

    @ti.kernel
    def compute_pressure_force(self):
        for i in range(self.ps.total_particle_num):
            if self.ps.is_static_rigid_body(i):
                self.ps.acceleration[i].fill(0.0)
            elif self.ps.material[i] == self.ps.material_fluid:
                acc = ti.Vector.zero(ti.f32, self.ps.dim)
                self.ps.for_all_neighbors(i, self.compute_pressure_force_task, acc)
                self.ps.acceleration[i] += acc

    @ti.func
    def compute_non_pressure_force_task(self, p_i, p_j, acc: ti.template()):
        # Surface Tension
        if self.ps.material[p_j] == self.ps.material_fluid:
            r_vec = self.ps.position[p_i] - self.ps.position[p_j]
            acc -= self.surface_tension[None] / self.ps.mass[p_i] * self.ps.mass[p_j] * r_vec * \
                   self.cubic_spline_kernel(r_vec.norm())

        # Viscosity Force
        if self.ps.material[p_j] == self.ps.material_fluid:
            nu = 2 * self.viscosity[None] * self.ps.support_length * self.c_s / (
                    self.ps.density[p_i] + self.ps.density[p_j])
            v_ij = self.ps.velocity[p_i] - self.ps.velocity[p_j]
            x_ij = self.ps.position[p_i] - self.ps.position[p_j]
            pi = -nu * ti.min(v_ij.dot(x_ij), 0.0) / (x_ij.dot(x_ij) + 0.01 * self.ps.support_length ** 2)
            acc -= self.ps.mass[p_j] * pi * self.cubic_spline_kernel_derivative(x_ij)
        else:
            sigma = self.ps.rigid_bodies_sigma[self.ps.object_id[p_j]]
            nu = sigma * self.ps.support_length * self.c_s / (2 * self.ps.density[p_i])
            v_ij = self.ps.velocity[p_i] - self.ps.velocity[p_j]
            x_ij = self.ps.position[p_i] - self.ps.position[p_j]
            pi = -nu * ti.min(v_ij.dot(x_ij), 0.0) / (x_ij.dot(x_ij) + 0.01 * self.ps.support_length ** 2)
            acc -= self.ps.density0 * self.ps.volume[p_j] * pi * self.cubic_spline_kernel_derivative(x_ij)

    @ti.kernel
    def compute_non_pressure_force(self):
        simulation_time = self.time_step[None] * self.dt[None]
        time_factor = ti.sin(2 * math.pi * self.time_step[None] / self.period)
        upward_force = self.lava_force_magnitude * (0.5 + 0.5 * time_factor)
        horizontal_force_magnitude = self.horizontal_force_magnitude * (0.5 + 0.5 * time_factor)

        for i in range(self.ps.total_particle_num):
            if self.ps.is_static_rigid_body(i):
                self.ps.acceleration[i].fill(0.0)
            else:
                acc = ti.Vector(self.g)
                # Compute viscosity/surface tension for fluid
                if self.ps.material[i] == self.ps.material_fluid:
                    self.ps.for_all_neighbors(i, self.compute_non_pressure_force_task, acc)

                    # Apply eruption forces after a specific time
                    if simulation_time > 0.6:
                        p_pos = self.ps.position[i]
                        horizontal_dist = ((p_pos[0] - self.crater_position[0])**2 + (p_pos[2] - self.crater_position[2])**2)**0.5

                        if horizontal_dist < self.crater_radius:
                            # Direction vector for horizontal force
                            direction = ti.Vector([p_pos[0] - self.crater_position[0], 0.0, p_pos[2] - self.crater_position[2]])
                            if horizontal_dist > 0:  # Normalize to avoid division by zero
                                direction = direction.normalized()
                            
                            # Apply horizontal and upward forces
                            acc += horizontal_force_magnitude * direction
                            acc[1] += upward_force

                self.ps.acceleration[i] = acc


    @ti.kernel
    def advect(self):
        for i in range(self.ps.total_particle_num):
            if self.ps.is_dynamic[i]:
                self.ps.velocity[i] += self.ps.acceleration[i] * self.dt[None]
                self.ps.position[i] += self.ps.velocity[i] * self.dt[None]

    def substep(self):
        self.update_density()
        self.update_pressure()
        self.compute_non_pressure_force()
        self.compute_pressure_force()
        self.advect()
        self.time_step[None] += 1
        self.increase_lifetime()
    
    @ti.kernel
    def increase_lifetime(self):
        for i in range(self.ps.total_particle_num):
            self.ps.lifetime[i] += self.dt[None]

