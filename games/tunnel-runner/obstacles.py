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
# VERSION 0.1.5
# CENTER-HOLE + HITBOX + VALIDATOR FIX
# ============================================================


OBSTACLE_CROSS = "cross"

EPSILON = 0.000001

# ============================================================
# FAIRNESS SETTINGS
# ============================================================

MIN_PLAYABLE_GAP = 50.0

MIN_SPINNER_GAP = 66.0

MIN_BAR_GAP = 128.0

# Rotating-bar geometry.
#
# The bar is split into two arms, leaving a visible open hole in
# the middle instead of one solid stick crossing the whole screen.
BAR_CENTER_HOLE_RADIUS = (
    TUNNEL_RADIUS
    * 0.28
)

# Width of each bar arm in world units.
BAR_ARM_WIDTH = 1.0

# Extra angular forgiveness around the true visual gap.
BAR_COLLISION_FORGIVENESS = 6.0

MAX_COLLISION_PADDING = 7.0


# ============================================================
# PERFORMANCE SETTINGS
# ============================================================

# Normal walls used to use many more pieces.
# 32 is still visually smooth while being cheaper.

WALL_RENDER_SEGMENTS = 32

# Finish ring does not need 32+ pieces.

FINISH_RENDER_SEGMENTS = 24

# Obstacles beyond this distance do not need animation updates.

ANIMATION_DISTANCE = 230.0

# Collision system only needs a tiny region around the player.

COLLISION_SEARCH_DISTANCE = 2.2


# ============================================================
# HELPERS
# ============================================================

def safe_colour(
    colour: tuple[int, int, int],
    multiplier: float,
) -> tuple[int, int, int]:

    return multiply_colour(
        colour,
        multiplier,
    )


def collision_padding() -> float:

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

        usable_width = max(
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

            usable_width,
        )


# ============================================================
# OBSTACLE STATE
# ============================================================

@dataclass
class ObstacleState:
    rotation: float = 0.0

    movement_offset: float = 0.0

    animation_time: float = 0.0

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

    # Static obstacles only need their mesh generated once.

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

        if (
            abs(
                self.rotation_speed
            )
            > EPSILON
        ):

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
                math.sin(
                    self.state.animation_time
                    * self.movement_speed
                    + self.phase
                )

                * self.movement_amount
            )

    # ========================================================
    # CURRENT ANGLE
    # ========================================================

    def current_angle(
        self,
    ) -> float:

        return normalize_degrees(
            self.state.rotation
            + self.state.movement_offset
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

        padding = (
            collision_padding()
        )

        return any(
            arc.contains(
                player_angle,
                padding=padding,
            )

            for arc
            in self.safe_arcs()
        )

    # ========================================================
    # COLLISION
    # ========================================================

    def collision_active(
        self,
        camera_z: float,
    ) -> bool:

        return (
            abs(
                self.z
                - camera_z
            )
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

        return not self.player_is_safe(
            player_angle
        )

    # ========================================================
    # PASSED
    # ========================================================

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
    # VISIBILITY
    # ========================================================

    def visible(
        self,
        camera_z: float,
        visible_distance: float,
    ) -> bool:

        distance = (
            self.z
            - camera_z
        )

        return (
            -2.0
            <= distance
            <= visible_distance
        )

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
# WALL
# ============================================================

class WallObstacle(
    TunnelObstacle
):
    pass


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

        width = (
            minimum
            + (
                maximum
                - minimum
            )
            * pulse
        )

        return [
            SafeArc(
                self.current_angle(),
                width,
            )
        ]


# ============================================================
# SINGLE ROTATING BAR
# ============================================================

class SingleBarObstacle(
    TunnelObstacle
):

    def safe_arcs(
        self,
    ) -> list[SafeArc]:
        """
        Return the two playable arcs beside the rotating bar.

        IMPORTANT:
        The physical bar lies on the obstacle's current angle and
        the opposite angle. Therefore those two angles are HAZARDS,
        not safe areas.

        The safe areas are centered 90 degrees away from the bar,
        which matches the visible geometry.
        """

        bar_angle = (
            self.current_angle()
        )

        # The old collision used safe arcs centered directly on
        # bar_angle and bar_angle + 180. That made the hitbox almost
        # exactly backwards: the visible stick looked dangerous where
        # collision said it was safe.
        #
        # Keep a generous opening on each side of the bar.
        safe_width = clamp(
            max(
                MIN_BAR_GAP,
                self.safe_width,
            )
            + BAR_COLLISION_FORGIVENESS,
            MIN_BAR_GAP,
            168.0,
        )

        return [
            SafeArc(
                normalize_degrees(
                    bar_angle
                    + 90.0
                ),
                safe_width,
            ),

            SafeArc(
                normalize_degrees(
                    bar_angle
                    + 270.0
                ),
                safe_width,
            ),
        ]


# ============================================================
# CROSS / SPINNER
# ============================================================

class CrossObstacle(
    TunnelObstacle
):

    def safe_arcs(
        self,
    ) -> list[SafeArc]:

        rotation = (
            self.current_angle()
        )

        width = clamp(
            max(
                MIN_SPINNER_GAP,
                self.safe_width,
            ),

            MIN_SPINNER_GAP,

            82.0,
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

            for index
            in range(
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
                self.blade_count
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

        angle = (
            self.current_angle()
        )

        return [
            SafeArc(
                normalize_degrees(
                    angle
                    + index
                    * spacing
                    + spacing
                    / 2.0
                ),

                safe_width,
            )

            for index
            in range(
                count
            )
        ]


# ============================================================
# TRIANGLE
# ============================================================

class TriangleObstacle(
    TunnelObstacle
):

    triangle_count: int = 1

    def safe_arcs(
        self,
    ) -> list[SafeArc]:

        rotation = (
            self.current_angle()
        )

        if (
            self.triangle_count
            <= 1
        ):

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

                84.0,
            ),

            SafeArc(
                normalize_degrees(
                    rotation
                    + 270.0
                ),

                84.0,
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
) -> list[Face3D]:

    faces: list[
        Face3D
    ] = []

    segment_angle = (
        360.0
        / WALL_RENDER_SEGMENTS
    )

    for index in range(
        WALL_RENDER_SEGMENTS
    ):

        start_angle = (
            index
            * segment_angle
        )

        end_angle = (
            start_angle
            + segment_angle
        )

        middle = (
            start_angle
            + segment_angle
            / 2.0
        )

        if any(
            angle_in_arc(
                middle,
                arc.center,
                arc.width,
            )

            for arc
            in safe_arcs
        ):

            continue

        face_colour = (
            colour

            if index
            % 2
            == 0

            else secondary_colour
        )

        faces.append(
            Face3D(
                vertices=[
                    tunnel_point(
                        start_angle,
                        z,
                        radius=0.18,
                    ),

                    tunnel_point(
                        start_angle,
                        z,
                        radius=TUNNEL_RADIUS,
                    ),

                    tunnel_point(
                        end_angle,
                        z,
                        radius=TUNNEL_RADIUS,
                    ),

                    tunnel_point(
                        end_angle,
                        z,
                        radius=0.18,
                    ),
                ],

                colour=face_colour,

                # Removing dozens of outline draws makes walls
                # substantially cheaper.

                outline_colour=None,

                outline_width=0,

                double_sided=True,
            )
        )

    return faces


def create_wall_mesh(
    obstacle: TunnelObstacle,
) -> Mesh3D:

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

    arcs = (
        obstacle.safe_arcs()
    )

    front_faces = (
        create_multi_gap_wall_faces(
            z=front_z,

            safe_arcs=arcs,

            colour=(
                obstacle.primary_colour
            ),

            secondary_colour=(
                obstacle.secondary_colour
            ),
        )
    )

    back_faces = (
        create_multi_gap_wall_faces(
            z=back_z,

            safe_arcs=arcs,

            colour=safe_colour(
                obstacle.primary_colour,
                0.70,
            ),

            secondary_colour=safe_colour(
                obstacle.secondary_colour,
                0.70,
            ),
        )
    )

    return Mesh3D(
        faces=(
            front_faces
            + back_faces
        ),

        metadata={
            "obstacle_type":
                obstacle.obstacle_type,

            "z":
                obstacle.z,
        },
    )


# ============================================================
# BAR GEOMETRY
# ============================================================

def create_bar_arm_mesh(
    *,
    z: float,
    angle: float,
    direction: float,
    colour: tuple[int, int, int],
    thickness: float = 0.75,
) -> Mesh3D:
    """
    Create one half of a rotating bar.

    direction:
        +1.0 = one side of the tunnel
        -1.0 = opposite side

    Two arms are used instead of one full-width box so there is a
    real visible opening in the center.
    """

    hole_radius = clamp(
        BAR_CENTER_HOLE_RADIUS,
        0.8,
        TUNNEL_RADIUS
        * 0.55,
    )

    outer_radius = (
        TUNNEL_RADIUS
        * 1.06
    )

    arm_length = max(
        0.25,
        outer_radius
        - hole_radius,
    )

    local_center_x = (
        direction
        * (
            hole_radius
            + arm_length
            / 2.0
        )
    )

    mesh = create_box_mesh(
        center=Vec3(
            local_center_x,
            0.0,
            z,
        ),

        size=Vec3(
            arm_length,
            BAR_ARM_WIDTH,
            thickness,
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


def create_bar_meshes(
    *,
    z: float,
    angle: float,
    colour: tuple[int, int, int],
    thickness: float = 0.75,
) -> list[Mesh3D]:
    """
    Create a rotating stick with a genuine center hole.
    """

    return [
        create_bar_arm_mesh(
            z=z,
            angle=angle,
            direction=1.0,
            colour=colour,
            thickness=thickness,
        ),

        create_bar_arm_mesh(
            z=z,
            angle=angle,
            direction=-1.0,
            colour=colour,
            thickness=thickness,
        ),
    ]


def build_bar(
    obstacle: TunnelObstacle,
    *,
    double: bool = False,
) -> list[Mesh3D]:

    angle = (
        obstacle.current_angle()
    )

    meshes: list[
        Mesh3D
    ] = []

    meshes.extend(
        create_bar_meshes(
            z=obstacle.z,

            angle=angle,

            colour=(
                obstacle.primary_colour
            ),

            thickness=(
                obstacle.thickness
            ),
        )
    )

    if double:

        meshes.extend(
            create_bar_meshes(
                z=obstacle.z,

                angle=(
                    angle
                    + 90.0
                ),

                colour=(
                    obstacle.secondary_colour
                ),

                thickness=(
                    obstacle.thickness
                ),
            )
        )

    return meshes


# ============================================================
# BLADE GEOMETRY
# ============================================================

def build_blades(
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

        half_width = min(
            16.0,

            spacing
            * 0.20,
        )

        faces.append(
            Face3D(
                vertices=[
                    Vec3(
                        0.0,
                        0.0,
                        obstacle.z,
                    ),

                    tunnel_point(
                        angle
                        - half_width,

                        obstacle.z,

                        radius=TUNNEL_RADIUS,
                    ),

                    tunnel_point(
                        angle
                        + half_width,

                        obstacle.z,

                        radius=TUNNEL_RADIUS,
                    ),
                ],

                colour=(
                    obstacle.primary_colour

                    if index
                    % 2
                    == 0

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

                    if index
                    % 2
                    == 0

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
                            angle - 55.0,

                            obstacle.z,

                            radius=TUNNEL_RADIUS,
                        ),

                        tunnel_point(
                            angle + 55.0,

                            obstacle.z,

                            radius=TUNNEL_RADIUS,
                        ),
                    ],

                    colour=(
                        obstacle.primary_colour
                    ),

                    outline_colour=WHITE,

                    outline_width=1,

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

    center = tunnel_point(
        obstacle.current_angle(),

        obstacle.z,

        radius=(
            TUNNEL_RADIUS
            * 0.45
        ),
    )

    size = 2.3

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

                    outline_width=1,

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

    step = (
        360.0
        / FINISH_RENDER_SEGMENTS
    )

    for index in range(
        FINISH_RENDER_SEGMENTS
    ):

        start_angle = (
            index
            * step
        )

        end_angle = (
            start_angle
            + step
        )

        faces.append(
            Face3D(
                vertices=[
                    tunnel_point(
                        start_angle,

                        obstacle.z,

                        radius=(
                            TUNNEL_RADIUS
                            * 0.82
                        ),
                    ),

                    tunnel_point(
                        start_angle,

                        obstacle.z,

                        radius=(
                            TUNNEL_RADIUS
                            * 0.96
                        ),
                    ),

                    tunnel_point(
                        end_angle,

                        obstacle.z,

                        radius=(
                            TUNNEL_RADIUS
                            * 0.96
                        ),
                    ),

                    tunnel_point(
                        end_angle,

                        obstacle.z,

                        radius=(
                            TUNNEL_RADIUS
                            * 0.82
                        ),
                    ),
                ],

                colour=(
                    CYAN

                    if index
                    % 2
                    == 0

                    else WHITE
                ),

                outline_colour=None,

                outline_width=0,

                double_sided=True,
            )
        )

    return [
        Mesh3D(
            faces=faces
        )
    ]


# ============================================================
# MESH ROUTER
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
            create_wall_mesh(
                obstacle
            )
        ]

    if (
        obstacle_type
        == OBSTACLE_ROTATING_BAR
    ):

        return build_bar(
            obstacle,

            double=False,
        )

    if obstacle_type in (
        OBSTACLE_DOUBLE_BAR,
        OBSTACLE_CROSS,
        OBSTACLE_ROTATING_CROSS,
        OBSTACLE_SPINNER,
    ):

        return build_bar(
            obstacle,

            double=True,
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

        rotation_speed=rotation_speed,

        movement_speed=movement_speed,

        movement_amount=movement_amount,

        phase=phase,

        thickness=thickness,

        primary_colour=primary_colour,

        secondary_colour=secondary_colour,

        metadata=(
            metadata

            if metadata
            is not None

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

        result = BladeObstacle(
            **common
        )

        if (
            obstacle_type
            == OBSTACLE_BLADE
        ):

            result.blade_count = 1

        elif (
            obstacle_type
            == OBSTACLE_DOUBLE_BLADE
        ):

            result.blade_count = 2

        else:

            result.blade_count = 3

        return result

    if obstacle_type in (
        OBSTACLE_TRIANGLE,
        OBSTACLE_DOUBLE_TRIANGLE,
        OBSTACLE_WEDGE,
        OBSTACLE_ROTATING_WEDGE,
        OBSTACLE_DIAMOND,
    ):

        result = TriangleObstacle(
            **common
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

        secondary_colour=safe_colour(
            colour,
            0.72,
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

        safe_width=MIN_BAR_GAP,

        rotation_speed=rotation_speed,

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

        rotation_speed=rotation_speed,

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

        rotation_speed=rotation_speed,

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

        movement_amount=movement_amount,

        movement_speed=movement_speed,

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

        movement_speed=movement_speed,

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

    if count <= 1:

        obstacle_type = (
            OBSTACLE_BLADE
        )

    elif count == 2:

        obstacle_type = (
            OBSTACLE_DOUBLE_BLADE
        )

    else:

        obstacle_type = (
            OBSTACLE_TRIPLE_BLADE
        )

    return create_obstacle(
        obstacle_type,

        z=z,

        angle=angle,

        safe_width=MIN_PLAYABLE_GAP,

        rotation_speed=rotation_speed,

        primary_colour=RED,

        secondary_colour=YELLOW,
    )


def make_finish(
    z: float,
) -> TunnelObstacle:

    return create_obstacle(
        OBSTACLE_FINISH,

        z=z,

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
            key=lambda item:
            item.z
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
            key=lambda item:
            item.z
        )

    # ========================================================
    # OPTIMIZED UPDATE
    # ========================================================

    def update(
        self,
        delta_time: float,
        camera_z: float,
    ) -> None:

        maximum_z = (
            camera_z
            + ANIMATION_DISTANCE
        )

        for obstacle in (
            self.obstacles
        ):

            if obstacle.state.passed:
                continue

            # -----------------------------------------------
            # ALREADY BEHIND PLAYER
            # -----------------------------------------------

            if (
                obstacle.z
                < camera_z
                - 4.0
            ):

                if obstacle.update_passed_state(
                    camera_z
                ):

                    if (
                        obstacle.obstacle_type
                        != OBSTACLE_FINISH
                    ):

                        self.total_passed += 1

                continue

            # -----------------------------------------------
            # TOO FAR AWAY
            # -----------------------------------------------
            #
            # The list is sorted by Z.
            #
            # Therefore everything after this obstacle is
            # even farther away.
            #

            if (
                obstacle.z
                > maximum_z
            ):

                break

            # -----------------------------------------------
            # ONLY UPDATE MOVING OBSTACLES
            # -----------------------------------------------

            if obstacle.animated:

                obstacle.update(
                    delta_time
                )

            if obstacle.update_passed_state(
                camera_z
            ):

                if (
                    obstacle.obstacle_type
                    != OBSTACLE_FINISH
                ):

                    self.total_passed += 1

    # ========================================================
    # OPTIMIZED COLLISION
    # ========================================================

    def check_collision(
        self,
        camera_z: float,
        player_angle: float,
    ) -> TunnelObstacle | None:

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

            # Sorted list.
            #
            # Nothing after this can collide yet.

            if (
                distance
                > COLLISION_SEARCH_DISTANCE
            ):

                break

            if (
                distance
                < -COLLISION_SEARCH_DISTANCE
            ):

                continue

            if obstacle.check_collision(
                camera_z,
                player_angle,
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
    # VISIBLE OBSTACLES
    # ========================================================

    def visible_obstacles(
        self,
        camera_z: float,
        visible_distance: float,
    ) -> list[
        TunnelObstacle
    ]:

        maximum_z = (
            camera_z
            + visible_distance
        )

        visible: list[
            TunnelObstacle
        ] = []

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

                visible.append(
                    obstacle
                )

        return visible

    # ========================================================
    # BUILD VISIBLE MESHES
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
        margin: float = 25.0,
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
# ENDLESS OBSTACLE GENERATOR
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

    # ========================================================
    # ANGLE
    # ========================================================

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

    # ========================================================
    # SAFE GAP
    # ========================================================

    safe_width = clamp(
        110.0
        - difficulty
        * 4.0,

        56.0,

        110.0,
    )

    # ========================================================
    # DIFFICULTY POOL
    # ========================================================

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
        >= 5.0
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

    # ========================================================
    # ROTATION
    # ========================================================

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

    # ========================================================
    # MOVING GAP
    # ========================================================

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

    # ========================================================
    # CLOSING WALL
    # ========================================================

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

    # ========================================================
    # CREATE
    # ========================================================

    return create_obstacle(
        obstacle_type,

        z=z,

        angle=angle,

        safe_width=safe_width,

        rotation_speed=rotation_speed,

        movement_speed=movement_speed,

        movement_amount=movement_amount,

        phase=rng.uniform(
            0.0,
            math.tau,
        ),

        thickness=0.8,

        primary_colour=rng.choice(
            (
                RED,
                ORANGE,
                PINK,
            )
        ),

        secondary_colour=rng.choice(
            (
                ORANGE,
                YELLOW,
                CYAN,
            )
        ),
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_obstacle_system(
) -> None:

    # ========================================================
    # GAP WALL
    # ========================================================

    wall = create_obstacle(
        OBSTACLE_GAP_WALL,

        z=100.0,

        angle=0.0,

        safe_width=90.0,
    )

    if not wall.player_is_safe(
        0.0
    ):

        raise ValueError(
            "Gap wall safe-zone validation failed."
        )

    if wall.player_is_safe(
        180.0
    ):

        raise ValueError(
            "Gap wall collision validation failed."
        )

    # ========================================================
    # ROTATING BAR
    # ========================================================

    bar = create_obstacle(
        OBSTACLE_ROTATING_BAR,

        z=100.0,

        angle=0.0,

        rotation_speed=0.0,
    )

    # The bar itself lies along 0 / 180 degrees when angle=0.
    # Therefore those directions are hazards.
    #
    # The open playable areas are perpendicular to the bar at
    # 90 / 270 degrees.
    if bar.player_is_safe(
        0.0
    ):

        raise ValueError(
            "Rotating bar collision validation failed."
        )

    if not bar.player_is_safe(
        90.0
    ):

        raise ValueError(
            "Rotating bar safe opening validation failed."
        )

    if bar.player_is_safe(
        180.0
    ):

        raise ValueError(
            "Rotating bar opposite collision validation failed."
        )

    if not bar.player_is_safe(
        270.0
    ):

        raise ValueError(
            "Rotating bar opposite safe opening validation failed."
        )

    # ========================================================
    # SPINNER
    # ========================================================

    spinner = create_obstacle(
        OBSTACLE_SPINNER,

        z=100.0,

        angle=0.0,

        rotation_speed=0.0,
    )

    if not spinner.player_is_safe(
        45.0
    ):

        raise ValueError(
            "Spinner opening validation failed."
        )

    # ========================================================
    # FINISH
    # ========================================================

    finish = make_finish(
        500.0
    )

    if not finish.player_is_safe(
        180.0
    ):

        raise ValueError(
            "Finish must always be safe."
        )

    # ========================================================
    # MESH
    # ========================================================

    if not wall.build_meshes():

        raise ValueError(
            "Obstacle mesh generation failed."
        )


validate_obstacle_system()