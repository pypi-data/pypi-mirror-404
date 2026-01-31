from mcshell.constants import *

# --- Helper for point-to-segment distance ---
def distance_point_to_segment(p, a, b):
    p_np = np.array(p)
    a_np = np.array(a)
    b_np = np.array(b)
    ab = b_np - a_np
    ap = p_np - a_np
    denominator = np.dot(ab, ab)
    if denominator < 1e-9:
        return np.linalg.norm(p_np - a_np)
    t = np.dot(ap, ab) / denominator
    t = max(0.0, min(1.0, t))
    closest_point = a_np + t * ab
    return np.linalg.norm(p_np - closest_point)

# --- Helper to get orthonormal basis ---
def get_plane_basis(normal_vec_norm_tuple_or_array):
    normal_vec_norm = np.array(normal_vec_norm_tuple_or_array)
    if np.linalg.norm(normal_vec_norm) < 1e-9:
        return np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0])
    if np.isclose(np.linalg.norm(np.cross(normal_vec_norm, [1,0,0])), 0):
        temp_vec = np.array([0.0, 1.0, 0.0])
    else:
        temp_vec = np.array([1.0, 0.0, 0.0])
    u_vec = np.cross(normal_vec_norm, temp_vec)
    u_vec_norm = np.linalg.norm(u_vec)
    if u_vec_norm < 1e-9:
        temp_vec = np.array([0.0,0.0,1.0])
        u_vec = np.cross(normal_vec_norm, temp_vec)
        u_vec_norm = np.linalg.norm(u_vec)
        if u_vec_norm < 1e-9:
            return (np.array([1.,0.,0.]), np.array([0.,1.,0.])
                    if not np.allclose(normal_vec_norm, [0,0,1])
                    else (np.array([1.,0.,0.]), np.array([0.,0.,1.]))) # Fixed tuple return
    u_vec = u_vec / u_vec_norm
    v_vec = np.cross(normal_vec_norm, u_vec)
    return u_vec, v_vec

# --- Geometric Construction Functions ---
def generate_digital_ball_coordinates(center: tuple[float, float, float], radius: float, inner_radius: float = 0.0):
    cx, cy, cz = center
    outer_r_squared = radius ** 2
    inner_r_squared = inner_radius ** 2
    digital_ball_coords = set()
    if inner_radius >= radius and radius > 0:
        print(f"Warning: inner_radius ({inner_radius}) >= outer_radius ({radius}) for ball.")
        return []
    x_min, y_min, z_min = int(math.floor(cx - radius)), int(math.floor(cy - radius)), int(math.floor(cz - radius))
    x_max, y_max, z_max = int(math.ceil(cx + radius)), int(math.ceil(cy + radius)), int(math.ceil(cz + radius))
    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            for z in range(z_min, z_max + 1):
                voxel_center_x, voxel_center_y, voxel_center_z = x + 0.5, y + 0.5, z + 0.5
                distance_squared = (voxel_center_x - cx)**2 + (voxel_center_y - cy)**2 + (voxel_center_z - cz)**2
                if inner_r_squared < distance_squared <= outer_r_squared:
                    digital_ball_coords.add((x, y, z))
    return sorted(list(digital_ball_coords))

def generate_digital_tube_coordinates(p1: tuple[float, float, float], p2: tuple[float, float, float],
                                      outer_thickness: float, inner_thickness: float = 0.0):
    """
    Generates integer XYZ coordinates for a digital line segment with a specified thickness.
    'thickness' parameters are treated as RADII.
    """
    outer_radius = outer_thickness
    inner_radius = inner_thickness

    if inner_radius >= outer_radius and outer_radius > 0:
        print(f"Warning: inner_radius ({inner_radius}) >= outer_radius ({outer_radius}) for tube.")
        return []

    tube_coords = set()

    # The bounding box should extend by the radius in every direction from the
    # minimal and maximal extent of the segment itself.
    min_x_bb = min(p1[0], p2[0]) - outer_radius
    max_x_bb = max(p1[0], p2[0]) + outer_radius
    min_y_bb = min(p1[1], p2[1]) - outer_radius
    max_y_bb = max(p1[1], p2[1]) + outer_radius
    min_z_bb = min(p1[2], p2[2]) - outer_radius
    max_z_bb = max(p1[2], p2[2]) + outer_radius

    # The iteration range for integer voxels
    x_min_iter = int(math.floor(min_x_bb))
    x_max_iter = int(math.ceil(max_x_bb))
    y_min_iter = int(math.floor(min_y_bb))
    y_max_iter = int(math.ceil(max_y_bb))
    z_min_iter = int(math.floor(min_z_bb))
    z_max_iter = int(math.ceil(max_z_bb))

    for x in range(x_min_iter, x_max_iter + 1):
        for y in range(y_min_iter, y_max_iter + 1):
            for z in range(z_min_iter, z_max_iter + 1):
                voxel_center = (x + 0.5, y + 0.5, z + 0.5)
                dist_to_segment = distance_point_to_segment(voxel_center, p1, p2)

                # Check if the voxel center is within the hollow cylinder's bounds
                if inner_radius < dist_to_segment <= outer_radius:
                    tube_coords.add((x, y, z))
    return sorted(list(tube_coords))

# def generate_digital_plane_coordinates(normal: tuple[float, float, float],
#                                          point_on_plane: tuple[float, float, float],
#                                          outer_rect_dims: tuple[float, float]):
#     """
#     Generates a contiguous, single-voxel-thick set of coordinates for a plane
#     of any orientation. This final version uses a robust voxel-checking algorithm
#     with a tie-breaking offset to ensure correctness for all cases.
#     """
#     coords = set()
#     n = np.array(normal, dtype=float)
#     n /= np.linalg.norm(n)  # Normalize the normal vector
#
#     # --- THE CRUCIAL FIX ---
#     # Add a tiny offset to the plane's position along its normal.
#     # This breaks the tie when a plane lies exactly between two voxel layers,
#     # ensuring only one layer is chosen for axis-aligned planes without
#     # affecting the outcome for diagonal planes.
#     point = np.array(point_on_plane, dtype=float) + (n * 1e-9)
#
#     width, height = outer_rect_dims
#
#     # Find two orthogonal basis vectors (u, v) that lie on the plane
#     if np.allclose(n, [0, 1, 0]) or np.allclose(n, [0, -1, 0]):
#         u = np.array([1, 0, 0])
#         v = np.array([0, 0, 1])
#     else:
#         u = np.cross(n, [0, 1, 0])
#         if np.linalg.norm(u) < 1e-6:
#             u = np.cross(n, [0, 0, 1])
#         u /= np.linalg.norm(u)
#         v = np.cross(n, u)
#         v /= np.linalg.norm(v)
#
#     # 1. Define the four corners of the geometric plane to create a bounding box
#     half_w_vec = u * (width / 2.0)
#     half_h_vec = v * (height / 2.0)
#     corners = [
#         point + half_w_vec + half_h_vec,
#         point + half_w_vec - half_h_vec,
#         point - half_w_vec + half_h_vec,
#         point - half_w_vec - half_h_vec,
#     ]
#
#     # 2. Create an integer bounding box around the plane
#     min_bounds = np.floor(np.min(corners, axis=0)).astype(int)
#     max_bounds = np.ceil(np.max(corners, axis=0)).astype(int)
#
#     # 3. Iterate through every voxel in the bounding box
#     for x in range(min_bounds[0], max_bounds[0]):
#         for y in range(min_bounds[1], max_bounds[1]):
#             for z in range(min_bounds[2], max_bounds[2]):
#                 voxel_center = np.array([x + 0.5, y + 0.5, z + 0.5])
#
#                 dist_from_plane = abs(np.dot(voxel_center - point, n))
#
#                 if dist_from_plane <= 0.5:
#                     # Find the closest point on the infinite plane to the voxel's center
#                     signed_dist = np.dot(voxel_center - point, n)
#                     closest_point_on_plane = voxel_center - signed_dist * n
#
#                     # Check if this projected point is within the rectangle's bounds
#                     vec_from_center = closest_point_on_plane - point
#                     proj_u = np.dot(vec_from_center, u)
#                     proj_v = np.dot(vec_from_center, v)
#
#                     if abs(proj_u) <= width / 2.0 and abs(proj_v) <= height / 2.0:
#                         coords.add((x, y, z))
#
#     return sorted(list(coords))

import numpy as np
import math

def generate_digital_plane_coordinates(normal: tuple[float, float, float],
                                         point_on_plane: tuple[float, float, float],
                                         outer_rect_dims: tuple[float, float]):
    """
    Generates a Standard Digital Plane (6-connected) using the Arithmetic Definition.

    Theory:
    A voxel v is part of the plane if:
       -thickness/2 <= dot(v - center, n) < thickness/2

    Where 'thickness' is variable and calculated to guarantee 6-connectivity:
       thickness = |nx| + |ny| + |nz| (for normalized n)
    """
    coords = set()
    n = np.array(normal, dtype=float)
    norm_len = np.linalg.norm(n)
    if norm_len == 0:
        return []
    n /= norm_len  # Normalized normal vector

    # --- 1. Calculate Arithmetic Thickness for 6-Connectivity ---
    # L1 norm ensures 6-connectivity.
    # We add a tiny epsilon to ensure robust floating-point comparisons,
    # preventing the set from fracturing at the exact boundaries.
    arithmetic_thickness = np.sum(np.abs(n))
    thickness_epsilon = 1e-9

    point = np.array(point_on_plane, dtype=float)
    width, height = outer_rect_dims

    # --- 2. Basis Vectors for Bounding ---
    if np.allclose(n, [0, 1, 0]) or np.allclose(n, [0, -1, 0]):
        u = np.array([1, 0, 0])
        v = np.array([0, 0, 1])
    else:
        u = np.cross(n, [0, 1, 0])
        if np.linalg.norm(u) < 1e-6:
            u = np.cross(n, [0, 0, 1])
        u /= np.linalg.norm(u)
        v = np.cross(n, u)
        v /= np.linalg.norm(v)

    # --- 3. Define Search Space (Bounding Box) ---
    half_w_vec = u * (width / 2.0)
    half_h_vec = v * (height / 2.0)
    corners = [
        point + half_w_vec + half_h_vec,
        point + half_w_vec - half_h_vec,
        point - half_w_vec + half_h_vec,
        point - half_w_vec - half_h_vec,
    ]

    # We use generous padding to ensure we iterate over all candidates.
    # The exact filtering happens inside the loop.
    padding = 2
    min_bounds = np.floor(np.min(corners, axis=0)).astype(int) - padding
    max_bounds = np.ceil(np.max(corners, axis=0)).astype(int) + padding

    # Robust boundary for the finite rectangle check.
    # We prioritize connectivity over strict size, so we include the boundary.
    boundary_u = width / 2.0 + 1e-9
    boundary_v = height / 2.0 + 1e-9

    # --- 4. Iterate and Validate ---
    for x in range(min_bounds[0], max_bounds[0] + 1):
        for y in range(min_bounds[1], max_bounds[1] + 1):
            for z in range(min_bounds[2], max_bounds[2] + 1):
                voxel_center = np.array([x, y, z], dtype=float)

                # A. The Arithmetic Plane Check (Infinite Plane)
                dist = np.dot(voxel_center - point, n)

                # Robust Inequality:
                # We widen the acceptance range slightly with epsilon to capture
                # voxels sitting exactly on the theoretical edge.
                threshold = (arithmetic_thickness / 2.0) + thickness_epsilon

                if -threshold <= dist < threshold:

                    # B. The Finite Rectangle Check
                    closest_point_on_plane = voxel_center - dist * n
                    vec_from_center = closest_point_on_plane - point

                    proj_u = np.dot(vec_from_center, u)
                    proj_v = np.dot(vec_from_center, v)

                    if abs(proj_u) <= boundary_u and abs(proj_v) <= boundary_v:
                        coords.add((x, y, z))

    return sorted(list(coords))


def generate_digital_disc_coordinates(normal: tuple[float, float, float],
                                      center_point: tuple[float, float, float], # Center of the disc
                                      outer_radius: float,
                                      disc_thickness: float = 1.0,
                                      inner_radius: float = 0.0): # For annulus
    """
    Generates integer XYZ coordinates for a digital disc or annulus (ring).
    normal: Normal vector of the disc's plane.
    center_point: A point on the plane that is the center of the disc/annulus.
    outer_radius: The outer radius of the disc/annulus.
    disc_thickness: Thickness of the disc along the normal vector.
    inner_radius: Inner radius for creating an annulus (ring). If 0, a solid disc is made.
    """
    nx, ny, nz = normal
    cx, cy, cz = center_point # This is the center of the disc in the plane

    disc_coords = set()

    norm_val = math.sqrt(nx**2 + ny**2 + nz**2)
    if norm_val < 1e-9:
        print("Error: Normal vector for disc cannot be zero.")
        return []

    normal_vec_norm = np.array([nx / norm_val, ny / norm_val, nz / norm_val])
    # D_plane defines the plane equation: normal_vec_norm . X + D_plane = 0
    # where X is a point on the plane. So, D_plane = - (normal_vec_norm . center_point)
    D_plane = -np.dot(normal_vec_norm, np.array(center_point))


    if inner_radius >= outer_radius and outer_radius > 0:
        print(f"Warning: inner_radius ({inner_radius}) >= outer_radius ({outer_radius}) for disc.")
        return []

    outer_radius_sq = outer_radius**2
    inner_radius_sq = inner_radius**2

    # Bounding box for iteration around the center_point
    # Extent is outer_radius for in-plane dimensions, and disc_thickness for out-of-plane
    x_min = int(math.floor(cx - outer_radius - disc_thickness)) # Add thickness to bounds in all dirs for safety with rotations
    x_max = int(math.ceil(cx + outer_radius + disc_thickness))
    y_min = int(math.floor(cy - outer_radius - disc_thickness))
    y_max = int(math.ceil(cy + outer_radius + disc_thickness))
    z_min = int(math.floor(cz - outer_radius - disc_thickness))
    z_max = int(math.ceil(cz + outer_radius + disc_thickness))


    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            for z in range(z_min, z_max + 1):
                voxel_center = np.array([x + 0.5, y + 0.5, z + 0.5])

                # Check distance from plane
                signed_perpendicular_dist = np.dot(normal_vec_norm, voxel_center - np.array(center_point))
                # Alternative using D_plane: signed_perpendicular_dist = np.dot(normal_vec_norm, voxel_center) + D_plane

                if not (abs(signed_perpendicular_dist) <= disc_thickness / 2.0):
                    continue

                # Project voxel_center onto the plane
                projected_point_on_plane = voxel_center - signed_perpendicular_dist * normal_vec_norm

                # Calculate squared distance from the disc's center_point to the projected point (in the plane)
                dist_in_plane_sq = np.sum((projected_point_on_plane - np.array(center_point))**2)

                if inner_radius_sq < dist_in_plane_sq <= outer_radius_sq:
                    disc_coords.add((x, y, z))

    return sorted(list(disc_coords))


def get_oriented_cube_vertices(center: np.ndarray, side_length: float, rotation_matrix: np.ndarray) -> list[tuple[float, float, float]]:
    # (Your existing get_oriented_cube_vertices code)
    h = side_length / 2.0
    local_vertices = [
        np.array([-h, -h, -h]), np.array([h, -h, -h]), np.array([-h, h, -h]), np.array([h, h, -h]),
        np.array([-h, -h, h]), np.array([h, -h, h]), np.array([-h, h, h]), np.array([h, h, h])
    ]
    world_vertices = []
    for lv in local_vertices:
        rotated_vertex = rotation_matrix @ lv
        world_vertex = center + rotated_vertex
        world_vertices.append(tuple(world_vertex))
    return world_vertices

import numpy as np
from typing import List, Union

def _is_point_inside_oriented_cube_helper(
    point_np: np.ndarray,
    cube_vertices: Union[List[np.ndarray], List[tuple], np.ndarray]
) -> bool:
    """
    Internal helper to check if a point is inside an arbitrarily oriented convex cube.
    This corrected version ensures all face normals point consistently outward and
    then checks if the point lies on the "inner" or negative side of all planes.

    Args:
        point_np: A 3D NumPy array representing the point to check (e.g., np.array([x, y, z])).
        cube_vertices: The 8 vertices of the cube, provided either as a list of 8 vectors
                       or as a single 8x3 NumPy array.

    Returns:
        True if the point is inside or on the surface of the cube, False otherwise.
    """
    # Correctly handle if input is a list of vectors or a single 2D np.ndarray
    if isinstance(cube_vertices, np.ndarray) and cube_vertices.ndim == 2:
        cube_vertices_np = cube_vertices
    else:
        cube_vertices_np = np.array(cube_vertices)

    if cube_vertices_np.shape != (8, 3):
        return False # Invalid input

    # Calculate the centroid, a reference point guaranteed to be inside the cube.
    centroid = np.mean(cube_vertices_np, axis=0)

    # Defines the 6 faces of the cube by the indices of their vertices.
    # The winding order (e.g., CCW) determines the initial direction of the normal.
    faces_vertex_indices = [
        (0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4),
        (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)
    ]

    for indices in faces_vertex_indices:
        v0, v1, v2 = cube_vertices_np[indices[0]], cube_vertices_np[indices[1]], cube_vertices_np[indices[2]]

        # Calculate the normal vector perpendicular to the face plane.
        normal = np.cross(v1 - v0, v2 - v0)

        norm_mag = np.linalg.norm(normal)
        if norm_mag < 1e-9: continue # Skip degenerate face
        normal /= norm_mag

        # Ensure all normals point OUTWARD from the cube's center.
        # The vector `v0 - centroid` points from the center to the face.
        # If the normal's dot product with this vector is negative, they are
        # pointing in opposite directions, meaning the normal is pointing inward.
        # So, we flip it to make it point outward.
        if np.dot(normal, v0 - centroid) < 0:
            normal = -normal

        # Check if the point lies on the "outside" of the plane.
        # For an outward-pointing normal, any point P inside the cube must satisfy:
        # normal · (P - v0) <= 0
        # If the result is positive, the point is outside this face.
        if np.dot(normal, point_np - v0) > 1e-6: # Using a small epsilon for float precision
            return False

    # If the point was not outside any of the 6 planes, it must be inside the cube.
    return True
import numpy as np
from typing import List, Set, Tuple

# Assuming get_oriented_cube_vertices and _is_point_inside_oriented_cube_helper exist
# and function as they did in the original context.

def generate_digital_cube_coordinates(
    center: Tuple[float, float, float],
    side_length: float,
    rotation_matrix: np.ndarray,
    wall_thickness: float = 0.0
) -> List[Tuple[int, int, int]]:
    """
    Generates integer XYZ coordinates for a solid or hollow digital cube with
    arbitrary orientation using wall thickness.

    Args:
        center: The (x, y, z) center of the cube.
        side_length: The length of the cube's sides.
        rotation_matrix: A 3x3 numpy array for orientation.
        wall_thickness: The thickness of the cube's walls. If 0, the cube is solid.
    """
    cube_coords: Set[Tuple[int, int, int]] = set()
    center_np = np.array(center)

    if side_length <= 0:
        return []

    # A wall thickness that is half the side length or more would result in no
    # inner volume, so the cube is effectively hollow or empty.
    if wall_thickness * 2 >= side_length and wall_thickness != 0.0:
        print(f"Warning: wall_thickness ({wall_thickness}) results in no inner volume for side_length ({side_length}).")
        # Proceeding will still generate the outer shell correctly.

    if wall_thickness < 0:
        print(f"Warning: wall_thickness ({wall_thickness}) is negative. Treating as 0 (solid).")
        wall_thickness = 0.0

    # 1. --- Outer Cube Calculation ---
    outer_cube_vertices = get_oriented_cube_vertices(center_np, side_length, rotation_matrix)
    if not outer_cube_vertices:
        return []

    outer_vertices_np = np.array(outer_cube_vertices)
    min_continuous_bounds = outer_vertices_np.min(axis=0)
    max_continuous_bounds = outer_vertices_np.max(axis=0)

    min_coords_bb = np.ceil(min_continuous_bounds).astype(int)
    max_coords_bb = np.floor(max_continuous_bounds).astype(int)
    min_x_bb, min_y_bb, min_z_bb = min_coords_bb
    max_x_bb, max_y_bb, max_z_bb = max_coords_bb

    # 2. --- Inner Cube Calculation (if hollow) ---
    inner_cube_vertices = None
    if wall_thickness > 0.0:
        # The inner cube's side length is the outer side length minus the thickness of two walls.
        inner_side_length = side_length - (2 * wall_thickness)
        if inner_side_length > 0:
            # The inner cube shares the same center and orientation.
            inner_cube_vertices = get_oriented_cube_vertices(center_np, inner_side_length, rotation_matrix)

    # 3. --- Voxel Iteration and Checking ---
    for x in range(min_x_bb, max_x_bb + 1):
        for y in range(min_y_bb, max_y_bb + 1):
            for z in range(min_z_bb, max_z_bb + 1):
                voxel_center = np.array([x + 0.5, y + 0.5, z + 0.5])

                # Check if the voxel is within the outer boundary
                if _is_point_inside_oriented_cube_helper(voxel_center, outer_vertices_np):
                    is_inside_inner = False
                    if inner_cube_vertices:
                        # If it's a hollow cube, check if it's also inside the inner boundary
                        is_inside_inner = _is_point_inside_oriented_cube_helper(voxel_center, np.array(inner_cube_vertices))

                    if not is_inside_inner:
                        cube_coords.add((x, y, z))

    return sorted(list(cube_coords))

def generate_digital_cube_coordinates_old(center: tuple[float, float, float], side_length: float, rotation_matrix: np.ndarray,
                                      inner_offset_factor: float = 0.0):
    """
    Generates integer XYZ coordinates for a solid or hollow digital cube with arbitrary orientation.
    """
    cube_coords = set()
    center_np = np.array(center)

    if inner_offset_factor >= 1.0 and inner_offset_factor != 0.0:
        print(f"Warning: inner_offset_factor ({inner_offset_factor}) is >= 1.0. This will result in an empty cube.")
        return []
    if side_length <= 0:
        return []

    # Calculate the 8 vertices of the cube in world space
    outer_cube_vertices_list_tuples = get_oriented_cube_vertices(center_np, side_length, rotation_matrix)
    outer_cube_vertices_for_check = [np.array(v) for v in outer_cube_vertices_list_tuples]

    if not outer_cube_vertices_for_check:
        return []

    outer_vertices_np_array = np.array(outer_cube_vertices_for_check)

    # Get the min/max coordinates from the vertices to define the continuous boundary
    min_continuous_bounds = outer_vertices_np_array.min(axis=0)
    max_continuous_bounds = outer_vertices_np_array.max(axis=0)

    # The iteration range for integer voxels must be calculated by taking the
    # ceiling of the minimum continuous bound and the floor of the maximum.
    min_coords_bb = np.ceil(min_continuous_bounds).astype(int)
    max_coords_bb = np.floor(max_continuous_bounds).astype(int)

    min_x_bb, min_y_bb, min_z_bb = min_coords_bb
    max_x_bb, max_y_bb, max_z_bb = max_coords_bb

    inner_cube_vertices_for_check = None
    if inner_offset_factor > 0.0: # Hollow cube
        inner_verts_temp = []
        for v_outer_tuple in outer_cube_vertices_list_tuples:
            v_outer_np = np.array(v_outer_tuple)
            v_inner = center_np + (v_outer_np - center_np) * inner_offset_factor
            inner_verts_temp.append(tuple(v_inner))
        inner_cube_vertices_for_check = [np.array(v) for v in inner_verts_temp]

    # The main loop now iterates over a much tighter, correct bounding box
    for x in range(min_x_bb, max_x_bb + 1):
        for y in range(min_y_bb, max_y_bb + 1):
            for z in range(min_z_bb, max_z_bb + 1):
                voxel_center = np.array([x + 0.5, y + 0.5, z + 0.5])
                is_inside_outer = _is_point_inside_oriented_cube_helper(voxel_center, outer_cube_vertices_for_check)

                if is_inside_outer:
                    if inner_offset_factor == 0.0: # Solid cube
                        cube_coords.add((x, y, z))
                    else: # Hollow cube, check if outside inner cube
                        if inner_cube_vertices_for_check:
                            is_inside_inner = _is_point_inside_oriented_cube_helper(voxel_center, inner_cube_vertices_for_check)
                            if not is_inside_inner:
                                cube_coords.add((x, y, z))
                        else: # Should not happen, but treat as solid if inner def failed
                            cube_coords.add((x, y, z))
    return sorted(list(cube_coords))


def _is_point_inside_tetrahedron_helper(point_np, tetra_vertices_np_list_of_arrays):
    if not isinstance(tetra_vertices_np_list_of_arrays, np.ndarray) or tetra_vertices_np_list_of_arrays.ndim != 2:
        tetra_vertices_np = np.array([list(v) for v in tetra_vertices_np_list_of_arrays], dtype=np.float64)
    else:
        tetra_vertices_np = tetra_vertices_np_list_of_arrays.astype(np.float64, copy=False)
    if tetra_vertices_np.shape[0] != 4: return False
    centroid_t = np.mean(tetra_vertices_np, axis=0)
    faces_defs = [
        ((tetra_vertices_np[0], tetra_vertices_np[1], tetra_vertices_np[2]), tetra_vertices_np[3]),
        ((tetra_vertices_np[0], tetra_vertices_np[1], tetra_vertices_np[3]), tetra_vertices_np[2]),
        ((tetra_vertices_np[0], tetra_vertices_np[2], tetra_vertices_np[3]), tetra_vertices_np[1]),
        ((tetra_vertices_np[1], tetra_vertices_np[2], tetra_vertices_np[3]), tetra_vertices_np[0])
    ]
    for (v0, v1, v2), v_opposite in faces_defs:
        normal = np.cross(v1 - v0, v2 - v0)
        norm_mag = np.linalg.norm(normal)
        if norm_mag < 1e-9: continue
        normal /= norm_mag
        if np.dot(normal, v_opposite - v0) < 0: # Corrected normal orientation check based on opposite vertex
            normal = -normal
        D_face = -np.dot(normal, v0)
        if np.dot(normal, point_np) + D_face > 1e-6:
            return False
    return True

def generate_digital_tetrahedron_coordinates(vertices: list[tuple[float,float,float]], inner_offset_factor: float = 0.0):
    if len(vertices) != 4: return []
    outer_tetra_vertices_tuples = vertices
    outer_tetra_vertices_for_check = [np.array(v) for v in outer_tetra_vertices_tuples]
    tetra_coords = set()
    if inner_offset_factor >= 1.0 and inner_offset_factor != 0.0: return []
    outer_vertices_np_array = np.array(outer_tetra_vertices_for_check)
    min_coords_bb, max_coords_bb = np.floor(outer_vertices_np_array.min(axis=0)).astype(int), np.ceil(outer_vertices_np_array.max(axis=0)).astype(int)
    min_x_bb, min_y_bb, min_z_bb = min_coords_bb
    max_x_bb, max_y_bb, max_z_bb = max_coords_bb
    inner_tetra_vertices_for_check = None
    if inner_offset_factor > 0.0:
        centroid_outer = np.mean(outer_vertices_np_array, axis=0)
        inner_verts_temp = []
        for v_outer_np in outer_tetra_vertices_for_check:
            v_inner = centroid_outer + (v_outer_np - centroid_outer) * inner_offset_factor
            inner_verts_temp.append(v_inner)
        inner_tetra_vertices_for_check = inner_verts_temp
    for x in range(min_x_bb, max_x_bb + 1):
        for y in range(min_y_bb, max_y_bb + 1):
            for z in range(min_z_bb, max_z_bb + 1):
                voxel_center = np.array([x + 0.5, y + 0.5, z + 0.5])
                is_inside_outer = _is_point_inside_tetrahedron_helper(voxel_center, outer_tetra_vertices_for_check)
                if is_inside_outer:
                    if inner_offset_factor == 0.0:
                        tetra_coords.add((x, y, z))
                    else:
                        if inner_tetra_vertices_for_check:
                            is_inside_inner = _is_point_inside_tetrahedron_helper(voxel_center, inner_tetra_vertices_for_check)
                            if not is_inside_inner:
                                tetra_coords.add((x, y, z))
                        else: tetra_coords.add((x, y, z))
    return sorted(list(tetra_coords))

def generate_digital_sphere_coordinates(center: tuple[float,float,float], radius: int, is_solid=False):
    center_x,center_y,center_z = int(round(center[0])), int(round(center[1])), int(round(center[2]))
    radius = int(round(radius)) # Ensure radius is integer for range iteration
    sphere_coords = set()
    for z_offset in range(-radius, radius + 1):
        z_coord = center_z + z_offset
        r_slice_squared = radius ** 2 - z_offset ** 2
        if r_slice_squared < 0: continue
        r_slice = int(round(math.sqrt(r_slice_squared)))
        # Midpoint Circle Algorithm for each slice
        cx_slice, cy_slice = center_x, center_y # Center of the slice is same as sphere's XY center
        x, y_circ, p = r_slice, 0, 1 - r_slice
        while x >= y_circ:
            if is_solid:
                for i in range(cx_slice - x, cx_slice + x + 1): # Fill scanline for (x, y_circ)
                    sphere_coords.add((i, cy_slice + y_circ, z_coord))
                    if y_circ != 0: sphere_coords.add((i, cy_slice - y_circ, z_coord))
                for i in range(cx_slice - y_circ, cx_slice + y_circ + 1): # Fill scanline for (y_circ, x)
                    sphere_coords.add((i, cy_slice + x, z_coord))
                    if x != 0: sphere_coords.add((i, cy_slice - x, z_coord))
            else: # Surface only
                points_to_add = [
                    (cx_slice + x, cy_slice + y_circ, z_coord), (cx_slice - x, cy_slice + y_circ, z_coord),
                    (cx_slice + x, cy_slice - y_circ, z_coord), (cx_slice - x, cy_slice - y_circ, z_coord),
                    (cx_slice + y_circ, cy_slice + x, z_coord), (cx_slice - y_circ, cy_slice + x, z_coord),
                    (cx_slice + y_circ, cy_slice - x, z_coord), (cx_slice - y_circ, cy_slice - x, z_coord)
                ]
                for pt in points_to_add: sphere_coords.add(pt)
            y_circ += 1
            if p < 0:
                p = p + 2 * y_circ + 1
            else:
                x -= 1
                p = p + 2 * y_circ - 2 * x + 1
    return sorted(list(sphere_coords))
# In your low-level Python geometry library file

def generate_digital_line_coordinates(p1: tuple[int, int, int], p2: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    """
    Generates integer XYZ coordinates for a 1-voxel-thick digital line segment
    from p1 to p2 using the 3D Bresenham's Line Algorithm.

    This guarantees the line starts at p1, ends at p2, and has no gaps.
    It works best with integer coordinates. Floats will be rounded.

    Args:
        p1: The (x, y, z) integer coordinates of the start point.
        p2: The (x, y, z) integer coordinates of the end point.

    Returns:
        list: A list of (x, y, z) tuples representing the integer coordinates
              of the voxels forming the digital line.
    """
    coords = []
    x1, y1, z1 = round(p1[0]), round(p1[1]), round(p1[2])
    x2, y2, z2 = round(p2[0]), round(p2[1]), round(p2[2])

    # Calculate deltas and step directions
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    dz = abs(z2 - z1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    sz = 1 if z1 < z2 else -1

    # Add the starting point
    coords.append((x1, y1, z1))

    # Determine dominant axis for iteration
    if (dx >= dy) and (dx >= dz):  # X-axis is dominant
        err_1 = 2 * dy - dx
        err_2 = 2 * dz - dx
        while x1 != x2:
            if err_1 > 0:
                y1 += sy
                err_1 -= 2 * dx
            if err_2 > 0:
                z1 += sz
                err_2 -= 2 * dx
            err_1 += 2 * dy
            err_2 += 2 * dz
            x1 += sx
            coords.append((x1, y1, z1))
    elif (dy >= dx) and (dy >= dz):  # Y-axis is dominant
        err_1 = 2 * dx - dy
        err_2 = 2 * dz - dy
        while y1 != y2:
            if err_1 > 0:
                x1 += sx
                err_1 -= 2 * dy
            if err_2 > 0:
                z1 += sz
                err_2 -= 2 * dy
            err_1 += 2 * dx
            err_2 += 2 * dz
            y1 += sy
            coords.append((x1, y1, z1))
    else:  # Z-axis is dominant
        err_1 = 2 * dy - dz
        err_2 = 2 * dx - dz
        while z1 != z2:
            if err_1 > 0:
                y1 += sy
                err_1 -= 2 * dz
            if err_2 > 0:
                x1 += sx
                err_2 -= 2 * dz
            err_1 += 2 * dy
            err_2 += 2 * dx
            z1 += sz
            coords.append((x1, y1, z1))

    return coords
