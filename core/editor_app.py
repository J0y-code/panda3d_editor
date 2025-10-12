try:
    from editor_camera import EditorCamera
except ImportError:
    from .editor_camera import EditorCamera

try:
    from editor_ui import *
except ImportError:
    from .editor_ui import *


class EditorApp(ShowBase):
    def __init__(self):
        super().__init__()

        # Crée l'UI Kivy
        self.kivy_ui = EditorUI(panda=self, app=self.render)

        # Zone viewport : adapter selon la taille des sidebars (propriétés + hiérarchie)
        left_margin = 0.15  # largeur PropertiesSidebar
        right_margin = 0.15 # largeur HierarchySidebar
        viewport_width = 1.0 - left_margin - right_margin
        self.editor_camera = EditorCamera(
            base=self,
            viewport_area=(left_margin, 0.0, viewport_width, 1.0)
        )

        # Lancer l'UI
        self.kivy_ui.run()


if __name__ == "__main__":
    app = EditorApp()
    app.run()
