# core/scripting/script.py
import traceback
import types
from pathlib import Path


class Script:
    """
    Représente un script Python unique pouvant être exécuté dans l'éditeur.
    """
    def __init__(self, path: Path = None, code: str = None, context=None):
        """
        :param path: Chemin du fichier du script (facultatif)
        :param code: Code source (facultatif)
        :param context: Dictionnaire d'environnement partagé (ex: {'app': app, 'render': render})
        """
        self.path = Path(path) if path else None
        self.code = code or ""
        self.context = context or {}
        self.locals = {}  # Variables locales spécifiques à ce script

    def load(self):
        """Charge le code du script depuis le fichier associé."""
        if not self.path:
            raise ValueError("Aucun chemin de script défini.")
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.code = f.read()
            print(f"[SCRIPT] Chargé : {self.path}")
        except Exception as e:
            print(f"[ERREUR] Lecture du script {self.path}: {e}")

    def execute(self):
        """Exécute le code du script dans un environnement isolé mais avec le contexte global."""
        try:
            env = dict(self.context)
            env.update(self.locals)
            exec(self.code, env)
            self.locals.update(env)
            print(f"[SCRIPT] Exécution terminée : {self.path or '<inline>'}")
        except Exception:
            print(f"[ERREUR] Dans le script {self.path or '<inline>'}:")
            traceback.print_exc()

    def call(self, func_name: str, *args, **kwargs):
        """Appelle une fonction définie dans le script."""
        func = self.locals.get(func_name)
        if isinstance(func, types.FunctionType):
            try:
                return func(*args, **kwargs)
            except Exception:
                traceback.print_exc()
        else:
            print(f"[SCRIPT] Fonction introuvable : {func_name}")

    def reload(self):
        """Recharge et réexécute le script depuis son fichier."""
        if self.path and self.path.exists():
            self.load()
            self.execute()
        else:
            print("[SCRIPT] Impossible de recharger (fichier introuvable).")