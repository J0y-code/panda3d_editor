from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from pathlib import Path
from kivy.uix.popup import Popup
from panda3d.core import Filename
import json
from kivy.uix.actionbar import ActionButton
from kivy.clock import Clock

class OpenScene:
    def __init__(self, editor_app):
        self.editor_app = editor_app
        self.panda = self.editor_app.panda
        self.current_scene_file = editor_app.current_scene_file
        self.models = editor_app.models
        self.sidebar = editor_app.sidebar
        self.properties_sidebar = editor_app.properties_sidebar
        self.file_group = self.editor_app.file_group
        self.open_btn = ActionButton(text='Ouvrir')
        self.file_group.add_widget(self.open_btn)

    def connect_events(self):
        print("[DEBUG] Connexion du bouton 'Ouvrir'")
        self.open_btn.bind(on_release=self.open_scene)

    def open_scene(self, *args):
        """Ouvre un fichier .json et recharge la scène"""
        box = BoxLayout(orientation='vertical')
        chooser = FileChooserListView(filters=["*.json"], path=str(Path.cwd()))
        box.add_widget(chooser)

        btn_box = BoxLayout(size_hint_y=None, height=40)
        load_btn = Button(text="Charger", background_color=(0.2, 0.5, 0.3, 1))
        cancel_btn = Button(text="Annuler", background_color=(0.3, 0.3, 0.3, 1))
        btn_box.add_widget(load_btn)
        btn_box.add_widget(cancel_btn)
        box.add_widget(btn_box)

        popup = Popup(title="Ouvrir la scène", content=box, size_hint=(0.9, 0.9))
        popup.open()

        def do_load(*args):
            if chooser.selection:
                path = Path(chooser.selection[0])
                self.load_scene_from_file(path)
                self.current_scene_file = path
                popup.dismiss()

        load_btn.bind(on_release=do_load)
        cancel_btn.bind(on_release=lambda *_: popup.dismiss())

    def load_scene_from_file(self, path):
        """Charge une scène JSON sans remplacer les noms de collections internes par le nom du fichier."""
        import json
        from pathlib import Path
        from panda3d.core import Filename, NodePath

        path = Path(path)
        if not path.exists():
            print(f"[ERREUR] Fichier introuvable : {path}")
            return

        # --- Lecture du JSON ---
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"[ERREUR] JSON invalide : {e}")
                return

        print(f"[INFO] Chargement de la scène : {path.name}")
        self.models.clear()

        def merge_node(json_node, parent_np):
            """Fusionne récursivement un node JSON dans la scène Panda3D."""
            name = json_node.get("name", "Unnamed")
            node_type = json_node.get("type", "group")
            transform = json_node.get("transform", {})

            pos = transform.get("pos", [0, 0, 0])
            hpr = transform.get("hpr", [0, 0, 0])
            scale = transform.get("scale", [1, 1, 1])

            file_info = json_node.get("file")
            model_path = None
            if file_info and file_info.get("path"):
                model_path = Filename.from_os_specific(file_info["path"]).get_fullpath()

            # --- Vérifie si un node du même nom existe déjà ---
            existing_np = parent_np.find(f"**/{name}")
            if not existing_np.is_empty():
                np = existing_np
                print(f"[FUSION] Node existant : {name}")
            else:
                # --- Charger un modèle si un chemin est défini ---
                if model_path:
                    try:
                        model = self.panda.loader.loadModel(model_path)
                        container = NodePath(name)
                        container.reparent_to(parent_np)
                        model.reparent_to(container)
                        np = container
                        print(f"[CHARGÉ] Modèle 3D importé : {file_info['path']}")
                    except Exception as e:
                        print(f"[ERREUR] Impossible de charger {model_path}: {e}")
                        np = parent_np.attach_new_node(name)
                else:
                    # --- Node vide (collection ou group) ---
                    np = parent_np.attach_new_node(name)
                    print(f"[CRÉATION] Node vide : {name}")

            # --- Appliquer les transformations du JSON ---
            np.set_pos(*pos)
            np.set_hpr(*hpr)
            np.set_scale(*scale)

            # --- Enregistrer le node ---
            self.models[name] = {
                "node": np,
                "type": node_type,
                "file": file_info,
                "pos": pos,
                "hpr": hpr,
                "scale": scale,
            }

            # --- Charger les enfants récursivement ---
            for child_data in json_node.get("childs", []):
                merge_node(child_data, np)

            return np

        # --- Fusion de toutes les racines ---
        for node_data in data:
            merge_node(node_data, self.panda.render)

        # --- Rafraîchir les panneaux ---
        if hasattr(self, "sidebar"):
            self.sidebar.refresh_hierarchy()
        if hasattr(self, "properties_sidebar"):
            self.properties_sidebar.set_node(None)

        print(f"[SUCCÈS] Scène chargée : {path.name}")
