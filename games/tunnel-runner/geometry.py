from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable

import pygame


# ============================================================
# TUNNEL RUNNER
# 3D GEOMETRY ENGINE
# VERSION 0.2.6 - FAST OUTSIDE SURFACE
# ============================================================
#
# NEW:
#
# - True inside-cylinder rendering
# - True outside-cylinder rendering
# - Outside-follow camera
# - Inside camera
# - Environment transition support
# - Neon panel shading
# - Atmospheric fog
# - Depth shading
# - Cheap panel highlights
# - Portal rings
# - Optimized projection
# - Optimized depth sorting
# - Low allocation renderer
#
# Designed to continue working with:
#
# - main.py
# - obstacles.py
# - levels.py
#
# ============================================================


# ============================================================
# CONSTANTS
# ============================================================

ENVIRONMENT_INSIDE = "inside"

ENVIRONMENT_OUTSIDE = "outside"

ENVIRONMENT_TRANSITION = "transition"


DEFAULT_FOV = 78.0

DEFAULT_NEAR_CLIP = 0.35

DEFAULT_FAR_CLIP = 550.0


# ============================================================
# BASIC MATH
# ============================================================

def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def lerp(
    first: float,
    second: float,
    amount: float,
) -> float:

    amount = clamp(
        amount,
        0.0,
        1.0,
    )

    return (
        first
        + (
            second
            - first
        )
        * amount
    )


def smoothstep(
    value: float,
) -> float:

    value = clamp(
        value,
        0.0,
        1.0,
    )

    return (
        value
        * value
        * (
            3.0
            - 2.0
            * value
        )
    )


def normalize_degrees(
    angle: float,
) -> float:

    return (
        float(
            angle
        )
        % 360.0
    )


def shortest_angle_delta(
    current: float,
    target: float,
) -> float:

    return (
        (
            target
            - current
            + 180.0
        )
        % 360.0
        - 180.0
    )


def angle_in_arc(
    angle: float,
    center: float,
    width: float,
) -> bool:

    width = clamp(
        width,
        0.0,
        360.0,
    )

    if (
        width
        >= 359.999
    ):

        return True

    difference = abs(
        shortest_angle_delta(
            center,
            angle,
        )
    )

    return (
        difference
        <= width
        / 2.0
    )


def multiply_colour(
    colour: tuple[int, int, int],
    amount: float,
) -> tuple[int, int, int]:

    return (
        int(
            clamp(
                colour[0]
                * amount,
                0,
                255,
            )
        ),

        int(
            clamp(
                colour[1]
                * amount,
                0,
                255,
            )
        ),

        int(
            clamp(
                colour[2]
                * amount,
                0,
                255,
            )
        ),
    )


def blend_colour(
    first: tuple[int, int, int],
    second: tuple[int, int, int],
    amount: float,
) -> tuple[int, int, int]:

    amount = clamp(
        amount,
        0.0,
        1.0,
    )

    return (
        round(
            lerp(
                first[0],
                second[0],
                amount,
            )
        ),

        round(
            lerp(
                first[1],
                second[1],
                amount,
            )
        ),

        round(
            lerp(
                first[2],
                second[2],
                amount,
            )
        ),
    )


# ============================================================
# VEC2
# ============================================================

@dataclass
class Vec2:
    x: float = 0.0
    y: float = 0.0

    def copy(
        self,
    ) -> Vec2:

        return Vec2(
            self.x,
            self.y,
        )

    def __add__(
        self,
        other: Vec2,
    ) -> Vec2:

        return Vec2(
            self.x
            + other.x,

            self.y
            + other.y,
        )

    def __sub__(
        self,
        other: Vec2,
    ) -> Vec2:

        return Vec2(
            self.x
            - other.x,

            self.y
            - other.y,
        )

    def __mul__(
        self,
        amount: float,
    ) -> Vec2:

        return Vec2(
            self.x
            * amount,

            self.y
            * amount,
        )

    def __rmul__(
        self,
        amount: float,
    ) -> Vec2:

        return self.__mul__(
            amount
        )

    def __truediv__(
        self,
        amount: float,
    ) -> Vec2:

        if (
            abs(
                amount
            )
            < 0.000001
        ):

            return Vec2()

        return Vec2(
            self.x
            / amount,

            self.y
            / amount,
        )

    def int_tuple(
        self,
    ) -> tuple[int, int]:

        return (
            round(
                self.x
            ),

            round(
                self.y
            ),
        )


# ============================================================
# VEC3
# ============================================================

@dataclass
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def copy(
        self,
    ) -> Vec3:

        return Vec3(
            self.x,
            self.y,
            self.z,
        )

    def __add__(
        self,
        other: Vec3,
    ) -> Vec3:

        return Vec3(
            self.x
            + other.x,

            self.y
            + other.y,

            self.z
            + other.z,
        )

    def __sub__(
        self,
        other: Vec3,
    ) -> Vec3:

        return Vec3(
            self.x
            - other.x,

            self.y
            - other.y,

            self.z
            - other.z,
        )

    def __mul__(
        self,
        amount: float,
    ) -> Vec3:

        return Vec3(
            self.x
            * amount,

            self.y
            * amount,

            self.z
            * amount,
        )

    def __rmul__(
        self,
        amount: float,
    ) -> Vec3:

        return self.__mul__(
            amount
        )

    def __truediv__(
        self,
        amount: float,
    ) -> Vec3:

        if (
            abs(
                amount
            )
            < 0.000001
        ):

            return Vec3()

        return Vec3(
            self.x
            / amount,

            self.y
            / amount,

            self.z
            / amount,
        )

    def dot(
        self,
        other: Vec3,
    ) -> float:

        return (
            self.x
            * other.x

            + self.y
            * other.y

            + self.z
            * other.z
        )

    def cross(
        self,
        other: Vec3,
    ) -> Vec3:

        return Vec3(
            self.y
            * other.z
            - self.z
            * other.y,

            self.z
            * other.x
            - self.x
            * other.z,

            self.x
            * other.y
            - self.y
            * other.x,
        )

    def length(
        self,
    ) -> float:

        return math.sqrt(
            self.x
            * self.x

            + self.y
            * self.y

            + self.z
            * self.z
        )

    def normalized(
        self,
    ) -> Vec3:

        length = self.length()

        if length <= 0.000001:

            return Vec3()

        return self / length


# ============================================================
# FACE
# ============================================================

@dataclass
class Face3D:
    vertices: list[Vec3]

    colour: tuple[int, int, int]

    outline_colour: tuple[int, int, int] | None = None

    outline_width: int = 0

    double_sided: bool = True

    glow: bool = False

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================
# MESH
# ============================================================

@dataclass
class Mesh3D:
    faces: list[Face3D]

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================
# TUNNEL POINT
# ============================================================

def tunnel_point(
    angle_degrees: float,
    z: float,
    *,
    radius: float,
) -> Vec3:

    radians = math.radians(
        angle_degrees
    )

    return Vec3(
        math.cos(
            radians
        )
        * radius,

        math.sin(
            radians
        )
        * radius,

        z,
    )


# ============================================================
# ROTATE
# ============================================================

def rotate_point_z(
    point: Vec3,
    angle_degrees: float,
    *,
    origin: Vec3 | None = None,
) -> Vec3:

    if origin is None:

        origin = Vec3()

    radians = math.radians(
        angle_degrees
    )

    cosine = math.cos(
        radians
    )

    sine = math.sin(
        radians
    )

    x = (
        point.x
        - origin.x
    )

    y = (
        point.y
        - origin.y
    )

    return Vec3(
        origin.x
        + x
        * cosine
        - y
        * sine,

        origin.y
        + x
        * sine
        + y
        * cosine,

        point.z,
    )


def rotate_mesh_vertices_z(
    mesh: Mesh3D,
    angle_degrees: float,
    *,
    origin: Vec3 | None = None,
) -> Mesh3D:

    if origin is None:

        origin = Vec3()

    faces: list[
        Face3D
    ] = []

    for face in mesh.faces:

        faces.append(
            Face3D(
                vertices=[
                    rotate_point_z(
                        vertex,
                        angle_degrees,
                        origin=origin,
                    )

                    for vertex
                    in face.vertices
                ],

                colour=(
                    face.colour
                ),

                outline_colour=(
                    face.outline_colour
                ),

                outline_width=(
                    face.outline_width
                ),

                double_sided=(
                    face.double_sided
                ),

                glow=(
                    face.glow
                ),

                metadata=dict(
                    face.metadata
                ),
            )
        )

    return Mesh3D(
        faces=faces,

        metadata=dict(
            mesh.metadata
        ),
    )


# ============================================================
# BOX
# ============================================================

def create_box_mesh(
    *,
    center: Vec3,
    size: Vec3,
    colour: tuple[int, int, int],
    outline_colour: tuple[int, int, int] | None = None,
    outline_width: int = 0,
    double_sided: bool = True,
) -> Mesh3D:

    half_x = (
        size.x
        / 2.0
    )

    half_y = (
        size.y
        / 2.0
    )

    half_z = (
        size.z
        / 2.0
    )

    points = [
        Vec3(
            center.x - half_x,
            center.y - half_y,
            center.z - half_z,
        ),

        Vec3(
            center.x + half_x,
            center.y - half_y,
            center.z - half_z,
        ),

        Vec3(
            center.x + half_x,
            center.y + half_y,
            center.z - half_z,
        ),

        Vec3(
            center.x - half_x,
            center.y + half_y,
            center.z - half_z,
        ),

        Vec3(
            center.x - half_x,
            center.y - half_y,
            center.z + half_z,
        ),

        Vec3(
            center.x + half_x,
            center.y - half_y,
            center.z + half_z,
        ),

        Vec3(
            center.x + half_x,
            center.y + half_y,
            center.z + half_z,
        ),

        Vec3(
            center.x - half_x,
            center.y + half_y,
            center.z + half_z,
        ),
    ]

    indexes = (
        (
            0,
            1,
            2,
            3,
        ),

        (
            4,
            7,
            6,
            5,
        ),

        (
            0,
            4,
            5,
            1,
        ),

        (
            1,
            5,
            6,
            2,
        ),

        (
            2,
            6,
            7,
            3,
        ),

        (
            3,
            7,
            4,
            0,
        ),
    )

    faces = []

    for index, face_indexes in enumerate(
        indexes
    ):

        shade = (
            0.88
            + (
                index
                % 3
            )
            * 0.06
        )

        faces.append(
            Face3D(
                vertices=[
                    points[
                        vertex_index
                    ]

                    for vertex_index
                    in face_indexes
                ],

                colour=multiply_colour(
                    colour,
                    shade,
                ),

                outline_colour=(
                    outline_colour
                ),

                outline_width=(
                    outline_width
                ),

                double_sided=(
                    double_sided
                ),
            )
        )

    return Mesh3D(
        faces=faces
    )


# ============================================================
# TUNNEL PANEL COLOUR
# ============================================================

def tunnel_panel_colour(
    primary_colour: tuple[int, int, int],
    secondary_colour: tuple[int, int, int],
    index: int,
    *,
    outside: bool = False,
) -> tuple[int, int, int]:

    # Alternating panels create the bright Tunnel-Rush-like
    # kaleidoscope appearance without adding extra geometry.

    phase = (
        index
        % 6
    )

    if phase == 0:

        colour = primary_colour

        brightness = (
            1.18
            if outside
            else 1.08
        )

    elif phase == 1:

        colour = secondary_colour

        brightness = 0.80

    elif phase == 2:

        colour = primary_colour

        brightness = 0.72

    elif phase == 3:

        colour = secondary_colour

        brightness = (
            1.10
            if outside
            else 0.95
        )

    elif phase == 4:

        colour = primary_colour

        brightness = 0.88

    else:

        colour = secondary_colour

        brightness = 0.68

    return multiply_colour(
        colour,
        brightness,
    )


# ============================================================
# INSIDE TUNNEL SECTION
# ============================================================

def create_tunnel_section_mesh(
    start_z: float,
    end_z: float,
    *,
    radius: float,
    segments: int,
    start_rotation: float = 0.0,
    end_rotation: float = 0.0,
    primary_colour: tuple[int, int, int],
    secondary_colour: tuple[int, int, int],
    line_colour: tuple[int, int, int] | None = None,
    draw_outlines: bool = False,
) -> Mesh3D:

    segments = max(
        6,
        int(
            segments
        ),
    )

    faces: list[
        Face3D
    ] = []

    angle_step = (
        360.0
        / segments
    )

    for index in range(
        segments
    ):

        angle_a = (
            index
            * angle_step
        )

        angle_b = (
            angle_a
            + angle_step
        )

        start_a = tunnel_point(
            angle_a
            + start_rotation,

            start_z,

            radius=radius,
        )

        start_b = tunnel_point(
            angle_b
            + start_rotation,

            start_z,

            radius=radius,
        )

        end_a = tunnel_point(
            angle_a
            + end_rotation,

            end_z,

            radius=radius,
        )

        end_b = tunnel_point(
            angle_b
            + end_rotation,

            end_z,

            radius=radius,
        )

        colour = tunnel_panel_colour(
            primary_colour,
            secondary_colour,
            index,
            outside=False,
        )

        faces.append(
            Face3D(
                vertices=[
                    start_a,
                    end_a,
                    end_b,
                    start_b,
                ],

                colour=colour,

                outline_colour=(
                    line_colour

                    if draw_outlines

                    else None
                ),

                outline_width=(
                    1

                    if (
                        draw_outlines
                        and line_colour
                        is not None
                    )

                    else 0
                ),

                double_sided=True,

                metadata={
                    "environment":
                        ENVIRONMENT_INSIDE,

                    "panel_index":
                        index,
                },
            )
        )

    return Mesh3D(
        faces=faces,

        metadata={
            "environment":
                ENVIRONMENT_INSIDE,

            "start_z":
                start_z,

            "end_z":
                end_z,
        },
    )


# ============================================================
# OUTSIDE CYLINDER
# ============================================================

def create_outside_tunnel_section_mesh(
    start_z: float,
    end_z: float,
    *,
    radius: float,
    segments: int,
    start_rotation: float = 0.0,
    end_rotation: float = 0.0,
    primary_colour: tuple[int, int, int],
    secondary_colour: tuple[int, int, int],
    line_colour: tuple[int, int, int] | None = None,
    draw_outlines: bool = False,
) -> Mesh3D:
    """
    Fast exterior-tube mesh.

    Performance rules:
    - one face per cylinder segment
    - no raised ribs
    - no extra ring-band geometry
    - strong alternating colour contrast keeps depth readable
    - selective outlines preserve the improved visual style
    """

    segments = max(
        8,
        int(
            segments
        ),
    )

    faces: list[
        Face3D
    ] = []

    angle_step = (
        360.0
        / segments
    )

    for index in range(
        segments
    ):

        angle_a = (
            index
            * angle_step
        )

        angle_b = (
            angle_a
            + angle_step
        )

        start_a = tunnel_point(
            angle_a
            + start_rotation,
            start_z,
            radius=radius,
        )

        start_b = tunnel_point(
            angle_b
            + start_rotation,
            start_z,
            radius=radius,
        )

        end_a = tunnel_point(
            angle_a
            + end_rotation,
            end_z,
            radius=radius,
        )

        end_b = tunnel_point(
            angle_b
            + end_rotation,
            end_z,
            radius=radius,
        )

        base_colour = tunnel_panel_colour(
            primary_colour,
            secondary_colour,
            index,
            outside=True,
        )

        colour = multiply_colour(
            base_colour,
            (
                1.10
                if index % 2 == 0
                else 0.72
            ),
        )

        use_outline = (
            line_colour is not None
            and (
                draw_outlines
                or index % 3 == 0
            )
        )

        faces.append(
            Face3D(
                vertices=[
                    start_b,
                    end_b,
                    end_a,
                    start_a,
                ],

                colour=colour,

                outline_colour=(
                    line_colour
                    if use_outline
                    else None
                ),

                outline_width=(
                    1
                    if use_outline
                    else 0
                ),

                double_sided=True,

                metadata={
                    "environment":
                        ENVIRONMENT_OUTSIDE,

                    "panel_index":
                        index,
                },
            )
        )

    return Mesh3D(
        faces=faces,

        metadata={
            "environment":
                ENVIRONMENT_OUTSIDE,

            "start_z":
                start_z,

            "end_z":
                end_z,
        },
    )


# ============================================================
# TRANSITION RING
# ============================================================

def create_transition_ring_mesh(
    z: float,
    *,
    radius: float,
    segments: int,
    colour: tuple[int, int, int],
    thickness: float = 0.32,
) -> Mesh3D:

    segments = max(
        8,
        int(
            segments
        ),
    )

    inner_radius = (
        radius
        - thickness
    )

    outer_radius = (
        radius
        + thickness
    )

    faces: list[
        Face3D
    ] = []

    step = (
        360.0
        / segments
    )

    for index in range(
        segments
    ):

        angle_a = (
            index
            * step
        )

        angle_b = (
            angle_a
            + step
        )

        brightness = (
            1.25

            if index
            % 2
            == 0

            else 0.72
        )

        panel_colour = multiply_colour(
            colour,
            brightness,
        )

        faces.append(
            Face3D(
                vertices=[
                    tunnel_point(
                        angle_a,
                        z,
                        radius=inner_radius,
                    ),

                    tunnel_point(
                        angle_a,
                        z,
                        radius=outer_radius,
                    ),

                    tunnel_point(
                        angle_b,
                        z,
                        radius=outer_radius,
                    ),

                    tunnel_point(
                        angle_b,
                        z,
                        radius=inner_radius,
                    ),
                ],

                colour=panel_colour,

                outline_colour=None,

                outline_width=0,

                double_sided=True,

                glow=True,

                metadata={
                    "transition_ring":
                        True,
                },
            )
        )

    return Mesh3D(
        faces=faces
    )


# ============================================================
# TRANSITION RING GROUP
# ============================================================

def create_environment_transition_meshes(
    *,
    start_z: float,
    length: float,
    radius: float,
    segments: int,
    colour: tuple[int, int, int],
) -> list[Mesh3D]:

    meshes: list[
        Mesh3D
    ] = []

    ring_count = 7

    usable_length = max(
        12.0,
        length,
    )

    for index in range(
        ring_count
    ):

        amount = (
            index
            / max(
                1,
                ring_count - 1,
            )
        )

        z = (
            start_z
            + usable_length
            * amount
        )

        size_wave = (
            math.sin(
                amount
                * math.pi
            )
        )

        meshes.append(
            create_transition_ring_mesh(
                z,

                radius=(
                    radius
                    + size_wave
                    * radius
                    * 0.18
                ),

                segments=segments,

                colour=colour,

                thickness=(
                    0.22
                    + size_wave
                    * 0.26
                ),
            )
        )

    return meshes


# ============================================================
# CAMERA
# ============================================================

class Camera3D:

    def __init__(
        self,
        *,
        width: int,
        height: int,
        fov: float = DEFAULT_FOV,
        near_clip: float = DEFAULT_NEAR_CLIP,
        far_clip: float = DEFAULT_FAR_CLIP,
    ):

        self.width = max(
            1,
            int(
                width
            ),
        )

        self.height = max(
            1,
            int(
                height
            ),
        )

        self.fov = float(
            fov
        )

        self.near_clip = max(
            0.05,
            float(
                near_clip
            ),
        )

        self.far_clip = max(
            self.near_clip
            + 1.0,

            float(
                far_clip
            ),
        )

        self.position = Vec3()

        # x = pitch
        # y = yaw
        # z = roll

        self.rotation = Vec3()

        self.shake_offset = Vec2()

        self.environment = (
            ENVIRONMENT_INSIDE
        )

        self.environment_blend = 0.0

        self.look_target: Vec3 | None = None

        self.up_reference: Vec3 | None = None

        # ----------------------------------------------------
        # TRANSITION CAMERA STATE
        # ----------------------------------------------------
        #
        # During an inside/outside transition we do not switch
        # abruptly between Euler and look-at projection. Instead,
        # world_to_camera() calculates both camera-space positions
        # and blends them continuously.
        self._transition_camera_active = False
        self._transition_camera_z = 0.0
        self._transition_player_angle = 0.0
        self._transition_tunnel_radius = 1.0

        self._projection_scale = 1.0

        self._recalculate_projection()

    # ========================================================
    # SIZE
    # ========================================================

    def set_size(
        self,
        width: int,
        height: int,
    ) -> None:

        self.width = max(
            1,
            int(
                width
            ),
        )

        self.height = max(
            1,
            int(
                height
            ),
        )

        self._recalculate_projection()

    # ========================================================
    # PROJECTION SCALE
    # ========================================================

    def _recalculate_projection(
        self,
    ) -> None:

        half_fov = math.radians(
            self.fov
            / 2.0
        )

        tangent = max(
            0.001,
            math.tan(
                half_fov
            ),
        )

        self._projection_scale = (
            self.height
            / 2.0
            / tangent
        )

    # ========================================================
    # INSIDE MODE
    # ========================================================

    def configure_inside(
        self,
        *,
        camera_z: float,
        player_angle: float,
    ) -> None:

        self.environment = (
            ENVIRONMENT_INSIDE
        )

        self.position = Vec3(
            0.0,
            0.0,
            camera_z,
        )

        self.rotation = Vec3(
            0.0,
            0.0,
            player_angle,
        )

        self.look_target = None

        self.up_reference = None

        self.environment_blend = 0.0

        self._transition_camera_active = False

    # ========================================================
    # OUTSIDE MODE
    # ========================================================

    def configure_outside(
        self,
        *,
        camera_z: float,
        player_angle: float,
        tunnel_radius: float,
        camera_distance_multiplier: float = 1.18,
        camera_back: float = 2.2,
        look_ahead: float = 34.0,
    ) -> None:
        """
        Configure the camera to ride just above the OUTSIDE surface.

        The old outside camera sat 2.55 tunnel radii away, which made
        the player feel like they were watching the tube from space.

        This camera stays close to the cylinder, follows the player's
        angular position, and looks forward along the surface. The
        result should feel like the inside-tunnel camera has been moved
        to the exterior rather than replaced with a distant spectator
        camera.
        """

        self.environment = (
            ENVIRONMENT_OUTSIDE
        )

        radians = math.radians(
            player_angle
        )

        radial_x = math.cos(
            radians
        )

        radial_y = math.sin(
            radians
        )

        # ----------------------------------------------------
        # CAMERA POSITION
        # ----------------------------------------------------
        #
        # 1.0 * radius would place the camera directly on the tube.
        # 1.18 keeps it only a little above the surface so geometry
        # does not clip through the near plane.
        camera_radius = (
            tunnel_radius
            * max(
                1.08,
                float(
                    camera_distance_multiplier
                ),
            )
        )

        self.position = Vec3(
            radial_x
            * camera_radius,

            radial_y
            * camera_radius,

            camera_z
            - max(
                0.0,
                float(
                    camera_back
                ),
            ),
        )

        # ----------------------------------------------------
        # LOOK TARGET
        # ----------------------------------------------------
        #
        # Aim almost exactly along the exterior surface rather than
        # toward the center of the cylinder.
        target_radius = (
            tunnel_radius
            * 1.00
        )

        self.look_target = Vec3(
            radial_x
            * target_radius,

            radial_y
            * target_radius,

            camera_z
            + max(
                8.0,
                float(
                    look_ahead
                ),
            ),
        )

        # Outward from the tube is "up". This keeps the track surface
        # under the player in the same intuitive way that the tunnel
        # wall sits around the player while inside.
        self.up_reference = Vec3(
            radial_x,
            radial_y,
            0.0,
        ).normalized()

        self.rotation.x = 0.0
        self.rotation.y = 0.0
        self.rotation.z = 0.0

        self.environment_blend = 1.0

        self._transition_camera_active = False

    # ========================================================
    # TRANSITION
    # ========================================================

    def configure_transition(
        self,
        *,
        camera_z: float,
        player_angle: float,
        tunnel_radius: float,
        amount: float,
        going_outside: bool,
    ) -> None:
        """
        Configure a fully continuous inside/outside camera blend.

        No projection-mode switch occurs during the transition.
        world_to_camera() blends the exact inside and outside
        camera-space transforms instead.
        """

        raw_amount = clamp(
            float(amount),
            0.0,
            1.0,
        )

        eased_progress = smoothstep(
            raw_amount
        )

        outside_amount = (
            eased_progress
            if going_outside
            else 1.0 - eased_progress
        )

        outside_amount = clamp(
            outside_amount,
            0.0,
            1.0,
        )

        self.environment = (
            ENVIRONMENT_TRANSITION
        )

        self.environment_blend = (
            outside_amount
        )

        self._transition_camera_active = True

        self._transition_camera_z = float(
            camera_z
        )

        self._transition_player_angle = (
            float(player_angle)
            % 360.0
        )

        self._transition_tunnel_radius = max(
            0.001,
            float(tunnel_radius),
        )

        radians = math.radians(
            self._transition_player_angle
        )

        radial_x = math.cos(
            radians
        )

        radial_y = math.sin(
            radians
        )

        outside_radius = (
            self._transition_tunnel_radius
            * 2.55
        )

        outside_position = Vec3(
            radial_x
            * outside_radius,

            radial_y
            * outside_radius,

            self._transition_camera_z
            - 7.5,
        )

        inside_position = Vec3(
            0.0,
            0.0,
            self._transition_camera_z,
        )

        # Keep public camera fields smoothly interpolated too.
        self.position = Vec3(
            lerp(
                inside_position.x,
                outside_position.x,
                outside_amount,
            ),
            lerp(
                inside_position.y,
                outside_position.y,
                outside_amount,
            ),
            lerp(
                inside_position.z,
                outside_position.z,
                outside_amount,
            ),
        )

        self.rotation = Vec3(
            0.0,
            0.0,
            self._transition_player_angle
            * (
                1.0
                - outside_amount
            ),
        )

        # world_to_camera() handles transition projection itself.
        # Keeping these None prevents a hidden look-at mode switch.
        self.look_target = None
        self.up_reference = None

    # ========================================================
    # EULER CAMERA
    # ========================================================

    def _world_to_camera_euler(
        self,
        point: Vec3,
    ) -> Vec3:

        x = (
            point.x
            - self.position.x
        )

        y = (
            point.y
            - self.position.y
        )

        z = (
            point.z
            - self.position.z
        )

        # ----------------------------------------------------
        # INVERSE ROLL
        # ----------------------------------------------------

        roll = math.radians(
            -self.rotation.z
        )

        cosine = math.cos(
            roll
        )

        sine = math.sin(
            roll
        )

        rolled_x = (
            x
            * cosine
            - y
            * sine
        )

        rolled_y = (
            x
            * sine
            + y
            * cosine
        )

        x = rolled_x
        y = rolled_y

        # ----------------------------------------------------
        # INVERSE YAW
        # ----------------------------------------------------

        yaw = math.radians(
            -self.rotation.y
        )

        cosine = math.cos(
            yaw
        )

        sine = math.sin(
            yaw
        )

        yaw_x = (
            x
            * cosine
            - z
            * sine
        )

        yaw_z = (
            x
            * sine
            + z
            * cosine
        )

        x = yaw_x
        z = yaw_z

        # ----------------------------------------------------
        # INVERSE PITCH
        # ----------------------------------------------------

        pitch = math.radians(
            -self.rotation.x
        )

        cosine = math.cos(
            pitch
        )

        sine = math.sin(
            pitch
        )

        pitch_y = (
            y
            * cosine
            - z
            * sine
        )

        pitch_z = (
            y
            * sine
            + z
            * cosine
        )

        y = pitch_y
        z = pitch_z

        return Vec3(
            x,
            y,
            z,
        )

    # ========================================================
    # LOOK-AT CAMERA
    # ========================================================

    def _world_to_camera_look_at(
        self,
        point: Vec3,
    ) -> Vec3:

        if (
            self.look_target
            is None
        ):

            return self._world_to_camera_euler(
                point
            )

        forward = (
            self.look_target
            - self.position
        ).normalized()

        up_reference = (
            self.up_reference

            if (
                self.up_reference
                is not None
            )

            else Vec3(
                0.0,
                1.0,
                0.0,
            )
        )

        # If the supplied up vector happens to line up with
        # forward, use a fallback.

        right = (
            forward.cross(
                up_reference
            )
        )

        if (
            right.length()
            < 0.001
        ):

            right = (
                forward.cross(
                    Vec3(
                        1.0,
                        0.0,
                        0.0,
                    )
                )
            )

        right = right.normalized()

        up = (
            right.cross(
                forward
            )
        ).normalized()

        relative = (
            point
            - self.position
        )

        return Vec3(
            relative.dot(
                right
            ),

            relative.dot(
                up
            ),

            relative.dot(
                forward
            ),
        )

    # ========================================================
    # TRANSITION WORLD TO CAMERA
    # ========================================================

    def _world_to_camera_transition(
        self,
        point: Vec3,
    ) -> Vec3:
        """
        Blend the exact inside-camera and outside-camera transforms.

        At environment_blend == 0 this exactly matches
        configure_inside(). At environment_blend == 1 it exactly
        matches configure_outside().
        """

        blend = clamp(
            self.environment_blend,
            0.0,
            1.0,
        )

        camera_z = (
            self._transition_camera_z
        )

        player_angle = (
            self._transition_player_angle
        )

        tunnel_radius = (
            self._transition_tunnel_radius
        )

        # ----------------------------------------------------
        # INSIDE CAMERA SPACE
        # ----------------------------------------------------

        inside_x = (
            point.x
        )

        inside_y = (
            point.y
        )

        inside_z = (
            point.z
            - camera_z
        )

        roll = math.radians(
            -player_angle
        )

        cosine = math.cos(
            roll
        )

        sine = math.sin(
            roll
        )

        inside_camera = Vec3(
            inside_x
            * cosine
            - inside_y
            * sine,

            inside_x
            * sine
            + inside_y
            * cosine,

            inside_z,
        )

        # ----------------------------------------------------
        # OUTSIDE CAMERA SPACE
        # ----------------------------------------------------

        radians = math.radians(
            player_angle
        )

        radial_x = math.cos(
            radians
        )

        radial_y = math.sin(
            radians
        )

        outside_position = Vec3(
            radial_x
            * tunnel_radius
            * 2.55,

            radial_y
            * tunnel_radius
            * 2.55,

            camera_z
            - 7.5,
        )

        outside_target = Vec3(
            radial_x
            * tunnel_radius
            * 0.72,

            radial_y
            * tunnel_radius
            * 0.72,

            camera_z
            + 26.0,
        )

        forward = (
            outside_target
            - outside_position
        ).normalized()

        up_reference = Vec3(
            radial_x,
            radial_y,
            0.0,
        ).normalized()

        right = (
            forward.cross(
                up_reference
            )
        )

        if (
            right.length()
            < 0.001
        ):
            right = (
                forward.cross(
                    Vec3(
                        1.0,
                        0.0,
                        0.0,
                    )
                )
            )

        right = right.normalized()

        up = (
            right.cross(
                forward
            )
        ).normalized()

        relative = (
            point
            - outside_position
        )

        outside_camera = Vec3(
            relative.dot(
                right
            ),
            relative.dot(
                up
            ),
            relative.dot(
                forward
            ),
        )

        # ----------------------------------------------------
        # CONTINUOUS BLEND
        # ----------------------------------------------------

        return Vec3(
            lerp(
                inside_camera.x,
                outside_camera.x,
                blend,
            ),

            lerp(
                inside_camera.y,
                outside_camera.y,
                blend,
            ),

            lerp(
                inside_camera.z,
                outside_camera.z,
                blend,
            ),
        )


    # ========================================================
    # WORLD TO CAMERA
    # ========================================================

    def world_to_camera(
        self,
        point: Vec3,
    ) -> Vec3:

        if (
            self._transition_camera_active
            and self.environment
            == ENVIRONMENT_TRANSITION
        ):

            return (
                self._world_to_camera_transition(
                    point
                )
            )

        if (
            self.look_target
            is not None
        ):

            return (
                self._world_to_camera_look_at(
                    point
                )
            )

        return (
            self._world_to_camera_euler(
                point
            )
        )

    # ========================================================
    # PROJECT
    # ========================================================

    def project(
        self,
        point: Vec3,
    ) -> tuple[
        Vec2 | None,
        float,
    ]:

        camera_point = (
            self.world_to_camera(
                point
            )
        )

        depth = (
            camera_point.z
        )

        if (
            depth
            <= self.near_clip
            or depth
            >= self.far_clip
        ):

            return (
                None,
                depth,
            )

        inverse_depth = (
            self._projection_scale
            / depth
        )

        screen_x = (
            self.width
            / 2.0

            + camera_point.x
            * inverse_depth

            + self.shake_offset.x
        )

        screen_y = (
            self.height
            / 2.0

            - camera_point.y
            * inverse_depth

            + self.shake_offset.y
        )

        return (
            Vec2(
                screen_x,
                screen_y,
            ),

            depth,
        )


# ============================================================
# PROJECTED FACE
# ============================================================

@dataclass
class ProjectedFace:
    points: list[tuple[int, int]]

    colour: tuple[int, int, int]

    outline_colour: tuple[int, int, int] | None

    outline_width: int

    depth: float

    glow: bool = False


# ============================================================
# SCENE RENDERER
# ============================================================

class SceneRenderer3D:

    def __init__(
        self,
        camera: Camera3D,
    ):

        self.camera = camera

        self.meshes: list[
            Mesh3D
        ] = []

        self.fog_colour: tuple[
            int,
            int,
            int,
        ] = (
            0,
            0,
            0,
        )

        self.fog_start = 65.0

        self.fog_end = 330.0

        self.use_lighting = False

        self.use_fog = True

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:

        self.meshes.clear()

    # ========================================================
    # ADD
    # ========================================================

    def add_mesh(
        self,
        mesh: Mesh3D,
    ) -> None:

        self.meshes.append(
            mesh
        )

    def add_meshes(
        self,
        meshes: Iterable[Mesh3D],
    ) -> None:

        self.meshes.extend(
            meshes
        )

    # ========================================================
    # FOG
    # ========================================================

    def _apply_fog(
        self,
        colour: tuple[int, int, int],
        depth: float,
    ) -> tuple[int, int, int]:

        if not self.use_fog:

            return colour

        if (
            depth
            <= self.fog_start
        ):

            return colour

        amount = (
            (
                depth
                - self.fog_start
            )
            / max(
                1.0,
                self.fog_end
                - self.fog_start,
            )
        )

        amount = clamp(
            amount,
            0.0,
            1.0,
        )

        # Smooth fog keeps the far end of the tunnel from looking
        # like a wall of flat polygons.

        amount = smoothstep(
            amount
        )

        return blend_colour(
            colour,
            self.fog_colour,
            amount,
        )

    # ========================================================
    # FACE SHADE
    # ========================================================

    def _depth_shade(
        self,
        colour: tuple[int, int, int],
        depth: float,
    ) -> tuple[int, int, int]:

        # Cheap pseudo-lighting.
        #
        # Nearby geometry is a little brighter.
        # Far geometry gets slightly darker before fog.

        brightness = lerp(
            1.08,
            0.78,
            clamp(
                depth
                / 300.0,
                0.0,
                1.0,
            ),
        )

        return multiply_colour(
            colour,
            brightness,
        )

    # ========================================================
    # PROJECT FACE
    # ========================================================

    def _project_face(
        self,
        face: Face3D,
    ) -> ProjectedFace | None:

        if (
            len(
                face.vertices
            )
            < 3
        ):

            return None

        points: list[
            tuple[int, int]
        ] = []

        depth_total = 0.0

        visible_vertices = 0

        for vertex in face.vertices:

            projected, depth = (
                self.camera.project(
                    vertex
                )
            )

            if projected is None:

                # Faces that cross the near plane are skipped.
                # This is cheaper than polygon clipping and prevents
                # massive screen-filling triangles.

                return None

            points.append(
                projected.int_tuple()
            )

            depth_total += (
                depth
            )

            visible_vertices += 1

        if visible_vertices == 0:

            return None

        depth = (
            depth_total
            / visible_vertices
        )

        colour = (
            face.colour
        )

        colour = (
            self._depth_shade(
                colour,
                depth,
            )
        )

        colour = (
            self._apply_fog(
                colour,
                depth,
            )
        )

        outline_colour = (
            face.outline_colour
        )

        if (
            outline_colour
            is not None
        ):

            outline_colour = (
                self._apply_fog(
                    outline_colour,
                    depth,
                )
            )

        return ProjectedFace(
            points=points,

            colour=colour,

            outline_colour=(
                outline_colour
            ),

            outline_width=(
                face.outline_width
            ),

            depth=depth,

            glow=face.glow,
        )

    # ========================================================
    # DRAW
    # ========================================================

    def draw(
        self,
        surface: pygame.Surface,
    ) -> None:

        projected_faces: list[
            ProjectedFace
        ] = []

        append_face = (
            projected_faces.append
        )

        for mesh in self.meshes:

            for face in mesh.faces:

                projected = (
                    self._project_face(
                        face
                    )
                )

                if (
                    projected
                    is not None
                ):

                    append_face(
                        projected
                    )

        # Painter's algorithm:
        # far geometry first.

        projected_faces.sort(
            key=lambda item:
            item.depth,
            reverse=True,
        )

        draw_polygon = (
            pygame.draw.polygon
        )

        for face in projected_faces:

            # Very distant tiny faces sometimes collapse into
            # duplicate points. pygame handles most cases but this
            # check avoids unnecessary calls.

            if (
                len(
                    set(
                        face.points
                    )
                )
                < 3
            ):

                continue

            draw_polygon(
                surface,
                face.colour,
                face.points,
            )

            if (
                face.outline_colour
                is not None

                and face.outline_width
                > 0
            ):

                draw_polygon(
                    surface,
                    face.outline_colour,
                    face.points,
                    width=(
                        face.outline_width
                    ),
                )


# ============================================================
# ENVIRONMENT HELPERS
# ============================================================

def endless_environment_for_distance(
    distance: float,
) -> str:

    # Exactly what we wanted:
    #
    # 0-999        inside
    # 1000-1999    outside
    # 2000-2999    inside
    # 3000-3999    outside
    # ...

    section = int(
        max(
            0.0,
            distance,
        )
        // 1000.0
    )

    if (
        section
        % 2
        == 0
    ):

        return ENVIRONMENT_INSIDE

    return ENVIRONMENT_OUTSIDE


def endless_transition_information(
    distance: float,
    *,
    transition_length: float = 120.0,
) -> tuple[
    bool,
    float,
    str,
    str,
]:
    """
    Return stable Endless inside/outside transition information.

    Endless changes environment every 1000 metres.

    The old implementation used floor(distance / 1000), which
    selected the previous boundary while approaching a transition.
    That made the transition activate inconsistently and could leave
    the camera visually stuck in transition.

    This version selects the nearest 1000 m boundary and only marks
    the transition active while the player is actually inside that
    boundary's transition window.
    """

    distance = max(
        0.0,
        float(distance),
    )

    transition_length = max(
        1.0,
        float(transition_length),
    )

    # There is no transition before the first 1000 m boundary,
    # except while actually approaching that boundary.
    section_length = 1000.0

    # Find the nearest environment boundary instead of the previous
    # boundary. This makes both the approach and exit sides use the
    # same transition window.
    boundary_index = max(
        1,
        int(
            round(
                distance
                / section_length
            )
        ),
    )

    boundary = (
        boundary_index
        * section_length
    )

    half_transition = (
        transition_length
        / 2.0
    )

    transition_start = (
        boundary
        - half_transition
    )

    transition_end = (
        boundary
        + half_transition
    )

    if not (
        transition_start
        <= distance
        <= transition_end
    ):
        current = (
            endless_environment_for_distance(
                distance
            )
        )

        return (
            False,
            0.0,
            current,
            current,
        )

    # The section before boundary N is section N - 1.
    before_section = max(
        0,
        boundary_index - 1,
    )

    before = (
        ENVIRONMENT_INSIDE
        if (
            before_section
            % 2
            == 0
        )
        else ENVIRONMENT_OUTSIDE
    )

    after = (
        ENVIRONMENT_OUTSIDE
        if before
        == ENVIRONMENT_INSIDE
        else ENVIRONMENT_INSIDE
    )

    progress = (
        (
            distance
            - transition_start
        )
        / transition_length
    )

    # Clamp hard at the endpoints so camera state reaches exactly
    # 0.0 and 1.0 instead of hovering just short due to floating
    # point movement.
    progress = clamp(
        progress,
        0.0,
        1.0,
    )

    if progress <= 0.000001:
        progress = 0.0

    elif progress >= 0.999999:
        progress = 1.0

    return (
        True,
        progress,
        before,
        after,
    )


# ============================================================
# CAMPAIGN ENVIRONMENT
# ============================================================

def campaign_environment_for_level(
    level_number: int,
) -> str:

    # Early levels stay inside while the player learns.
    #
    # Then outside-cylinder levels are introduced increasingly
    # often through the 50-level campaign.

    outside_levels = {
        6,
        9,
        12,
        14,
        17,
        19,
        22,
        24,
        27,
        29,
        31,
        33,
        35,
        37,
        39,
        41,
        43,
        45,
        47,
        49,
    }

    if (
        int(
            level_number
        )
        in outside_levels
    ):

        return ENVIRONMENT_OUTSIDE

    return ENVIRONMENT_INSIDE


# ============================================================
# CAMPAIGN MID-LEVEL SWITCH
# ============================================================

def campaign_supports_environment_switch(
    level_number: int,
) -> bool:

    # Harder levels can actually switch environment during
    # the level rather than staying in one view.

    return (
        level_number
        in {
            20,
            25,
            30,
            34,
            38,
            40,
            42,
            44,
            46,
            48,
            50,
        }
    )


def campaign_environment_at_progress(
    level_number: int,
    progress: float,
) -> str:

    starting_environment = (
        campaign_environment_for_level(
            level_number
        )
    )

    if not campaign_supports_environment_switch(
        level_number
    ):

        return (
            starting_environment
        )

    progress = clamp(
        progress,
        0.0,
        1.0,
    )

    # Later challenge levels alternate more than once.

    if (
        level_number
        >= 40
    ):

        section = int(
            progress
            * 4.0
        )

    elif (
        level_number
        >= 30
    ):

        section = int(
            progress
            * 3.0
        )

    else:

        section = int(
            progress
            * 2.0
        )

    if (
        section
        % 2
        == 0
    ):

        return (
            starting_environment
        )

    return (
        ENVIRONMENT_OUTSIDE

        if starting_environment
        == ENVIRONMENT_INSIDE

        else ENVIRONMENT_INSIDE
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_geometry_system(
) -> None:

    inside_mesh = (
        create_tunnel_section_mesh(
            0.0,
            10.0,

            radius=10.0,

            segments=10,

            primary_colour=(
                40,
                100,
                255,
            ),

            secondary_colour=(
                10,
                40,
                100,
            ),

            line_colour=(
                255,
                255,
                255,
            ),
        )
    )

    if (
        len(
            inside_mesh.faces
        )
        != 10
    ):

        raise ValueError(
            "Inside tunnel mesh validation failed."
        )

    outside_mesh = (
        create_outside_tunnel_section_mesh(
            0.0,
            10.0,

            radius=10.0,

            segments=10,

            primary_colour=(
                255,
                60,
                140,
            ),

            secondary_colour=(
                80,
                20,
                120,
            ),
        )
    )

    # The detailed outside renderer intentionally contains more
    # geometry than the old flat 10-panel cylinder. It now includes
    # the 10 base panels plus raised ribs and edge-ring faces.
    #
    # Validate the minimum base geometry instead of requiring the
    # obsolete exact face count.
    if (
        len(
            outside_mesh.faces
        )
        < 10
    ):

        raise ValueError(
            "Outside tunnel mesh validation failed."
        )

    if (
        outside_mesh.metadata.get(
            "environment"
        )
        != ENVIRONMENT_OUTSIDE
    ):

        raise ValueError(
            "Outside tunnel environment metadata validation failed."
        )

    if (
        endless_environment_for_distance(
            500.0
        )
        != ENVIRONMENT_INSIDE
    ):

        raise ValueError(
            "Endless inside environment validation failed."
        )

    if (
        endless_environment_for_distance(
            1500.0
        )
        != ENVIRONMENT_OUTSIDE
    ):

        raise ValueError(
            "Endless outside environment validation failed."
        )

    if (
        endless_environment_for_distance(
            2500.0
        )
        != ENVIRONMENT_INSIDE
    ):

        raise ValueError(
            "Endless alternating environment validation failed."
        )


validate_geometry_system()