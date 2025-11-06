from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle

class BaseToolbar(BoxLayout):
    """Barre d'outils de base avec un fond gris et padding."""
    def __init__(self, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None,
            height=36,
            spacing=4,
            padding=[4, 4, 4, 4],
            **kwargs
        )

        # Fond gris foncé
        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update_bg)
        self.bind(size=self._update_bg)

    def _update_bg(self, *_):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
