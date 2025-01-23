import numpy as np
import trimesh

def create_realistic_volcano_with_bowl(base_radius, height, crater_radius, crater_depth, wall_thickness, bowl_depth, segments=50, sawtooth_scale=0.1, height_variation=0.1):
    """
    Create a realistic 3D volcano mesh with a larger crater, a hollow bowl, and a sealed base.

    Args:
        base_radius (float): Outer radius of the volcano's base.
        height (float): Total height of the volcano.
        crater_radius (float): Radius of the outer crater at the top.
        crater_depth (float): Depth of the crater.
        wall_thickness (float): Thickness of the volcano walls.
        bowl_depth (float): Depth of the bowl inside the volcano.
        segments (int): Number of segments for circular parts (controls smoothness).
        sawtooth_scale (float): Amount of jaggedness for the crater edge.
        height_variation (float): Maximum variation in crater edge height.

    Returns:
        trimesh.Trimesh: A 3D volcano mesh.
    """
    # Generate angles for circular sections
    angles = np.linspace(0, 2 * np.pi, segments, endpoint=False)

    # Outer base vertices
    outer_base = np.array([[base_radius * np.cos(a), 0, base_radius * np.sin(a)] for a in angles])

    # Outer crater vertices with jagged edges and height variation
    outer_crater = np.array([
        [
            (crater_radius + sawtooth_scale * (-1)**i) * np.cos(a),
            height - crater_depth + np.random.uniform(-height_variation, height_variation),
            (crater_radius + sawtooth_scale * (-1)**i) * np.sin(a)
        ]
        for i, a in enumerate(angles)
    ])

    # Bowl vertices
    bowl = np.array([
        [
            (crater_radius - wall_thickness) * np.cos(a),
            height - crater_depth - bowl_depth * (1 - np.cos(a)),  # Bowl curve
            (crater_radius - wall_thickness) * np.sin(a)
        ]
        for a in angles
    ])

    # Combine vertices
    vertices = np.vstack((outer_base, outer_crater, bowl))

    # Faces for the volcano
    faces = []
    n = len(angles)

    # Seal the base
    for i in range(n):
        # Triangle connecting outer base vertices
        faces.append([i, (i + 1) % n, n + i])

    # Outer wall faces
    for i in range(n):
        faces.append([i, (i + 1) % n, n + i])
        faces.append([(i + 1) % n, n + (i + 1) % n, n + i])

    # Bowl faces
    for i in range(n):
        faces.append([n + i, n + (i + 1) % n, 2 * n + i])
        faces.append([n + (i + 1) % n, 2 * n + (i + 1) % n, 2 * n + i])

    # Create the mesh
    faces = np.array(faces)
    volcano_mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

    return volcano_mesh


if __name__ == "__main__":
    # Define volcano dimensions
    base_radius = 0.5          # Outer radius of the base
    height = 0.5               # Total height of the volcano
    crater_radius = 0.25       # Radius for the crater
    crater_depth = 0.2         # Depth of the crater
    wall_thickness = 0.04      # Thickness of the volcano walls
    bowl_depth = 0.1           # Depth of the bowl inside
    segments = 50              # Number of segments (smoothness)
    sawtooth_scale = 0.03      # Jaggedness of the crater edge
    height_variation = 0.02    # Height variation of the crater edge

    # Create the volcano mesh
    volcano_mesh = create_realistic_volcano_with_bowl(
        base_radius, height, crater_radius, crater_depth, wall_thickness,
        bowl_depth, segments, sawtooth_scale, height_variation
    )

    # Export and visualize the volcano
    volcano_mesh.show()
    output_path = "realistic_volcano.obj"
    volcano_mesh.export(output_path)
    print(f"Volcano mesh exported to {output_path}")
