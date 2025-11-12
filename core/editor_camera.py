from panda3d.core import Vec3
from direct.showbase.DirectObject import DirectObject
import json


class EditorCamera(DirectObject):
    def __init__(self, base, camera=None):
        """
        base : instance de ShowBase
        camera : NodePath de la caméra à contrôler (ex: base.cam ou ta caméra custom)
        """
        super().__init__()
        self.base = base
        self.camera2 = camera

        self.paramètres = json.load(open("core/config/keyboard.json", "r", encoding="utf-8"))
        print(self.paramètres)
        self.front = str(self.paramètres["move_controls"]["front"])
        self.back = str(self.paramètres["move_controls"]["back"])
        self.left = str(self.paramètres["move_controls"]["left"])
        self.right = str(self.paramètres["move_controls"]["right"])
        self.up = str(self.paramètres["move_controls"]["up"])
        self.down = str(self.paramètres["move_controls"]["down"])

        self.disable_default_camera()
        self.camera2.node().getLens().setFov(120)

        # États et paramètres
        self.enabled = True
        self.is_on_script = False
        self.move_speed = 25.0
        self.mouse_sensitivity = 0.25
        self.zoom_speed = 100.0

        # États clavier/souris
        self.keys = {self.front: False, self.back: False, self.left: False, self.right: False, self.up: False, self.down: False}
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

    # ---------------------------------------------------------
    def disable_default_camera(self):
        try:
            self.base.disableMouse()
        except Exception:
            pass

    # ---------------------------------------------------------
    def set_enabled(self, value: bool):
        self.enabled = value
        print(f"[EditorCamera] {'Activée' if value else 'Désactivée'}")

    def toggle_enabled(self):
        self.set_enabled(not self.enabled)

    # ---------------------------------------------------------
    def set_key(self, key, value):
        if self.enabled:
            self.keys[key] = value

    def set_right_button(self, state):
        if not self.enabled or self.is_on_script:
            return

        if state:
            if not self.is_mouse_in_viewport():
                return  # Ignore si la souris n'est pas dans le viewport
        self.right_button_held = state

        if not self.enabled or self.is_on_script:
            return
        self.right_button_held = state

        if state and self.base.win:
            p = self.base.win.getPointer(0)
            self.prev_pointer_x = p.getX()
            self.prev_pointer_y = p.getY()
        else:
            self.prev_pointer_x = None
            self.prev_pointer_y = None

    # ---------------------------------------------------------
    def zoom_in(self):
        if not self.is_mouse_in_viewport() and not self.enabled or self.is_on_script:
            return
        if self.is_mouse_in_viewport():
            dt = globalClock.getDt()
            self.camera2.setY(self.camera2, self.zoom_speed * dt)

    def zoom_out(self):
        if not self.is_mouse_in_viewport() and not self.enabled or self.is_on_script:
            return
        if self.is_mouse_in_viewport():
            dt = globalClock.getDt()
            self.camera2.setY(self.camera2, -self.zoom_speed * dt)

    # ---------------------------------------------------------
    def update(self, task):
        if not self.enabled or self.is_on_script:
            return task.cont

        dt = globalClock.getDt()
        speed = self.move_speed * dt

        if self.is_mouse_in_viewport():
            # --- Déplacement clavier ---
            if self.keys[self.front]:
                self.camera2.setPos(self.camera2, Vec3(0, speed, 0))
            if self.keys[self.back]:
                self.camera2.setPos(self.camera2, Vec3(0, -speed, 0))
            if self.keys[self.left]:
                self.camera2.setPos(self.camera2, Vec3(-speed, 0, 0))
            if self.keys[self.right]:
                self.camera2.setPos(self.camera2, Vec3(speed, 0, 0))
            if self.keys[self.down]:
                self.camera2.setZ(self.camera2, -speed)
            if self.keys[self.up]:
                self.camera2.setZ(self.camera2, speed)


        # --- Rotation clic droit ---
        if self.right_button_held and self.is_mouse_in_viewport():
            p = self.base.win.getPointer(0)
            x, y = p.getX(), p.getY()

            if self.prev_pointer_x is not None and self.prev_pointer_y is not None:
                dx = x - self.prev_pointer_x
                dy = y - self.prev_pointer_y

                h = self.camera2.getH() - dx * self.mouse_sensitivity
                p_angle = self.camera2.getP() - dy * self.mouse_sensitivity
                p_angle = max(-89, min(89, p_angle))
                self.camera2.setHpr(h, p_angle, 0)

            self.prev_pointer_x = x
            self.prev_pointer_y = y

        return task.cont


    def is_mouse_in_viewport(self):
        if not self.base.mouseWatcherNode.hasMouse():
            return False

        # Normalisé en [-1,1]
        mx = self.base.mouseWatcherNode.getMouseX()
        my = self.base.mouseWatcherNode.getMouseY()

        # Dimensions de la display region
        dr = self.base.viewport_region
        if not dr:
            return False

        # Calculer la position en pixels
        win = self.base.win
        if not win:
            return False

        x_min, x_max, y_min, y_max = dr.getDimensions()  # renvoie (xmin, xmax, ymin, ymax)
        win_w = win.getXSize()
        win_h = win.getYSize()

        # Convertir les coordonnées de [-1,1] en [0,1] pour comparer avec DR
        px = (mx + 1) / 2
        py = (my + 1) / 2

        return x_min <= px <= x_max and y_min <= py <= y_max
