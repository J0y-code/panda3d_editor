from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.uix.scrollview import ScrollView

class ClosableTabBar(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', **kwargs)

        # Rectangle de fond pour toute la barre
        with self.canvas.before:
            Color(0.2, 0.2, 0.2, 1)  # gris foncé
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda w, *a: setattr(self.bg_rect, 'pos', self.pos))
        self.bind(size=lambda w, *a: setattr(self.bg_rect, 'size', self.size))

        self.tab_bar = BoxLayout(size_hint_y=1, spacing=2)
        scroll = ScrollView(size_hint=(1,1), bar_width=8)
        scroll.add_widget(self.tab_bar)
        self.add_widget(scroll)
        self.contents = {}  # nom_onglet -> callback à exécuter

    def add_tab(self, name, erasable=True, action=None, on_close=None):
        """
        Ajoute un onglet. `action` est appelée au clic sur le titre.
        `on_close` est une fonction appelée quand on ferme l'onglet.
        """
        tab_box = BoxLayout(size_hint_x=None, width=150, spacing=0)
        btn_title = Button(text=name, size_hint_x=0.8, background_color=(0, 0, 0, 1))
        tab_box.add_widget(btn_title)

        if erasable:
            btn_close = Button(text="X", size_hint_x=0.2, background_color=(1, 0, 0, 1))

            def close_tab(instance):
                # Supprime le widget de la barre
                self.tab_bar.remove_widget(tab_box)
                # Supprime l'action enregistrée
                if name in self.contents:
                    del self.contents[name]
                # Appelle callback supplémentaire (ex: fermer le script)
                if on_close:
                    on_close()

            btn_close.bind(on_press=close_tab)
            tab_box.add_widget(btn_close)

        self.tab_bar.add_widget(tab_box)

        # Enregistre l’action du clic sur le titre
        if action:
            self.contents[name] = action
            btn_title.bind(on_press=lambda inst, n=name: self.contents[n](n))

