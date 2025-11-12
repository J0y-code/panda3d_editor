from kivy.uix.popup import Popup
from kivy.uix.codeinput import CodeInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.core.window import Window
from pygments.lexers import PythonLexer

class CodeEditor(CodeInput):
    """
    Sous-classe de CodeInput qui gère les raccourcis clavier :
    - Ctrl + + / =  -> augmenter la taille de police
    - Ctrl + -      -> diminuer la taille de police
    - Ctrl + S      -> sauvegarder le script
    Retourne True pour stopper la propagation quand on gère le raccourci.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.on_save = None  # callback pour sauvegarder (assigné par ScriptEditor)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if modifiers and 'ctrl' in modifiers:
            # déterminer un code numérique pour la touche : privilégier 'text'
            if text:
                try:
                    key_num = ord(text)
                except Exception:
                    key_num = keycode[1]
            else:
                key_num = keycode[1]

            # codes pour + , - , = et Ctrl+S
            increase_keys = (43, 61, 270)   # + , = , keypad plus
            decrease_keys = (45, 269)       # - , keypad minus
            save_keys     = (115, )         # 's' minuscule -> ord('s')=115

            if key_num in increase_keys:
                self.font_size = max(6, self.font_size + 1)
                return True
            if key_num in decrease_keys:
                self.font_size = max(6, self.font_size - 1)
                return True
            if key_num in save_keys:
                if self.on_save:
                    self.on_save()
                    return True  # empêche la propagation
        return super().keyboard_on_key_down(window, keycode, text, modifiers)



class ScriptEditor(BoxLayout):
    def __init__(self, file_path=None, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.file_path = file_path

        self.code_input = CodeEditor(
            lexer=PythonLexer(),
            tab_width=4,
            font_size=14,
            foreground_color=(1, 1, 1, 1),
            background_color=(0.1, 0.1, 0.1, 1)
        )

        # Assigner le callback de sauvegarde
        self.code_input.on_save = self.save

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.code_input.text = f.read()
            except Exception as e:
                print(f"[ERREUR] Impossible de charger {file_path}: {e}")

        self.add_widget(self.code_input)

    def save(self):
        if self.file_path:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(self.code_input.text)
            print(f"[ScriptEditor] Sauvegardé {self.file_path}")
        else:
            print("[ScriptEditor] Aucun fichier défini, impossible de sauvegarder.")


    def close_editor(self, *args):
        # Supprime ce widget du parent
        if self.parent:
            self.parent.remove_widget(self)