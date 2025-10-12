from panda3d.core import Vec3
from direct.showbase.DirectObject import DirectObject

class EditorCamera(DirectObject):
    def __init__(self, base, viewport_area=(0.15, 0.0, 0.8, 1.0)):
        """
        base: ShowBase
        viewport_area: tuple (x_min, y_min, x_max, y_max) normalisé 0..1
                       zone où la caméra est active (zone 3D)
        """
        super().__init__()
        self.base = base
        self.cam = base.cam
        self.viewport_area = viewport_area
        self.disable_default_camera()
        self.cam.node().getLens().setFov(120)

        # Paramètres
        self.move_speed = 25.0
        self.mouse_sensitivity = 0.25
        self.zoom_speed = 100.0

        # États
        self.keys = {"z": False, "s": False, "q": False, "d": False,
                     "a": False, "e": False}
        self.right_button_held = False
        self.prev_pointer_x = None
        self.prev_pointer_y = None

        # --- Bind clavier AZERTY ---
        for key in self.keys.keys():
            self.accept(key, self.set_key, [key, True])
            self.accept(f"{key}-up", self.set_key, [key, False])

        # --- Bind souris ---
        self.accept("mouse3", self.set_right_button, [True])
        self.accept("mouse3-up", self.set_right_button, [False])
        self.accept("wheel_up", self.zoom_in)
        self.accept("wheel_down", self.zoom_out)

        # Ajout de la tâche d'update
        base.taskMgr.add(self.update, "EditorCameraUpdate")

    def disable_default_camera(self):
        try:
            self.base.disableMouse()
        except Exception:
            pass

    def set_key(self, key, value):
        self.keys[key] = value

    def set_right_button(self, state):
        if state and not self.is_mouse_in_viewport():
            return
        self.right_button_held = state
        if state and self.base.win:
            p = self.base.win.getPointer(0)
            self.prev_pointer_x = p.getX()
            self.prev_pointer_y = p.getY()
        else:
            self.prev_pointer_x = None
            self.prev_pointer_y = None

    def zoom_in(self):
        if not self.is_mouse_in_viewport():
            return
        dt = globalClock.getDt()
        self.cam.setY(self.cam, self.zoom_speed * dt)

    def zoom_out(self):
        if not self.is_mouse_in_viewport():
            return
        dt = globalClock.getDt()
        self.cam.setY(self.cam, -self.zoom_speed * dt)

    def update(self, task):
        dt = globalClock.getDt()
        speed = self.move_speed * dt

        if not self.is_mouse_in_viewport():
            return task.cont

        # --- Déplacement clavier (AZERTY) ---
        if self.keys["z"]:
            self.cam.setPos(self.cam, Vec3(0, speed, 0))
        if self.keys["s"]:
            self.cam.setPos(self.cam, Vec3(0, -speed, 0))
        if self.keys["q"]:
            self.cam.setPos(self.cam, Vec3(-speed, 0, 0))
        if self.keys["d"]:
            self.cam.setPos(self.cam, Vec3(speed, 0, 0))
        if self.keys["a"]:
            self.cam.setZ(self.cam, -speed)
        if self.keys["e"]:
            self.cam.setZ(self.cam, speed)

        # --- Rotation clic droit ---
        if self.right_button_held and self.base.win:
            p = self.base.win.getPointer(0)
            x, y = p.getX(), p.getY()

            if self.prev_pointer_x is not None and self.prev_pointer_y is not None:
                dx = x - self.prev_pointer_x
                dy = y - self.prev_pointer_y

                h = self.cam.getH() - dx * self.mouse_sensitivity
                p_angle = self.cam.getP() - dy * self.mouse_sensitivity
                p_angle = max(-89, min(89, p_angle))
                self.cam.setHpr(h, p_angle, 0)

            self.prev_pointer_x = x
            self.prev_pointer_y = y

        return task.cont

    # ------------------------------------------
    # Vérifie si la souris est dans la zone du viewport 3D
    # ------------------------------------------
    def is_mouse_in_viewport(self):
        if not self.base.mouseWatcherNode.hasMouse() or not self.base.win:
            return False
        pointer = self.base.win.getPointer(0)
        x = pointer.getX()
        y = pointer.getY()
        w, h = self.base.win.getXSize(), self.base.win.getYSize()
        if w == 0 or h == 0:
            return False

        nx, ny = x / w, y / h
        x_min, y_min, x_max, y_max = self.viewport_area
        return x_min <= nx <= x_max and y_min <= ny <= y_max
