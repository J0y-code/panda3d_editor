from kivy.uix.codeinput import CodeInput
from pygments.lexers import PythonLexer

class ScriptConsole(BoxLayout):
    def __init__(self, editor_app=None, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.editor_app = editor_app

        # --- Zone de code ---
        self.code_input = CodeInput(lexer=PythonLexer(), font_size=14, size_hint_y=0.9)
        self.add_widget(self.code_input)

        # --- Boutons ---
        btn_run = Button(text="▶ Exécuter", size_hint_y=0.1, background_color=(0.2,0.6,0.2,1))
        btn_run.bind(on_release=self.run_script)
        self.add_widget(btn_run)

    def run_script(self, *args):
        code = self.code_input.text
        if not code.strip():
            return

        try:
            # 🔹 Créer un contexte local pour le script
            context = {
                "app": self.editor_app,
                "render": self.editor_app.panda.render,
                "loader": self.editor_app.panda.loader,
                "selected": getattr(self.editor_app.properties_sidebar, "selected_node", None),
            }
            exec(code, context)
            print("[SCRIPT] Exécution réussie ✅")
        except Exception as e:
            print(f"[ERREUR SCRIPT] {e}")