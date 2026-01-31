Kigo Physics 2D v1.5

# kigo/physics.py

import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pybullet as p
import pybullet_data
from PyQt6.QtCore import QTimer, pyqtSignal, QObject


# ==========================================================
# 3D Physics (PyBullet) - Existing Engine (unchanged behavior)
# ==========================================================

class PhysicsEngine(QObject):
    """
    Kigo Physics Engine v1.1.0
    A high-level wrapper for PyBullet that integrates seamlessly with the
    PyQt6 event loop. This allows Kigo UI elements to control 3D simulations.
    """

    # Signal emitted after every physics step to sync with Kigo UI updates
    frame_updated = pyqtSignal()

    def __init__(self, use_gui=True):
        super().__init__()
        # Initialize PyBullet
        # p.GUI opens the 3D visualizer; p.DIRECT runs headless for AI training
        self.mode = p.GUI if use_gui else p.DIRECT
        try:
            self.client = p.connect(self.mode)
        except Exception as e:
            print(f"Physics connection failed: {e}. Falling back to DIRECT mode.")
            self.client = p.connect(p.DIRECT)

        # Load standard PyBullet assets path
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.81)

        # Simulation Timer to sync with Kigo UI (defaulting to 60 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self._step)
        self.is_running = False

    def setup_scene(self):
        """Clears the world and loads a standard ground plane."""
        p.resetSimulation()
        p.setGravity(0, 0, -9.81)
        return p.loadURDF("plane.urdf")

    def spawn_object(self, shape="cube", position=[0, 0, 2], mass=1.0, color=[0.1, 0.7, 0.2, 1]):
        """
        Spawns a physics-enabled object into the Kigo-Simulation world.
        Returns the unique ID of the created object.
        """
        if shape == "cube":
            geom = p.GEOM_BOX
            dims = [0.5, 0.5, 0.5]
            visual_id = p.createVisualShape(geom, halfExtents=dims, rgbaColor=color)
            collision_id = p.createCollisionShape(geom, halfExtents=dims)

        elif shape == "sphere":
            # NOTE: For spheres, Bullet expects radius. Keeping behavior close to original.
            geom = p.GEOM_SPHERE
            radius = 0.5
            visual_id = p.createVisualShape(geom, radius=radius, rgbaColor=color)
            collision_id = p.createCollisionShape(geom, radius=radius)

        else:
            geom = p.GEOM_BOX
            dims = [0.5, 0.5, 0.5]
            visual_id = p.createVisualShape(geom, halfExtents=dims, rgbaColor=color)
            collision_id = p.createCollisionShape(geom, halfExtents=dims)

        return p.createMultiBody(
            baseMass=mass,
            baseCollisionShapeIndex=collision_id,
            baseVisualShapeIndex=visual_id,
            basePosition=position
        )

    def toggle_simulation(self, start=True, fps=60):
        """Starts or stops the physics engine clock."""
        if start:
            self.timer.start(int(1000 / fps))
            self.is_running = True
        else:
            self.timer.stop()
            self.is_running = False

    def _step(self):
        """The core tick of the simulation. Notifies the UI loop on every step."""
        p.stepSimulation()
        self.frame_updated.emit()

    def apply_impulse(self, obj_id, vector=[0, 0, 100]):
        """Apply a sudden force to an object (e.g., a 'Jump' button)."""
        p.applyExternalForce(obj_id, -1, vector, [0, 0, 0], p.WORLD_FRAME)

    def get_pos(self, obj_id):
        """Returns the [x, y, z] position for display in Kigo widgets."""
        pos, _ = p.getBasePositionAndOrientation(obj_id)
        return list(pos)

    def disconnect(self):
        """Cleanly shuts down the physics server."""
        if self.is_running:
            self.timer.stop()
        p.disconnect()


# ==========================================================
# 2D UI Physics (Kigo v1.4) - Float, Snap, Orbit, Interaction
# ==========================================================

Vec2 = Tuple[float, float]


@dataclass
class UIBody:
    """
    Lightweight 2D physics body for Kigo widgets.
    Coordinates are in pixels. Designed for float/snap/orbit/drag.
    """
    x: float
    y: float
    w: float = 80.0
    h: float = 40.0

    vx: float = 0.0
    vy: float = 0.0

    fx: float = 0.0
    fy: float = 0.0

    mass: float = 1.0
    damping: float = 0.92  # 0.90–0.97 recommended
    gravity: Vec2 = (0.0, 0.0)

    # "dynamic": physics updates pos/vel
    # "kinematic": your code sets x/y (physics doesn't integrate)
    # "static": never moves
    mode: str = "dynamic"

    user_data: dict = field(default_factory=dict)

    def apply_force(self, fx: float, fy: float):
        self.fx += fx
        self.fy += fy

    def clear_forces(self):
        self.fx = 0.0
        self.fy = 0.0

    def set_pos(self, x: float, y: float):
        self.x, self.y = x, y

    @property
    def center(self) -> Vec2:
        return (self.x + self.w / 2.0, self.y + self.h / 2.0)


class Constraint:
    def solve(self, world: "UIPhysicsWorld", body: UIBody, dt: float) -> None:
        """Apply positional correction and/or forces."""
        return


@dataclass
class BoundsConstraint(Constraint):
    """
    Keeps a body inside a rectangle (window/container).
    bounce=0 -> clamp; bounce>0 -> bounce reflection.
    """
    left: float
    top: float
    right: float
    bottom: float
    bounce: float = 0.0  # 0 clamp, 0.2–0.5 bounce

    def solve(self, world: "UIPhysicsWorld", body: UIBody, dt: float) -> None:
        if body.mode != "dynamic":
            return

        # X bounds
        if body.x < self.left:
            body.x = self.left
            body.vx = -body.vx * self.bounce
        elif body.x + body.w > self.right:
            body.x = self.right - body.w
            body.vx = -body.vx * self.bounce

        # Y bounds
        if body.y < self.top:
            body.y = self.top
            body.vy = -body.vy * self.bounce
        elif body.y + body.h > self.bottom:
            body.y = self.bottom - body.h
            body.vy = -body.vy * self.bounce


@dataclass
class SnapConstraint(Constraint):
    """
    Snaps a body to a grid and/or to container edges/centers.
    """
    grid: Optional[int] = None
    threshold: float = 10.0

    snap_to_edges: bool = True
    snap_to_centers: bool = True

    hard_snap: bool = True          # True: position correction; False: magnet force
    magnet_strength: float = 120.0  # used only if hard_snap=False
    velocity_dampen: float = 0.25   # damp velocity on snapped axis

    def solve(self, world: "UIPhysicsWorld", body: UIBody, dt: float) -> None:
        if body.mode != "dynamic":
            return

        best_dx = None
        best_dy = None

        # --- Grid snap
        if self.grid and self.grid > 1:
            gx = round(body.x / self.grid) * self.grid
            gy = round(body.y / self.grid) * self.grid
            dx = gx - body.x
            dy = gy - body.y

            if abs(dx) < self.threshold:
                best_dx = dx if (best_dx is None or abs(dx) < abs(best_dx)) else best_dx
            if abs(dy) < self.threshold:
                best_dy = dy if (best_dy is None or abs(dy) < abs(best_dy)) else best_dy

        # --- Container snap
        if world.bounds and (self.snap_to_edges or self.snap_to_centers):
            left, top, right, bottom = world.bounds

            if self.snap_to_edges:
                # Left edge
                dx = left - body.x
                if abs(dx) < self.threshold:
                    best_dx = dx if (best_dx is None or abs(dx) < abs(best_dx)) else best_dx

                # Right edge
                dx = (right - body.w) - body.x
                if abs(dx) < self.threshold:
                    best_dx = dx if (best_dx is None or abs(dx) < abs(best_dx)) else best_dx

                # Top edge
                dy = top - body.y
                if abs(dy) < self.threshold:
                    best_dy = dy if (best_dy is None or abs(dy) < abs(best_dy)) else best_dy

                # Bottom edge
                dy = (bottom - body.h) - body.y
                if abs(dy) < self.threshold:
                    best_dy = dy if (best_dy is None or abs(dy) < abs(best_dy)) else best_dy

            if self.snap_to_centers:
                cx_target = (left + right - body.w) / 2.0
                cy_target = (top + bottom - body.h) / 2.0
                dx = cx_target - body.x
                dy = cy_target - body.y

                if abs(dx) < self.threshold:
                    best_dx = dx if (best_dx is None or abs(dx) < abs(best_dx)) else best_dx
                if abs(dy) < self.threshold:
                    best_dy = dy if (best_dy is None or abs(dy) < abs(best_dy)) else best_dy

        # --- Apply
        if best_dx is not None or best_dy is not None:
            if self.hard_snap:
                if best_dx is not None:
                    body.x += best_dx
                    body.vx *= self.velocity_dampen
                if best_dy is not None:
                    body.y += best_dy
                    body.vy *= self.velocity_dampen
            else:
                if best_dx is not None:
                    body.apply_force(best_dx * self.magnet_strength, 0.0)
                if best_dy is not None:
                    body.apply_force(0.0, best_dy * self.magnet_strength)


@dataclass
class OrbitConstraint(Constraint):
    """
    Orbits 'body' around a target body.
    - soft=True: applies spring force toward orbit point (feels physical)
    - soft=False: hard lock to orbit point (pure animation)
    """
    target: UIBody
    radius: float = 120.0
    angular_velocity: float = 1.2  # radians/sec
    angle: float = 0.0

    ellipse: Optional[Tuple[float, float]] = None  # (rx, ry)
    soft: bool = True
    k: float = 80.0  # spring strength if soft=True

    def solve(self, world: "UIPhysicsWorld", body: UIBody, dt: float) -> None:
        if body.mode == "static":
            return

        self.angle += self.angular_velocity * dt

        rx, ry = (self.radius, self.radius) if self.ellipse is None else self.ellipse

        # Orbit around target's center, but position body by its top-left (so it looks centered)
        tx, ty = self.target.center
        desired_x = tx + math.cos(self.angle) * rx - body.w / 2.0
        desired_y = ty + math.sin(self.angle) * ry - body.h / 2.0

        if self.soft and body.mode == "dynamic":
            dx = desired_x - body.x
            dy = desired_y - body.y
            body.apply_force(dx * self.k, dy * self.k)
        else:
            body.x = desired_x
            body.y = desired_y
            body.vx = 0.0
            body.vy = 0.0


class DragController:
    """
    Spring-drag + throw. Call pointer_down/move/up from your widget event system.
    world.step() will call apply() automatically.
    """
    def __init__(self, k: float = 90.0, c: float = 14.0, throw_scale: float = 1.0):
        self.k = k
        self.c = c
        self.throw_scale = throw_scale

        self.active: Optional[UIBody] = None
        self.grab_offset: Vec2 = (0.0, 0.0)
        self._history: List[Tuple[float, float, float]] = []  # (t, x, y)

    def pointer_down(self, body: UIBody, px: float, py: float):
        self.active = body
        self.grab_offset = (px - body.x, py - body.y)
        self._history.clear()
        self._push_hist(px, py)

    def pointer_move(self, px: float, py: float):
        if not self.active:
            return
        self._push_hist(px, py)

    def pointer_up(self):
        if not self.active:
            return
        body = self.active

        # Throw velocity from last segment
        if len(self._history) >= 2:
            t0, x0, y0 = self._history[-2]
            t1, x1, y1 = self._history[-1]
            dt = max(1e-6, t1 - t0)
            body.vx = ((x1 - x0) / dt) * self.throw_scale
            body.vy = ((y1 - y0) / dt) * self.throw_scale

        self.active = None
        self._history.clear()

    def apply(self):
        if not self.active or self.active.mode != "dynamic":
            return
        if not self._history:
            return

        body = self.active
        _, px, py = self._history[-1]
        target_x = px - self.grab_offset[0]
        target_y = py - self.grab_offset[1]

        # Spring force: F = k*(target - pos) - c*vel
        fx = (target_x - body.x) * self.k - body.vx * self.c
        fy = (target_y - body.y) * self.k - body.vy * self.c
        body.apply_force(fx, fy)

    def _push_hist(self, px: float, py: float):
        now = time.perf_counter()
        self._history.append((now, px, py))
        if len(self._history) > 6:
            self._history.pop(0)


class UIPhysicsWorld:
    """
    Manages 2D widget bodies.
    Call step(dt) from your app loop (Tkinter, PyQt, etc.).
    """
    def __init__(self):
        self.bodies: List[UIBody] = []
        self.constraints: Dict[UIBody, List[Constraint]] = {}
        self.bounds: Optional[Tuple[float, float, float, float]] = None  # (l,t,r,b)

        self.drag = DragController()
        self._bounds_constraint: Optional[BoundsConstraint] = None

    def set_bounds(self, left: float, top: float, right: float, bottom: float, bounce: float = 0.0):
        self.bounds = (left, top, right, bottom)
        self._bounds_constraint = BoundsConstraint(left, top, right, bottom, bounce=bounce)

    def add_body(self, body: UIBody) -> UIBody:
        if body not in self.bodies:
            self.bodies.append(body)
            self.constraints[body] = []
        return body

    def add_constraint(self, body: UIBody, constraint: Constraint):
        self.add_body(body)
        self.constraints[body].append(constraint)

    def step(self, dt: float):
        # Clamp dt to avoid huge physics jumps
        dt = min(max(dt, 1e-6), 1.0 / 30.0)

        # Apply interaction drag forces
        self.drag.apply()

        # Integrate bodies
        for b in self.bodies:
            if b.mode != "dynamic":
                b.clear_forces()
                continue

            # gravity (as force)
            gx, gy = b.gravity
            b.apply_force(gx * b.mass, gy * b.mass)

            ax = b.fx / max(1e-6, b.mass)
            ay = b.fy / max(1e-6, b.mass)

            # Semi-implicit Euler
            b.vx += ax * dt
            b.vy += ay * dt

            b.vx *= b.damping
            b.vy *= b.damping

            b.x += b.vx * dt
            b.y += b.vy * dt

            b.clear_forces()

        # Solve constraints (bounds first, then per-body constraints)
        for b in self.bodies:
            if self._bounds_constraint:
                self._bounds_constraint.solve(self, b, dt)

            for c in self.constraints.get(b, []):
                c.solve(self, b, dt)


# Always remember: somewhere, somehow, a duck is watching you.

__all__ = [
    'PhysicsEngine',
    'UIPhysicsWorld', 'UIBody',
    'SnapConstraint', 'OrbitConstraint', 'BoundsConstraint',
    'DragController'
]
