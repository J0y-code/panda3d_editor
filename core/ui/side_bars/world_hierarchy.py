from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.graphics import Color, Rectangle
from pathlib import Path

class HierarchySidebar(BoxLayout):
    def __init__(self, panda_app, app, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_x = 1
        self.size_hint_y = 0.6
        self.panda_app = panda_app
        self.app = app
        self.selected_node = None
        self.models = panda_app.models

        # Fond gris foncé
        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

        # Titre
        self.add_widget(Label(
            text="[b]Hiérarchie[/b]",
            markup=True,
            size_hint_y=None,
            height=36,
            color=(1,1,1,1),
            font_size=15,
        ))

        # Scroll + TreeView
        self.scroll = ScrollView(do_scroll_x=False, bar_width=8)
        self.tree = TreeView(root_options=dict(text="Scene"), hide_root=False, indent_level=20)
        self.tree.bind(selected_node=self.on_select_node)
        self.scroll.add_widget(self.tree)
        self.add_widget(self.scroll)

        self.refresh_hierarchy()

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def refresh_hierarchy(self):
        """Affiche la hiérarchie en respectant les collections et fichiers importés."""
        # Supprime tous les nœuds existants
        for node in list(self.tree.iterate_all_nodes()):
            self.tree.remove_node(node)

        def add_node(panda_node, parent_label=None):
            # Récupérer info du fichier si existant
            display_name = panda_node.get_name()
            print(display_name)

            label = TreeViewLabel(text=display_name)
            self.tree.add_node(label, parent_label)
            label.panda_node = panda_node

            for child in panda_node.get_children():
                add_node(child, parent_label=label)

        # Parcourir tous les NodePaths racine de la scène
        for root_node in self.app.get_children():
            add_node(root_node)

    def on_select_node(self, tree, node):
        if node:
            self.selected_node = getattr(node, 'panda_node', None)
            # Mettre à jour la sidebar propriétés
            if self.selected_node:
                self.panda_app.properties_sidebar.set_node(self.selected_node)
