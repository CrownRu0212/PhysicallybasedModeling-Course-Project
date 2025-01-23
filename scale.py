import trimesh

def scale_obj_file(input_path, output_path, scale_factor):
    """
    Load an OBJ file, apply scaling, and save the scaled version.

    Args:
        input_path (str): Path to the input OBJ file.
        output_path (str): Path to save the scaled OBJ file.
        scale_factor (float): Scaling factor to apply.
    """
    # Load the OBJ file
    mesh = trimesh.load(input_path)

    # Apply scaling
    mesh.apply_scale(scale_factor)

    # Export the scaled OBJ file
    mesh.export(output_path)
    print(f"Scaled OBJ file saved to {output_path}")


# Example Usage
input_file = "D:/sph_randy/Final-Project/data/models/volcano_landscape.obj"
output_file = "./data/models/scaled_volcano_landscape.obj"
scaling_factor = 1.0 / 2500.0

scale_obj_file(input_file, output_file, scaling_factor)
