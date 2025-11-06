from panda3d.core import (
    LineSegs,
    VBase4,
    GeomNode,
    NodePath,
    Vec3,
    Point3,
    Point2,
    Mat4,
    Plane,
)
import math


class Gizmos:
    def __init__(self, render_node, scale=1.0, handle_dist=1.0, handle_screen_radius=0.05):
        print("[Gizmos] Initialisation...")
        self.render = render_node
        self._scale = float(scale)
        self._handle_dist = float(handle_dist)
        self._handle_screen_radius = float(handle_screen_radius)

        self.axis_colors = {'x': VBase4(1, 0, 0, 1), 'y': VBase4(0, 1, 0, 1), 'z': VBase4(0, 0, 1, 1)}
        self._highlight_color = VBase4(1, 1, 0, 1)

        print("[Gizmos] Construction des axes principaux...")
        self._node = self._build_gizmo(self._scale)
        self._node.reparentTo(self.render)

        print("[Gizmos] Construction des handles...")
        self.handles = {}
        self._build_handles()

        self.target = None
        self._drag_mode = None
        self._selected_axis = None
        self._start_point_world = None
        self._start_target_pos = None
        self._start_target_mat = None
        self._start_target_scale = None
        self._start_handle_world = None
        self._start_handle_length = None
        self._start_rot_vector = None

        print("[Gizmos] Initialisation terminée ✅")

    @property
    def node(self):
        return self._node

    def _build_gizmo(self, scale):
        print(f"[Gizmos] Création du gizmo de taille {scale}")
        lines = LineSegs()
        lines.setThickness(10.0)
        for axis, col, end in [('x', self.axis_colors['x'], (scale, 0, 0)),
                               ('y', self.axis_colors['y'], (0, scale, 0)),
                               ('z', self.axis_colors['z'], (0, 0, scale))]:
            print(f"[Gizmos] Axe {axis} → couleur {col}, extrémité {end}")
            lines.setColor(col)
            lines.moveTo(0, 0, 0)
            lines.drawTo(*end)
        geom_node = lines.create()
        return NodePath(geom_node)

    def _make_handle_visual(self, axis, size=0.06):
        print(f"[Gizmos] Création du handle pour l’axe {axis} (taille {size})")
        ls = LineSegs()
        ls.setThickness(10.0)
        col = self.axis_colors.get(axis, VBase4(1, 1, 0, 1))
        ls.setColor(col)

        if axis == 'x':
            ls.moveTo(0, -size, 0); ls.drawTo(0, size, 0)
            ls.moveTo(0, 0, -size); ls.drawTo(0, 0, size)
        elif axis == 'y':
            ls.moveTo(-size, 0, 0); ls.drawTo(size, 0, 0)
            ls.moveTo(0, 0, -size); ls.drawTo(0, 0, size)
        else:
            ls.moveTo(-size, 0, 0); ls.drawTo(size, 0, 0)
            ls.moveTo(0, -size, 0); ls.drawTo(0, size, 0)

        return NodePath(ls.create())

    def _build_handles(self):
        for axis in ('x', 'y', 'z'):
            h = self._make_handle_visual(axis)
            if axis == 'x':
                pos = (self._handle_dist, 0, 0)
            elif axis == 'y':
                pos = (0, self._handle_dist, 0)
            else:
                pos = (0, 0, self._handle_dist)
            print(f"[Gizmos] Position du handle {axis} → {pos}")
            h.setPos(*pos)
            h.reparentTo(self._node)
            self.handles[axis] = h

    def show(self):
        print("[Gizmos] Gizmo visible")
        self._node.show()

    def hide(self):
        print("[Gizmos] Gizmo caché")
        self._node.hide()

    def set_target(self, nodepath):
        print(f"[Gizmos] set_target({nodepath})")
        self.target = nodepath
        if nodepath is None:
            print("[Gizmos] Aucun target, gizmo désactivé.")
            return
        pos = nodepath.getPos(self.render)
        print(f"[Gizmos] Position du gizmo alignée sur la cible → {pos}")
        self._node.setPos(pos)

    def pick_handle(self, mouse_pos, base):
        print(f"[Gizmos] pick_handle(mouse_pos={mouse_pos})")
        best = None
        best_dist = 1e9
        for axis, hp in self.handles.items():
            world_pos = self._node.getPos(self.render) + hp.getPos(self._node)
            cam_pos = base.cam.getRelativePoint(self.render, world_pos)
            p2 = Point2()
            ok = base.camLens.project(cam_pos, p2)
            if not ok:
                print(f"[Gizmos] {axis}: hors champ")
                continue
            dx = mouse_pos.getX() - p2.getX()
            dy = mouse_pos.getY() - p2.getY()
            dist = math.sqrt(dx * dx + dy * dy)
            print(f"[Gizmos] Axe {axis} → distance écran {dist:.4f}")
            if dist < best_dist:
                best_dist = dist
                best = axis
        if best and best_dist <= self._handle_screen_radius:
            print(f"[Gizmos] Axe sélectionné: {best} (dist={best_dist:.4f})")
            return best
        print("[Gizmos] Aucun axe sélectionné")
        return None

    def _mouse_to_world_line(self, mouse_pos, base):
        near_cam = Point3(); far_cam = Point3()
        if not base.camLens.extrude(mouse_pos, near_cam, far_cam):
            print("[Gizmos] Extrusion de rayon échouée")
            return None, None
        cam_mat = base.cam.getMat(self.render)
        near_world = cam_mat.xformPoint(near_cam)
        far_world = cam_mat.xformPoint(far_cam)
        return near_world, far_world

    def start_drag(self, mouse_pos, base, mode):
        self._drag_mode = mode
        self._start_target_pos = self.target.getPos(self.render)
        self._start_target_scale = self.target.getScale()
        self._start_target_hpr = self.target.getHpr()
        self._start_cam_pos = base.cam.getPos(self.render)  # ✅ Ajout nécessaire

        # (le reste de ton code start_drag habituel)

        print(f"[Gizmos] start_drag(mode={mode}, mouse_pos={mouse_pos})")
        if self.target is None:
            print("[Gizmos] Aucun target → annulation")
            return False
        self._drag_mode = mode
        self._selected_axis = self.pick_handle(mouse_pos, base)
        self._start_target_mat = self.target.getMat(self.render)
        self._start_target_pos = self.target.getPos(self.render)
        self._start_target_scale = Vec3(self.target.getScale(self.render))
        near_w, far_w = self._mouse_to_world_line(mouse_pos, base)
        if near_w is None:
            return False
        if self._selected_axis:
            axis_vec = self._axis_vector_world(self._selected_axis)
            plane = Plane(axis_vec, Point3(self._start_target_pos))
        else:
            cam_forward = base.cam.getQuat(self.render).getForward()
            plane = Plane(cam_forward, Point3(self._start_target_pos))
        p = Point3()
        got = plane.intersectsLine(p, near_w, far_w)
        if got:
            self._start_point_world = Point3(p)
        else:
            print("[Gizmos] Aucune intersection trouvée")
            self._start_point_world = Point3(self._start_target_pos)
        if self._selected_axis:
            self._start_handle_world = self._handle_world_pos(self._selected_axis)
            self._start_handle_length = (self._start_handle_world - self._start_target_pos).length()
        print("[Gizmos] Drag démarré ✅")
        return True

    def update_drag(self, mouse_pos, base):
        if not self._drag_mode:
            return

        near_w, far_w = self._mouse_to_world_line(mouse_pos, base)
        if near_w is None:
            return

        # Plan parallèle à la caméra pour stabilité
        cam_forward = base.cam.getQuat(self.render).getForward()
        plane = Plane(cam_forward, Point3(self._start_target_pos))

        cur_point = Point3()
        if not plane.intersectsLine(cur_point, near_w, far_w):
            print("[Gizmos] Pas d’intersection pendant le drag")
            return


        axis_vec = None
        if self._selected_axis:
            axis_vec = self._axis_vector_world(self._selected_axis).normalized()

        if self._drag_mode == 'translate':
            if axis_vec is not None:
                delta = cur_point - self._start_target_pos
                move_amount = delta.dot(axis_vec)
                new_pos = self._start_target_pos + axis_vec * move_amount
                self.target.setPos(new_pos)


        elif self._drag_mode == 'scale':
            if axis_vec is not None:
                delta = cur_point - self._start_target_pos
                scale_factor = 1.0 + delta.dot(axis_vec)
                scale_factor = max(0.01, scale_factor)  # éviter les inversions

                sx, sy, sz = self._start_target_scale

                if self._selected_axis == 'x':
                    new_scale = Vec3(sx * scale_factor, sy, sz)
                elif self._selected_axis == 'y':
                    new_scale = Vec3(sx, sy * scale_factor, sz)
                elif self._selected_axis == 'z':
                    new_scale = Vec3(sx, sy, sz * scale_factor)
                else:
                    # Aucun axe sélectionné → mise à l’échelle uniforme
                    new_scale = self._start_target_scale * scale_factor

                self.target.setScale(new_scale)


        elif self._drag_mode == 'rotate':
            if axis_vec is not None:
                # Projeter cur_point dans le plan de rotation
                start_vec = (self._start_target_pos - self._start_cam_pos).normalized()
                cur_vec = (cur_point - self._start_cam_pos).normalized()
                angle = start_vec.signedAngleDeg(cur_vec, axis_vec)
                new_hpr = self._start_target_hpr + Vec3(axis_vec * angle)
                self.target.setHpr(new_hpr)

        # Optionnel : repositionner le gizmo visuel
        self._node.setPos(self.target.getPos(self.render))

    def stop_drag(self):
        self._drag_mode = None
        self._selected_axis = None
        self._start_point_world = None
        self._start_target_pos = None
        self._start_target_mat = None
        self._start_target_scale = None
        self._start_handle_world = None
        self._start_handle_length = None
        self._start_rot_vector = None

    # ----- Helpers -----
    def _handle_world_pos(self, axis):
        world = self._node.getPos(self.render) + self.handles[axis].getPos(self._node)
        return Point3(world)

    def _axis_vector_world(self, axis):
        origin = self._node.getPos(self.render)
        handle = self._handle_world_pos(axis)
        vec = Vec3(handle - origin)
        if vec.length() == 0:
            return Vec3(1, 0, 0)
        vec.normalize()
        return vec

    def _apply_translation(self, cur_point_world):
        delta = cur_point_world - self._start_point_world
        if self._selected_axis:
            axis = self._axis_vector_world(self._selected_axis)
            proj = axis * delta.dot(axis)
            newpos = self._start_target_pos + proj
        else:
            newpos = self._start_target_pos + delta
        self.target.setPos(self.render, newpos)

    def _apply_scale(self, cur_point_world):
        if self._selected_axis:
            start_len = self._start_handle_length or 1.0
            cur_len = (cur_point_world - self._start_target_pos).length()
            factor = max(0.001, cur_len / start_len)
            sx, sy, sz = self._start_target_scale
            if self._selected_axis == 'x':
                sx *= factor
            elif self._selected_axis == 'y':
                sy *= factor
            else:
                sz *= factor
            self.target.setScale(self.render, Vec3(sx, sy, sz))
        else:
            d0 = (self._start_point_world - self._start_target_pos).length()
            d1 = (cur_point_world - self._start_target_pos).length()
            factor = max(0.001, d1 / d0) if d0 != 0 else 1.0
            self.target.setScale(self.render, self._start_target_scale * factor)

    def _apply_rotation(self, cur_point_world):
        center = self._start_target_pos
        v0 = Vec3(self._start_point_world - center)
        v1 = Vec3(cur_point_world - center)
        axis = self._axis_vector_world(self._selected_axis) if self._selected_axis else Vec3(0, 0, 1)
        axis.normalize()
        p0 = v0 - axis * v0.dot(axis)
        p1 = v1 - axis * v1.dot(axis)
        if p0.length() == 0 or p1.length() == 0:
            return
        p0.normalize(); p1.normalize()
        dot = max(-1.0, min(1.0, p0.dot(p1)))
        angle = math.degrees(math.acos(dot))
        cross = p0.cross(p1)
        sign = 1.0 if cross.dot(axis) >= 0 else -1.0
        angle *= sign
        rot = Mat4()
        rot.setRotateMat(angle, axis)
        T1 = Mat4.translateMat(-center)
        T2 = Mat4.translateMat(center)
        new_mat = T2 * rot * T1 * self._start_target_mat
        self.target.setMat(self.render, new_mat)

    def detach(self):
        print("[Gizmos] detach() → gizmo détaché")
        if self._node:
            self._node.detachNode()

    def attach_to(self, nodepath):
        print(f"[Gizmos] attach_to({nodepath})")
        if self._node and nodepath:
            self._node.reparentTo(self.render)
            self._node.setPos(nodepath.getPos(self.render))
            self.show()
