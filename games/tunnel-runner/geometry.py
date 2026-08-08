from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable

import pygame

from config import (
    BLACK,
    CAMERA_FAR_CLIP,
    CAMERA_FOV_DEGREES,
    CAMERA_NEAR_CLIP,
    CYAN,
    ENABLE_DEPTH_FOG,
    GAME_CENTER_X,
    GAME_CENTER_Y,
    GAME_HEIGHT,
    GAME_WIDTH,
    LIGHT_BLUE,
    TUNNEL_RADIUS,
    TUNNEL_SEGMENTS,
    TUNNEL_VISIBLE_LENGTH,
    WHITE,
    clamp,
)


# ============================================================
# TUNNEL RUNNER
# GEOMETRY / 3D ENGINE
# ============================================================
#
# This file is the mathematical foundation of Tunnel Runner.
#
# It contains:
#
# - 2D vectors
# - 3D vectors
# - 3D rotation
# - Camera transformation
# - Perspective projection
# - Near-plane clipping
# - Polygon clipping
# - 3D faces
# - 3D meshes
# - Depth sorting
# - Tunnel-ring generation
# - Tunnel-wall generation
# - Arc generation
# - Circular/angular helpers
# - Lighting helpers
# - Fog helpers
# - Safe Pygame polygon rendering
#
# IMPORTANT:
#
# No gameplay logic should be placed here.
#
# obstacles.py will use these tools to build actual 3D barriers.
#
# levels.py will decide where those barriers appear.
#
# main.py will control the camera and game loop.
#
# ============================================================


# ============================================================
# BASIC HELPERS
# ============================================================

EPSILON = 0.000001


def lerp(
    first: float,
    second: float,
    amount: float,
) -> float:
    return (
        first
        + (
            second
            - first
        )
        * amount
    )


def inverse_lerp(
    first: float,
    second: float,
    value: float,
) -> float:
    difference = (
        second
        - first
    )

    if abs(
        difference
    ) <= EPSILON:
        return 0.0

    return (
        value
        - first
    ) / difference


def smoothstep(
    amount: float,
) -> float:
    amount = clamp(
        amount,
        0.0,
        1.0,
    )

    return (
        amount
        * amount
        * (
            3.0
            - 2.0
            * amount
        )
    )


def colour_lerp(
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


def multiply_colour(
    colour: tuple[int, int, int],
    multiplier: float,
) -> tuple[int, int, int]:
    return (
        int(
            clamp(
                colour[0]
                * multiplier,
                0,
                255,
            )
        ),
        int(
            clamp(
                colour[1]
                * multiplier,
                0,
                255,
            )
        ),
        int(
            clamp(
                colour[2]
                * multiplier,
                0,
                255,
            )
        ),
    )


def add_colour(
    colour: tuple[int, int, int],
    amount: int,
) -> tuple[int, int, int]:
    return (
        int(
            clamp(
                colour[0]
                + amount,
                0,
                255,
            )
        ),
        int(
            clamp(
                colour[1]
                + amount,
                0,
                255,
            )
        ),
        int(
            clamp(
                colour[2]
                + amount,
                0,
                255,
            )
        ),
    )


# ============================================================
# ANGLE HELPERS
# ============================================================

def normalize_degrees(
    angle: float,
) -> float:
    return (
        float(
            angle
        )
        % 360.0
    )


def degrees_to_radians(
    degrees: float,
) -> float:
    return math.radians(
        degrees
    )


def radians_to_degrees(
    radians: float,
) -> float:
    return math.degrees(
        radians
    )


def shortest_angle_difference(
    first: float,
    second: float,
) -> float:
    return (
        (
            second
            - first
            + 180.0
        )
        % 360.0
        - 180.0
    )


def angular_distance(
    first: float,
    second: float,
) -> float:
    return abs(
        shortest_angle_difference(
            first,
            second,
        )
    )


def angle_in_arc(
    angle: float,
    arc_center: float,
    arc_width: float,
) -> bool:
    return (
        angular_distance(
            angle,
            arc_center,
        )
        <= arc_width
        / 2.0
    )


# ============================================================
# VECTOR 2
# ============================================================

@dataclass
class Vec2:
    x: float = 0.0
    y: float = 0.0

    def copy(
        self,
    ) -> "Vec2":
        return Vec2(
            self.x,
            self.y,
        )

    def __add__(
        self,
        other: "Vec2",
    ) -> "Vec2":
        return Vec2(
            self.x
            + other.x,

            self.y
            + other.y,
        )

    def __sub__(
        self,
        other: "Vec2",
    ) -> "Vec2":
        return Vec2(
            self.x
            - other.x,

            self.y
            - other.y,
        )

    def __mul__(
        self,
        scalar: float,
    ) -> "Vec2":
        return Vec2(
            self.x
            * scalar,

            self.y
            * scalar,
        )

    def __rmul__(
        self,
        scalar: float,
    ) -> "Vec2":
        return self.__mul__(
            scalar
        )

    def __truediv__(
        self,
        scalar: float,
    ) -> "Vec2":
        if abs(
            scalar
        ) <= EPSILON:
            return Vec2()

        return Vec2(
            self.x
            / scalar,

            self.y
            / scalar,
        )

    def length_squared(
        self,
    ) -> float:
        return (
            self.x
            * self.x
            + self.y
            * self.y
        )

    def length(
        self,
    ) -> float:
        return math.sqrt(
            self.length_squared()
        )

    def normalized(
        self,
    ) -> "Vec2":
        magnitude = (
            self.length()
        )

        if magnitude <= EPSILON:
            return Vec2()

        return self / magnitude

    def tuple(
        self,
    ) -> tuple[float, float]:
        return (
            self.x,
            self.y,
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
# VECTOR 3
# ============================================================

@dataclass
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def copy(
        self,
    ) -> "Vec3":
        return Vec3(
            self.x,
            self.y,
            self.z,
        )

    def __add__(
        self,
        other: "Vec3",
    ) -> "Vec3":
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
        other: "Vec3",
    ) -> "Vec3":
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
        scalar: float,
    ) -> "Vec3":
        return Vec3(
            self.x
            * scalar,

            self.y
            * scalar,

            self.z
            * scalar,
        )

    def __rmul__(
        self,
        scalar: float,
    ) -> "Vec3":
        return self.__mul__(
            scalar
        )

    def __truediv__(
        self,
        scalar: float,
    ) -> "Vec3":
        if abs(
            scalar
        ) <= EPSILON:
            return Vec3()

        return Vec3(
            self.x
            / scalar,

            self.y
            / scalar,

            self.z
            / scalar,
        )

    def length_squared(
        self,
    ) -> float:
        return (
            self.x
            * self.x
            + self.y
            * self.y
            + self.z
            * self.z
        )

    def length(
        self,
    ) -> float:
        return math.sqrt(
            self.length_squared()
        )

    def normalized(
        self,
    ) -> "Vec3":
        magnitude = (
            self.length()
        )

        if magnitude <= EPSILON:
            return Vec3()

        return self / magnitude

    def dot(
        self,
        other: "Vec3",
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
        other: "Vec3",
    ) -> "Vec3":
        return Vec3(
            (
                self.y
                * other.z
                - self.z
                * other.y
            ),

            (
                self.z
                * other.x
                - self.x
                * other.z
            ),

            (
                self.x
                * other.y
                - self.y
                * other.x
            ),
        )

    def distance_to(
        self,
        other: "Vec3",
    ) -> float:
        return (
            self
            - other
        ).length()

    def tuple(
        self,
    ) -> tuple[
        float,
        float,
        float,
    ]:
        return (
            self.x,
            self.y,
            self.z,
        )


# ============================================================
# ROTATION
# ============================================================

def rotate_x(
    point: Vec3,
    degrees: float,
) -> Vec3:
    radians = math.radians(
        degrees
    )

    cosine = math.cos(
        radians
    )

    sine = math.sin(
        radians
    )

    return Vec3(
        point.x,

        point.y
        * cosine
        - point.z
        * sine,

        point.y
        * sine
        + point.z
        * cosine,
    )


def rotate_y(
    point: Vec3,
    degrees: float,
) -> Vec3:
    radians = math.radians(
        degrees
    )

    cosine = math.cos(
        radians
    )

    sine = math.sin(
        radians
    )

    return Vec3(
        point.x
        * cosine
        + point.z
        * sine,

        point.y,

        -point.x
        * sine
        + point.z
        * cosine,
    )


def rotate_z(
    point: Vec3,
    degrees: float,
) -> Vec3:
    radians = math.radians(
        degrees
    )

    cosine = math.cos(
        radians
    )

    sine = math.sin(
        radians
    )

    return Vec3(
        point.x
        * cosine
        - point.y
        * sine,

        point.x
        * sine
        + point.y
        * cosine,

        point.z,
    )


def rotate_xyz(
    point: Vec3,
    rotation: Vec3,
) -> Vec3:
    result = rotate_x(
        point,
        rotation.x,
    )

    result = rotate_y(
        result,
        rotation.y,
    )

    result = rotate_z(
        result,
        rotation.z,
    )

    return result


def inverse_rotate_xyz(
    point: Vec3,
    rotation: Vec3,
) -> Vec3:
    result = rotate_z(
        point,
        -rotation.z,
    )

    result = rotate_y(
        result,
        -rotation.y,
    )

    result = rotate_x(
        result,
        -rotation.x,
    )

    return result


# ============================================================
# TRANSFORM
# ============================================================

@dataclass
class Transform3D:
    position: Vec3 = field(
        default_factory=Vec3
    )

    rotation: Vec3 = field(
        default_factory=Vec3
    )

    scale: Vec3 = field(
        default_factory=lambda: Vec3(
            1.0,
            1.0,
            1.0,
        )
    )

    def transform_point(
        self,
        point: Vec3,
    ) -> Vec3:
        scaled = Vec3(
            point.x
            * self.scale.x,

            point.y
            * self.scale.y,

            point.z
            * self.scale.z,
        )

        rotated = rotate_xyz(
            scaled,
            self.rotation,
        )

        return (
            rotated
            + self.position
        )


# ============================================================
# CAMERA
# ============================================================

class Camera3D:
    """
    Perspective camera used by Tunnel Runner.

    The camera moves forward through world space.

    Player movement around the tunnel is represented by camera roll.

    This keeps the gameplay first-person:
    the player remains visually centered while the tunnel rotates.
    """

    def __init__(
        self,
        *,
        width: int = GAME_WIDTH,
        height: int = GAME_HEIGHT,
        fov_degrees: float = CAMERA_FOV_DEGREES,
        near_clip: float = CAMERA_NEAR_CLIP,
        far_clip: float = CAMERA_FAR_CLIP,
    ):
        self.width = int(
            width
        )

        self.height = int(
            height
        )

        self.center_x = (
            self.width
            / 2.0
        )

        self.center_y = (
            self.height
            / 2.0
        )

        self.fov_degrees = float(
            fov_degrees
        )

        self.near_clip = float(
            near_clip
        )

        self.far_clip = float(
            far_clip
        )

        self.position = Vec3()

        self.rotation = Vec3()

        self.shake_offset = Vec2()

        self._recalculate_projection()

    # ========================================================
    # PROJECTION SETTINGS
    # ========================================================

    def _recalculate_projection(
        self,
    ) -> None:
        half_fov_radians = math.radians(
            self.fov_degrees
            / 2.0
        )

        tangent = math.tan(
            half_fov_radians
        )

        if abs(
            tangent
        ) <= EPSILON:
            tangent = 1.0

        self.focal_length = (
            self.width
            / 2.0
        ) / tangent

    def resize(
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

        self.center_x = (
            self.width
            / 2.0
        )

        self.center_y = (
            self.height
            / 2.0
        )

        self._recalculate_projection()

    # ========================================================
    # WORLD TO CAMERA
    # ========================================================

    def world_to_camera(
        self,
        world_point: Vec3,
    ) -> Vec3:
        relative = (
            world_point
            - self.position
        )

        return inverse_rotate_xyz(
            relative,
            self.rotation,
        )

    # ========================================================
    # CAMERA TO SCREEN
    # ========================================================

    def camera_to_screen(
        self,
        camera_point: Vec3,
    ) -> Vec2 | None:
        if (
            camera_point.z
            <= self.near_clip
        ):
            return None

        scale = (
            self.focal_length
            / camera_point.z
        )

        screen_x = (
            self.center_x
            + camera_point.x
            * scale
            + self.shake_offset.x
        )

        screen_y = (
            self.center_y
            - camera_point.y
            * scale
            + self.shake_offset.y
        )

        return Vec2(
            screen_x,
            screen_y,
        )

    # ========================================================
    # WORLD TO SCREEN
    # ========================================================

    def project(
        self,
        world_point: Vec3,
    ) -> Vec2 | None:
        camera_point = (
            self.world_to_camera(
                world_point
            )
        )

        return (
            self.camera_to_screen(
                camera_point
            )
        )

    # ========================================================
    # VISIBILITY
    # ========================================================

    def depth_visible(
        self,
        camera_z: float,
    ) -> bool:
        return (
            self.near_clip
            < camera_z
            < self.far_clip
        )

    def world_point_visible(
        self,
        world_point: Vec3,
    ) -> bool:
        camera_point = (
            self.world_to_camera(
                world_point
            )
        )

        return (
            self.depth_visible(
                camera_point.z
            )
        )


# ============================================================
# NEAR-PLANE CLIPPING
# ============================================================

def interpolate_vec3(
    first: Vec3,
    second: Vec3,
    amount: float,
) -> Vec3:
    return Vec3(
        lerp(
            first.x,
            second.x,
            amount,
        ),

        lerp(
            first.y,
            second.y,
            amount,
        ),

        lerp(
            first.z,
            second.z,
            amount,
        ),
    )


def clip_line_to_near_plane(
    first: Vec3,
    second: Vec3,
    near_clip: float,
) -> tuple[
    Vec3,
    Vec3,
] | None:
    first_inside = (
        first.z
        >= near_clip
    )

    second_inside = (
        second.z
        >= near_clip
    )

    if (
        first_inside
        and second_inside
    ):
        return (
            first,
            second,
        )

    if (
        not first_inside
        and not second_inside
    ):
        return None

    denominator = (
        second.z
        - first.z
    )

    if abs(
        denominator
    ) <= EPSILON:
        return None

    amount = (
        near_clip
        - first.z
    ) / denominator

    intersection = (
        interpolate_vec3(
            first,
            second,
            amount,
        )
    )

    intersection.z = (
        near_clip
    )

    if first_inside:
        return (
            first,
            intersection,
        )

    return (
        intersection,
        second,
    )


def clip_polygon_to_near_plane(
    vertices: list[Vec3],
    near_clip: float,
) -> list[Vec3]:
    """
    Sutherland-Hodgman clipping against Z >= near_clip.
    """

    if len(
        vertices
    ) < 3:
        return []

    output: list[
        Vec3
    ] = []

    previous = (
        vertices[-1]
    )

    previous_inside = (
        previous.z
        >= near_clip
    )

    for current in vertices:
        current_inside = (
            current.z
            >= near_clip
        )

        if current_inside:
            if not previous_inside:
                denominator = (
                    current.z
                    - previous.z
                )

                if abs(
                    denominator
                ) > EPSILON:
                    amount = (
                        near_clip
                        - previous.z
                    ) / denominator

                    output.append(
                        interpolate_vec3(
                            previous,
                            current,
                            amount,
                        )
                    )

                    output[-1].z = (
                        near_clip
                    )

            output.append(
                current
            )

        elif previous_inside:
            denominator = (
                current.z
                - previous.z
            )

            if abs(
                denominator
            ) > EPSILON:
                amount = (
                    near_clip
                    - previous.z
                ) / denominator

                output.append(
                    interpolate_vec3(
                        previous,
                        current,
                        amount,
                    )
                )

                output[-1].z = (
                    near_clip
                )

        previous = current

        previous_inside = (
            current_inside
        )

    return output


# ============================================================
# FACE
# ============================================================

@dataclass
class Face3D:
    vertices: list[Vec3]

    colour: tuple[int, int, int]

    outline_colour: (
        tuple[int, int, int]
        | None
    ) = None

    outline_width: int = 0

    double_sided: bool = True

    glow: bool = False

    metadata: dict[
        str,
        object,
    ] = field(
        default_factory=dict
    )

    def copy(
        self,
    ) -> "Face3D":
        return Face3D(
            vertices=[
                vertex.copy()
                for vertex in self.vertices
            ],

            colour=self.colour,

            outline_colour=(
                self.outline_colour
            ),

            outline_width=(
                self.outline_width
            ),

            double_sided=(
                self.double_sided
            ),

            glow=(
                self.glow
            ),

            metadata=dict(
                self.metadata
            ),
        )

    # ========================================================
    # CENTRE
    # ========================================================

    def center(
        self,
    ) -> Vec3:
        if not self.vertices:
            return Vec3()

        x = sum(
            vertex.x
            for vertex in self.vertices
        )

        y = sum(
            vertex.y
            for vertex in self.vertices
        )

        z = sum(
            vertex.z
            for vertex in self.vertices
        )

        count = len(
            self.vertices
        )

        return Vec3(
            x / count,
            y / count,
            z / count,
        )

    # ========================================================
    # NORMAL
    # ========================================================

    def normal(
        self,
    ) -> Vec3:
        if len(
            self.vertices
        ) < 3:
            return Vec3()

        edge_one = (
            self.vertices[1]
            - self.vertices[0]
        )

        edge_two = (
            self.vertices[2]
            - self.vertices[0]
        )

        return (
            edge_one.cross(
                edge_two
            ).normalized()
        )


# ============================================================
# MESH
# ============================================================

@dataclass
class Mesh3D:
    faces: list[
        Face3D
    ] = field(
        default_factory=list
    )

    transform: Transform3D = field(
        default_factory=Transform3D
    )

    visible: bool = True

    metadata: dict[
        str,
        object,
    ] = field(
        default_factory=dict
    )

    def transformed_faces(
        self,
    ) -> list[
        Face3D
    ]:
        if not self.visible:
            return []

        transformed: list[
            Face3D
        ] = []

        for face in self.faces:
            transformed.append(
                Face3D(
                    vertices=[
                        self.transform
                        .transform_point(
                            vertex
                        )
                        for vertex
                        in face.vertices
                    ],

                    colour=face.colour,

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

        return transformed


# ============================================================
# RENDERABLE FACE
# ============================================================

@dataclass
class RenderFace:
    points: list[
        tuple[int, int]
    ]

    depth: float

    colour: tuple[
        int,
        int,
        int,
    ]

    outline_colour: (
        tuple[int, int, int]
        | None
    ) = None

    outline_width: int = 0

    glow: bool = False

    metadata: dict[
        str,
        object,
    ] = field(
        default_factory=dict
    )


# ============================================================
# BACKFACE CHECK
# ============================================================

def face_facing_camera(
    camera_vertices: list[
        Vec3
    ],
) -> bool:
    if len(
        camera_vertices
    ) < 3:
        return False

    edge_one = (
        camera_vertices[1]
        - camera_vertices[0]
    )

    edge_two = (
        camera_vertices[2]
        - camera_vertices[0]
    )

    normal = edge_one.cross(
        edge_two
    )

    center = Vec3(
        sum(
            vertex.x
            for vertex
            in camera_vertices
        )
        / len(
            camera_vertices
        ),

        sum(
            vertex.y
            for vertex
            in camera_vertices
        )
        / len(
            camera_vertices
        ),

        sum(
            vertex.z
            for vertex
            in camera_vertices
        )
        / len(
            camera_vertices
        ),
    )

    camera_direction = Vec3(
        -center.x,
        -center.y,
        -center.z,
    )

    return (
        normal.dot(
            camera_direction
        )
        > 0.0
    )


# ============================================================
# FOG
# ============================================================

def fog_amount_for_depth(
    depth: float,
    *,
    start_distance: float = (
        TUNNEL_VISIBLE_LENGTH
        * 0.55
    ),
    end_distance: float = (
        TUNNEL_VISIBLE_LENGTH
    ),
) -> float:
    if not ENABLE_DEPTH_FOG:
        return 0.0

    return clamp(
        inverse_lerp(
            start_distance,
            end_distance,
            depth,
        ),
        0.0,
        1.0,
    )


def apply_depth_fog(
    colour: tuple[int, int, int],
    depth: float,
    fog_colour: tuple[int, int, int],
) -> tuple[int, int, int]:
    amount = (
        fog_amount_for_depth(
            depth
        )
    )

    return colour_lerp(
        colour,
        fog_colour,
        amount,
    )


# ============================================================
# SIMPLE LIGHTING
# ============================================================

def directional_light(
    normal: Vec3,
    light_direction: Vec3,
    *,
    ambient: float = 0.45,
    strength: float = 0.55,
) -> float:
    normal = (
        normal.normalized()
    )

    light_direction = (
        light_direction
        .normalized()
    )

    amount = max(
        0.0,
        normal.dot(
            light_direction
        ),
    )

    return clamp(
        ambient
        + amount
        * strength,
        0.0,
        1.5,
    )


# ============================================================
# FACE PROJECTION
# ============================================================

def project_face(
    face: Face3D,
    camera: Camera3D,
    *,
    fog_colour: tuple[int, int, int] = BLACK,
    use_lighting: bool = False,
    light_direction: Vec3 = Vec3(
        0.2,
        -0.4,
        -1.0,
    ),
) -> RenderFace | None:
    if len(
        face.vertices
    ) < 3:
        return None

    camera_vertices = [
        camera.world_to_camera(
            vertex
        )
        for vertex
        in face.vertices
    ]

    clipped = (
        clip_polygon_to_near_plane(
            camera_vertices,
            camera.near_clip,
        )
    )

    if len(
        clipped
    ) < 3:
        return None

    if (
        not face.double_sided
        and not face_facing_camera(
            clipped
        )
    ):
        return None

    depth = sum(
        vertex.z
        for vertex
        in clipped
    ) / len(
        clipped
    )

    if depth > camera.far_clip:
        return None

    screen_points: list[
        tuple[int, int]
    ] = []

    for vertex in clipped:
        projected = (
            camera.camera_to_screen(
                vertex
            )
        )

        if projected is None:
            return None

        screen_points.append(
            projected.int_tuple()
        )

    colour = (
        face.colour
    )

    if use_lighting:
        if len(
            clipped
        ) >= 3:
            edge_one = (
                clipped[1]
                - clipped[0]
            )

            edge_two = (
                clipped[2]
                - clipped[0]
            )

            normal = (
                edge_one.cross(
                    edge_two
                )
                .normalized()
            )

            lighting = (
                directional_light(
                    normal,
                    light_direction,
                )
            )

            colour = (
                multiply_colour(
                    colour,
                    lighting,
                )
            )

    colour = apply_depth_fog(
        colour,
        depth,
        fog_colour,
    )

    outline_colour = (
        face.outline_colour
    )

    if outline_colour is not None:
        outline_colour = (
            apply_depth_fog(
                outline_colour,
                depth,
                fog_colour,
            )
        )

    return RenderFace(
        points=screen_points,

        depth=depth,

        colour=colour,

        outline_colour=(
            outline_colour
        ),

        outline_width=(
            face.outline_width
        ),

        glow=face.glow,

        metadata=dict(
            face.metadata
        ),
    )


# ============================================================
# MESH PROJECTION
# ============================================================

def project_mesh(
    mesh: Mesh3D,
    camera: Camera3D,
    *,
    fog_colour: tuple[int, int, int] = BLACK,
    use_lighting: bool = False,
) -> list[
    RenderFace
]:
    faces: list[
        RenderFace
    ] = []

    for face in (
        mesh.transformed_faces()
    ):
        projected = (
            project_face(
                face,
                camera,
                fog_colour=fog_colour,
                use_lighting=(
                    use_lighting
                ),
            )
        )

        if projected is not None:
            faces.append(
                projected
            )

    return faces


# ============================================================
# DEPTH SORTING
# ============================================================

def sort_render_faces(
    faces: Iterable[
        RenderFace
    ],
) -> list[
    RenderFace
]:
    return sorted(
        faces,
        key=lambda face: (
            face.depth
        ),
        reverse=True,
    )


# ============================================================
# SAFE POLYGON DRAWING
# ============================================================

def polygon_is_reasonable(
    points: list[
        tuple[int, int]
    ],
) -> bool:
    if len(
        points
    ) < 3:
        return False

    minimum_x = min(
        point[0]
        for point in points
    )

    maximum_x = max(
        point[0]
        for point in points
    )

    minimum_y = min(
        point[1]
        for point in points
    )

    maximum_y = max(
        point[1]
        for point in points
    )

    width = (
        maximum_x
        - minimum_x
    )

    height = (
        maximum_y
        - minimum_y
    )

    if (
        width <= 0
        or height <= 0
    ):
        return False

    # Reject extreme clipping explosions.
    maximum_allowed = (
        max(
            GAME_WIDTH,
            GAME_HEIGHT,
        )
        * 12
    )

    return (
        width
        <= maximum_allowed
        and height
        <= maximum_allowed
    )


def draw_render_face(
    surface: pygame.Surface,
    render_face: RenderFace,
) -> None:
    if not polygon_is_reasonable(
        render_face.points
    ):
        return

    if render_face.glow:
        glow_surface = (
            pygame.Surface(
                (
                    GAME_WIDTH,
                    GAME_HEIGHT,
                ),
                pygame.SRCALPHA,
            )
        )

        glow_colour = (
            render_face.colour[0],
            render_face.colour[1],
            render_face.colour[2],
            55,
        )

        pygame.draw.polygon(
            glow_surface,
            glow_colour,
            render_face.points,
        )

        surface.blit(
            glow_surface,
            (
                0,
                0,
            ),
        )

    pygame.draw.polygon(
        surface,
        render_face.colour,
        render_face.points,
    )

    if (
        render_face.outline_colour
        is not None
        and render_face.outline_width
        > 0
    ):
        pygame.draw.lines(
            surface,
            render_face.outline_colour,
            True,
            render_face.points,
            render_face.outline_width,
        )


def draw_render_faces(
    surface: pygame.Surface,
    faces: Iterable[
        RenderFace
    ],
) -> None:
    for face in (
        sort_render_faces(
            faces
        )
    ):
        draw_render_face(
            surface,
            face,
        )


# ============================================================
# CYLINDER / TUNNEL HELPERS
# ============================================================

def tunnel_point(
    angle_degrees: float,
    z: float,
    *,
    radius: float = TUNNEL_RADIUS,
    center_x: float = 0.0,
    center_y: float = 0.0,
) -> Vec3:
    """
    Return one point on the inside circumference of the tunnel.

    Tunnel angle convention:

        0°   = bottom
        90°  = right
        180° = top
        270° = left

    This matches player movement around the tunnel.
    """

    radians = math.radians(
        angle_degrees
    )

    return Vec3(
        center_x
        + math.sin(
            radians
        )
        * radius,

        center_y
        - math.cos(
            radians
        )
        * radius,

        z,
    )


def tunnel_direction(
    angle_degrees: float,
) -> Vec3:
    radians = math.radians(
        angle_degrees
    )

    return Vec3(
        math.sin(
            radians
        ),

        -math.cos(
            radians
        ),

        0.0,
    )


def tunnel_tangent(
    angle_degrees: float,
) -> Vec3:
    radians = math.radians(
        angle_degrees
    )

    return Vec3(
        math.cos(
            radians
        ),

        math.sin(
            radians
        ),

        0.0,
    )


# ============================================================
# TUNNEL RING
# ============================================================

def create_tunnel_ring_points(
    z: float,
    *,
    radius: float = TUNNEL_RADIUS,
    segments: int = TUNNEL_SEGMENTS,
    rotation_degrees: float = 0.0,
    center_x: float = 0.0,
    center_y: float = 0.0,
) -> list[
    Vec3
]:
    points: list[
        Vec3
    ] = []

    segments = max(
        3,
        int(
            segments
        ),
    )

    for index in range(
        segments
    ):
        angle = (
            rotation_degrees
            + index
            / segments
            * 360.0
        )

        points.append(
            tunnel_point(
                angle,
                z,
                radius=radius,
                center_x=center_x,
                center_y=center_y,
            )
        )

    return points


# ============================================================
# TUNNEL WALL SECTION
# ============================================================

def create_tunnel_section_mesh(
    start_z: float,
    end_z: float,
    *,
    radius: float = TUNNEL_RADIUS,
    segments: int = TUNNEL_SEGMENTS,
    start_rotation: float = 0.0,
    end_rotation: float = 0.0,
    start_center: Vec2 | None = None,
    end_center: Vec2 | None = None,
    primary_colour: tuple[
        int,
        int,
        int,
    ] = (
        18,
        45,
        90,
    ),
    secondary_colour: tuple[
        int,
        int,
        int,
    ] = (
        28,
        72,
        140,
    ),
    line_colour: tuple[
        int,
        int,
        int,
    ] = LIGHT_BLUE,
    draw_outlines: bool = True,
) -> Mesh3D:
    """
    Create one complete cylindrical tunnel section.

    This is true 3D geometry: each wall panel is a quad connecting
    two rings in world space.
    """

    if start_center is None:
        start_center = Vec2()

    if end_center is None:
        end_center = Vec2()

    segments = max(
        3,
        int(
            segments
        ),
    )

    start_ring = (
        create_tunnel_ring_points(
            start_z,

            radius=radius,

            segments=segments,

            rotation_degrees=(
                start_rotation
            ),

            center_x=(
                start_center.x
            ),

            center_y=(
                start_center.y
            ),
        )
    )

    end_ring = (
        create_tunnel_ring_points(
            end_z,

            radius=radius,

            segments=segments,

            rotation_degrees=(
                end_rotation
            ),

            center_x=(
                end_center.x
            ),

            center_y=(
                end_center.y
            ),
        )
    )

    faces: list[
        Face3D
    ] = []

    for index in range(
        segments
    ):
        next_index = (
            index + 1
        ) % segments

        amount = (
            index
            / max(
                1,
                segments - 1,
            )
        )

        colour = (
            primary_colour
            if index % 2 == 0
            else secondary_colour
        )

        # Add slight cylindrical lighting variation.
        angle = (
            amount
            * 360.0
        )

        light_multiplier = (
            0.78
            + 0.22
            * (
                (
                    math.cos(
                        math.radians(
                            angle
                            - 180.0
                        )
                    )
                    + 1.0
                )
                / 2.0
            )
        )

        colour = (
            multiply_colour(
                colour,
                light_multiplier,
            )
        )

        faces.append(
            Face3D(
                vertices=[
                    start_ring[
                        index
                    ],

                    start_ring[
                        next_index
                    ],

                    end_ring[
                        next_index
                    ],

                    end_ring[
                        index
                    ],
                ],

                colour=colour,

                outline_colour=(
                    line_colour
                    if draw_outlines
                    and index % 4 == 0
                    else None
                ),

                outline_width=(
                    1
                    if draw_outlines
                    and index % 4 == 0
                    else 0
                ),

                double_sided=True,

                metadata={
                    "type": (
                        "tunnel_wall"
                    ),

                    "segment": (
                        index
                    ),
                },
            )
        )

    return Mesh3D(
        faces=faces,

        metadata={
            "type": (
                "tunnel_section"
            ),

            "start_z": (
                start_z
            ),

            "end_z": (
                end_z
            ),
        },
    )


# ============================================================
# TUNNEL ARC
# ============================================================

def create_tunnel_arc_points(
    *,
    z: float,
    center_angle: float,
    width_degrees: float,
    radius: float = TUNNEL_RADIUS,
    samples: int = 12,
) -> list[
    Vec3
]:
    width_degrees = clamp(
        width_degrees,
        0.0,
        360.0,
    )

    start_angle = (
        center_angle
        - width_degrees
        / 2.0
    )

    end_angle = (
        center_angle
        + width_degrees
        / 2.0
    )

    points: list[
        Vec3
    ] = []

    for index in range(
        max(
            1,
            samples,
        )
        + 1
    ):
        amount = (
            index
            / max(
                1,
                samples,
            )
        )

        angle = lerp(
            start_angle,
            end_angle,
            amount,
        )

        points.append(
            tunnel_point(
                angle,
                z,
                radius=radius,
            )
        )

    return points


# ============================================================
# RADIAL WALL QUAD
# ============================================================

def create_radial_wall_quad(
    *,
    angle_start: float,
    angle_end: float,
    z: float,
    inner_radius: float,
    outer_radius: float,
    colour: tuple[int, int, int],
    outline_colour: (
        tuple[int, int, int]
        | None
    ) = None,
    outline_width: int = 0,
    glow: bool = False,
) -> Face3D:
    return Face3D(
        vertices=[
            tunnel_point(
                angle_start,
                z,
                radius=inner_radius,
            ),

            tunnel_point(
                angle_end,
                z,
                radius=inner_radius,
            ),

            tunnel_point(
                angle_end,
                z,
                radius=outer_radius,
            ),

            tunnel_point(
                angle_start,
                z,
                radius=outer_radius,
            ),
        ],

        colour=colour,

        outline_colour=(
            outline_colour
        ),

        outline_width=(
            outline_width
        ),

        double_sided=True,

        glow=glow,
    )


# ============================================================
# DISC / WALL WITH ANGULAR GAP
# ============================================================

def create_ring_wall_faces(
    *,
    z: float,
    safe_angle: float,
    safe_width_degrees: float,
    radius: float = TUNNEL_RADIUS,
    inner_radius: float = 0.0,
    segments: int = 48,
    colour: tuple[int, int, int] = (
        255,
        70,
        80,
    ),
    outline_colour: tuple[
        int,
        int,
        int,
    ] = WHITE,
) -> list[
    Face3D
]:
    """
    Create a circular wall across the tunnel with an angular opening.

    This is useful for classic Tunnel-Rush-style walls:
    almost the entire tunnel is blocked except one opening.
    """

    faces: list[
        Face3D
    ] = []

    segments = max(
        8,
        int(
            segments
        ),
    )

    segment_angle = (
        360.0
        / segments
    )

    for index in range(
        segments
    ):
        start_angle = (
            index
            * segment_angle
        )

        end_angle = (
            start_angle
            + segment_angle
        )

        midpoint = (
            start_angle
            + segment_angle
            / 2.0
        )

        if angle_in_arc(
            midpoint,
            safe_angle,
            safe_width_degrees,
        ):
            continue

        faces.append(
            create_radial_wall_quad(
                angle_start=(
                    start_angle
                ),

                angle_end=(
                    end_angle
                ),

                z=z,

                inner_radius=(
                    inner_radius
                ),

                outer_radius=(
                    radius
                ),

                colour=colour,

                outline_colour=(
                    outline_colour
                ),

                outline_width=1,

                glow=False,
            )
        )

    return faces


# ============================================================
# BOX MESH
# ============================================================

def create_box_mesh(
    *,
    center: Vec3,
    size: Vec3,
    colour: tuple[int, int, int],
    outline_colour: tuple[
        int,
        int,
        int,
    ] | None = None,
    outline_width: int = 0,
    double_sided: bool = True,
) -> Mesh3D:
    half = Vec3(
        size.x / 2.0,
        size.y / 2.0,
        size.z / 2.0,
    )

    vertices = [
        Vec3(
            center.x - half.x,
            center.y - half.y,
            center.z - half.z,
        ),

        Vec3(
            center.x + half.x,
            center.y - half.y,
            center.z - half.z,
        ),

        Vec3(
            center.x + half.x,
            center.y + half.y,
            center.z - half.z,
        ),

        Vec3(
            center.x - half.x,
            center.y + half.y,
            center.z - half.z,
        ),

        Vec3(
            center.x - half.x,
            center.y - half.y,
            center.z + half.z,
        ),

        Vec3(
            center.x + half.x,
            center.y - half.y,
            center.z + half.z,
        ),

        Vec3(
            center.x + half.x,
            center.y + half.y,
            center.z + half.z,
        ),

        Vec3(
            center.x - half.x,
            center.y + half.y,
            center.z + half.z,
        ),
    ]

    indices = (
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
            3,
            2,
            6,
            7,
        ),

        (
            1,
            5,
            6,
            2,
        ),

        (
            0,
            3,
            7,
            4,
        ),
    )

    faces: list[
        Face3D
    ] = []

    for face_indices in indices:
        faces.append(
            Face3D(
                vertices=[
                    vertices[
                        index
                    ]
                    for index
                    in face_indices
                ],

                colour=colour,

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
# TRIANGLE PRISM
# ============================================================

def create_triangle_prism_mesh(
    *,
    center: Vec3,
    width: float,
    height: float,
    depth: float,
    colour: tuple[int, int, int],
    outline_colour: tuple[
        int,
        int,
        int,
    ] | None = WHITE,
) -> Mesh3D:
    half_width = (
        width / 2.0
    )

    half_height = (
        height / 2.0
    )

    half_depth = (
        depth / 2.0
    )

    front_z = (
        center.z
        - half_depth
    )

    back_z = (
        center.z
        + half_depth
    )

    front = [
        Vec3(
            center.x,
            center.y
            - half_height,
            front_z,
        ),

        Vec3(
            center.x
            - half_width,
            center.y
            + half_height,
            front_z,
        ),

        Vec3(
            center.x
            + half_width,
            center.y
            + half_height,
            front_z,
        ),
    ]

    back = [
        Vec3(
            center.x,
            center.y
            - half_height,
            back_z,
        ),

        Vec3(
            center.x
            - half_width,
            center.y
            + half_height,
            back_z,
        ),

        Vec3(
            center.x
            + half_width,
            center.y
            + half_height,
            back_z,
        ),
    ]

    faces = [
        Face3D(
            vertices=front,
            colour=colour,
            outline_colour=(
                outline_colour
            ),
            outline_width=1,
        ),

        Face3D(
            vertices=[
                back[2],
                back[1],
                back[0],
            ],
            colour=colour,
            outline_colour=(
                outline_colour
            ),
            outline_width=1,
        ),
    ]

    for index in range(
        3
    ):
        next_index = (
            index + 1
        ) % 3

        faces.append(
            Face3D(
                vertices=[
                    front[
                        index
                    ],

                    back[
                        index
                    ],

                    back[
                        next_index
                    ],

                    front[
                        next_index
                    ],
                ],

                colour=(
                    multiply_colour(
                        colour,
                        0.82,
                    )
                ),

                outline_colour=(
                    outline_colour
                ),

                outline_width=1,
            )
        )

    return Mesh3D(
        faces=faces
    )


# ============================================================
# ROTATE MESH AROUND Z
# ============================================================

def rotate_mesh_vertices_z(
    mesh: Mesh3D,
    degrees: float,
    *,
    origin: Vec3 | None = None,
) -> Mesh3D:
    if origin is None:
        origin = Vec3()

    result = Mesh3D(
        metadata=dict(
            mesh.metadata
        )
    )

    for face in mesh.faces:
        new_vertices: list[
            Vec3
        ] = []

        for vertex in face.vertices:
            relative = (
                vertex
                - origin
            )

            rotated = rotate_z(
                relative,
                degrees,
            )

            new_vertices.append(
                rotated
                + origin
            )

        result.faces.append(
            Face3D(
                vertices=(
                    new_vertices
                ),

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

    return result


# ============================================================
# TRANSLATE MESH
# ============================================================

def translate_mesh(
    mesh: Mesh3D,
    offset: Vec3,
) -> Mesh3D:
    result = Mesh3D(
        metadata=dict(
            mesh.metadata
        )
    )

    for face in mesh.faces:
        result.faces.append(
            Face3D(
                vertices=[
                    vertex
                    + offset
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

    return result


# ============================================================
# MERGE MESHES
# ============================================================

def merge_meshes(
    meshes: Iterable[
        Mesh3D
    ],
) -> Mesh3D:
    result = Mesh3D()

    for mesh in meshes:
        result.faces.extend(
            mesh.transformed_faces()
        )

    return result


# ============================================================
# TUNNEL CENTRE CURVE
# ============================================================

def tunnel_center_offset(
    distance: float,
    *,
    curve_strength: float = 0.0,
    curve_frequency: float = 0.0,
    phase: float = 0.0,
) -> Vec2:
    if abs(
        curve_strength
    ) <= EPSILON:
        return Vec2()

    angle = (
        distance
        * curve_frequency
        + phase
    )

    return Vec2(
        math.sin(
            angle
        )
        * curve_strength,

        math.cos(
            angle
            * 0.73
        )
        * curve_strength
        * 0.55,
    )


# ============================================================
# TUNNEL STRIP GENERATOR
# ============================================================

def create_tunnel_strip_meshes(
    *,
    start_z: float,
    end_z: float,
    section_length: float,
    radius: float = TUNNEL_RADIUS,
    segments: int = TUNNEL_SEGMENTS,
    rotation_start: float = 0.0,
    rotation_per_unit: float = 0.0,
    curve_strength: float = 0.0,
    curve_frequency: float = 0.0,
    curve_phase: float = 0.0,
    primary_colour: tuple[
        int,
        int,
        int,
    ] = (
        18,
        45,
        90,
    ),
    secondary_colour: tuple[
        int,
        int,
        int,
    ] = (
        28,
        72,
        140,
    ),
    line_colour: tuple[
        int,
        int,
        int,
    ] = LIGHT_BLUE,
) -> list[
    Mesh3D
]:
    """
    Generate many connected tunnel pieces.

    This is what main.py will use to make the environment appear
    continuous as the camera flies forward.
    """

    meshes: list[
        Mesh3D
    ] = []

    distance = float(
        start_z
    )

    section_length = max(
        0.25,
        float(
            section_length
        ),
    )

    while distance < end_z:
        next_distance = min(
            end_z,
            distance
            + section_length,
        )

        start_rotation = (
            rotation_start
            + distance
            * rotation_per_unit
        )

        end_rotation = (
            rotation_start
            + next_distance
            * rotation_per_unit
        )

        start_center = (
            tunnel_center_offset(
                distance,

                curve_strength=(
                    curve_strength
                ),

                curve_frequency=(
                    curve_frequency
                ),

                phase=(
                    curve_phase
                ),
            )
        )

        end_center = (
            tunnel_center_offset(
                next_distance,

                curve_strength=(
                    curve_strength
                ),

                curve_frequency=(
                    curve_frequency
                ),

                phase=(
                    curve_phase
                ),
            )
        )

        meshes.append(
            create_tunnel_section_mesh(
                distance,
                next_distance,

                radius=radius,

                segments=segments,

                start_rotation=(
                    start_rotation
                ),

                end_rotation=(
                    end_rotation
                ),

                start_center=(
                    start_center
                ),

                end_center=(
                    end_center
                ),

                primary_colour=(
                    primary_colour
                ),

                secondary_colour=(
                    secondary_colour
                ),

                line_colour=(
                    line_colour
                ),

                draw_outlines=True,
            )
        )

        distance = (
            next_distance
        )

    return meshes


# ============================================================
# 3D LINE PROJECTION
# ============================================================

def draw_3d_line(
    surface: pygame.Surface,
    camera: Camera3D,
    start: Vec3,
    end: Vec3,
    colour: tuple[int, int, int],
    width: int = 1,
) -> None:
    camera_start = (
        camera.world_to_camera(
            start
        )
    )

    camera_end = (
        camera.world_to_camera(
            end
        )
    )

    clipped = (
        clip_line_to_near_plane(
            camera_start,
            camera_end,
            camera.near_clip,
        )
    )

    if clipped is None:
        return

    camera_start, camera_end = (
        clipped
    )

    first = (
        camera.camera_to_screen(
            camera_start
        )
    )

    second = (
        camera.camera_to_screen(
            camera_end
        )
    )

    if (
        first is None
        or second is None
    ):
        return

    pygame.draw.line(
        surface,
        colour,
        first.int_tuple(),
        second.int_tuple(),
        max(
            1,
            int(
                width
            ),
        ),
    )


# ============================================================
# DEBUG AXES
# ============================================================

def draw_debug_axes(
    surface: pygame.Surface,
    camera: Camera3D,
    *,
    origin: Vec3 = Vec3(),
    axis_length: float = 4.0,
) -> None:
    draw_3d_line(
        surface,
        camera,
        origin,
        origin
        + Vec3(
            axis_length,
            0.0,
            0.0,
        ),
        (
            255,
            60,
            60,
        ),
        2,
    )

    draw_3d_line(
        surface,
        camera,
        origin,
        origin
        + Vec3(
            0.0,
            axis_length,
            0.0,
        ),
        (
            60,
            255,
            80,
        ),
        2,
    )

    draw_3d_line(
        surface,
        camera,
        origin,
        origin
        + Vec3(
            0.0,
            0.0,
            axis_length,
        ),
        (
            60,
            130,
            255,
        ),
        2,
    )


# ============================================================
# SCREEN BOUNDS HELPERS
# ============================================================

def point_inside_screen(
    point: tuple[
        int,
        int,
    ],
    *,
    margin: int = 0,
) -> bool:
    return (
        -margin
        <= point[0]
        <= GAME_WIDTH
        + margin
        and -margin
        <= point[1]
        <= GAME_HEIGHT
        + margin
    )


def polygon_intersects_screen(
    points: list[
        tuple[
            int,
            int,
        ]
    ],
) -> bool:
    if not points:
        return False

    if any(
        point_inside_screen(
            point
        )
        for point
        in points
    ):
        return True

    minimum_x = min(
        point[0]
        for point in points
    )

    maximum_x = max(
        point[0]
        for point in points
    )

    minimum_y = min(
        point[1]
        for point in points
    )

    maximum_y = max(
        point[1]
        for point in points
    )

    return not (
        maximum_x < 0
        or minimum_x > GAME_WIDTH
        or maximum_y < 0
        or minimum_y > GAME_HEIGHT
    )


# ============================================================
# 3D SCENE RENDERER
# ============================================================

class SceneRenderer3D:
    """
    Collects meshes and renders all faces in depth order.

    obstacles.py and main.py can both submit meshes here.
    """

    def __init__(
        self,
        camera: Camera3D,
    ):
        self.camera = camera

        self.meshes: list[
            Mesh3D
        ] = []

        self.extra_faces: list[
            Face3D
        ] = []

        self.fog_colour = BLACK

        self.use_lighting = False

    def clear(
        self,
    ) -> None:
        self.meshes.clear()

        self.extra_faces.clear()

    def add_mesh(
        self,
        mesh: Mesh3D,
    ) -> None:
        if mesh.visible:
            self.meshes.append(
                mesh
            )

    def add_meshes(
        self,
        meshes: Iterable[
            Mesh3D
        ],
    ) -> None:
        for mesh in meshes:
            self.add_mesh(
                mesh
            )

    def add_face(
        self,
        face: Face3D,
    ) -> None:
        self.extra_faces.append(
            face
        )

    def build_render_faces(
        self,
    ) -> list[
        RenderFace
    ]:
        render_faces: list[
            RenderFace
        ] = []

        for mesh in self.meshes:
            render_faces.extend(
                project_mesh(
                    mesh,
                    self.camera,

                    fog_colour=(
                        self.fog_colour
                    ),

                    use_lighting=(
                        self.use_lighting
                    ),
                )
            )

        for face in (
            self.extra_faces
        ):
            projected = (
                project_face(
                    face,
                    self.camera,

                    fog_colour=(
                        self.fog_colour
                    ),

                    use_lighting=(
                        self.use_lighting
                    ),
                )
            )

            if projected is not None:
                render_faces.append(
                    projected
                )

        return (
            sort_render_faces(
                render_faces
            )
        )

    def draw(
        self,
        surface: pygame.Surface,
    ) -> None:
        render_faces = (
            self.build_render_faces()
        )

        for render_face in (
            render_faces
        ):
            if not (
                polygon_intersects_screen(
                    render_face.points
                )
            ):
                continue

            draw_render_face(
                surface,
                render_face,
            )


# ============================================================
# PROJECTED TUNNEL POSITION
# ============================================================

def projected_tunnel_position(
    camera: Camera3D,
    angle_degrees: float,
    distance: float,
    *,
    radius: float = TUNNEL_RADIUS,
) -> Vec2 | None:
    point = tunnel_point(
        angle_degrees,
        camera.position.z
        + distance,
        radius=radius,
    )

    return camera.project(
        point
    )


# ============================================================
# ANGULAR PLAYER MARKER POSITION
# ============================================================

def projected_player_tunnel_point(
    camera: Camera3D,
    player_angle: float,
    *,
    distance: float = 3.0,
    radius: float = TUNNEL_RADIUS,
) -> Vec2 | None:
    """
    Useful for debugging.

    In normal gameplay the player is first-person and not rendered.
    """

    return (
        projected_tunnel_position(
            camera,
            player_angle,
            distance,

            radius=radius,
        )
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_geometry(
) -> None:
    if GAME_WIDTH <= 0:
        raise ValueError(
            "GAME_WIDTH must be positive."
        )

    if GAME_HEIGHT <= 0:
        raise ValueError(
            "GAME_HEIGHT must be positive."
        )

    if CAMERA_NEAR_CLIP <= 0:
        raise ValueError(
            "CAMERA_NEAR_CLIP must be positive."
        )

    if (
        CAMERA_FAR_CLIP
        <= CAMERA_NEAR_CLIP
    ):
        raise ValueError(
            "Camera clipping range is invalid."
        )

    if TUNNEL_RADIUS <= 0:
        raise ValueError(
            "TUNNEL_RADIUS must be positive."
        )

    if TUNNEL_SEGMENTS < 8:
        raise ValueError(
            "TUNNEL_SEGMENTS must be at least 8."
        )

    test_camera = (
        Camera3D()
    )

    test_point = Vec3(
        0.0,
        0.0,
        10.0,
    )

    projected = (
        test_camera.project(
            test_point
        )
    )

    if projected is None:
        raise ValueError(
            "3D camera failed basic projection test."
        )

    if abs(
        projected.x
        - GAME_CENTER_X
    ) > 1.0:
        raise ValueError(
            "Camera horizontal projection is incorrect."
        )

    if abs(
        projected.y
        - GAME_CENTER_Y
    ) > 1.0:
        raise ValueError(
            "Camera vertical projection is incorrect."
        )


validate_geometry()