from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.textinput import TextInput
from panda3d.core import NodePath
# Lights
from panda3d.core import DirectionalLight, AmbientLight, PointLight, Vec4
# Barre des propriétés

class PropertiesSidebar(BoxLayout):
    def __init__(self, editor_app=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_x = 1
        self.size_hint_y = 0.4
        self.padding = 0
        self.spacing = 0
        self.selected_node = None
        self.editor_app = editor_app

        with self.canvas.before:
            Color(0.15,0.15,0.15,1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

        scroll = ScrollView(size_hint=(1,1), bar_width=8)
        self.content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4, padding=4)
        self.content.bind(minimum_height=self.content.setter('height'))
        scroll.add_widget(self.content)
        self.add_widget(scroll)

        # Titre
        self.content.add_widget(Label(text="[b]Properties[/b]", markup=True, size_hint_y=None, height=30, color=(1,1,1,1)))

        # --- Position en tableau ---
        self.pos_inputs = {}
        self.content.add_widget(Label(text="Position", size_hint_y=None, height=20, color=(1,1,1,1)))

        # Ligne des labels X Y Z
        header = BoxLayout(size_hint_y=None, height=24)
        for axis in "XYZ":
            header.add_widget(Label(text=axis, size_hint_x=1, color=(1,1,1,1)))
        self.content.add_widget(header)

        # Ligne des TextInput
        pos_row = BoxLayout(size_hint_y=None, height=28, spacing=2)
        for axis in "XYZ":
            ti = TextInput(text="0", multiline=False)
            ti.bind(on_text_validate=self.on_text_validate)
            self.pos_inputs[axis] = ti
            pos_row.add_widget(ti)
        self.content.add_widget(pos_row)

        # --- Rotation en tableau ---
        self.rot_inputs = {}
        self.content.add_widget(Label(text="Rotation", size_hint_y=None, height=20, color=(1,1,1,1)))
        header_rot = BoxLayout(size_hint_y=None, height=24)
        for axis in "HPR":
            header_rot.add_widget(Label(text=axis, size_hint_x=1, color=(1,1,1,1)))
        self.content.add_widget(header_rot)

        rot_row = BoxLayout(size_hint_y=None, height=28, spacing=2)
        for axis in "HPR":
            ti = TextInput(text="0", multiline=False)
            ti.bind(on_text_validate=self.on_text_validate)
            self.rot_inputs[axis] = ti
            rot_row.add_widget(ti)
        self.content.add_widget(rot_row)

        # --- Échelle en tableau ---
        self.scale_inputs = {}
        self.content.add_widget(Label(text="Scale", size_hint_y=None, height=20, color=(1,1,1,1)))
        header_scale = BoxLayout(size_hint_y=None, height=24)
        for axis in "XYZ":
            header_scale.add_widget(Label(text=axis, size_hint_x=1, color=(1,1,1,1)))
        self.content.add_widget(header_scale)

        scale_row = BoxLayout(size_hint_y=None, height=28, spacing=2)
        for axis in "XYZ":
            ti = TextInput(text="1", multiline=False)
            ti.bind(on_text_validate=self.on_text_validate)
            self.scale_inputs[axis] = ti
            scale_row.add_widget(ti)
        self.content.add_widget(scale_row)

        # Container pour les contrôles spécifiques aux lights
        self.light_controls_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4)
        # assure la hauteur minimale et permet d'ajouter/supprimer des widgets
        self.light_controls_container.bind(minimum_height=self.light_controls_container.setter('height'))
        self.content.add_widget(self.light_controls_container)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def set_node(self, node: NodePath) -> None:
        """Met à jour les champs de transformation selon le node sélectionné."""
        self.selected_node = node

        # --- Sécurité : aucun node sélectionné ---
        if node is None:
            for ti in self.pos_inputs.values():
                ti.text = ""
            for ti in self.rot_inputs.values():
                ti.text = ""
            for ti in self.scale_inputs.values():
                ti.text = ""
            print("[INFO] Aucun node sélectionné (panneau propriétés vidé).")
            return

        # --- Node valide ---
        pos = node.get_pos()
        hpr = node.get_hpr()
        scale = node.get_scale()

        # Position
        for axis, ti in self.pos_inputs.items():
            ti.text = str(round(getattr(pos, axis.lower()), 3))

        # Rotation
        for i, axis in enumerate("HPR"):
            ti = self.rot_inputs[axis]
            ti.text = str(round(hpr[i], 3))

        # Échelle
        for axis, ti in self.scale_inputs.items():
            ti.text = str(round(getattr(scale, axis.lower()), 3))

        # --- Si le node est une light, afficher les contrôles supplémentaires ---
        try:
            node_obj = node.node()
        except Exception:
            node_obj = None

        # Nettoyer anciens contrôles
        self.clear_light_controls()

        if node_obj is not None and isinstance(node_obj, (DirectionalLight, AmbientLight, PointLight)):
            self.show_light_controls(node)

    def on_text_validate(self, instance):
        if not self.selected_node:
            return
        try:
            x, y, z = [float(self.pos_inputs[a].text) for a in "XYZ"]
            self.selected_node.set_pos(x, y, z)
            h, p, r = [float(self.rot_inputs[a].text) for a in "HPR"]
            self.selected_node.set_hpr(h, p, r)
            sx, sy, sz = [float(self.scale_inputs[a].text) for a in "XYZ"]
            self.selected_node.set_scale(sx, sy, sz)

            # 🔹 Synchroniser avec le dictionnaire de modèles
            if self.editor_app:
                self.update_model_info(self.selected_node)

        except ValueError:
            pass

    def update_model_info(self, model):
        """Met à jour les infos du modèle dans self.models"""
        name = model.get_name()
        if name in self.editor_app.models:
            self.editor_app.models[name]["pos"] = list(model.get_pos())
            self.editor_app.models[name]["hpr"] = list(model.get_hpr())
            self.editor_app.models[name]["scale"] = list(model.get_scale())
            # Debug
            print(f"[SYNC] {name} mis à jour -> pos={self.editor_app.models[name]['pos']}")

    # ---------------- Light controls ----------------
    def clear_light_controls(self):
        """Supprime tous les widgets de light controls."""
        self.light_controls_container.clear_widgets()

    def show_light_controls(self, light_np: NodePath):
        """Affiche les contrôles de modification pour la light donnée (NodePath)."""
        # header
        lbl = Label(text=f"Light: {light_np.get_name()}", size_hint_y=None, height=24, color=(1,1,1,1))
        self.light_controls_container.add_widget(lbl)

        # R,G,B,A inputs
        col_row = BoxLayout(size_hint_y=None, height=28, spacing=2)
        self.r_input = TextInput(text="1.0", multiline=False)
        self.g_input = TextInput(text="1.0", multiline=False)
        self.b_input = TextInput(text="1.0", multiline=False)
        self.a_input = TextInput(text="1.0", multiline=False)
        for ti, name in ((self.r_input,'R'),(self.g_input,'G'),(self.b_input,'B'),(self.a_input,'A')):
            ti.bind(on_text_validate=lambda inst: self.apply_light_color())
            col_row.add_widget(ti)
        self.light_controls_container.add_widget(Label(text='Couleur RGBA (valeurs 0..1)', size_hint_y=None, height=20, color=(1,1,1,1)))
        self.light_controls_container.add_widget(col_row)

        # Boutons
        btn_row = BoxLayout(size_hint_y=None, height=30, spacing=4)
        apply_btn = Button(text='Appliquer', size_hint_x=0.6)
        remove_btn = Button(text='Supprimer light', size_hint_x=0.4)
        apply_btn.bind(on_release=lambda *_: self.apply_light_color())
        remove_btn.bind(on_release=lambda *_: self.remove_light(light_np))
        btn_row.add_widget(apply_btn)
        btn_row.add_widget(remove_btn)
        self.light_controls_container.add_widget(btn_row)

        # Préremplir avec la couleur actuelle si possible
        try:
            light_obj = light_np.node()
            c = light_obj.getColor()
            self.r_input.text = str(round(c[0], 3))
            self.g_input.text = str(round(c[1], 3))
            self.b_input.text = str(round(c[2], 3))
            # certains Light n'ont pas alpha, on met 1.0 par défaut
            self.a_input.text = str(round(c[3] if len(c) > 3 else 1.0, 3))
        except Exception:
            pass

        # Transform controls for lights (position / hpr)
        trans_row = BoxLayout(size_hint_y=None, height=28, spacing=2)
        self.light_pos_inputs = {}
        for axis in "XYZ":
            ti = TextInput(text="0", multiline=False)
            trans_row.add_widget(ti)
            self.light_pos_inputs[axis] = ti
        self.light_controls_container.add_widget(Label(text='Position (X Y Z)', size_hint_y=None, height=20, color=(1,1,1,1)))
        self.light_controls_container.add_widget(trans_row)

        hpr_row = BoxLayout(size_hint_y=None, height=28, spacing=2)
        self.light_hpr_inputs = {}
        for axis in "HPR":
            ti = TextInput(text="0", multiline=False)
            hpr_row.add_widget(ti)
            self.light_hpr_inputs[axis] = ti
        self.light_controls_container.add_widget(Label(text='HPR (pour DirectionalLight)', size_hint_y=None, height=20, color=(1,1,1,1)))
        self.light_controls_container.add_widget(hpr_row)

        apply_trans_btn = Button(text='Appliquer transform', size_hint_y=None, height=30)
        apply_trans_btn.bind(on_release=lambda *_: self.apply_light_transform())
        self.light_controls_container.add_widget(apply_trans_btn)

        # Préremplir les valeurs actuelles
        try:
            lp = light_np.get_pos(self.editor_app.panda.render)
            self.light_pos_inputs['X'].text = str(round(lp[0],3))
            self.light_pos_inputs['Y'].text = str(round(lp[1],3))
            self.light_pos_inputs['Z'].text = str(round(lp[2],3))
        except Exception:
            pass
        try:
            lh = light_np.get_hpr(self.editor_app.panda.render)
            self.light_hpr_inputs['H'].text = str(round(lh[0],3))
            self.light_hpr_inputs['P'].text = str(round(lh[1],3))
            self.light_hpr_inputs['R'].text = str(round(lh[2],3))
        except Exception:
            pass

    def apply_light_color(self):
        """Lit les champs RGBA et applique la couleur sur la light sélectionnée."""
        if not self.selected_node:
            return
        try:
            r = float(self.r_input.text)
            g = float(self.g_input.text)
            b = float(self.b_input.text)
            a = float(self.a_input.text)
        except Exception:
            print('[Properties] Valeurs de couleur invalides.')
            return

        try:
            light_obj = self.selected_node.node()
            light_obj.setColor(Vec4(r, g, b, a))
            print(f"[Properties] Couleur light appliquée: {(r,g,b,a)}")
        except Exception as e:
            print(f"[Properties] Impossible d'appliquer la couleur: {e}")

    def remove_light(self, light_np: NodePath):
        """Retire la light du render et supprime le node."""
        try:
            self.editor_app.panda.render.clearLight(light_np)
        except Exception:
            pass
        try:
            light_np.remove_node()
            print(f"[Properties] Light {light_np.get_name()} supprimée.")
            # vider les contrôles
            self.clear_light_controls()
            # Rafraîchir la hiérarchie
            try:
                self.editor_app.sidebar.refresh_hierarchy()
            except Exception:
                pass
        except Exception as e:
            print(f"[Properties] Impossible de supprimer la light: {e}")

    def apply_light_transform(self):
        """Applique la position/HPR depuis les champs vers la light sélectionnée."""
        if not self.selected_node:
            return
        try:
            x = float(self.light_pos_inputs['X'].text)
            y = float(self.light_pos_inputs['Y'].text)
            z = float(self.light_pos_inputs['Z'].text)
        except Exception:
            print('[Properties] Valeurs de position invalides.')
            return

        try:
            self.selected_node.setPos(self.editor_app.panda.render, x, y, z)
        except Exception as e:
            print(f"[Properties] Impossible d'appliquer la position: {e}")

        # HPR (optionnel pour DirectionalLight)
        try:
            h = float(self.light_hpr_inputs['H'].text)
            p = float(self.light_hpr_inputs['P'].text)
            r = float(self.light_hpr_inputs['R'].text)
            # appliquer si le node est DirectionalLight
            node_obj = self.selected_node.node()
            if isinstance(node_obj, DirectionalLight):
                self.selected_node.setHpr(self.editor_app.panda.render, h, p, r)
        except Exception:
            # ignore HPR si non fournie ou non applicable
            pass
        print('[Properties] Transform appliqué à la light.')
