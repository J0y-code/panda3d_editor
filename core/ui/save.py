from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from pathlib import Path
from kivy.uix.popup import Popup
from kivy.uix.actionbar import ActionButton
from kivy.clock import Clock

class Save:
    def __init__(self, editor_app):
        self.editor_app = editor_app
        self.panda = self.editor_app.panda
        self.current_scene_file = editor_app.current_scene_file
        self.models = editor_app.models
        self.file_group = self.editor_app.file_group

        # Autres options classiques
        self.save_btn = ActionButton(text='Enregistrer')
        self.file_group.add_widget(self.save_btn)

        self.save_as_btn = ActionButton(text='Enregistrer sous')
        self.file_group.add_widget(self.save_as_btn)

    def connect_events(self):
        self.save_btn.bind(on_release=self.save_scene)
        self.save_as_btn.bind(on_release=self.save_scene_as)

    def save_scene(self, *args):
        """Sauvegarde sur le fichier courant, sinon demande 'Enregistrer sous'"""
        if self.current_scene_file:
            self._write_scene_to_file(self.current_scene_file)
        else:
            self.save_scene_as()

    def save_scene_as(self, *args):
        """Ouvre un FileChooser pour choisir où sauvegarder la scène"""
        box = BoxLayout(orientation='vertical')
        chooser = FileChooserListView(filters=["*.json"], path=str(Path.cwd()))
        box.add_widget(chooser)

        btn_box = BoxLayout(size_hint_y=None, height=40)
        save_btn = Button(text="Enregistrer", background_color=(0.2, 0.5, 0.3, 1))
        cancel_btn = Button(text="Annuler", background_color=(0.3, 0.3, 0.3, 1))
        btn_box.add_widget(save_btn)
        btn_box.add_widget(cancel_btn)
        box.add_widget(btn_box)

        popup = Popup(title="Enregistrer la scène", content=box, size_hint=(0.9, 0.9))
        popup.open()

        def do_save(*args):
            # récupère le dossier courant du chooser
            folder = Path(chooser.path)
            # récupère le nom tapé dans le champ de nom de fichier
            filename = chooser.selection[0] if chooser.selection else "scene.json"
            path = folder / filename
            if not path.suffix == ".json":
                path = path.with_suffix(".json")
            self.current_scene_file = path
            self._write_scene_to_file(path)
            popup.dismiss()

        save_btn.bind(on_release=do_save)
        cancel_btn.bind(on_release=lambda *_: popup.dismiss())

    def _write_scene_to_file(self, path: Path):
        import json
        from pathlib import Path

        def serialize_node(node):
            """Convertit un NodePath et ses enfants en dictionnaire JSON étendu"""
            node_name = node.get_name()

            # 🔹 Ignorer la caméra et les lumières
            if node_name.lower() in {"camera", "light", "directionallight"}:
                return None

            # 🔹 Récupérer les infos depuis self.models
            model_info = self.models.get(node_name, {})
            node_type = model_info.get("type", "group")
            file_info = model_info.get("file")

            # 🔹 Si pas de structure 'file', la construire pour compatibilité
            if not file_info and model_info.get("path"):
                file_info = {
                    "name": Path(model_info["path"]).stem,
                    "path": model_info["path"],
                    "data": None
                }

            # 🔹 Vérifier si c’est un conteneur racine (fichier importé)
            is_container = bool(file_info and node.has_parent() and node.get_parent() == self.panda.render)

            # 🔹 Construire le dictionnaire
            entry = {
                "name": node_name,
                "type": node_type,
                "file": file_info,
                "transform": {
                    "pos": list(node.get_pos()),
                    "hpr": list(node.get_hpr()),
                    "scale": list(node.get_scale())
                },
                "is_container": is_container,
                "childs": []
            }

            # 🔹 Sérialiser les enfants récursivement
            for child in node.get_children():
                child_entry = serialize_node(child)
                if child_entry:
                    entry["childs"].append(child_entry)

            return entry

        # --- Construire la scène complète ---
        scene_data = []
        for node in self.panda.render.get_children():
            entry = serialize_node(node)
            if entry:
                scene_data.append(entry)

        # --- Sauvegarder en JSON ---
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(scene_data, f, indent=2, ensure_ascii=False)

        print(f"[SUCCÈS] Scène sauvegardée avec les fichiers et collections : {path}")
