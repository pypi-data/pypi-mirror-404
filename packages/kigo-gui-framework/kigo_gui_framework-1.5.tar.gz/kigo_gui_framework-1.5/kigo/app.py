
# kigo/app.py
from __future__ import annotations

import sys
import math
import random
from typing import List, Dict, Any, Tuple

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt


class _PhysicsMount(QFrame):
    """
    A thin container that holds one child QWidget and lets us apply per-frame
    pixel offsets (dx, dy) without fighting the outer layout.
    """
    def __init__(self, child_widget, pad_x: int = 24, pad_y: int = 24, parent=None):
        super().__init__(parent)
        self.setObjectName("_kigo_physics_mount")
        self.setStyleSheet("QFrame#_kigo_physics_mount { background: transparent; border: none; }")
        # absolute positioning of child inside the mount
        self.setLayout(None)

        # unwrap Kigo widget wrapper if present
        self.child = getattr(child_widget, "qt_widget", child_widget)
        self.child.setParent(self)

        hint = self.child.sizeHint()
        self._pad_x = max(0, int(pad_x))
        self._pad_y = max(0, int(pad_y))
        self._base_x = self._pad_x
        self._base_y = self._pad_y

        self.resize(hint.width() + 2 * self._pad_x, hint.height() + 2 * self._pad_y)
        self.child.resize(hint)
        self.child.move(self._base_x, self._base_y)

    def update_offset(self, dx_px: int, dy_px: int):
        """Move the child within the mount by clamped offsets."""
        dx_px = max(-self._pad_x, min(self._pad_x, int(dx_px)))
        dy_px = max(-self._pad_y, min(self._pad_y, int(dy_px)))
        self.child.move(self._base_x + dx_px, self._base_y + dy_px)


class App:
    """
    Main application window with a global Bullet-driven physics toggle and
    per-widget effects: 'spring', 'bounce', 'fall', 'gravity', 'move'.

    - physics="Yes"|True  → start Bullet engine; new widgets get animated
    - physics="No"|False  → no Bullet; widgets are added normally

    Use `add_widget(widget, effect="spring", **effect_params)` to assign an effect
    at add-time (only when physics is ON).
    """

    def __init__(
        self,
        title: str = "Kigo App",
        size: Tuple[int, int] = (800, 600),
        physics: str | bool = "No",
        *,
        physics_fps: int = 120,            # Bullet step rate
        pad_x_px: int = 24,                # horizontal play room per widget mount
        pad_y_px: int = 24,                # vertical play room per widget mount
        pixels_per_meter: float = 80.0,    # world→UI scale for both axes
        bullet_gui: bool = False           # True to also show Bullet GUI window
    ):
        # Single QApplication
        self.qt_app = QApplication.instance() or QApplication(sys.argv)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

        self.root = QWidget()
        self.root.setWindowTitle(title)
        self.root.resize(*size)
        self.layout = QVBoxLayout(self.root)

        # Physics config
        self.physics_enabled = self._as_bool(physics)
        self._physics_fps = max(1, int(physics_fps))
        self._px_per_m = float(pixels_per_meter)
        self._pad_x = int(pad_x_px)
        self._pad_y = int(pad_y_px)
        self._bullet_gui = bool(bullet_gui)

        # Engine & registry (one entry per animated widget)
        self._engine = None  # lazy
        # entry schema:
        # { 'mount': _PhysicsMount, 'body': int, 'origin': (x0,y0,z0),
        #   'last_pos': (x,y,z), 'effect': str, 'params': dict, 'phase': float, 'done': bool }
        self._entries: List[Dict[str, Any]] = []

        if self.physics_enabled:
            self._enable_physics_engine()

        print(f"Kigo App initialized. Version: 0.3.0 | physics={'ON' if self.physics_enabled else 'OFF'}")

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def set_physics(self, value: str | bool):
        """Globally enable/disable Bullet-driven effects for subsequently added widgets."""
        enable = self._as_bool(value)
        if enable == self.physics_enabled:
            return
        self.physics_enabled = enable
        if enable:
            self._enable_physics_engine()
            print("[Kigo] Physics: ON")
        else:
            self._disable_physics_engine()
            print("[Kigo] Physics: OFF")

    def add_widget(self, widget, *, effect: str = "bounce", **effect_params):
        """
        Add a widget to the app. If physics is ON, wrap it in a mount and attach a Bullet body
        with the chosen effect. If physics is OFF, add normally.

        effect ∈ {'spring','bounce','fall','gravity','move'}
        - spring : vertical spring-damper to a baseline (Hooke + damping)
            params: k (stiffness, N/m, default 40.0), c (damping, N·s/m, default 4.0)
        - bounce : periodic upward force for a bounce feel
            params: freq (Hz, default 0.8), force (N, default 12.0)
        - fall   : one-time drop under gravity; stops updating near rest on the floor
            params: eps (m, default 0.01), v_eps (m/s, default 0.05)
        - gravity: just gravity (no extra forces)
        - move   : lateral motion via sinusoidal force (maps x to pixels)
            params: freq (Hz, default 0.6), force (N, default 6.0), axis ('x'|'y', default 'x')
        """
        w = widget.qt_widget if hasattr(widget, "qt_widget") else widget

        if not self.physics_enabled:
            self.layout.addWidget(w)
            return

        effect = (effect or "bounce").strip().lower()
        self._validate_effect(effect)

        # Create a mount (adds play room in both axes)
        mount = _PhysicsMount(w, pad_x=self._pad_x, pad_y=self._pad_y)
        self.layout.addWidget(mount)

        # Spawn Bullet body and register entry
        body_id, origin = self._spawn_body_for_widget(effect)
        defaults = self._default_params_for(effect)
        params = {**defaults, **effect_params}
        phase = random.uniform(0.0, 2.0 * math.pi)

        self._entries.append({
            "mount": mount,
            "body": body_id,
            "origin": origin,     # (x0,y0,z0)
            "last_pos": origin,   # initialize velocity estimate
            "effect": effect,
            "params": params,
            "phase": phase,
            "done": False
        })

    def run(self):
        """Start the Qt event loop."""
        self.root.show()
        sys.exit(self.qt_app.exec())

    # ---------------------------------------------------------------------
    # Internals: engine control
    # ---------------------------------------------------------------------
    def _enable_physics_engine(self):
        if self._engine is not None:
            return
        # Lazy import to keep import-time light
        from kigo.physics import PhysicsEngine
        self._engine = PhysicsEngine(use_gui=self._bullet_gui, fps=self._physics_fps)
        self._engine.setup_scene()  # plane at z=0
        self._engine.frame_updated.connect(self._on_bullet_frame)  # type: ignore
        self._engine.toggle_simulation(True)

    def _disable_physics_engine(self):
        if self._engine is None:
            return
        try:
            self._engine.frame_updated.disconnect(self._on_bullet_frame)  # type: ignore
        except Exception:
            pass
        try:
            self._engine.toggle_simulation(False)
            self._engine.disconnect()
        except Exception:
            pass
        self._engine = None
        # Keep mounts rendered where they are; they just stop moving.

    # ---------------------------------------------------------------------
    # Internals: per-widget body & frame updates
    # ---------------------------------------------------------------------
    def _spawn_body_for_widget(self, effect: str) -> Tuple[int, Tuple[float, float, float]]:
        """
        Create a small dynamic body. Start slightly above the floor so
        'fall' and 'gravity' have visible effects; other effects use their own forces.
        """
        assert self._engine is not None
        # Start positions tailored a bit per effect
        if effect in ("fall", "gravity"):
            z0 = random.uniform(0.9, 1.4)
        else:
            z0 = random.uniform(0.6, 1.2)
        x0 = random.uniform(-0.1, 0.1)
        y0 = 0.0

        size_m = 0.10   # cube half-extent
        mass_kg = 1.0

        body_id = self._engine.spawn_object(
            shape="cube",
            position=(x0, y0, z0),
            mass=mass_kg,
            size=size_m
        )
        return body_id, (x0, y0, z0)

    def _on_bullet_frame(self):
        """
        On each Bullet step:
        - read body positions
        - apply per-effect forces/logic
        - map world offsets (x-x0, z-z0) to pixel offsets in their mounts
        """
        if self._engine is None or not self._entries:
            return

        dt = 1.0 / float(self._physics_fps)
        two_pi = 2.0 * math.pi

        # Iterate a copy so we can remove finished 'fall' entries safely
        for entry in list(self._entries):
            if entry.get("done"):
                continue

            body = entry["body"]
            x0, y0, z0 = entry["origin"]
            last_x, last_y, last_z = entry["last_pos"]
            effect = entry["effect"]
            params = entry["params"]
            phase = entry["phase"]

            # 1) Read position and estimate velocity by finite difference
            x, y, z = self._engine.get_pos(body)
            vx = (x - last_x) / dt
            vy = (y - last_y) / dt
            vz = (z - last_z) / dt
            entry["last_pos"] = (x, y, z)

            # 2) Effect-specific forces/logic
            if effect == "spring":
                # Hooke: F = -k(x - x0) - c*v  (on z axis)
                k = float(params.get("k", 40.0))
                c = float(params.get("c", 4.0))
                fz = -k * (z - z0) - c * vz
                self._engine.apply_impulse(body, vector=(0.0, 0.0, fz))

            elif effect == "bounce":
                # Periodic upward force for a bouncy feel
                freq = float(params.get("freq", 0.8))
                force = float(params.get("force", 12.0))
                phase += two_pi * freq * dt
                entry["phase"] = phase
                fz = max(0.0, force * math.sin(phase))  # upward only
                if fz > 0.0:
                    self._engine.apply_impulse(body, vector=(0.0, 0.0, fz))

            elif effect == "fall":
                # Free fall under gravity; mark done when near rest on the floor
                eps = float(params.get("eps", 0.01))      # meters
                v_eps = float(params.get("v_eps", 0.05))  # m/s
                if z <= (0.0 + eps) and abs(vz) < v_eps:
                    entry["done"] = True  # stop updating; leave mount where it is

            elif effect == "gravity":
                # Just let gravity act (no extra forces)
                pass

            elif effect == "move":
                # Lateral sinusoid; map x (or y) to horizontal pixel offset as well
                freq = float(params.get("freq", 0.6))
                force = float(params.get("force", 6.0))
                axis = (params.get("axis", "x") or "x").lower()
                phase += two_pi * freq * dt
                entry["phase"] = phase
                f = force * math.sin(phase)
                if axis == "y":
                    self._engine.apply_impulse(body, vector=(0.0, f, 0.0))
                else:
                    self._engine.apply_impulse(body, vector=(f, 0.0, 0.0))

            else:
                # Unknown effect: treat as gravity
                pass

            # 3) Map world deltas to pixel offsets & update mount
            dx_px = (x - x0) * self._px_per_m if effect == "move" else 0.0
            dy_px = (z - z0) * self._px_per_m
            entry["mount"].update_offset(int(dx_px), int(dy_px))

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    @staticmethod
    def _as_bool(value) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in ("yes", "y", "true", "1", "on")
        return bool(value)

    @staticmethod
    def _validate_effect(effect: str):
        allowed = {"spring", "bounce", "fall", "gravity", "move"}
        if effect not in allowed:
            raise ValueError(f"Unknown effect '{effect}'. Allowed: {sorted(allowed)}")

    @staticmethod
    def _default_params_for(effect: str) -> Dict[str, Any]:
        if effect == "spring":
            return {"k": 40.0, "c": 4.0}
        if effect == "bounce":
            return {"freq": 0.8, "force": 12.0}
        if effect == "fall":
            return {"eps": 0.01, "v_eps": 0.05}
        if effect == "gravity":
            return {}
        if effect == "move":
            return {"freq": 0.6, "force": 6.0, "axis": "x"}
        return {}
