from pathlib import Path
from panda3d.core import Filename
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle

try:
    from core.panda3d_kivy.app import App
except ImportError:
    from ..panda3d_kivy.app import App

from .side_bars.properties import PropertiesSidebar
from .side_bars.world_hierarchy import HierarchySidebar
from .side_bars.project_hierarchy import ProjectHierarchySidebar
from .script_console import KivyConsole
from .onglets import ClosableTabBar
from .menubar.menu import MenuBar
from .toolbar import TransformToolbar
from core.gizmos.gizmos import Gizmos
from .script_ui import ScriptEditor
from panda3d.core import Point2
from panda3d.core import DirectionalLight, AmbientLight, Vec4, PointLight

class EditorUI(App):
    """
    UI principale de l'éditeur utilisant la nouvelle classe Gizmos.
    """

    current_scene_file: Path = None

    def __init__(self, panda, app):
        super().__init__(panda)
        self.panda = panda
        self.app = app
        self.scripting = None
        self.current_scene_file = None
        self.models = {}  # registre des modèles chargés

        # --- Gizmo unique pour tout type de transformation ---
        self.gizmo = Gizmos(self.panda.render)
        self.gizmo.detach()
        self.current_gizmo_mode = None  # 'translate', 'rotate', 'scale'

        self.is_running = False

    def build(self):
        root = BoxLayout(orientation='vertical')

        # --- Menu ---
        self.menu = MenuBar(editor_ui=self)
        root.add_widget(self.menu)

        # --- Toolbar ---
        self.toolbar = TransformToolbar(editor=self)
        root.add_widget(self.toolbar)

        # --- Onglets ---
        self.script_tab_bar = ClosableTabBar(size_hint_y=None, height=28)
        self.script_tab_bar.add_tab("Viewport", action=self.show_default_viewport, erasable=False)
        root.add_widget(self.script_tab_bar)

        # --- Main Area ---
        main_area = BoxLayout(orientation='horizontal', spacing=0, padding=0)

        # Barre projet (gauche)
        self.project_hierarchic_sidebar = ProjectHierarchySidebar(
            panda_app=self.panda,
            ui_app=self,
            project_root=str('default')
        )
        main_area.add_widget(self.project_hierarchic_sidebar)

        # Viewport (centre)
        self.viewport_box = BoxLayout()
        with self.viewport_box.canvas.before:
            Color(0, 0, 0, 0)
            self.viewport_rect = Rectangle(pos=self.viewport_box.pos, size=self.viewport_box.size)
        self.viewport_box.bind(pos=lambda w, *a: setattr(self.viewport_rect, 'pos', w.pos))
        self.viewport_box.bind(size=lambda w, *a: setattr(self.viewport_rect, 'size', w.size))
        main_area.add_widget(self.viewport_box)

        # Panneau droit (hiérarchie + propriétés)
        rightpanel = BoxLayout(orientation='vertical', spacing=0, padding=0, size_hint_x=0.15)

        self.sidebar = HierarchySidebar(self, app=self.app)
        rightpanel.add_widget(self.sidebar)

        self.properties_sidebar = PropertiesSidebar(editor_app=self)
        rightpanel.add_widget(self.properties_sidebar)

        main_area.add_widget(rightpanel)
        root.add_widget(main_area)


        # --- Console (bas) ---
        if True:
            console_box = BoxLayout(orientation='vertical', size_hint_y=0.25)
            self.console = KivyConsole()
            console_box.add_widget(self.console)
            root.add_widget(console_box)

        # --- Setup menu ---
        self.menu._setup_file_actions()
        self.setup_mouse_controls()


        self.set_ambient_light()
        self.sidebar.refresh_hierarchy()

        return root

    # --- Scripts ---
    def open_script(self, path: str):
        name = Path(path).name
        if name in self.script_tab_bar.contents:
            self.script_tab_bar.contents[name]()
            return

        editor_widget = ScriptEditor(file_path=path)

        def show_editor(_=None):
            self.viewport_box.clear_widgets()
            self.viewport_box.add_widget(editor_widget)
            self.panda.editor_camera.is_on_script = True

        def close_editor():
            if editor_widget in self.viewport_box.children:
                self.viewport_box.remove_widget(editor_widget)
            self.panda.editor_camera.is_on_script = False

        self.script_tab_bar.add_tab(name, action=show_editor, on_close=close_editor)

    def show_default_viewport(self, _=None):
        """Remet le viewport à son état par défaut (sans script)."""
        self.viewport_box.clear_widgets()
        self.panda.editor_camera.is_on_script = False

    # --- Gizmo ---
    def activate_gizmo(self, tool):
        """Active le gizmo sur le node sélectionné et définit le mode."""
        selected = self.sidebar.selected_node
        if selected is None:
            # rien à sélectionner => on désactive le gizmo
            self.gizmo.detach()
            self.current_gizmo_mode = None
            return

        # stocke le mode actif
        if tool == "move":
            self.current_gizmo_mode = "translate"
            print('translate')
        elif tool == "rotate":
            self.current_gizmo_mode = "rotate"
        elif tool == "scale":
            self.current_gizmo_mode = "scale"

        self.gizmo.set_target(selected)
        print(selected)
        self.gizmo._node.setScale(2.0)  # augmente la taille pour tester
        self.gizmo.attach_to(selected)
        self.gizmo.show()

    def deactivate_gizmos(self):
        """Désactive le gizmo."""
        self.gizmo.detach()
        self.current_gizmo_mode = None

    def setup_mouse_controls(self):
        self.panda.accept("mouse1", self.on_mouse_click)
        self.panda.accept("mouse1-up", self.on_mouse_release)
        self.panda.taskMgr.add(self.mouse_task, "update_gizmo_drag")

        self.dragging = False

    def get_mouse_ndc(self):
        if not self.panda.mouseWatcherNode.hasMouse():
            return None
        x = self.panda.mouseWatcherNode.getMouseX()
        y = self.panda.mouseWatcherNode.getMouseY()
        return Point2(x, y)

    def on_mouse_click(self):
        if self.gizmo is None or self.current_gizmo_mode is None:
            return
        mouse_pos = self.get_mouse_ndc()
        if mouse_pos is None:
            return
        ok = self.gizmo.start_drag(mouse_pos, self.panda, self.current_gizmo_mode)
        if ok:
            print("[EditorUI] Gizmo drag started")
            self.dragging = True

    def on_mouse_release(self):
        if self.dragging:
            self.gizmo.stop_drag()
            print("[EditorUI] Gizmo drag stopped")
            self.dragging = False

    def mouse_task(self, task):
        if self.dragging:
            mouse_pos = self.get_mouse_ndc()
            if mouse_pos:
                self.gizmo.update_drag(mouse_pos, self.panda)
        return task.cont

    def run_all_scripts(self):
        """
        Exécute tous les scripts Python (.py) dans le dossier du projet actuel.
        Chaque script est exécuté dans un try/except pour isoler les erreurs.
        """
        if self.is_running:
            print("[INFO] already running")
            return

        project_path = Path(self.project_hierarchic_sidebar.project_root)
        if not project_path.exists():
            print(f"[EditorUI] Dossier projet introuvable : {project_path}")
            return

        py_files = list(project_path.rglob("*.py"))
        if not py_files:
            print("[EditorUI] Aucun script Python trouvé dans le projet.")
            return

        for script_file in py_files:
            try:
                print(f"[EditorUI] Exécution du script : {script_file}")
                self.scripting.run_script(script_file)
                self.is_running = True
            except Exception as e:
                print(f"[EditorUI] Erreur lors de l'exécution de {script_file}: {e}")

    def stop_all_scripts(self):
        """
        Arrête tous les scripts et tasks créées via ScriptManager.register_task().
        """
        print("[EditorUI] Arrêt de tous les scripts et tâches...")

        try:
            # Stop tasks enregistrées
            if hasattr(self, "scripting") and hasattr(self.scripting, "_registered_tasks"):
                from direct.task import TaskManagerGlobal
                taskMgr = TaskManagerGlobal.taskMgr

                for name, task in list(self.scripting._registered_tasks):
                    try:
                        taskMgr.remove(name)
                        print(f"[EditorUI] Task stoppée : {name}")
                    except Exception as e:
                        print(f"[EditorUI] Erreur lors de l’arrêt de {name} : {e}")

                self.scripting._registered_tasks.clear()
                print("[EditorUI] Toutes les tasks enregistrées ont été stoppées.")

            # Appeler stop() sur chaque script actif
            if hasattr(self.scripting, "scripts"):
                for name, script in list(self.scripting.scripts.items()):
                    stop_func = script.locals.get("stop") if hasattr(script, "locals") else None
                    if callable(stop_func):
                        try:
                            stop_func()
                            print(f"[EditorUI] Script stoppé : {name}")
                        except Exception as e:
                            print(f"[EditorUI] Erreur lors de stop() sur {name}: {e}")
                self.scripting.scripts.clear()
                print("[EditorUI] Cache des scripts vidé.")

        except Exception as e:
            print(f"[EditorUI] Erreur lors de l’arrêt des scripts : {e}")

        self.is_running = False
        print("[EditorUI] Tous les scripts et tâches ont été arrêtés.")

    # ---------------- Lights utilities ----------------
    def create_sun(self, name='Sun', color=(1.0, 0.98, 0.9, 1.0), hpr=(0, -45, 0)):
        """Crée une DirectionalLight (soleil) et l'attache à render.

        Returns the NodePath of the light.
        """
        dl = DirectionalLight(name)
        dl.setColor(Vec4(*color))
        dl_np = self.panda.render.attachNewNode(dl)
        dl_np.setHpr(*hpr)
        self.panda.render.setLight(dl_np)
        print(f"[EditorUI] Soleil ajouté : {name}")
        self.sidebar.refresh_hierarchy()
        return dl_np

    def set_ambient_light(self, color=(1.0, 0.98, 0.9, 1.0), name='Ambient'):
        """Ajoute ou remplace une AmbientLight globale.
        Retourne le NodePath de l'ambient light.
        """
        al = AmbientLight(name)
        al.setColor(Vec4(*color))
        al_np = self.panda.render.attachNewNode(al)
        self.panda.render.setLight(al_np)
        print(f"[EditorUI] Ambient light ajouté : {name}")
        self.sidebar.refresh_hierarchy()
        return al_np

    def add_light_to_model(self, model_nodepath, kind='point', color=(1,1,1,1), name_prefix='Light'):
        """Ajoute une light (point ou spot) au NodePath du modèle.

        model_nodepath: NodePath cible
        kind: 'point' ou 'spot' (point par défaut)
        """
        if model_nodepath is None:
            print("[EditorUI] Aucun modèle fourni pour ajouter une light.")
            return None

        if kind == 'point':
            pl = PointLight(f"{name_prefix}_{model_nodepath.get_name()}")
            pl.setColor(Vec4(*color))
            # Attacher la light à render (global) mais la positionner au modèle
            pl_np = self.panda.render.attachNewNode(pl)
            # positioner la light au centre du modèle dans les coordonnées de render
            try:
                pos = model_nodepath.get_pos(self.panda.render)
                pl_np.setPos(pos)
            except Exception:
                # fallback: position locale
                pl_np.setPos(model_nodepath.get_pos())
            # Appliquer la light globalement
            self.panda.render.setLight(pl_np)
            print(f"[EditorUI] Point light (attachée à render) positionnée sur {model_nodepath.get_name()}")
            # Rafraîchir la hiérarchie pour afficher la nouvelle light
            try:
                self.sidebar.refresh_hierarchy()
            except Exception:
                pass
            return pl_np
        else:
            # Par défaut fallback sur point light
            return self.add_light_to_model(model_nodepath, kind='point', color=color, name_prefix=name_prefix)