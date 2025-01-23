import trimesh

# Load the OBJ file
file_path = "D:/sph_randy/Final-Project/data/models/scaled_volcano_landscape.obj"
mesh = trimesh.load(file_path)


# Print summary of the mesh
print(mesh)
print("Bounding box dimensions:", mesh.bounds)
print("Scale factor:", mesh.scale)

# Display the mesh (requires an appropriate viewer)
mesh.apply_scale(1.0 / mesh.scale)  # Normalize the scale
mesh.show()

