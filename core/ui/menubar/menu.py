# core/ui/menubar/menu.py
from .file.save import Save
from .file.model_loader import ModelLoader
from .file.file_ops import OpenScene
from .file.export import Export

from kivy.uix.actionbar import ActionBar, ActionView, ActionPrevious, ActionButton, ActionGroup
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

class MenuBar(ActionBar):
    def __init__(self, editor_ui=None, **kwargs):
        super().__init__(**kwargs)
        self.editor_ui = editor_ui
        self.pos_hint = {'top': 1}
        self.background_color = (0, 0, 0, 1)
        self.run = False

        # ActionView principal
        self.action_view = ActionView()
        self.add_widget(self.action_view)

        # --- Titre ---
        self.action_view.add_widget(ActionPrevious(title='Scene editor', with_previous=False))

        # --- Groupe "Fichier" ---
        self.file_group = ActionGroup(text='File')
        self.action_view.add_widget(self.file_group)

        # --- Groupe "Edition" ---
        self.edit_group = ActionGroup(text='Edition')
        self.edit_group.add_widget(ActionButton(text='Undo'))
        self.edit_group.add_widget(ActionButton(text='Redo'))
        self.action_view.add_widget(self.edit_group)

        # --- Groupe "Test" (Run Script) ---
        self.scripts_group = ActionGroup(text='Script test')
        self.action_view.add_widget(self.scripts_group)

        # Bouton pour exécuter tous les scripts
        self.scripts_group.add_widget(
            ActionButton(text='Run', on_press=lambda *a: self.editor_ui.run_all_scripts()))

        # Bouton pour arrêter tous les scripts
        self.scripts_group.add_widget(
            ActionButton(text='Stop', on_press=lambda *a: self.editor_ui.stop_all_scripts()))

        # --- Groupe "Aide" ---
        self.help_group = ActionGroup(text='Help')
        self.help_group.add_widget(ActionButton(text='Documentation'))
        self.help_group.add_widget(ActionButton(text='About'))
        self.help_group.add_widget(ActionButton(text='Help'))
        self.action_view.add_widget(self.help_group)

        # --- Groupe "Lumières" ---
        self.lights_group = ActionGroup(text='Lights & effects')
        self.action_view.add_widget(self.lights_group)

        # Boutons pour ajouter des lights
        self.add_sun_btn = ActionButton(text='Directional Light (sun)')
        self.add_light_to_model_btn = ActionButton(text='Light attached to a Model')
        self.lights_group.add_widget(self.add_sun_btn)
        self.lights_group.add_widget(self.add_light_to_model_btn)

    def _setup_file_actions(self):
        """Ajoute les actions du groupe Fichier en lien avec l'EditorUI."""
        self.open_scene_tool = OpenScene(self.editor_ui)
        self.load_tool = ModelLoader(self.editor_ui)
        self.save_tool = Save(self.editor_ui)

        self.export_tool = Export(self.editor_ui)

        Clock.schedule_once(lambda dt: (
            self.open_scene_tool.connect_events(),
            self.load_tool.connect_events(),
            self.save_tool.connect_events(),
            self.export_tool.connect_events()
        ))
        # Connect light actions after a short delay to ensure editor_ui exist
        Clock.schedule_once(lambda dt: (
            self.add_sun_btn.bind(on_release=lambda *_: self.editor_ui.create_sun()),
            self.add_light_to_model_btn.bind(on_release=lambda *_: self._add_light_to_selected())
        ), 0.1)

    def _add_light_to_selected(self):
        selected = self.editor_ui.sidebar.selected_node
        if selected is None:
            print('[MenuBar] Aucun modèle sélectionné pour ajouter une light.')
            return
        self.editor_ui.add_light_to_model(selected)