from kivy.uix.boxlayout import BoxLayout
from kivy.uix.treeview import TreeView, TreeViewLabel, TreeViewNode
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from pathlib import Path

def truncate_filename(filename, max_chars=12):
    """
    Tronque le nom d'un fichier en gardant l'extension.
    Exemple : "fichier_long_nom.py" -> "fichier_l....py"
    """
    filename = str(filename)
    if len(filename) <= max_chars:
        return filename
    parts = filename.rsplit('.', 1)
    if len(parts) == 2:
        name, ext = parts
        keep = max_chars - len(ext) - 4  # 4 pour "...."
        if keep <= 0:
            return f"....{ext}"
        return f"{name[:keep]}....{ext}"
    else:
        return filename[:max_chars-4] + "...."

class ProjectHierarchySidebar(BoxLayout):
    def __init__(self, panda_app=None, ui_app=None, project_root: str = ".", **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_x = 0.15
        self.spacing = 2
        self.padding = 2
        self.panda_app = panda_app
        self.ui_app = ui_app
        self.loaded_models = set()
        self.selected_node = None

        # Fond gris foncé
        with self.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

        # Titre
        self.add_widget(Label(
            text="[b]Projet[/b]",
            markup=True,
            size_hint_y=None,
            height=36,
            color=(1, 1, 1, 1),
            font_size=14
        ))

        # Scroll et TreeView
        self.scroll = ScrollView(do_scroll_x=False, bar_width=8)
        self.tree = TreeView(root_options=dict(text="Projet"), hide_root=True, indent_level=20)
        self.scroll.add_widget(self.tree)
        self.add_widget(self.scroll)

        self.project_root = Path(project_root)
        self.refresh()

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def refresh(self):
        """Recharge l’arborescence depuis le dossier racine"""
        self.tree.clear_widgets()
        self._add_node(self.project_root, parent=None)

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

            # Charger modèle si fichier 3D
            if path.is_file() and path.suffix.lower() in (".bam", ".egg", ".gltf", ".glb", ".pz"):
                if path not in self.loaded_models and self.ui_app:
                    self.ui_app.load_model_from_project(path)
                    self.loaded_models.add(path)

        node.bind(on_touch_down=lambda inst, touch: on_select(inst) if node.collide_point(*touch.pos) else None)

        if path.is_dir():
            try:
                for child in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                    self._add_node(child, parent=node)
            except PermissionError:
                pass
