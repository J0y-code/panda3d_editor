from pathlib import Path
import os
from kivy.uix.actionbar import ActionButton
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
import re
from typing import List
from panda3d.core import AmbientLight, DirectionalLight, PointLight, Spotlight, Vec4
from panda3d.core import PerspectiveLens

class Export:
    """
    Exporte la scène Panda3D actuelle en fichier .py.
    - Option : inclure une instance ShowBase (standalone) ou non.
    """

    def __init__(self, editor_app):
        self.editor_app = editor_app
        self.panda = editor_app.panda
        self.models = editor_app.models
        self.file_group = editor_app.menu.file_group

        # --- Boutons dans le menu Fichier ---
        self.export_btn = ActionButton(text="To python")
        self.file_group.add_widget(self.export_btn)

    def connect_events(self):
        self.export_btn.bind(on_release=self.export_scene)
        self.export_standalone_btn.bind(on_release=lambda x: self.export_scene(x, standalone=True))

    def serialize_lights(self) -> List[str]:
        """Retourne les lignes Python pour recréer les lumières dans la scène."""
        lines = []
        for light_np in self.panda.render.find_all_matches("**/+Light"):
            light = light_np.node()
            name = light_np.get_name()
            pos = light_np.get_pos()
            hpr = light_np.get_hpr()
            color = light.get_color()

            if isinstance(light, AmbientLight):
                lines.append(f"        # AmbientLight: {name}")
                lines.append(f"        {name}_light = AmbientLight('{name}')")
                lines.append(f"        {name}_light.setColor(Vec4({color[0]:.3f}, {color[1]:.3f}, {color[2]:.3f}, {color[3]:.3f}))")
                lines.append(f"        {name} = render.attachNewNode({name}_light)")
                lines.append(f"        render.setLight({name})")

            elif isinstance(light, DirectionalLight):
                lines.append(f"        # DirectionalLight: {name}")
                lines.append(f"        {name}_light = DirectionalLight('{name}')")
                lines.append(f"        {name}_light.setColor(Vec4({color[0]:.3f}, {color[1]:.3f}, {color[2]:.3f}, {color[3]:.3f}))")
                lines.append(f"        {name} = render.attachNewNode({name}_light)")
                lines.append(f"        {name}.setPos({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")
                lines.append(f"        {name}.setHpr({hpr[0]:.3f}, {hpr[1]:.3f}, {hpr[2]:.3f})")
                lines.append(f"        render.setLight({name})")

            elif isinstance(light, PointLight):
                lines.append(f"        # PointLight: {name}")
                lines.append(f"        {name}_light = PointLight('{name}')")
                lines.append(f"        {name}_light.setColor(Vec4({color[0]:.3f}, {color[1]:.3f}, {color[2]:.3f}, {color[3]:.3f}))")
                lines.append(f"        {name} = render.attachNewNode({name}_light)")
                lines.append(f"        {name}.setPos({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")
                lines.append(f"        render.setLight({name})")

            # Tu peux ajouter Spotlight ici si tu l'utilises
        return lines

    # -----------------------------------------------------------------------
    def export_scene(self, *args, standalone=False):
        """Popup pour choisir le fichier et options d'export
        
        Args:
            standalone (bool): Si True, exporte une version standalone avec ShowBase"""
        box = BoxLayout(orientation="vertical", spacing=5)

        chooser = FileChooserListView(filters=["*.py"], path=str(Path.cwd()))
        box.add_widget(chooser)

        # Text input to allow typing a filename directly
        name_box = BoxLayout(size_hint_y=None, height=40)
        name_input = TextInput(hint_text='Nom du fichier (optionnel)', multiline=False)
        name_box.add_widget(name_input)
        box.add_widget(name_box)

        # --- Option ShowBase ---
        opt_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40, padding=10)
        opt_label = Label(text="Inclure instance ShowBase :", size_hint_x=0.7)
        include_showbase_cb = CheckBox(active=True)
        opt_box.add_widget(opt_label)
        opt_box.add_widget(include_showbase_cb)
        box.add_widget(opt_box)

        # --- Boutons ---
        btn_box = BoxLayout(size_hint_y=None, height=40, spacing=10, padding=5)
        export_btn = Button(text="Exporter", background_color=(0.2, 0.5, 0.3, 1))
        cancel_btn = Button(text="Annuler", background_color=(0.3, 0.3, 0.3, 1))
        btn_box.add_widget(export_btn)
        btn_box.add_widget(cancel_btn)
        box.add_widget(btn_box)

        popup = Popup(title="Exporter la scène en .py", content=box, size_hint=(0.9, 0.9))
        popup.open()

        def do_export(*_):
            typed = name_input.text.strip() if name_input else ''
            if typed:
                filename = typed
            else:
                filename = chooser.selection[0] if chooser.selection else "scene_export.py"
            path = Path(filename)
            if not path.suffix == ".py":
                path = path.with_suffix(".py")
            include_showbase = include_showbase_cb.active
            self._write_py_scene(path, include_showbase)
            popup.dismiss()

        export_btn.bind(on_release=do_export)
        cancel_btn.bind(on_release=lambda *_: popup.dismiss())

    # -----------------------------------------------------------------------
    from pathlib import Path
    import re

    def _write_py_scene(self, path: Path, include_showbase: bool):
        """Génère un fichier Python de la scène, indépendant de self.models"""
        print(f"[Export] Exportation vers {path} (ShowBase inclus: {include_showbase})")

        def sanitize_name(name: str) -> str:
            """Rend un nom valide pour une variable Python."""
            name = re.sub(r"[^0-9a-zA-Z_]", "_", name)
            if name and name[0].isdigit():
                name = "_" + name
            return name

        def serialize_node(node, parent_var: str, level: int = 0):
            """Retourne une liste de lignes Python avec indentation correcte"""
            node_name = node.get_name()
            safe_name = sanitize_name(node_name)
            
            # Ignorer nodes techniques
            if node_name.lower() in {"camera", "light", "directionallight"}:
                return []
                
            indent = " " * (level * 4)
            lines = []
            
            # Vérifier si le nœud est dans self.models
            model_info = self.models.get(node_name)
            
            if model_info is not None and isinstance(model_info, dict):
                if "file" in model_info and isinstance(model_info["file"], dict) and "path" in model_info["file"]:
                    # C'est un modèle chargé, on utilise loadModel
                    target_path = Path(model_info["file"]["path"])
                    source_path = Path(path).parent  # Le dossier où sera le fichier exporté
                    
                    try:
                        # Calculer le chemin relatif entre le fichier exporté et le modèle
                        rel_path = os.path.relpath(target_path, source_path)
                        # Convertir en format avec forward slashes
                        model_path = str(Path(rel_path).as_posix())
                    except ValueError:
                        # En cas d'erreur, utiliser le chemin absolu
                        model_path = str(target_path.as_posix())
                        
                    lines.append(f"{indent}# Chargement du modèle {node_name}")
                    lines.append(f"{indent}{safe_name}_model = loader.loadModel('{model_path}')")
                    lines.append(f"{indent}{safe_name} = {parent_var}.attachNewNode('{node_name}')")
                    
                    # Appliquer les transformations au nœud parent
                    pos = node.getPos()
                    hpr = node.getHpr()
                    scale = node.getScale()
                    lines.append(f"{indent}{safe_name}.setPos({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")
                    lines.append(f"{indent}{safe_name}.setHpr({hpr[0]:.3f}, {hpr[1]:.3f}, {hpr[2]:.3f})")
                    lines.append(f"{indent}{safe_name}.setScale({scale[0]:.3f}, {scale[1]:.3f}, {scale[2]:.3f})")
                    
                    # Reparenter le modèle
                    lines.append(f"{indent}{safe_name}_model.reparentTo({safe_name})")
                    
                    # Pour chaque enfant du modèle, préserver ses transformations
                    model_children = node.get_children()
                    if model_children:
                        lines.append(f"{indent}# Configuration des parties du modèle")
                        for child in model_children:
                            if child.get_name() != node.get_name():  # Éviter le nœud racine
                                child_name = child.get_name()
                                safe_child_name = sanitize_name(child_name)
                                # Obtenir le chemin relatif depuis la racine du modèle
                                rel_path = ''
                                current = child
                                while current and current != node:
                                    if rel_path:
                                        rel_path = current.get_name() + '/' + rel_path
                                    else:
                                        rel_path = current.get_name()
                                    current = current.get_parent()
                                lines.append(f"{indent}# Configuration de {child_name}")
                                lines.append(f"{indent}{safe_name}_{safe_child_name} = {safe_name}_model.find('{rel_path}')")
                                # Appliquer les transformations de l'enfant
                                pos = child.get_pos(node)  # Position relative au parent
                                hpr = child.get_hpr(node)  # Rotation relative au parent
                                scale = child.get_scale(node)  # Échelle relative au parent
                                lines.append(f"{indent}if {safe_name}_{safe_child_name}:")
                                lines.append(f"{indent}    {safe_name}_{safe_child_name}.setPos({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")
                                lines.append(f"{indent}    {safe_name}_{safe_child_name}.setHpr({hpr[0]:.3f}, {hpr[1]:.3f}, {hpr[2]:.3f})")
                                lines.append(f"{indent}    {safe_name}_{safe_child_name}.setScale({scale[0]:.3f}, {scale[1]:.3f}, {scale[2]:.3f})")
            else:
                # C'est un nœud sans modèle, vérifier s'il a des enfants
                has_model_children = False
                for child in node.get_children():
                    child_name = child.get_name()
                    child_info = self.models.get(child_name)
                    if child_info is not None and isinstance(child_info, dict) and "file" in child_info:
                        has_model_children = True
                        break

                if has_model_children:
                    # Créer le nœud seulement s'il a des enfants qui sont des modèles
                    lines.append(f"{indent}{safe_name} = {parent_var}.attachNewNode('{node_name}')")
                else:
                    # Ignorer les nœuds vides sans enfants modèles
                    return []

            # Ajouter les transformations si le nœud a été créé
            if lines:
                pos = node.get_pos()
                hpr = node.get_hpr()
                scale = node.get_scale()
                lines.append(f"{indent}{safe_name}.setPos({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")
                lines.append(f"{indent}{safe_name}.setHpr({hpr[0]:.3f}, {hpr[1]:.3f}, {hpr[2]:.3f})")
                lines.append(f"{indent}{safe_name}.setScale({scale[0]:.3f}, {scale[1]:.3f}, {scale[2]:.3f})")

            # Enfants récursifs
            for child in node.get_children(): 
                child_lines = serialize_node(child, safe_name, level + 1)
                lines.extend(child_lines)

            return lines


        # --- Construction du code principal ---
        lines = [
            "# --- Scene exportée depuis Panda3D Editor ---",
            "from pathlib import Path",
            "import os",
            "from panda3d.core import *",
            "",
            "# Chemin du dossier du projet",
            f"PROJECT_ROOT = Path('{Path(self.editor_app.project_hierarchic_sidebar.project_root).as_posix()}')",
        ]

        if include_showbase:
            lines.append("from direct.showbase.ShowBase import ShowBase\n")
            lines.append("class ExportedScene(ShowBase):")
            lines.append("    def __init__(self):")
            lines.append("        super().__init__()")
            lines.append("        parent = render\n")
            base_level = 2  # 2 niveaux = 8 espaces
        else:
            lines.append("\n# Utiliser 'parent' comme NodePath parent (ex: render)")
            lines.append("def load_scene(parent):")
            base_level = 1  # 1 niveau = 4 espaces

        # Sérialisation de tous les enfants de render
        for node in self.panda.render.get_children():
            lines.extend(serialize_node(node, "parent", base_level))

        light_lines = self.serialize_lights()
        lines.extend(light_lines)

        # Fin de fichier
        if include_showbase:
            lines.append("\nif __name__ == '__main__':")
            lines.append("    app = ExportedScene()")
            lines.append("    app.run()")
        else:
            lines.append("    return parent")

        # Écriture dans le fichier
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"[SUCCÈS] Scène exportée vers {path}")
