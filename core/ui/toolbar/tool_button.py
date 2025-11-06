from kivy.uix.togglebutton import ToggleButton

class ToolButton(ToggleButton):
    """Bouton de la barre d'outils pour activer/désactiver les gizmos."""
    def __init__(self, text, tool_name, editor, **kwargs):
        super().__init__(
            text=text,
            group='tool',
            size_hint=(None, 1),
            width=96,
            background_normal='',
            background_down='',
            background_color=(0.01, 0.01, 0.01, 1),
            color=(1, 1, 1, 1),
            font_size=13,
            **kwargs
        )
        self.editor = editor
        self.tool_name = tool_name
        self.bind(on_release=self.on_tool_selected)

    def on_tool_selected(self, *_):
        """Active ou désactive le gizmo correspondant."""
        if self.state == 'down':
            self.editor.activate_gizmo(self.tool_name)
        else:
            self.editor.deactivate_gizmos()
