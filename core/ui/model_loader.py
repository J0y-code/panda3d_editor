from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from pathlib import Path
from kivy.uix.popup import Popup
from kivy.uix.actionbar import ActionButton
from kivy.clock import Clock
from panda3d.core import Filename, NodePath

class ModelLoader:
    def __init__(self, editor_app):
        self.editor_app = editor_app
        self.panda = self.editor_app.panda
        self.current_scene_file = editor_app.current_scene_file
        self.models = editor_app.models
        self.sidebar = editor_app.sidebar
        self.properties_sidebar = editor_app.properties_sidebar
        self.file_group = self.editor_app.file_group

        self.import_btn = ActionButton(text='Import')
        self.file_group.add_widget(self.import_btn)

    def connect_events(self):
        self.import_btn.bind(on_release=self.open_file_chooser)
        

    # File chooser 
    def open_file_chooser(self, instance):
        box = BoxLayout(orientation='vertical')
        chooser = FileChooserListView(filters=["*.egg", "*.bam", "*.gltf", "*.glb", "*.pz"])
        box.add_widget(chooser)

        btn_box = BoxLayout(size_hint_y=None, height=40)
        select_btn = Button(text="import", background_color=(0.2, 0.5, 0.3, 1))
        cancel_btn = Button(text="cancel", background_color=(0.3, 0.3, 0.3, 1))
        btn_box.add_widget(select_btn)
        btn_box.add_widget(cancel_btn)
        box.add_widget(btn_box)

        popup = Popup(title="Choose a model", content=box, size_hint=(0.9, 0.9))
        popup.open()

        def load_model(*args):
            if chooser.selection:
                path = Path(chooser.selection[0])
                panda_path = Filename.from_os_specific(str(path)).get_fullpath()
                try:
                    model = self.panda.loader.loadModel(panda_path)

                    # Crée un conteneur racine nommé d'après le fichier
                    container_name = path.stem
                    container = NodePath(container_name)
                    container.reparentTo(self.panda.render)

                    # Reparent le modèle dans le conteneur
                    model.reparentTo(container)

                    # Nom unique si déjà utilisé
                    base_name = container_name
                    name = base_name
                    i = 1
                    while name in self.models:
                        name = f"{base_name}_{i}"
                        i += 1
                    container.set_name(name)

                    # Enregistre le conteneur dans self.models
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

                    print(f"[INFO] Modèle importé et ajouté à la scène : {name}")

                    popup.dismiss()
                    self.sidebar.refresh_hierarchy()

                    # Sélection automatique
                    self.sidebar.selected_node = container
                    self.properties_sidebar.set_node(container)

                except Exception as e:
                    print(f"[ERREUR] Impossible de charger {path}: {e}")

        select_btn.bind(on_release=load_model)

        cancel_btn.bind(on_release=lambda *_: popup.dismiss())
