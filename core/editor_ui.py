from panda3d.core import NodePath, Filename
try:
    from .panda3d_kivy.app import App
except ImportError:
    from panda3d_kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.uix.textinput import TextInput
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from pathlib import Path
from direct.showbase.ShowBase import ShowBase
from kivy.graphics import Color, Rectangle


import subprocess
import sys

def run_python_in_venv(self, code):
    """
    Exécute du code Python dans un venv séparé et retourne la sortie.
    """
    venv_python = r".venv_console\Scripts\python.exe"  # chemin vers le Python du venv
    try:
        result = subprocess.run(
            [venv_python, "-c", code],
            capture_output=True,
            text=True,
            check=False,
        )
        output = result.stdout.strip()
        errors = result.stderr.strip()
        if output:
            self.print_to_console(output)
        if errors:
            self.print_to_console(f"[Erreur] {errors}")
    except Exception as e:
        self.print_to_console(f"[Exception] {e}")


# ----------------------------
# Barre des propriétés
# ----------------------------
class PropertiesSidebar(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_x = 0.15
        self.size_hint_y = 1
        self.padding = 0
        self.spacing = 0
        self.selected_node = None

        with self.canvas.before:
            Color(0.12,0.12,0.12,1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

        # ScrollView pour le contenu
        scroll = ScrollView(size_hint=(1, 1), bar_width=8)
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4, padding=4)
        content.bind(minimum_height=content.setter('height'))
        scroll.add_widget(content)
        self.add_widget(scroll)

        # Titre
        content.add_widget(Label(text="[b]Propriétés[/b]", markup=True, size_hint_y=None, height=30, color=(1,1,1,1)))

        # Position
        self.pos_inputs = {}
        for axis in "XYZ":
            box = BoxLayout(size_hint_y=None, height=28)
            box.add_widget(Label(text=f"Pos {axis}:", size_hint_x=0.3, color=(1,1,1,1)))
            ti = TextInput(text="0", multiline=False, size_hint_x=0.7)
            ti.bind(on_text_validate=self.on_text_validate)
            box.add_widget(ti)
            self.pos_inputs[axis] = ti
            content.add_widget(box)

        # Rotation
        self.rot_inputs = {}
        for axis in "HPR":
            box = BoxLayout(size_hint_y=None, height=28)
            box.add_widget(Label(text=f"Rot {axis}:", size_hint_x=0.3, color=(1,1,1,1)))
            ti = TextInput(text="0", multiline=False, size_hint_x=0.7)
            ti.bind(on_text_validate=self.on_text_validate)
            box.add_widget(ti)
            self.rot_inputs[axis] = ti
            content.add_widget(box)

        # Échelle
        self.scale_inputs = {}
        for axis in "XYZ":
            box = BoxLayout(size_hint_y=None, height=28)
            box.add_widget(Label(text=f"Scale {axis}:", size_hint_x=0.3, color=(1,1,1,1)))
            ti = TextInput(text="1", multiline=False, size_hint_x=0.7)
            ti.bind(on_text_validate=self.on_text_validate)
            box.add_widget(ti)
            self.scale_inputs[axis] = ti
            content.add_widget(box)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def set_node(self, node: NodePath):
        self.selected_node = node
        pos = node.get_pos()
        hpr = node.get_hpr()
        scale = node.get_scale()
        for axis, ti in zip("XYZ", [self.pos_inputs[a] for a in "XYZ"]):
            ti.text = str(round(getattr(pos, axis.lower()), 3))
        for axis, ti in zip("HPR", [self.rot_inputs[a] for a in "HPR"]):
            ti.text = str(round(getattr(hpr, axis.lower()), 3))
        for axis, ti in zip("XYZ", [self.scale_inputs[a] for a in "XYZ"]):
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
        except ValueError:
            pass

# ----------------------------
# Sidebar hiérarchie
# ----------------------------
class HierarchySidebar(BoxLayout):
    def __init__(self, panda_app, app, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_x = 0.15
        self.size_hint_y = 1
        self.panda_app = panda_app
        self.app = app
        self.selected_node = None

        with self.canvas.before:
            Color(0.1,0.1,0.1,1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

        self.add_widget(Label(
            text="[b]Hiérarchie[/b]",
            markup=True,
            size_hint_y=None,
            height=36,
            color=(1,1,1,1),
            font_size=15,
        ))

        self.scroll = ScrollView(do_scroll_x=False, bar_width=8, size_hint=(1, 1))
        self.layout = GridLayout(cols=1, spacing=2, size_hint_y=None, padding=(2,2))
        self.layout.bind(minimum_height=self.layout.setter("height"))
        self.scroll.add_widget(self.layout)
        self.add_widget(self.scroll)

        refresh_bar = BoxLayout(size_hint_y=None, height=36)
        self.refresh_btn = Button(text="↻ Rafraîchir", size_hint_y=None, height=32,
                                  background_color=(0.18,0.18,0.18,1), color=(1,1,1,1), font_size=13)
        self.refresh_btn.bind(on_press=self.refresh_hierarchy)
        refresh_bar.add_widget(self.refresh_btn)
        self.add_widget(refresh_bar)
        self.refresh_hierarchy()

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def refresh_hierarchy(self, *args):
        self.layout.clear_widgets()
        def add_node(node):
            icon = "📁" if node.get_num_children() > 0 else "🔹"
            name = node.get_name()
            btn = Button(text=f"{icon} {name}", size_hint_y=None, height=28,
                         background_color=(0,0,0,0), color=(0.9,0.9,0.9,1),
                         halign="left", valign="middle", font_size=12)
            btn.text_size = (self.width - 20, None)
            def select_node(*_):
                if self.selected_node:
                    self.selected_node.background_color = (0,0,0,0)
                btn.background_color = (0.2,0.4,0.8,1)
                self.selected_node = btn
                self.panda_app.properties_sidebar.set_node(node)
            btn.bind(on_release=select_node)
            self.layout.add_widget(btn)

        for root in self.app.get_children():
            add_node(root)

# ----------------------------
# UI principale
# ----------------------------
class EditorUI(App):
    def __init__(self, panda, app):
        super().__init__(panda)
        self.panda = panda
        self.app = app

    def build(self):
        root = BoxLayout(orientation='vertical')

        # ---------------- Menu bar ----------------
        menu_bar = BoxLayout(size_hint_y=None, height=36, spacing=0, padding=0)
        with menu_bar.canvas.before:
            Color(0,0,0,1)
            menu_bar.rect = Rectangle(pos=menu_bar.pos, size=menu_bar.size)
        menu_bar.bind(pos=lambda w,*a: setattr(menu_bar.rect,'pos',menu_bar.pos))
        menu_bar.bind(size=lambda w,*a: setattr(menu_bar.rect,'size',menu_bar.size))
        for name in ["Fichier","Édition","Affichage","Aide"]:
            menu_bar.add_widget(Button(text=name, background_color=(0,0,0,0), color=(1,1,1,1)))
        root.add_widget(menu_bar)

        # ---------------- Toolbar ----------------
        toolbar = BoxLayout(size_hint_y=None, height=36, spacing=0, padding=0)
        load_btn = Button(text="Charger", background_color=(0.2,0.5,0.3,1), color=(1,1,1,1))
        load_btn.bind(on_release=self.open_file_chooser)
        toolbar.add_widget(load_btn)
        toolbar.add_widget(Button(text="Déplacer", background_color=(0.2,0.2,0.25,1), color=(1,1,1,1)))
        toolbar.add_widget(Button(text="Supprimer", background_color=(0.2,0.2,0.25,1), color=(1,1,1,1)))
        root.add_widget(toolbar)

        # ---------------- Main area ----------------
        main_area = BoxLayout(orientation='horizontal', spacing=0, padding=0)

        # Sidebar propriétés (gauche)
        self.properties_sidebar = PropertiesSidebar()
        main_area.add_widget(self.properties_sidebar)



        # Onglets viewport / script (centre)
        self.tab_panel = TabbedPanel(do_default_tab=False, background_color=(0, 0, 0, 0))  # fond transparent

        # Onglet Viewport
        viewport_tab = TabbedPanelItem(text="Viewport")

        # BoxLayout pour le viewport
        self.viewport_box = BoxLayout()
        with self.viewport_box.canvas.before:
            Color(0, 0, 0, 0)  # fond totalement transparent
            self.viewport_rect = Rectangle(pos=self.viewport_box.pos, size=self.viewport_box.size)

        # Mettre à jour le rectangle si la taille ou la position change
        self.viewport_box.bind(pos=lambda w, *a: setattr(self.viewport_rect, 'pos', w.pos))
        self.viewport_box.bind(size=lambda w, *a: setattr(self.viewport_rect, 'size', w.size))

        viewport_tab.add_widget(self.viewport_box)
        self.tab_panel.add_widget(viewport_tab)

        # Onglet Script
        script_tab = TabbedPanelItem(text="Script")
        self.script_box = BoxLayout(orientation="vertical")
        self.script_editor = TextInput(text="# Écris ton script ici", multiline=True)
        self.script_box.add_widget(self.script_editor)
        script_tab.add_widget(self.script_box)
        self.tab_panel.add_widget(script_tab)

        main_area.add_widget(self.tab_panel)

        # Sidebar hiérarchie (droite)
        self.sidebar = HierarchySidebar(self, app=self.app)
        main_area.add_widget(self.sidebar)

        root.add_widget(main_area)

        # ---------------- Status bar ----------------
        '''status_bar = BoxLayout(size_hint_y=None, height=24, padding=(6,2))
        self.status_label = Label(text="Prêt.", color=(0.8,0.8,0.8,1), font_size=12)
        status_bar.add_widget(self.status_label)
        root.add_widget(status_bar)'''

        # TextInput multi-ligne pour la console
        self.console = TextInput(
            text=">>> ",
            readonly=False,
            multiline=True,
            size_hint_y=0.2,  # 25% de la hauteur totale
            background_color=(0.1, 0.1, 0.1, 1),
            foreground_color=(1, 1, 1, 1),
            font_size=12,
            cursor_color=(1, 1, 1, 1),
        )
        root.add_widget(self.console)
        self.console.bind(on_text_validate=self.on_console_enter)

        return root

    def bind_console(self):
        self.console.bind(on_key_down=self.on_console_key)

    def on_console_key(self, instance, keyboard, keycode, text, modifiers):
        if keycode[1] == 'enter' and 'shift' not in modifiers:
            script = instance.text
            self.execute_console(script)
            return True  # empêche le saut de ligne

    def on_console_enter(self, instance):
        # Récupère tout le script dans la console
        script = instance.text

        if script.strip():  # si ce n’est pas vide
            try:
                # Exécute le script dans un contexte séparé
                exec(script, globals())
                self.print_to_console("[OK] Script exécuté.")
            except Exception as e:
                self.print_to_console(f"[Erreur] {e}")

        # Vide la console après exécution
        instance.text = ""

    def print_to_console(self, message):
        self.console.text += str(message) + "\n"
        # scroll automatique
        self.console.cursor = (len(self.console.text), 0)

    # ---------------- File chooser ----------------
    def open_file_chooser(self, instance):
        box = BoxLayout(orientation='vertical')
        chooser = FileChooserListView(filters=["*.egg","*.bam","*.gltf","*.glb","*.pz"])
        box.add_widget(chooser)

        btn_box = BoxLayout(size_hint_y=None, height=40)
        select_btn = Button(text="Charger", background_color=(0.2,0.5,0.3,1))
        cancel_btn = Button(text="Annuler", background_color=(0.3,0.3,0.3,1))
        btn_box.add_widget(select_btn)
        btn_box.add_widget(cancel_btn)
        box.add_widget(btn_box)

        popup = Popup(title="Choisir un modèle", content=box, size_hint=(0.9,0.9))
        popup.open()

        def load_model(*args):
            if chooser.selection:
                path = Path(chooser.selection[0])
                panda_path = Filename.from_os_specific(str(path)).get_fullpath()
                try:
                    model = self.panda.loader.loadModel(panda_path)
                    model.reparentTo(self.panda.render)
                    model.set_pos(0,10,0)
                    self.status_label.text = f"Modèle chargé : {path.name}"
                    popup.dismiss()
                except Exception as e:
                    self.status_label.text = f"[ERREUR] {e}"

        select_btn.bind(on_release=load_model)
        cancel_btn.bind(on_release=lambda *_: popup.dismiss())