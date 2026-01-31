import numpy as np
import math
from collections import deque

class DigitalSet:
    """
    A discrete set of integer coordinates (voxels) in 3D space.
    Supports set arithmetic, affine transformations, and morphology.
    """
    def __init__(self, voxels=None):
        if isinstance(voxels, DigitalSet):
            self.voxels = voxels.voxels.copy()
        else:
            self.voxels = set(tuple(v) for v in voxels) if voxels else set()

    def __iter__(self):
        return iter(sorted(list(self.voxels)))

    def __len__(self):
        return len(self.voxels)

    def add(self, voxel):
        self.voxels.add(tuple(voxel))

    def to_list(self):
        return sorted(list(self.voxels))

    # --- Set Operations ---
    def union(self, other):
        return DigitalSet(self.voxels.union(other.voxels))

    def intersection(self, other):
        return DigitalSet(self.voxels.intersection(other.voxels))

    def difference(self, other):
        return DigitalSet(self.voxels.difference(other.voxels))

    # --- Affine Transformations (Local) ---
    def translate(self, dx, dy, dz):
        new_voxels = { (x + int(dx), y + int(dy), z + int(dz)) for x, y, z in self.voxels }
        return DigitalSet(new_voxels)

    def shear(self, axis_primary, axis_secondary, factor):
        """
        Discrete Bijective Shear on the set elements.
        New P = Old P + floor(factor * Old S)
        """
        idx_p = {'x': 0, 'y': 1, 'z': 2}[axis_primary.lower()]
        idx_s = {'x': 0, 'y': 1, 'z': 2}[axis_secondary.lower()]

        new_voxels = set()
        for v in self.voxels:
            coords = list(v)
            shift = math.floor(coords[idx_s] * factor)
            coords[idx_p] += shift
            new_voxels.add(tuple(coords))

        return DigitalSet(new_voxels)

    # --- Morphology ---
    def dilate(self, connectivity=6):
        offsets = self._get_connectivity_offsets(connectivity)
        new_voxels = set(self.voxels)
        for x, y, z in self.voxels:
            for dx, dy, dz in offsets:
                new_voxels.add((x + dx, y + dy, z + dz))
        return DigitalSet(new_voxels)

    def erode(self, connectivity=6):
        offsets = self._get_connectivity_offsets(connectivity)
        new_voxels = set()
        for x, y, z in self.voxels:
            is_interior = True
            for dx, dy, dz in offsets:
                if (x + dx, y + dy, z + dz) not in self.voxels:
                    is_interior = False
                    break
            if is_interior:
                new_voxels.add((x, y, z))
        return DigitalSet(new_voxels)

    def shell(self, thickness=1):
        eroded = self
        for _ in range(thickness):
            eroded = eroded.erode()
        return self.difference(eroded)

    def extrude(self, vector):
        vx, vy, vz = vector
        path = generate_linear_path((0,0,0), (vx, vy, vz))
        new_voxels = set()
        for px, py, pz in path:
            for vx, vy, vz in self.voxels:
                new_voxels.add((vx + px, vy + py, vz + pz))
        return DigitalSet(new_voxels)

    def _get_connectivity_offsets(self, connectivity):
        if connectivity == 6:
            return [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]
        elif connectivity == 26:
            return [(x,y,z) for x in (-1,0,1) for y in (-1,0,1) for z in (-1,0,1) if not (x==0 and y==0 and z==0)]
        return []

# --- Generators ---

def generate_linear_path(p1, p2):
    """
    3D Bresenham Algorithm (26-connected).
    Returns a DigitalSet containing all voxels on the line segment from p1 to p2, inclusive.
    """
    x1, y1, z1 = map(int, p1)
    x2, y2, z2 = map(int, p2)
    points = []

    # Always include the starting point
    points.append((x1, y1, z1))

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    dz = abs(z2 - z1)

    xs = 1 if x2 > x1 else -1
    ys = 1 if y2 > y1 else -1
    zs = 1 if z2 > z1 else -1

    # Driving axis is X
    if dx >= dy and dx >= dz:
        p1_err = 2 * dy - dx
        p2_err = 2 * dz - dx
        while x1 != x2:
            x1 += xs
            if p1_err >= 0:
                y1 += ys
                p1_err -= 2 * dx
            if p2_err >= 0:
                z1 += zs
                p2_err -= 2 * dx
            p1_err += 2 * dy
            p2_err += 2 * dz
            points.append((x1, y1, z1))

    # Driving axis is Y
    elif dy >= dx and dy >= dz:
        p1_err = 2 * dx - dy
        p2_err = 2 * dz - dy
        while y1 != y2:
            y1 += ys
            if p1_err >= 0:
                x1 += xs
                p1_err -= 2 * dy
            if p2_err >= 0:
                z1 += zs
                p2_err -= 2 * dy
            p1_err += 2 * dx
            p2_err += 2 * dz
            points.append((x1, y1, z1))

    # Driving axis is Z
    else:
        p1_err = 2 * dy - dz
        p2_err = 2 * dx - dz
        while z1 != z2:
            z1 += zs
            if p1_err >= 0:
                y1 += ys
                p1_err -= 2 * dz
            if p2_err >= 0:
                x1 += xs
                p2_err -= 2 * dz
            p1_err += 2 * dy
            p2_err += 2 * dx
            points.append((x1, y1, z1))

    return DigitalSet(points)

def generate_metric_ball(center, radius, metric='euclidean'):
    cx, cy, cz = center
    r = int(radius)
    voxels = set()
    for x in range(cx - r, cx + r + 1):
        for y in range(cy - r, cy + r + 1):
            for z in range(cz - r, cz + r + 1):
                dx, dy, dz = abs(x-cx), abs(y-cy), abs(z-cz)
                dist = 0
                if metric == 'euclidean': dist = math.sqrt(dx*dx + dy*dy + dz*dz)
                elif metric == 'manhattan': dist = dx + dy + dz
                elif metric == 'chebyshev': dist = max(dx, dy, dz)
                if dist <= r: voxels.add((x, y, z))
    return DigitalSet(voxels)

def generate_digital_plane_coordinates(normal, point_on_plane, outer_rect_dims):
    coords = set()
    n = np.array(normal, dtype=float)
    if np.linalg.norm(n) == 0: return DigitalSet()
    n /= np.linalg.norm(n)

    arithmetic_thickness = np.sum(np.abs(n))
    thickness_epsilon = 1e-9
    point = np.array(point_on_plane, dtype=float)
    width, height = outer_rect_dims

    if np.allclose(n, [0, 1, 0]) or np.allclose(n, [0, -1, 0]):
        u = np.array([1, 0, 0]); v = np.array([0, 0, 1])
    else:
        u = np.cross(n, [0, 1, 0])
        if np.linalg.norm(u) < 1e-6: u = np.cross(n, [0, 0, 1])
        u /= np.linalg.norm(u); v = np.cross(n, u); v /= np.linalg.norm(v)

    half_w_vec = u * (width / 2.0); half_h_vec = v * (height / 2.0)
    corners = [point+half_w_vec+half_h_vec, point+half_w_vec-half_h_vec, point-half_w_vec+half_h_vec, point-half_w_vec-half_h_vec]
    padding = 2
    min_bounds = np.floor(np.min(corners, axis=0)).astype(int) - padding
    max_bounds = np.ceil(np.max(corners, axis=0)).astype(int) + padding
    boundary_u = width / 2.0 + 1e-9; boundary_v = height / 2.0 + 1e-9

    for x in range(min_bounds[0], max_bounds[0] + 1):
        for y in range(min_bounds[1], max_bounds[1] + 1):
            for z in range(min_bounds[2], max_bounds[2] + 1):
                voxel_center = np.array([x, y, z], dtype=float)
                dist = np.dot(voxel_center - point, n)
                threshold = (arithmetic_thickness / 2.0) + thickness_epsilon
                if -threshold <= dist < threshold:
                    closest = voxel_center - dist * n
                    vec = closest - point
                    proj_u = np.dot(vec, u); proj_v = np.dot(vec, v)
                    if abs(proj_u) <= boundary_u and abs(proj_v) <= boundary_v:
                        coords.add((x, y, z))
    return DigitalSet(coords)

# --- The Discrete Affine Turtle ---

class DigitalTurtle:
    """
    A 3D Turtle moving on the Integer Lattice (Z^3).
    Instead of continuous rotation, it uses:
    1. Discrete Rotations (90 degree increments)
    2. Integer Shears (Skewing the coordinate system)
    """
    def __init__(self, start_pos=(0,0,0)):
        # Position is strictly integer
        self.pos = np.array(start_pos, dtype=int)

        # Basis Vectors (The Turtle's Coordinate Frame)
        self.right   = np.array([1, 0, 0], dtype=int)
        self.up      = np.array([0, 1, 0], dtype=int)
        self.forward = np.array([0, 0, 1], dtype=int)

        # Scale State (for L-Systems)
        self.scale = 1.0
        self.scale_factor = 0.666 # Default delta

        self.brush = DigitalSet()
        self.stack = []

    def set_scale_factor(self, factor):
        self.scale_factor = float(factor)

    def set_brush(self, digital_set):
        if isinstance(digital_set, DigitalSet):
            self.brush = digital_set

    def move(self, distance: int, direction='forward'):
        """Moves the turtle along its current basis vectors."""
        vec = np.array([0,0,0], dtype=int)
        direction = direction.lower()
        if direction == 'forward': vec = self.forward
        elif direction == 'back':  vec = -self.forward
        elif direction == 'up':    vec = self.up
        elif direction == 'down':  vec = -self.up
        elif direction == 'right': vec = self.right
        elif direction == 'left':  vec = -self.right

        # Apply scaling if relevant context, but standard move usually is unit based.
        # For L-system parity, we apply it if called via interpret_symbol.
        # But this is the raw API. Let's keep it raw integer steps here.
        self.pos += vec * int(distance)

    def rotate_90(self, axis='y', steps=1):
        """
        Discrete rotation of the turtle's entire frame around a GLOBAL axis.
        """
        axis = axis.lower()

        # Define the permutation function for a single vector [x, y, z]
        def apply_rotation(vec, axis_char):
            x, y, z = vec
            if axis_char == 'x':   # Rot X: (x, -z, y)
                return np.array([x, -z, y], dtype=int)
            elif axis_char == 'y': # Rot Y: (z, y, -x)
                return np.array([z, y, -x], dtype=int)
            elif axis_char == 'z': # Rot Z: (-y, x, z)
                return np.array([-y, x, z], dtype=int)
            return vec

        for _ in range(steps % 4):
            # Apply the global rotation to ALL basis vectors independently
            self.right   = apply_rotation(self.right, axis)
            self.up      = apply_rotation(self.up, axis)
            self.forward = apply_rotation(self.forward, axis)

    def shear(self, primary_axis, secondary_axis, factor: int):
        """
        Affine Shear of the coordinate basis.
        Example: shear('x', 'y', 1) adds 1*Up to Right.
        This skews the grid, allowing for diagonal movement and organic shapes
        while strictly preserving integer coordinates.
        """
        primary_axis = primary_axis.lower()
        secondary_axis = secondary_axis.lower()

        vec_map = {'x': self.right, 'y': self.up, 'z': self.forward}
        v_prim = vec_map.get(primary_axis)
        v_sec  = vec_map.get(secondary_axis)

        if v_prim is None or v_sec is None: return

        result = v_prim + v_sec * int(factor)

        if primary_axis == 'x': self.right = result
        elif primary_axis == 'y': self.up = result
        elif primary_axis == 'z': self.forward = result

    def stamp(self):
        if not self.brush: return DigitalSet()
        world_voxels = []
        for bx, by, bz in self.brush:
            offset = (bx * self.right) + (by * self.up) + (bz * self.forward)
            final_pos = self.pos + offset
            world_voxels.append(tuple(final_pos))
        return DigitalSet(world_voxels)

    def extrude(self, distance: int, direction: str = 'forward'):
        """
        Sweeps the brush forward using the current (possibly sheared) Forward vector.
        Returns a DigitalSet.
        """
        vec = np.array([0,0,0], dtype=int)
        direction = direction.lower() # Robustness
        if direction == 'forward': vec = self.forward
        elif direction == 'back':  vec = -self.forward
        elif direction == 'up':    vec = self.up
        elif direction == 'down':  vec = -self.up
        elif direction == 'right': vec = self.right
        elif direction == 'left':  vec = -self.right

        start_pos = self.pos.copy()
        move_vec = vec * int(distance)

        path = generate_linear_path((0,0,0), tuple(move_vec))

        world_voxels = set()
        for px, py, pz in path:
            step_offset = np.array([px, py, pz])
            current_turtle_pos = start_pos + step_offset
            for bx, by, bz in self.brush:
                brush_offset = (bx * self.right) + (by * self.up) + (bz * self.forward)
                final_pos = current_turtle_pos + brush_offset
                world_voxels.add(tuple(final_pos))

        self.pos += move_vec
        return DigitalSet(world_voxels)

    def push_state(self):
        # Save Scale + Vectors
        self.stack.append((
            self.pos.copy(),
            self.forward.copy(),
            self.up.copy(),
            self.right.copy(),
            self.scale
        ))

    def pop_state(self):
        if self.stack:
            self.pos, self.forward, self.up, self.right, self.scale = self.stack.pop()

    def interpret_symbol(self, symbol, step_size):
        """
        Executes a single L-System symbol.
        Returns a DigitalSet of placed blocks (if drawing occurred), or None.

        New Symbols:
        " : Multiply scale by scale_factor (Shrink)
        ! : Divide scale by scale_factor (Grow)
        """
        # Calculate Scaled Step Size (Minimum 1 block)
        scaled_step = max(1, int(step_size * self.scale))

        if symbol == 'F':
            return self.extrude(scaled_step)
        elif symbol == 'f':
            self.move(scaled_step)
        elif symbol == '+':
            self.rotate_90('y', 1)
        elif symbol == '-':
            self.rotate_90('y', -1)
        elif symbol == '&':
            self.rotate_90('x', 1)
        elif symbol == '^':
            self.rotate_90('x', -1)
        elif symbol == '\\':
            self.rotate_90('z', 1)
        elif symbol == '/':
            self.rotate_90('z', -1)
        elif symbol == '|':
            self.rotate_90('y', 2)
        elif symbol == '[':
            self.push_state()
        elif symbol == ']':
            self.pop_state()
        elif symbol == '>': # "Bend Right"
             self.shear('z', 'x', 1)
        elif symbol == '<': # "Bend Left"
             self.shear('z', 'x', -1)
        elif symbol == '@': # Shrink
             self.scale *= self.scale_factor
             return self.extrude(scaled_step)
        elif symbol == '!': # Grow
             if self.scale_factor > 0:
                 self.scale /= self.scale_factor
             return self.extrude(scaled_step)
        return None