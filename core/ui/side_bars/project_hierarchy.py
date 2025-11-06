#core/ui/side_bars/world_hierarchy.py

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.treeview import TreeView, TreeViewLabel, TreeViewNode
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle
from pathlib import Path
from panda3d.core import Filename, NodePath

def truncate_filename(filename, max_chars=12):
    filename = str(filename)
    if len(filename) <= max_chars:
        return filename
    parts = filename.rsplit('.', 1)
    if len(parts) == 2:
        name, ext = parts
        keep = max_chars - len(ext) - 4
        if keep <= 0:
            return f"....{ext}"
        return f"{name[:keep]}....{ext}"
    else:
        return filename[:max_chars-4] + "...."

from kivy.clock import Clock
class ProjectHierarchySidebar(BoxLayout):
    DOUBLE_CLICK_TIME = 10  # intervalle max pour double clic (en secondes)
    def __init__(self, panda_app=None, ui_app=None, project_root: str = ".", **kwargs):
        super().__init__(**kwargs)
        self._last_click_time = {}
        self.orientation = 'vertical'
        self.size_hint_x = 0.15
        self.spacing = 2
        self.padding = 2
        self.panda_app = panda_app
        self.ui_app = ui_app
        self.loaded_models = set()
        self.selected_node = None
        self.project_root = Path(project_root)

        # Fond gris foncé
        with self.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

        # Titre
        title_label = Label(text="[b]Project[/b]", markup=True, size_hint_y=None, height=36,
                            color=(1, 1, 1, 1), font_size=14)
        self.add_widget(title_label)

        # Boutons pour changer dossier / refresh
        btn_layout = BoxLayout(size_hint_y=None, height=28, spacing=2)
        choose_btn = Button(text="change directory", font_size=12, background_color=(0.2,0.2,0.2,1), color=(1,1,1,1))
        choose_btn.bind(on_release=self.choose_project_folder)
        refresh_btn = Button(text="refresh", font_size=12, background_color=(0.2,0.2,0.2,1), color=(1,1,1,1))
        refresh_btn.bind(on_release=lambda *_: self.refresh())
        btn_layout.add_widget(choose_btn)
        btn_layout.add_widget(refresh_btn)
        self.add_widget(btn_layout)

        # Scrollable TreeView
        self.scroll = ScrollView(
            do_scroll_x=False,   # uniquement scroll vertical
            do_scroll_y=True,
            bar_width=8,
            size_hint=(1, 1)
        )

        self.tree = TreeView(
            root_options=dict(text=str(self.project_root)),
            hide_root=True,
            indent_level=20,
            size_hint_y=None   # nécessaire pour le scroll
        )
        self.tree.bind(minimum_height=self.tree.setter('height'))

        self.scroll.add_widget(self.tree)
        self.add_widget(self.scroll)
        self.refresh()

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def choose_project_folder(self, *_):
        from kivy.uix.filechooser import FileChooserListView
        chooser = FileChooserListView(path=str(self.project_root), dirselect=True)
        popup_layout = BoxLayout(orientation='vertical')
        popup_layout.add_widget(chooser)
        popup_btns = BoxLayout(size_hint_y=None, height=32, spacing=4)
        ok_btn = Button(text="OK")
        cancel_btn = Button(text="Annuler")
        popup_btns.add_widget(ok_btn)
        popup_btns.add_widget(cancel_btn)
        popup_layout.add_widget(popup_btns)
        popup = Popup(title="Select Project Folder", content=popup_layout, size_hint=(0.8, 0.8))

        ok_btn.bind(on_release=lambda *_: (setattr(self, "project_root", Path(chooser.selection[0])) if chooser.selection else None, self.refresh(), popup.dismiss()))
        cancel_btn.bind(on_release=lambda *_: popup.dismiss())
        popup.open()

    def refresh(self):
        """Recharge le contenu du projet avec scroll fonctionnel."""
        # Supprimer complètement l’ancienne TreeView
        if hasattr(self, 'scroll') and hasattr(self, 'tree'):
            self.scroll.clear_widgets()
            self.remove_widget(self.scroll)

        # Créer une nouvelle TreeView avec scroll vertical
        self.scroll = ScrollView(do_scroll_x=False, do_scroll_y=True, bar_width=8, size_hint=(1, 1))
        self.tree = TreeView(
            root_options=dict(text=str(self.project_root)),
            hide_root=True,
            indent_level=20,
            size_hint_y=None
        )
        self.tree.bind(minimum_height=self.tree.setter('height'))

        self.scroll.add_widget(self.tree)
        self.add_widget(self.scroll)

        # Ajouter les nœuds du projet
        self._add_node(self.project_root, parent=None)


    def refreshforbtn(self, *_):
        """Recharge l’arborescence depuis le dossier racine (bouton Refresh)."""
        self.refresh()


    def _add_node(self, path: Path, parent: TreeViewNode = None):
        if not path.exists():
            return

        display_name = truncate_filename(path.name, max_chars=20)
        node = TreeViewLabel(text=display_name)
        self.tree.add_node(node, parent)

        def on_select(instance):
            if self.selected_node:
                self.selected_node.color = (1, 1, 1, 1)
            instance.color = (0.2, 0.4, 0.8, 1)
            self.selected_node = instance
            if path.is_file() and self.ui_app:
                suffix = path.suffix.lower()
                if suffix in (".bam", ".egg", ".gltf", ".glb", ".pz"):
                    self.load_model_from_project(path)
                elif suffix == ".py":
                    self.ui_app.open_script(path)

        def on_touch_down(inst, touch):
            if not node.collide_point(*touch.pos):
                return False

            # clic gauche = sélection normale
            if touch.button == 'left':
                on_select(inst)

            # clic droit sur dossier = popup
            elif touch.button == 'right' and path.is_dir():
                self._maybe_add_node_popup(inst, path)

            # on ne bloque pas le touch pour TreeView
            return False

        node.bind(on_touch_down=on_touch_down)

        if path.is_dir():
            try:
                for child in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                    self._add_node(child, parent=node)
            except PermissionError:
                pass

    def _maybe_add_node_popup(self, node, path):
        # Popup pour ajouter un fichier/dossier
        popup_layout = BoxLayout(orientation='vertical', spacing=4)
        input_name = TextInput(hint_text="Nale file/directory", size_hint_y=None, height=28)
        popup_layout.add_widget(input_name)

        btn_layout = BoxLayout(size_hint_y=None, height=32, spacing=4)
        btn_file = Button(text="Create file")
        btn_dir = Button(text="Create directory")
        btn_cancel = Button(text="Cancel")
        btn_layout.add_widget(btn_file)
        btn_layout.add_widget(btn_dir)
        btn_layout.add_widget(btn_cancel)
        popup_layout.add_widget(btn_layout)

        popup = Popup(title=f"Add to {path.name}", content=popup_layout, size_hint=(0.5,0.5))

        def create_file(*_):
            name = input_name.text.strip()
            if name:
                (path / name).touch(exist_ok=True)
                self.refresh()
            popup.dismiss()

        def create_dir(*_):
            name = input_name.text.strip()
            if name:
                (path / name).mkdir(exist_ok=True)
                self.refresh()
            popup.dismiss()

        btn_file.bind(on_release=create_file)
        btn_dir.bind(on_release=create_dir)
        btn_cancel.bind(on_release=lambda *_: popup.dismiss())

        popup.open()


    def load_model_from_project(self, path):
        """Charge un modèle 3D depuis le panneau Projet, encapsulé dans un node portant le nom du fichier."""
        panda_path = Filename.from_os_specific(str(path)).get_fullpath()
        try:
            model = self.panda_app.loader.loadModel(panda_path)

            container_name = path.stem
            container = NodePath(container_name)
            container.reparentTo(self.panda_app.render)

            # Reparent le modèle dans le conteneur
            model.reparentTo(container)

            # Donne un nom unique si déjà pris
            base_name = container_name
            name = base_name
            i = 1
            while name in self.ui_app.models:
                name = f"{base_name}_{i}"
                i += 1
            container.set_name(name)

            self.ui_app.models[name] = {
                "path": str(path),
                "file": {
                    "name": path.stem,
                    "path": str(path),
                    "data": None
                },
                "node": container,
                "pos": list(container.get_pos()),
                "hpr": list(container.get_hpr()),
                "scale": list(container.get_scale()),
                "type": "group"
            }

            print(f"[INFO] Modèle ajouté à la scène : {name}")

            # Rafraîchit la hiérarchie
            self.ui_app.sidebar.refresh_hierarchy()

            # Sélectionne le modèle dans les propriétés
            self.ui_app.sidebar.selected_node = container
            self.ui_app.properties_sidebar.set_node(container)

        except Exception as e:
            print(f"[ERREUR] Impossible de charger {path}: {e}")