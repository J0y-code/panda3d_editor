from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.textinput import TextInput
from panda3d.core import NodePath
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
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4, padding=4)
        content.bind(minimum_height=content.setter('height'))
        scroll.add_widget(content)
        self.add_widget(scroll)

        # Titre
        content.add_widget(Label(text="[b]Properties[/b]", markup=True, size_hint_y=None, height=30, color=(1,1,1,1)))

        # --- Position en tableau ---
        self.pos_inputs = {}
        content.add_widget(Label(text="Position", size_hint_y=None, height=20, color=(1,1,1,1)))

        # Ligne des labels X Y Z
        header = BoxLayout(size_hint_y=None, height=24)
        for axis in "XYZ":
            header.add_widget(Label(text=axis, size_hint_x=1, color=(1,1,1,1)))
        content.add_widget(header)

        # Ligne des TextInput
        pos_row = BoxLayout(size_hint_y=None, height=28, spacing=2)
        for axis in "XYZ":
            ti = TextInput(text="0", multiline=False)
            ti.bind(on_text_validate=self.on_text_validate)
            self.pos_inputs[axis] = ti
            pos_row.add_widget(ti)
        content.add_widget(pos_row)

        # --- Rotation en tableau ---
        self.rot_inputs = {}
        content.add_widget(Label(text="Rotation", size_hint_y=None, height=20, color=(1,1,1,1)))
        header_rot = BoxLayout(size_hint_y=None, height=24)
        for axis in "HPR":
            header_rot.add_widget(Label(text=axis, size_hint_x=1, color=(1,1,1,1)))
        content.add_widget(header_rot)

        rot_row = BoxLayout(size_hint_y=None, height=28, spacing=2)
        for axis in "HPR":
            ti = TextInput(text="0", multiline=False)
            ti.bind(on_text_validate=self.on_text_validate)
            self.rot_inputs[axis] = ti
            rot_row.add_widget(ti)
        content.add_widget(rot_row)

        # --- Échelle en tableau ---
        self.scale_inputs = {}
        content.add_widget(Label(text="Échelle", size_hint_y=None, height=20, color=(1,1,1,1)))
        header_scale = BoxLayout(size_hint_y=None, height=24)
        for axis in "XYZ":
            header_scale.add_widget(Label(text=axis, size_hint_x=1, color=(1,1,1,1)))
        content.add_widget(header_scale)

        scale_row = BoxLayout(size_hint_y=None, height=28, spacing=2)
        for axis in "XYZ":
            ti = TextInput(text="1", multiline=False)
            ti.bind(on_text_validate=self.on_text_validate)
            self.scale_inputs[axis] = ti
            scale_row.add_widget(ti)
        content.add_widget(scale_row)

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
                self.editor_app.update_model_info(self.selected_node)
                print(f"[SYNC] {self.selected_node.get_name()} mis à jour")

        except ValueError:
            pass

    def update_model_info(self, model):
        """Met à jour la position, rotation et échelle du modèle dans self.models"""
        name = model.get_name()
        if name in self.models:
            self.models[name]["pos"] = list(model.get_pos())
            self.models[name]["hpr"] = list(model.get_hpr())
            self.models[name]["scale"] = list(model.get_scale())
            # Debug
            print(f"[SYNC] {name} mis à jour -> pos={self.models[name]['pos']}")


