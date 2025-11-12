from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.graphics import Color, Rectangle


class TransformToolbar(BoxLayout):
    """Barre d’outils pour activer les gizmos de transformation."""

    def __init__(self, editor, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=36, spacing=4, padding=[4, 4, 4, 4], **kwargs)
        self.editor = editor

        # Fond gris foncé
        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        btn_style = dict(
            size_hint=(None, 1),
            width=96,
            background_normal='',
            background_down='',
            background_color=(0.15, 0.15, 0.15, 1),
            color=(1, 1, 1, 1),
            font_size=13,
            group='transform_tool'
        )

        # --- Boutons principaux ---
        self.move_btn = ToggleButton(text="Place", **btn_style)
        self.rotate_btn = ToggleButton(text="Rotate", **btn_style)
        self.scale_btn = ToggleButton(text="Scale", **btn_style)

        # --- Liens avec les gizmos ---
        self.move_btn.bind(on_release=lambda *_: self.editor.activate_gizmo("move"))
        self.rotate_btn.bind(on_release=lambda *_: self.editor.activate_gizmo("rotate"))
        self.scale_btn.bind(on_release=lambda *_: self.editor.activate_gizmo("scale"))

        for btn in (self.move_btn, self.rotate_btn, self.scale_btn):
            self.add_widget(btn)

        self.add_widget(BoxLayout())  # espace flexible

    def _update_bg(self, *_):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def activate_tool(self, tool_name):
        """Active un gizmo selon le bouton sélectionné."""
        self.editor.activate_gizmo(tool_name)
