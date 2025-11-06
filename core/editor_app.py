try:
    from editor_camera import EditorCamera
except ImportError:
    from .editor_camera import EditorCamera

try:
    from core.ui.editor_ui import *
except ImportError:
    from .ui.editor_ui import *

from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import BulletWorld, BulletRigidBodyNode, BulletTriangleMesh, BulletTriangleMeshShape
from core.scripting.scriptmgr import ScriptManager


class EditorApp(ShowBase):
    def __init__(self):
        super().__init__()

        # Crée l'UI Kivy
        left_margin = 0.115  # largeur PropertiesSidebar
        right_margin = 0.15 # largeur HierarchySidebar
        viewport_width = 1.15 - left_margin - right_margin
        self.editor_camera = EditorCamera(
            base=self,
            viewport_area=(left_margin, 0.0, viewport_width, 0.82)
        )
        self.kivy_ui = EditorUI(panda=self, app=self.render)
        self.scripting = ScriptManager(self, editor_camera=self.editor_camera)
        self.kivy_ui.scripting = self.scripting
        # Zone viewport : adapter selon la taille des sidebars (propriétés + hiérarchie)


        # Lancer l'UI
        self.kivy_ui.run()


if __name__ == "__main__":
    app = EditorApp()
    app.run()
