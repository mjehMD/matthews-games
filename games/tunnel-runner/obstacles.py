from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from config import (
    CYAN,
    OBSTACLE_BLADE,
    OBSTACLE_CLOSING_WALL,
    OBSTACLE_COLLISION_DISTANCE,
    OBSTACLE_DIAMOND,
    OBSTACLE_DOUBLE_BLADE,
    OBSTACLE_DOUBLE_BAR,
    OBSTACLE_DOUBLE_TRIANGLE,
    OBSTACLE_FINISH,
    OBSTACLE_GAP_WALL,
    OBSTACLE_MOVING_GAP,
    OBSTACLE_RING_GAP,
    OBSTACLE_ROTATING_BAR,
    OBSTACLE_ROTATING_CROSS,
    OBSTACLE_ROTATING_WEDGE,
    OBSTACLE_SLIDING_WALL,
    OBSTACLE_SPINNER,
    OBSTACLE_TRIANGLE,
    OBSTACLE_TRIPLE_BLADE,
    OBSTACLE_WALL,
    OBSTACLE_WEDGE,
    ORANGE,
    PINK,
    PLAYER_COLLISION_ANGLE,
    RED,
    TUNNEL_RADIUS,
    WHITE,
    YELLOW,
    clamp,
)

from geometry import (
    Face3D,
    Mesh3D,
    Vec3,
    angle_in_arc,
    create_box_mesh,
    multiply_colour,
    normalize_degrees,
    rotate_mesh_vertices_z,
    tunnel_point,
)


# ============================================================
# TUNNEL RUNNER
# OBSTACLE SYSTEM
# VERSION 0.1.1
# ============================================================
#
# FIXES:
#
# - Rotating-bar collision now matches the visible bar.
# - Spinners/crosses have guaranteed usable gaps.
# - Collision padding is less aggressive.
# - Static obstacle meshes are cached.
# - Collision only checks obstacles near the player.
# - Endless spinning speeds are more reasonable.
#
# ============================================================


OBSTACLE_CROSS = "cross"

EPSILON = 0.000001

MIN_PLAYABLE_GAP = 48.0
MIN_SPINNER_GAP = 64.0
MIN_BAR_GAP = 125.0

MAX_COLLISION_PADDING = 8.0


# ============================================================
# HELPERS
# ============================================================

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


def cyclic_sine(
    time_seconds: float,
    speed: float,
    phase: float = 0.0,
) -> float:
    return math.sin(
        time_seconds
        * speed
        + phase
    )


def safe_colour(
    colour: tuple[int, int, int],
    multiplier: float,
) -> tuple[int, int, int]:
    return multiply_colour(
        colour,
        multiplier,
    )


def collision_padding(
) -> float:
    return min(
        MAX_COLLISION_PADDING,
        max(
            0.0,
            PLAYER_COLLISION_ANGLE,
        ),
    )


# ============================================================
# SAFE ARC
# ============================================================

@dataclass
class SafeArc:
    center: float

    width: float

    def contains(
        self,
        player_angle: float,
        *,
        padding: float = 0.0,
    ) -> bool:
        effective_width = max(
            0.0,
            self.width
            - padding
            * 2.0,
        )

        return angle_in_arc(
            normalize_degrees(
                player_angle
            ),
            normalize_degrees(
                self.center
            ),
            effective_width,
        )


# ============================================================
# OBSTACLE STATE
# ============================================================

@dataclass
class ObstacleState:
    rotation: float = 0.0

    movement_offset: float = 0.0

    animation_time: float = 0.0

    collision_checked: bool = False

    passed: bool = False

    active: bool = True


# ============================================================
# BASE OBSTACLE
# ============================================================

@dataclass
class TunnelObstacle:
    obstacle_type: str

    z: float

    angle: float = 0.0

    safe_width: float = 90.0

    rotation_speed: float = 0.0

    movement_speed: float = 0.0

    movement_amount: float = 0.0

    phase: float = 0.0

    thickness: float = 0.8

    primary_colour: tuple[int, int, int] = RED

    secondary_colour: tuple[int, int, int] = ORANGE

    enabled: bool = True

    metadata: dict[str, object] = field(
        default_factory=dict
    )

    state: ObstacleState = field(
        default_factory=ObstacleState
    )

    _cached_meshes: list[Mesh3D] | None = field(
        default=None,
        init=False,
        repr=False,
    )

    def __post_init__(
        self,
    ) -> None:
        self.angle = normalize_degrees(
            self.angle
        )

        self.safe_width = clamp(
            self.safe_width,
            0.0,
            360.0,
        )

        self.thickness = max(
            0.05,
            float(
                self.thickness
            ),
        )

        self.state.rotation = (
            self.angle
        )

    # ========================================================
    # ANIMATION
    # ========================================================

    @property
    def animated(
        self,
    ) -> bool:
        return (
            abs(
                self.rotation_speed
            )
            > EPSILON

            or abs(
                self.movement_speed
            )
            > EPSILON

            or self.obstacle_type
            == OBSTACLE_CLOSING_WALL
        )

    def update(
        self,
        delta_time: float,
    ) -> None:
        if not self.enabled:
            return

        self.state.animation_time += (
            delta_time
        )

        if abs(
            self.rotation_speed
        ) > EPSILON:
            self.state.rotation = (
                normalize_degrees(
                    self.state.rotation
                    + self.rotation_speed
                    * delta_time
                )
            )

        if (
            abs(
                self.movement_speed
            )
            > EPSILON

            and abs(
                self.movement_amount
            )
            > EPSILON
        ):
            self.state.movement_offset = (
                cyclic_sine(
                    self.state.animation_time,
                    self.movement_speed,
                    self.phase,
                )
                * self.movement_amount
            )

    def current_angle(
        self,
    ) -> float:
        return normalize_degrees(
            self.state.rotation
            + self.state.movement_offset
        )

    # ========================================================
    # VISIBILITY
    # ========================================================

    def distance_from_camera(
        self,
        camera_z: float,
    ) -> float:
        return (
            self.z
            - camera_z
        )

    def visible(
        self,
        camera_z: float,
        visible_distance: float,
    ) -> bool:
        distance = (
            self.distance_from_camera(
                camera_z
            )
        )

        return (
            -2.0
            <= distance
            <= visible_distance
        )

    # ========================================================
    # SAFE AREAS
    # ========================================================

    def safe_arcs(
        self,
    ) -> list[SafeArc]:
        return [
            SafeArc(
                self.current_angle(),

                max(
                    MIN_PLAYABLE_GAP,
                    self.safe_width,
                ),
            )
        ]

    def player_is_safe(
        self,
        player_angle: float,
    ) -> bool:
        if (
            self.obstacle_type
            == OBSTACLE_FINISH
        ):
            return True

        arcs = (
            self.safe_arcs()
        )

        if not arcs:
            return False

        padding = (
            collision_padding()
        )

        return any(
            arc.contains(
                player_angle,
                padding=padding,
            )

            for arc in arcs
        )

    # ========================================================
    # COLLISION
    # ========================================================

    def collision_active(
        self,
        camera_z: float,
    ) -> bool:
        distance = abs(
            self.z
            - camera_z
        )

        return (
            distance
            <= max(
                OBSTACLE_COLLISION_DISTANCE,

                self.thickness
                * 0.75,
            )
        )

    def check_collision(
        self,
        camera_z: float,
        player_angle: float,
    ) -> bool:
        if (
            not self.enabled

            or self.state.passed
        ):
            return False

        if not self.collision_active(
            camera_z
        ):
            return False

        self.state.collision_checked = (
            True
        )

        return not self.player_is_safe(
            player_angle
        )

    def update_passed_state(
        self,
        camera_z: float,
    ) -> bool:
        if self.state.passed:
            return False

        if (
            camera_z
            > self.z
            + max(
                1.5,
                self.thickness,
            )
        ):
            self.state.passed = True

            return True

        return False

    # ========================================================
    # MESH CACHE
    # ========================================================

    def build_meshes(
        self,
    ) -> list[Mesh3D]:
        if (
            not self.animated

            and self._cached_meshes
            is not None
        ):
            return (
                self._cached_meshes
            )

        meshes = (
            build_obstacle_meshes(
                self
            )
        )

        if not self.animated:
            self._cached_meshes = (
                meshes
            )

        return meshes


# ============================================================
# NORMAL WALL
# ============================================================

class WallObstacle(
    TunnelObstacle
):
    def safe_arcs(
        self,
    ) -> list[SafeArc]:
        return [
            SafeArc(
                self.current_angle(),

                max(
                    MIN_PLAYABLE_GAP,
                    self.safe_width,
                ),
            )
        ]


# ============================================================
# MOVING GAP
# ============================================================

class MovingGapObstacle(
    WallObstacle
):
    def current_angle(
        self,
    ) -> float:
        movement = (
            math.sin(
                self.state.animation_time
                * max(
                    0.25,
                    abs(
                        self.movement_speed
                    ),
                )
                + self.phase
            )

            * max(
                0.0,
                self.movement_amount,
            )
        )

        return normalize_degrees(
            self.angle
            + movement
        )


# ============================================================
# CLOSING WALL
# ============================================================

class ClosingWallObstacle(
    WallObstacle
):
    def safe_arcs(
        self,
    ) -> list[SafeArc]:
        pulse = (
            math.sin(
                self.state.animation_time
                * max(
                    0.45,
                    abs(
                        self.movement_speed
                    ),
                )
                + self.phase
            )
            + 1.0
        ) / 2.0

        maximum = max(
            72.0,
            self.safe_width,
        )

        minimum = max(
            MIN_PLAYABLE_GAP,

            self.safe_width
            * 0.62,
        )

        return [
            SafeArc(
                self.current_angle(),

                lerp(
                    minimum,
                    maximum,
                    pulse,
                ),
            )
        ]


# ============================================================
# SINGLE ROTATING BAR
# ============================================================

class SingleBarObstacle(
    TunnelObstacle
):
    """
    The visible bar passes through the middle of the tunnel.

    A horizontal bar touches the tunnel at 90° and 270°.

    Therefore the safest areas are around 0° and 180°.

    The old version incorrectly treated this as a cross.
    """

    def safe_arcs(
        self,
    ) -> list[SafeArc]:
        angle = (
            self.current_angle()
        )

        width = max(
            MIN_BAR_GAP,
            self.safe_width,
        )

        return [
            SafeArc(
                angle,
                width,
            ),

            SafeArc(
                normalize_degrees(
                    angle
                    + 180.0
                ),
                width,
            ),
        ]


# ============================================================
# CROSS / DOUBLE BAR / SPINNER
# ============================================================

class CrossObstacle(
    TunnelObstacle
):
    """
    Four arms block the tunnel.

    Safe openings are halfway between the arms.
    """

    def safe_arcs(
        self,
    ) -> list[SafeArc]:
        rotation = (
            self.current_angle()
        )

        width = max(
            MIN_SPINNER_GAP,
            self.safe_width,
        )

        width = min(
            82.0,
            width,
        )

        return [
            SafeArc(
                normalize_degrees(
                    rotation
                    + 45.0
                    + index
                    * 90.0
                ),

                width,
            )

            for index in range(
                4
            )
        ]


# ============================================================
# BLADES
# ============================================================

class BladeObstacle(
    TunnelObstacle
):
    blade_count: int = 1

    def safe_arcs(
        self,
    ) -> list[SafeArc]:
        count = max(
            1,

            int(
                getattr(
                    self,
                    "blade_count",
                    1,
                )
            ),
        )

        spacing = (
            360.0
            / count
        )

        safe_width = max(
            MIN_PLAYABLE_GAP,

            spacing
            - 38.0,
        )

        rotation = (
            self.current_angle()
        )

        return [
            SafeArc(
                normalize_degrees(
                    rotation
                    + index
                    * spacing
                    + spacing
                    / 2.0
                ),

                safe_width,
            )

            for index in range(
                count
            )
        ]


# ============================================================
# TRIANGLE / WEDGE
# ============================================================

class TriangleObstacle(
    TunnelObstacle
):
    triangle_count: int = 1

    def safe_arcs(
        self,
    ) -> list[SafeArc]:
        count = max(
            1,

            int(
                getattr(
                    self,
                    "triangle_count",
                    1,
                )
            ),
        )

        rotation = (
            self.current_angle()
        )

        if count == 1:
            return [
                SafeArc(
                    normalize_degrees(
                        rotation
                        + 180.0
                    ),

                    190.0,
                )
            ]

        return [
            SafeArc(
                normalize_degrees(
                    rotation
                    + 90.0
                ),

                82.0,
            ),

            SafeArc(
                normalize_degrees(
                    rotation
                    + 270.0
                ),

                82.0,
            ),
        ]


# ============================================================
# FINISH
# ============================================================

class FinishObstacle(
    TunnelObstacle
):
    def safe_arcs(
        self,
    ) -> list[SafeArc]:
        return [
            SafeArc(
                0.0,
                360.0,
            )
        ]


# ============================================================
# WALL GEOMETRY
# ============================================================

def create_multi_gap_wall_faces(
    *,
    z: float,

    safe_arcs: list[SafeArc],

    colour: tuple[int, int, int],

    secondary_colour: tuple[int, int, int],

    radius: float = TUNNEL_RADIUS,

    segments: int = 48,
) -> list[Face3D]:

    faces: list[
        Face3D
    ] = []

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
            + end_angle
        ) / 2.0

        if any(
            angle_in_arc(
                midpoint,
                arc.center,
                arc.width,
            )

            for arc in safe_arcs
        ):
            continue

        inner_radius = 0.18

        face_colour = (
            colour

            if index % 2 == 0

            else secondary_colour
        )

        faces.append(
            Face3D(
                vertices=[
                    tunnel_point(
                        start_angle,
                        z,
                        radius=inner_radius,
                    ),

                    tunnel_point(
                        start_angle,
                        z,
                        radius=radius,
                    ),

                    tunnel_point(
                        end_angle,
                        z,
                        radius=radius,
                    ),

                    tunnel_point(
                        end_angle,
                        z,
                        radius=inner_radius,
                    ),
                ],

                colour=face_colour,

                outline_colour=(
                    safe_colour(
                        face_colour,
                        1.20,
                    )
                ),

                outline_width=1,

                double_sided=True,

                metadata={
                    "obstacle_surface":
                        True,
                },
            )
        )

    return faces


def create_thick_wall_mesh(
    obstacle: TunnelObstacle,
) -> Mesh3D:

    safe_arcs = (
        obstacle.safe_arcs()
    )

    front_z = (
        obstacle.z
        - obstacle.thickness
        / 2.0
    )

    back_z = (
        obstacle.z
        + obstacle.thickness
        / 2.0
    )

    return Mesh3D(
        faces=(
            create_multi_gap_wall_faces(
                z=front_z,

                safe_arcs=safe_arcs,

                colour=(
                    obstacle.primary_colour
                ),

                secondary_colour=(
                    obstacle.secondary_colour
                ),
            )

            +

            create_multi_gap_wall_faces(
                z=back_z,

                safe_arcs=safe_arcs,

                colour=(
                    safe_colour(
                        obstacle.primary_colour,
                        0.72,
                    )
                ),

                secondary_colour=(
                    safe_colour(
                        obstacle.secondary_colour,
                        0.72,
                    )
                ),
            )
        ),

        metadata={
            "type":
                obstacle.obstacle_type,

            "z":
                obstacle.z,
        },
    )


# ============================================================
# BAR GEOMETRY
# ============================================================

def create_bar_mesh(
    *,
    z: float,

    angle: float,

    length: float,

    width: float,

    depth: float,

    colour: tuple[int, int, int],
) -> Mesh3D:

    mesh = create_box_mesh(
        center=Vec3(
            0.0,
            0.0,
            z,
        ),

        size=Vec3(
            length,
            width,
            depth,
        ),

        colour=colour,

        outline_colour=WHITE,

        outline_width=1,

        double_sided=True,
    )

    return rotate_mesh_vertices_z(
        mesh,

        angle,

        origin=Vec3(
            0.0,
            0.0,
            z,
        ),
    )


def build_rotating_bar(
    obstacle: TunnelObstacle,
    *,
    double: bool = False,
) -> list[Mesh3D]:

    angle = (
        obstacle.current_angle()
    )

    meshes = [
        create_bar_mesh(
            z=obstacle.z,

            angle=angle,

            length=(
                TUNNEL_RADIUS
                * 2.15
            ),

            width=1.05,

            depth=(
                obstacle.thickness
            ),

            colour=(
                obstacle.primary_colour
            ),
        )
    ]

    if double:
        meshes.append(
            create_bar_mesh(
                z=obstacle.z,

                angle=(
                    angle
                    + 90.0
                ),

                length=(
                    TUNNEL_RADIUS
                    * 2.15
                ),

                width=1.05,

                depth=(
                    obstacle.thickness
                ),

                colour=(
                    obstacle.secondary_colour
                ),
            )
        )

    return meshes


def build_cross(
    obstacle: TunnelObstacle,
) -> list[Mesh3D]:

    return build_rotating_bar(
        obstacle,
        double=True,
    )


# ============================================================
# BLADE GEOMETRY
# ============================================================

def create_blade_face(
    *,
    z: float,

    angle: float,

    width_degrees: float,

    colour: tuple[int, int, int],
) -> Face3D:

    half_width = (
        width_degrees
        / 2.0
    )

    return Face3D(
        vertices=[
            Vec3(
                0.0,
                0.0,
                z,
            ),

            tunnel_point(
                angle
                - half_width,

                z,

                radius=(
                    TUNNEL_RADIUS
                    * 1.02
                ),
            ),

            tunnel_point(
                angle
                + half_width,

                z,

                radius=(
                    TUNNEL_RADIUS
                    * 1.02
                ),
            ),
        ],

        colour=colour,

        outline_colour=WHITE,

        outline_width=1,

        double_sided=True,
    )


def build_blades(
    obstacle: TunnelObstacle,
    blade_count: int,
) -> list[Mesh3D]:

    blade_count = max(
        1,
        blade_count,
    )

    spacing = (
        360.0
        / blade_count
    )

    faces: list[
        Face3D
    ] = []

    for index in range(
        blade_count
    ):
        faces.append(
            create_blade_face(
                z=obstacle.z,

                angle=(
                    obstacle.current_angle()
                    + index
                    * spacing
                ),

                width_degrees=min(
                    32.0,

                    spacing
                    * 0.42,
                ),

                colour=(
                    obstacle.primary_colour

                    if index % 2 == 0

                    else obstacle.secondary_colour
                ),
            )
        )

    return [
        Mesh3D(
            faces=faces
        )
    ]


# ============================================================
# TRIANGLE GEOMETRY
# ============================================================

def build_triangles(
    obstacle: TunnelObstacle,
    count: int,
) -> list[Mesh3D]:

    count = max(
        1,
        count,
    )

    spacing = (
        360.0
        / count
    )

    faces: list[
        Face3D
    ] = []

    for index in range(
        count
    ):
        angle = (
            obstacle.current_angle()
            + index
            * spacing
        )

        faces.append(
            Face3D(
                vertices=[
                    tunnel_point(
                        angle - 38.0,

                        obstacle.z,

                        radius=TUNNEL_RADIUS,
                    ),

                    tunnel_point(
                        angle + 38.0,

                        obstacle.z,

                        radius=TUNNEL_RADIUS,
                    ),

                    tunnel_point(
                        angle,

                        obstacle.z,

                        radius=(
                            TUNNEL_RADIUS
                            * 0.12
                        ),
                    ),
                ],

                colour=(
                    obstacle.primary_colour

                    if index % 2 == 0

                    else obstacle.secondary_colour
                ),

                outline_colour=WHITE,

                outline_width=1,

                double_sided=True,
            )
        )

    return [
        Mesh3D(
            faces=faces
        )
    ]


# ============================================================
# WEDGE
# ============================================================

def build_wedge(
    obstacle: TunnelObstacle,
) -> list[Mesh3D]:

    angle = (
        obstacle.current_angle()
    )

    width = 110.0

    return [
        Mesh3D(
            faces=[
                Face3D(
                    vertices=[
                        Vec3(
                            0.0,
                            0.0,
                            obstacle.z,
                        ),

                        tunnel_point(
                            angle
                            - width / 2.0,

                            obstacle.z,

                            radius=TUNNEL_RADIUS,
                        ),

                        tunnel_point(
                            angle
                            + width / 2.0,

                            obstacle.z,

                            radius=TUNNEL_RADIUS,
                        ),
                    ],

                    colour=(
                        obstacle.primary_colour
                    ),

                    outline_colour=WHITE,

                    outline_width=2,

                    double_sided=True,
                )
            ]
        )
    ]


# ============================================================
# DIAMOND
# ============================================================

def build_diamond(
    obstacle: TunnelObstacle,
) -> list[Mesh3D]:

    angle = (
        obstacle.current_angle()
    )

    center = tunnel_point(
        angle,

        obstacle.z,

        radius=(
            TUNNEL_RADIUS
            * 0.45
        ),
    )

    size = 2.4

    return [
        Mesh3D(
            faces=[
                Face3D(
                    vertices=[
                        Vec3(
                            center.x,
                            center.y - size,
                            obstacle.z,
                        ),

                        Vec3(
                            center.x + size,
                            center.y,
                            obstacle.z,
                        ),

                        Vec3(
                            center.x,
                            center.y + size,
                            obstacle.z,
                        ),

                        Vec3(
                            center.x - size,
                            center.y,
                            obstacle.z,
                        ),
                    ],

                    colour=(
                        obstacle.primary_colour
                    ),

                    outline_colour=WHITE,

                    outline_width=2,

                    double_sided=True,
                )
            ]
        )
    ]


# ============================================================
# FINISH RING
# ============================================================

def build_finish_ring(
    obstacle: TunnelObstacle,
) -> list[Mesh3D]:

    faces: list[
        Face3D
    ] = []

    segments = 32

    segment_angle = (
        360.0
        / segments
    )

    for index in range(
        segments
    ):
        a0 = (
            index
            * segment_angle
        )

        a1 = (
            a0
            + segment_angle
        )

        colour = (
            CYAN

            if index % 2 == 0

            else WHITE
        )

        faces.append(
            Face3D(
                vertices=[
                    tunnel_point(
                        a0,

                        obstacle.z,

                        radius=(
                            TUNNEL_RADIUS
                            * 0.82
                        ),
                    ),

                    tunnel_point(
                        a0,

                        obstacle.z,

                        radius=(
                            TUNNEL_RADIUS
                            * 0.96
                        ),
                    ),

                    tunnel_point(
                        a1,

                        obstacle.z,

                        radius=(
                            TUNNEL_RADIUS
                            * 0.96
                        ),
                    ),

                    tunnel_point(
                        a1,

                        obstacle.z,

                        radius=(
                            TUNNEL_RADIUS
                            * 0.82
                        ),
                    ),
                ],

                colour=colour,

                double_sided=True,

                glow=False,
            )
        )

    return [
        Mesh3D(
            faces=faces
        )
    ]


# ============================================================
# MESH BUILDER
# ============================================================

def build_obstacle_meshes(
    obstacle: TunnelObstacle,
) -> list[Mesh3D]:

    obstacle_type = (
        obstacle.obstacle_type
    )

    if obstacle_type in (
        OBSTACLE_WALL,
        OBSTACLE_GAP_WALL,
        OBSTACLE_RING_GAP,
        OBSTACLE_SLIDING_WALL,
        OBSTACLE_CLOSING_WALL,
        OBSTACLE_MOVING_GAP,
    ):
        return [
            create_thick_wall_mesh(
                obstacle
            )
        ]

    if (
        obstacle_type
        == OBSTACLE_ROTATING_BAR
    ):
        return build_rotating_bar(
            obstacle,

            double=False,
        )

    if (
        obstacle_type
        == OBSTACLE_DOUBLE_BAR
    ):
        return build_rotating_bar(
            obstacle,

            double=True,
        )

    if obstacle_type in (
        OBSTACLE_CROSS,
        OBSTACLE_ROTATING_CROSS,
        OBSTACLE_SPINNER,
    ):
        return build_cross(
            obstacle
        )

    if (
        obstacle_type
        == OBSTACLE_TRIANGLE
    ):
        return build_triangles(
            obstacle,
            1,
        )

    if (
        obstacle_type
        == OBSTACLE_DOUBLE_TRIANGLE
    ):
        return build_triangles(
            obstacle,
            2,
        )

    if obstacle_type in (
        OBSTACLE_WEDGE,
        OBSTACLE_ROTATING_WEDGE,
    ):
        return build_wedge(
            obstacle
        )

    if (
        obstacle_type
        == OBSTACLE_DIAMOND
    ):
        return build_diamond(
            obstacle
        )

    if (
        obstacle_type
        == OBSTACLE_BLADE
    ):
        return build_blades(
            obstacle,
            1,
        )

    if (
        obstacle_type
        == OBSTACLE_DOUBLE_BLADE
    ):
        return build_blades(
            obstacle,
            2,
        )

    if (
        obstacle_type
        == OBSTACLE_TRIPLE_BLADE
    ):
        return build_blades(
            obstacle,
            3,
        )

    if (
        obstacle_type
        == OBSTACLE_FINISH
    ):
        return build_finish_ring(
            obstacle
        )

    return []


# ============================================================
# FACTORY
# ============================================================

def create_obstacle(
    obstacle_type: str,
    *,
    z: float,
    angle: float = 0.0,
    safe_width: float = 90.0,
    rotation_speed: float = 0.0,
    movement_speed: float = 0.0,
    movement_amount: float = 0.0,
    phase: float = 0.0,
    thickness: float = 0.8,
    primary_colour: tuple[int, int, int] = RED,
    secondary_colour: tuple[int, int, int] = ORANGE,
    metadata: dict[str, object] | None = None,
) -> TunnelObstacle:

    common = dict(
        obstacle_type=obstacle_type,

        z=z,

        angle=angle,

        safe_width=safe_width,

        rotation_speed=(
            rotation_speed
        ),

        movement_speed=(
            movement_speed
        ),

        movement_amount=(
            movement_amount
        ),

        phase=phase,

        thickness=thickness,

        primary_colour=(
            primary_colour
        ),

        secondary_colour=(
            secondary_colour
        ),

        metadata=(
            metadata

            if metadata is not None

            else {}
        ),
    )

    if obstacle_type in (
        OBSTACLE_WALL,
        OBSTACLE_GAP_WALL,
        OBSTACLE_RING_GAP,
        OBSTACLE_SLIDING_WALL,
    ):
        return WallObstacle(
            **common
        )

    if (
        obstacle_type
        == OBSTACLE_MOVING_GAP
    ):
        return MovingGapObstacle(
            **common
        )

    if (
        obstacle_type
        == OBSTACLE_CLOSING_WALL
    ):
        return ClosingWallObstacle(
            **common
        )

    if (
        obstacle_type
        == OBSTACLE_ROTATING_BAR
    ):
        common[
            "safe_width"
        ] = max(
            MIN_BAR_GAP,

            safe_width,
        )

        return SingleBarObstacle(
            **common
        )

    if obstacle_type in (
        OBSTACLE_DOUBLE_BAR,
        OBSTACLE_CROSS,
        OBSTACLE_ROTATING_CROSS,
        OBSTACLE_SPINNER,
    ):
        common[
            "safe_width"
        ] = max(
            MIN_SPINNER_GAP,

            safe_width,
        )

        return CrossObstacle(
            **common
        )

    if obstacle_type in (
        OBSTACLE_BLADE,
        OBSTACLE_DOUBLE_BLADE,
        OBSTACLE_TRIPLE_BLADE,
    ):
        result = (
            BladeObstacle(
                **common
            )
        )

        result.blade_count = (
            1

            if obstacle_type
            == OBSTACLE_BLADE

            else 2

            if obstacle_type
            == OBSTACLE_DOUBLE_BLADE

            else 3
        )

        return result

    if obstacle_type in (
        OBSTACLE_TRIANGLE,
        OBSTACLE_DOUBLE_TRIANGLE,
        OBSTACLE_WEDGE,
        OBSTACLE_ROTATING_WEDGE,
        OBSTACLE_DIAMOND,
    ):
        result = (
            TriangleObstacle(
                **common
            )
        )

        result.triangle_count = (
            2

            if obstacle_type
            == OBSTACLE_DOUBLE_TRIANGLE

            else 1
        )

        return result

    if (
        obstacle_type
        == OBSTACLE_FINISH
    ):
        return FinishObstacle(
            **common
        )

    return TunnelObstacle(
        **common
    )


# ============================================================
# PRESET FACTORIES
# ============================================================

def make_gap_wall(
    z: float,
    *,
    angle: float,
    safe_width: float,
    colour: tuple[int, int, int] = RED,
) -> TunnelObstacle:

    return create_obstacle(
        OBSTACLE_GAP_WALL,

        z=z,

        angle=angle,

        safe_width=max(
            MIN_PLAYABLE_GAP,
            safe_width,
        ),

        primary_colour=colour,

        secondary_colour=(
            safe_colour(
                colour,
                0.72,
            )
        ),
    )


def make_rotating_bar(
    z: float,
    *,
    angle: float = 0.0,
    rotation_speed: float = 42.0,
) -> TunnelObstacle:

    return create_obstacle(
        OBSTACLE_ROTATING_BAR,

        z=z,

        angle=angle,

        safe_width=(
            MIN_BAR_GAP
        ),

        rotation_speed=(
            rotation_speed
        ),

        primary_colour=ORANGE,

        secondary_colour=YELLOW,
    )


def make_rotating_cross(
    z: float,
    *,
    angle: float = 0.0,
    rotation_speed: float = 34.0,
) -> TunnelObstacle:

    return create_obstacle(
        OBSTACLE_ROTATING_CROSS,

        z=z,

        angle=angle,

        safe_width=70.0,

        rotation_speed=(
            rotation_speed
        ),

        primary_colour=RED,

        secondary_colour=ORANGE,
    )


def make_spinner(
    z: float,
    *,
    angle: float = 0.0,
    rotation_speed: float = 58.0,
) -> TunnelObstacle:

    return create_obstacle(
        OBSTACLE_SPINNER,

        z=z,

        angle=angle,

        safe_width=72.0,

        rotation_speed=(
            rotation_speed
        ),

        primary_colour=PINK,

        secondary_colour=CYAN,
    )


def make_moving_gap(
    z: float,
    *,
    angle: float,
    safe_width: float,
    movement_amount: float = 70.0,
    movement_speed: float = 0.9,
) -> TunnelObstacle:

    return create_obstacle(
        OBSTACLE_MOVING_GAP,

        z=z,

        angle=angle,

        safe_width=max(
            62.0,
            safe_width,
        ),

        movement_amount=(
            movement_amount
        ),

        movement_speed=(
            movement_speed
        ),

        primary_colour=RED,

        secondary_colour=ORANGE,
    )


def make_closing_wall(
    z: float,
    *,
    angle: float,
    safe_width: float = 100.0,
    movement_speed: float = 1.0,
) -> TunnelObstacle:

    return create_obstacle(
        OBSTACLE_CLOSING_WALL,

        z=z,

        angle=angle,

        safe_width=max(
            72.0,
            safe_width,
        ),

        movement_speed=(
            movement_speed
        ),

        primary_colour=ORANGE,

        secondary_colour=RED,
    )


def make_blades(
    z: float,
    *,
    count: int,
    angle: float = 0.0,
    rotation_speed: float = 48.0,
) -> TunnelObstacle:

    obstacle_type = (
        OBSTACLE_BLADE

        if count <= 1

        else OBSTACLE_DOUBLE_BLADE

        if count == 2

        else OBSTACLE_TRIPLE_BLADE
    )

    return create_obstacle(
        obstacle_type,

        z=z,

        angle=angle,

        safe_width=(
            MIN_PLAYABLE_GAP
        ),

        rotation_speed=(
            rotation_speed
        ),

        primary_colour=RED,

        secondary_colour=YELLOW,
    )


def make_finish(
    z: float,
) -> TunnelObstacle:

    return create_obstacle(
        OBSTACLE_FINISH,

        z=z,

        angle=0.0,

        safe_width=360.0,

        primary_colour=CYAN,

        secondary_colour=WHITE,
    )


# ============================================================
# OBSTACLE MANAGER
# ============================================================

class ObstacleManager:
    def __init__(
        self,
    ):
        self.obstacles: list[
            TunnelObstacle
        ] = []

        self.total_passed = 0

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:
        self.obstacles.clear()

        self.total_passed = 0

    # ========================================================
    # ADD
    # ========================================================

    def add(
        self,
        obstacle: TunnelObstacle,
    ) -> None:
        self.obstacles.append(
            obstacle
        )

        self.obstacles.sort(
            key=lambda item: (
                item.z
            )
        )

    def extend(
        self,
        obstacles: list[
            TunnelObstacle
        ],
    ) -> None:
        self.obstacles.extend(
            obstacles
        )

        self.obstacles.sort(
            key=lambda item: (
                item.z
            )
        )

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        delta_time: float,
        camera_z: float,
    ) -> None:
        for obstacle in (
            self.obstacles
        ):
            obstacle.update(
                delta_time
            )

            if (
                obstacle.update_passed_state(
                    camera_z
                )
            ):
                if (
                    obstacle.obstacle_type
                    != OBSTACLE_FINISH
                ):
                    self.total_passed += 1

    # ========================================================
    # COLLISION
    # ========================================================

    def check_collision(
        self,
        camera_z: float,
        player_angle: float,
    ) -> TunnelObstacle | None:

        # Obstacles are sorted by Z, so there is no reason to
        # collision-test the entire level every frame.

        for obstacle in (
            self.obstacles
        ):
            if (
                obstacle.state.passed

                or not obstacle.enabled
            ):
                continue

            distance = (
                obstacle.z
                - camera_z
            )

            if (
                distance
                > 3.0
            ):
                break

            if (
                distance
                < -3.0
            ):
                continue

            if (
                obstacle.check_collision(
                    camera_z,
                    player_angle,
                )
            ):
                return obstacle

        return None

    # ========================================================
    # FINISH
    # ========================================================

    def reached_finish(
        self,
        camera_z: float,
    ) -> bool:

        for obstacle in reversed(
            self.obstacles
        ):
            if (
                obstacle.obstacle_type
                == OBSTACLE_FINISH
            ):
                return (
                    camera_z
                    >= obstacle.z
                )

        return False

    # ========================================================
    # VISIBLE
    # ========================================================

    def visible_obstacles(
        self,
        camera_z: float,
        visible_distance: float,
    ) -> list[
        TunnelObstacle
    ]:

        result: list[
            TunnelObstacle
        ] = []

        maximum_z = (
            camera_z
            + visible_distance
        )

        for obstacle in (
            self.obstacles
        ):
            if (
                obstacle.z
                < camera_z
                - 2.0
            ):
                continue

            if (
                obstacle.z
                > maximum_z
            ):
                break

            if obstacle.enabled:
                result.append(
                    obstacle
                )

        return result

    # ========================================================
    # MESHES
    # ========================================================

    def build_visible_meshes(
        self,
        camera_z: float,
        visible_distance: float,
    ) -> list[
        Mesh3D
    ]:

        meshes: list[
            Mesh3D
        ] = []

        for obstacle in (
            self.visible_obstacles(
                camera_z,
                visible_distance,
            )
        ):
            meshes.extend(
                obstacle.build_meshes()
            )

        return meshes

    # ========================================================
    # ENDLESS CLEANUP
    # ========================================================

    def remove_behind(
        self,
        camera_z: float,
        *,
        margin: float = 30.0,
    ) -> None:

        self.obstacles = [
            obstacle

            for obstacle
            in self.obstacles

            if (
                obstacle.z
                >= camera_z
                - margin
            )
        ]

    # ========================================================
    # NEXT OBSTACLE
    # ========================================================

    def next_obstacle(
        self,
        camera_z: float,
    ) -> TunnelObstacle | None:

        for obstacle in (
            self.obstacles
        ):
            if (
                obstacle.enabled

                and not obstacle.state.passed

                and obstacle.z
                >= camera_z
            ):
                return obstacle

        return None


# ============================================================
# ENDLESS RANDOM OBSTACLE
# ============================================================

def create_random_endless_obstacle(
    *,
    z: float,
    difficulty: float,
    previous_angle: float | None = None,
    rng: random.Random | None = None,
) -> TunnelObstacle:

    if rng is None:
        rng = random.Random()

    difficulty = max(
        0.0,
        difficulty,
    )

    if previous_angle is None:
        angle = rng.uniform(
            0.0,
            360.0,
        )

    else:
        maximum_change = clamp(
            70.0
            + difficulty
            * 7.0,

            70.0,

            145.0,
        )

        angle = normalize_degrees(
            previous_angle
            + rng.uniform(
                -maximum_change,
                maximum_change,
            )
        )

    safe_width = clamp(
        110.0
        - difficulty
        * 4.0,

        56.0,

        110.0,
    )

    choices = [
        OBSTACLE_GAP_WALL,
        OBSTACLE_GAP_WALL,
        OBSTACLE_GAP_WALL,
    ]

    if (
        difficulty
        >= 0.8
    ):
        choices.extend(
            [
                OBSTACLE_ROTATING_BAR,
                OBSTACLE_TRIANGLE,
            ]
        )

    if (
        difficulty
        >= 1.8
    ):
        choices.extend(
            [
                OBSTACLE_ROTATING_CROSS,
                OBSTACLE_MOVING_GAP,
                OBSTACLE_DOUBLE_TRIANGLE,
            ]
        )

    if (
        difficulty
        >= 3.0
    ):
        choices.extend(
            [
                OBSTACLE_SPINNER,
                OBSTACLE_DOUBLE_BLADE,
                OBSTACLE_CLOSING_WALL,
            ]
        )

    if (
        difficulty
        >= 4.8
    ):
        choices.extend(
            [
                OBSTACLE_TRIPLE_BLADE,
                OBSTACLE_ROTATING_WEDGE,
            ]
        )

    obstacle_type = (
        rng.choice(
            choices
        )
    )

    rotation_speed = 0.0

    movement_speed = 0.0

    movement_amount = 0.0

    if obstacle_type in (
        OBSTACLE_ROTATING_BAR,
        OBSTACLE_ROTATING_CROSS,
        OBSTACLE_SPINNER,
        OBSTACLE_DOUBLE_BLADE,
        OBSTACLE_TRIPLE_BLADE,
        OBSTACLE_ROTATING_WEDGE,
    ):

        rotation_speed = (
            rng.choice(
                (
                    -1.0,
                    1.0,
                )
            )

            * clamp(
                28.0
                + difficulty
                * 6.0,

                28.0,

                82.0,
            )
        )

    if (
        obstacle_type
        == OBSTACLE_MOVING_GAP
    ):

        movement_speed = clamp(
            0.65
            + difficulty
            * 0.055,

            0.65,

            1.35,
        )

        movement_amount = clamp(
            48.0
            + difficulty
            * 3.2,

            48.0,

            88.0,
        )

    if (
        obstacle_type
        == OBSTACLE_CLOSING_WALL
    ):

        movement_speed = clamp(
            0.7
            + difficulty
            * 0.05,

            0.7,

            1.3,
        )

    return create_obstacle(
        obstacle_type,

        z=z,

        angle=angle,

        safe_width=safe_width,

        rotation_speed=(
            rotation_speed
        ),

        movement_speed=(
            movement_speed
        ),

        movement_amount=(
            movement_amount
        ),

        phase=rng.uniform(
            0.0,
            math.tau,
        ),

        thickness=0.8,

        primary_colour=(
            rng.choice(
                (
                    RED,
                    ORANGE,
                    PINK,
                )
            )
        ),

        secondary_colour=(
            rng.choice(
                (
                    ORANGE,
                    YELLOW,
                    CYAN,
                )
            )
        ),
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_obstacle_system(
) -> None:

    wall = create_obstacle(
        OBSTACLE_GAP_WALL,

        z=100.0,

        angle=0.0,

        safe_width=90.0,
    )

    if not (
        wall.player_is_safe(
            0.0
        )
    ):
        raise ValueError(
            "Gap-wall safe-zone validation failed."
        )

    if (
        wall.player_is_safe(
            180.0
        )
    ):
        raise ValueError(
            "Gap-wall collision validation failed."
        )

    bar = create_obstacle(
        OBSTACLE_ROTATING_BAR,

        z=100.0,

        angle=0.0,

        rotation_speed=0.0,
    )

    # Horizontal bar:
    # bottom/top safe.
    # left/right blocked.

    if not (
        bar.player_is_safe(
            0.0
        )
    ):
        raise ValueError(
            "Rotating-bar collision does not match visible geometry."
        )

    if (
        bar.player_is_safe(
            90.0
        )
    ):
        raise ValueError(
            "Rotating-bar blocked side is incorrectly safe."
        )

    spinner = create_obstacle(
        OBSTACLE_SPINNER,

        z=100.0,

        angle=0.0,

        rotation_speed=0.0,
    )

    if not (
        spinner.player_is_safe(
            45.0
        )
    ):
        raise ValueError(
            "Spinner should have a usable visible opening."
        )

    finish = make_finish(
        500.0
    )

    if not (
        finish.player_is_safe(
            180.0
        )
    ):
        raise ValueError(
            "Finish must always be safe."
        )

    if not (
        wall.build_meshes()
    ):
        raise ValueError(
            "Obstacle mesh generation failed."
        )


validate_obstacle_system()