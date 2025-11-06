from kivy.base import runTouchApp
from kivy.lang import Builder
from kivy.properties import (
    ObjectProperty, StringProperty, ListProperty, NumericProperty
)
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
import sys

Builder.load_string('''
<KivyConsole>:
    orientation: 'vertical'
    spacing: 2
    canvas.before:
        Color:
            rgba: root.background_color
        Rectangle:
            pos: self.pos
            size: self.size

    # Barre du haut
    BoxLayout:
        size_hint_y: None
        height: 28
        padding: [4, 2]
        spacing: 4
        canvas.before:
            Color:
                rgba: 0.1, 0.1, 0.1, 1
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: "Console"
            color: 0.8, 0.8, 0.8, 1
            bold: True
            halign: 'left'
            valign: 'middle'
            size_hint_x: 1
            text_size: self.size

        Button:
            text: "Effacer"
            size_hint_x: None
            width: 80
            background_normal: ''
            background_color: (0.3, 0.3, 0.3, 1)
            color: (1, 1, 1, 1)
            font_size: 12
            on_release: root.clear()

    ScrollView:
        id: scroll_view
        bar_width: 8
        scroll_type: ['bars', 'content']
        do_scroll_x: False

        Label:
            id: console_label
            text: root.log_text
            markup: True
            size_hint_y: None
            text_size: self.width - 12, None  # 🔹 moins de largeur pour éviter le clipping
            height: self.texture_size[1]
            color: root.foreground_color
            font_name: root.font_name
            font_size: root.font_size
            halign: 'left'       # 🔹 alignement horizontal
            valign: 'top'        # 🔹 alignement vertical
            padding: 6, 4        # 🔹 petit espace interne
''')

class KivyConsole(BoxLayout):
    """Console de logs avec redirection stdout/stderr et coloration."""

    scroll_view = ObjectProperty(None)
    console_label = ObjectProperty(None)
    log_text = StringProperty("")

    foreground_color = ListProperty((1, 1, 1, 1))
    background_color = ListProperty((0, 0, 0, 1))
    font_name = StringProperty("Roboto")
    font_size = NumericProperty(13)
    max_lines = NumericProperty(500)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._post_init)

    def _post_init(self, *args):
        self.scroll_view = self.ids.scroll_view
        self.console_label = self.ids.console_label
        self.console_label.markup = True  # 🔹 Assure la coloration
        self._scroll_trigger = Clock.create_trigger(self.scroll_to_bottom, 0.05)

        # 🔹 Retarde la redirection pour éviter d’écrire avant que le Label soit prêt
        Clock.schedule_once(lambda dt: self._redirect_streams(), 0.1)

    def _redirect_streams(self):
        sys.stdout = self
        sys.stderr = self

    def write(self, text):
        """Affiche du texte dans la console."""
        if not text.strip():
            return

        # Coloration
        if "ERROR" in text or "ERREUR" in text:
            text = f"[color=ff5555]{text}[/color]"
        elif "WARN" in text or "WARNING" in text:
            text = f"[color=ffaa00]{text}[/color]"
        elif "INFO" in text:
            text = f"[color=55ff55]{text}[/color]"

        self.log_text += text + "\n"

        # Limite du buffer
        lines = self.log_text.splitlines()
        if len(lines) > self.max_lines:
            lines = lines[-self.max_lines:]
            self.log_text = "\n".join(lines)

        self._scroll_trigger()

    def flush(self):
        pass

    def clear(self):
        self.log_text = ""

    def scroll_to_bottom(self, *args):
        if self.scroll_view:
            self.scroll_view.scroll_y = 0

    def append(self, text):
        self.write("\n" + text)


# Test rapide
if __name__ == "__main__":
    console = KivyConsole()
    Clock.schedule_once(lambda dt: print("[INFO] Console initialisée."), 1)
    Clock.schedule_once(lambda dt: print("[WARN] Ceci est un avertissement."), 2)
    Clock.schedule_once(lambda dt: print("[ERROR] Exemple d’erreur."), 3)
    runTouchApp(console)
