from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from pathlib import Path
from panda3d.core import DirectionalLight, AmbientLight, PointLight, NodePath

class HierarchySidebar(BoxLayout):
    def __init__(self, panda_app, app, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_x = 1
        self.size_hint_y = 0.6
        self.padding = 10
        self.spacing = 10
        self.panda_app = panda_app
        self.app = app
        self.selected_node = None
        self.models = panda_app.models

        # Fond gris foncé
        with self.canvas.before:
            Color(0.08, 0.08, 0.08, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

        # Titre
        self.add_widget(Label(
            text="[b]Tree node[/b]",
            markup=True,
            size_hint_y=None,
            height=20,
            color=(1,1,1,1),
            font_size=15,
        ))

        # --- Nouveau BoxLayout pour englober le TreeView ---
        tree_container = BoxLayout(orientation='vertical', padding=2, spacing=2)
        with tree_container.canvas.before:
            Color(0.1, 0.1, 0.1, 1)  # couleur du rectangle
            tree_container.rect = Rectangle(pos=tree_container.pos, size=tree_container.size)
        tree_container.bind(pos=self.update_rect_container, size=self.update_rect_container)

        # Scroll + TreeView
        self.scroll = ScrollView(do_scroll_x=False, do_scroll_y=True, bar_width=8, size_hint_y=1)
        self.tree = TreeView(root_options=dict(text="render"), hide_root=False, indent_level=15)

        self.tree.size_hint_y = None
        self.tree.bind(minimum_height=self.tree.setter('height'))
        self.tree.bind(selected_node=self.on_select_node)

        self.scroll.add_widget(self.tree)
        tree_container.add_widget(self.scroll)  # TreeView dans le container
        self.add_widget(tree_container)          # container dans le panel

        self.refresh_hierarchy()

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def update_rect_container(self, instance, *args):
        instance.rect.pos = instance.pos
        instance.rect.size = instance.size

    def refresh_hierarchy(self):
        """Affiche la hiérarchie en respectant les collections et fichiers importés."""
        # Supprime tous les nœuds existants
        for node in list(self.tree.iterate_all_nodes()):
            self.tree.remove_node(node)
        # Helper: ajoute récursivement un panda_node et ses enfants dans l'arbre,
        # en sautant les nodes de type Light (ils seront listés dans le groupe Lights).
        def add_node(panda_node, parent_label=None):
            try:
                node_obj = panda_node.node()
            except Exception:
                node_obj = None

            # Skip lights here (we'll list them in the Lights group)
            if node_obj is not None and isinstance(node_obj, (DirectionalLight, AmbientLight, PointLight)):
                return

            display_name = panda_node.get_name() or '<unnamed>'

            label = TreeViewLabel(text=display_name)
            self.tree.add_node(label, parent_label)
            label.panda_node = panda_node

            for child in panda_node.get_children():
                add_node(child, parent_label=label)

        # First, add a 'Lights' group and collect all lights under render
        lights_group = TreeViewLabel(text='Lights')
        self.tree.add_node(lights_group)

        def collect_lights(node, out_list):
            try:
                for child in node.get_children():
                    try:
                        obj = child.node()
                    except Exception:
                        obj = None
                    if obj is not None and isinstance(obj, (DirectionalLight, AmbientLight, PointLight)):
                        out_list.append(child)
                    # Recurse
                    collect_lights(child, out_list)
            except Exception:
                pass

        lights = []
        collect_lights(self.app, lights)
        for light_np in lights:
            lname = light_np.get_name() or '<light>'
            llabel = TreeViewLabel(text=lname)
            llabel.panda_node = light_np
            self.tree.add_node(llabel, lights_group)

        # Parcourir tous les NodePaths racine de la scène (en sautant les lights déjà listées)
        for root_node in self.app.get_children():
            add_node(root_node)

    def on_select_node(self, tree, node):
        if node:
            self.selected_node = getattr(node, 'panda_node', None)
            print("[INFO] selection du node:"+str(self.selected_node))
            # Mettre à jour la sidebar propriétés
            if self.selected_node:
                self.panda_app.properties_sidebar.set_node(self.selected_node)
