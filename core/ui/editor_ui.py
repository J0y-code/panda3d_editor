from panda3d.core import Filename, NodePath
try:
    from core.panda3d_kivy.app import App
except ImportError:
    from ..panda3d_kivy.app import App

from .side_bars.properties import *
from .side_bars.world_hierarchy import *
from .side_bars.project_hierarchy import *
from .save import Save
from .model_loader import ModelLoader
from .file_ops import OpenScene

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.actionbar import ActionBar, ActionView, ActionPrevious, ActionButton, ActionGroup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.clock import Clock

# UI principale

class EditorUI(App):
    current_scene_file: Path = None  # pour stocker le chemin actuel
    def __init__(self, panda, app):
        super().__init__(panda)
        self.panda = panda
        self.app = app
        self.current_scene_file = None
        self.models = {}  # <- registre des modèles chargés

    def build(self):
        # ROOT LAYOUT PRINCIPAL
        root = BoxLayout(orientation='vertical')

        # MENU BAR (ActionBar)
        action_bar = ActionBar(pos_hint={'top': 1}, background_color=(0, 0, 0, 1))
        action_view = ActionView()
        action_bar.add_widget(action_view)
        root.add_widget(action_bar)

        # --- Titre ---
        action_view.add_widget(ActionPrevious(title='Éditeur Panda3D', with_previous=False))

        # --- Groupe "Fichier" ---
        self.file_group = ActionGroup(text='Fichier')
        action_view.add_widget(self.file_group)

        # --- Groupe "Édition" ---
        edit_group = ActionGroup(text='Édition')
        edit_group.add_widget(ActionButton(text='Annuler'))
        edit_group.add_widget(ActionButton(text='Rétablir'))
        edit_group.add_widget(ActionButton(text='Supprimer'))
        action_view.add_widget(edit_group)

        # --- Groupe "Aide" ---
        help_group = ActionGroup(text='Aide')
        help_group.add_widget(ActionButton(text='Documentation'))
        help_group.add_widget(ActionButton(text='À propos'))
        action_view.add_widget(help_group)

        # TOOLBAR (barre d’outils grise)
        toolbar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=36,
            spacing=4,
            padding=[4, 4, 4, 4],
        )

        # Fond gris foncé
        with toolbar.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            toolbar.bg_rect = Rectangle(pos=toolbar.pos, size=toolbar.size)
        toolbar.bind(pos=lambda w, *a: setattr(toolbar.bg_rect, 'pos', w.pos))
        toolbar.bind(size=lambda w, *a: setattr(toolbar.bg_rect, 'size', w.size))

        # Style des boutons
        btn_kwargs = dict(
            size_hint=(None, 1),
            width=96,
            background_normal='',
            background_down='',
            background_color=(0.01, 0.01, 0.01, 1),
            color=(1, 1, 1, 1),
            font_size=13,
        )

        # Boutons d’outils
        move_btn = ToggleButton(text="Déplacer", group='tool', **btn_kwargs)
        delete_btn = ToggleButton(text="Supprimer", group='tool', **btn_kwargs)
        select_btn = ToggleButton(text="Sélection", group='tool', **btn_kwargs)
        rotate_btn = ToggleButton(text="Rotation", group='tool', **btn_kwargs)
        scale_btn = ToggleButton(text="Échelle", group='tool', **btn_kwargs)

        # Actions
        move_btn.bind(on_release=lambda *_: setattr(self, 'active_tool', 'move'))
        delete_btn.bind(on_release=lambda *_: setattr(self, 'active_tool', 'delete'))
        select_btn.bind(on_release=lambda *_: setattr(self, 'active_tool', 'select'))
        rotate_btn.bind(on_release=lambda *_: setattr(self, 'active_tool', 'rotate'))
        scale_btn.bind(on_release=lambda *_: setattr(self, 'active_tool', 'scale'))

        # Ajout boutons dans toolbar
        for b in (move_btn, delete_btn, select_btn, rotate_btn, scale_btn):
            toolbar.add_widget(b)
        toolbar.add_widget(BoxLayout())  # Espace flexible à droite

        root.add_widget(toolbar)

        # ZONE PRINCIPALE (main area)
        main_area = BoxLayout(orientation='horizontal', spacing=0, padding=0)

        # --- Barre de gauche : arborescence du projet
        project_root = Path("..") / "test"
        self.project_hierarchic_sidebar = ProjectHierarchySidebar(
            panda_app=self.panda,
            ui_app=self,
            project_root=str('default')
        )
        main_area.add_widget(self.project_hierarchic_sidebar)

        # --- Viewport (centre)
        self.viewport_box = BoxLayout()
        with self.viewport_box.canvas.before:
            Color(0, 0, 0, 0)
            self.viewport_rect = Rectangle(pos=self.viewport_box.pos, size=self.viewport_box.size)
        self.viewport_box.bind(pos=lambda w, *a: setattr(self.viewport_rect, 'pos', w.pos))
        self.viewport_box.bind(size=lambda w, *a: setattr(self.viewport_rect, 'size', w.size))
        main_area.add_widget(self.viewport_box)

        # --- Panneau de droite : Hiérarchie + Propriétés
        rightpanel = BoxLayout(orientation='vertical', spacing=0, padding=0, size_hint_x=0.15)

        # Sidebar hiérarchie (droite)
        self.sidebar = HierarchySidebar(self, app=self.app)
        rightpanel.add_widget(self.sidebar)

        # Sidebar propriétés
        self.properties_sidebar = PropertiesSidebar(editor_app=self)
        rightpanel.add_widget(self.properties_sidebar)

        main_area.add_widget(rightpanel)
        root.add_widget(main_area)

        # Initialisation des outils de la barre d'action
        self.open_scene_tool = OpenScene(self)
        self.load_tool = ModelLoader(self)
        self.save_tool = Save(self)

        # Boutons supplémentaires
        self.file_group.add_widget(ActionButton(text='Exporter'))
        self.file_group.add_widget(ActionButton(text='Quitter'))

        # Connecter tous les boutons après le rendu de l'UI
        Clock.schedule_once(lambda dt: (self.open_scene_tool.connect_events(), self.load_tool.connect_events(), self.save_tool.connect_events()))

        return root

    def update_model_info(self, model):
        """Met à jour les infos du modèle dans self.models"""
        name = model.get_name()
        if name in self.models:
            self.models[name]["pos"] = list(model.get_pos())
            self.models[name]["hpr"] = list(model.get_hpr())
            self.models[name]["scale"] = list(model.get_scale())

    def load_model_from_project(self, path):
        """Charge un modèle 3D depuis le panneau Projet, encapsulé dans un node portant le nom du fichier."""


        panda_path = Filename.from_os_specific(str(path)).get_fullpath()
        try:
            model = self.panda.loader.loadModel(panda_path)

            container_name = path.stem
            container = NodePath(container_name)
            container.reparentTo(self.panda.render)

            # Reparent le modèle dans le conteneur
            model.reparentTo(container)

            # Donne un nom unique si déjà pris
            base_name = container_name
            name = base_name
            i = 1
            while name in self.models:
                name = f"{base_name}_{i}"
                i += 1
            container.set_name(name)

            self.models[name] = {
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
            self.sidebar.refresh_hierarchy()

            # Sélectionne le modèle dans les propriétés
            self.sidebar.selected_node = container
            self.properties_sidebar.set_node(container)

        except Exception as e:
            print(f"[ERREUR] Impossible de charger {path}: {e}")
