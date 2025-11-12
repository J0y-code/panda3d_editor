import traceback
import types
import asyncio
import time
import re
from pathlib import Path
from panda3d.bullet import *
from panda3d.core import *

import traceback
import asyncio
import re
from pathlib import Path

class Script:
    """
    Représente un script Python exécutable dans l’éditeur.

    Fonctionnalités :
      - Chargement depuis fichier ou inline
      - Namespace persistant entre exécutions
      - Reload automatique si fichier modifié
      - Détection automatique de type (module ou script)
      - Support async
      - Gestion d’erreurs avec traceback
    """

    def __init__(self, path: Path = None, code: str = None, context=None):
        self.path = Path(path) if path else None
        self.code = code or ""
        self.context = context or {}
        self.env = dict(self.context)  # espace d’exécution persistant
        self._last_modified = None
        self.type = "unknown"  # 'script' ou 'library'

    # -------------------------------------------------------------
    def detect_type(self):
        """Détecte si le script est un module à partir de 'ismodule = True'."""
        code = self.code.strip()
        header = "\n".join(code.splitlines()[:10])  # lire les 10 premières lignes

        if re.search(r"^\s*ismodule\s*=\s*True\s*$", header, re.MULTILINE):
            self.type = "library"
        else:
            self.type = "script"

    # -------------------------------------------------------------
    def load(self):
        """Charge le code depuis le fichier si celui-ci a changé."""
        if not self.path:
            raise ValueError("Aucun chemin de script défini.")
        try:
            mtime = self.path.stat().st_mtime
        except FileNotFoundError:
            print(f"[SCRIPT] Fichier introuvable : {self.path}")
            return

        if self._last_modified != mtime:
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.code = f.read()
                self._last_modified = mtime
                self.detect_type()
                print(f"[SCRIPT] Chargé : {self.path}  → Type : {self.type.upper()}")
            except Exception as e:
                print(f"[ERREUR] Lecture du script {self.path}: {e}")
                traceback.print_exc()
        else:
            print(f"[SCRIPT] Pas de changement détecté : {self.path}")

    # -------------------------------------------------------------
    def execute(self, reset_env=False):
        """
        Exécute le script dans un espace persistant.
        Si reset_env=True, recrée un namespace propre basé sur le contexte.
        """
        try:
            if self.type == "library":
                print(f"[SCRIPT] {self.path} est une bibliothèque (ismodule=True), non exécutée directement.")
                return

            if reset_env:
                self.env = dict(self.context)

            exec(self.code, self.env)

            print(f"[SCRIPT] Exécution terminée : {self.path or '<inline>'}")

        except Exception as e:
            msg = f"[SCRIPT ERROR] {self.path or '<inline>'} : {e}"
            print(msg)
            traceback.print_exc()

    # -------------------------------------------------------------
    def call(self, func_name: str, *args, **kwargs):
        """
        Appelle une fonction définie dans le script.
        Gère les fonctions async automatiquement.
        """
        func = self.env.get(func_name)
        if callable(func):
            try:
                result = func(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
                return result
            except Exception:
                print(f"[SCRIPT ERROR] lors de l'appel de {func_name}()")
                traceback.print_exc()
        else:
            print(f"[SCRIPT] Fonction introuvable : {func_name}")

    # -------------------------------------------------------------
    def reload(self):
        """Recharge et réexécute le script depuis le fichier s’il existe."""
        if self.path and self.path.exists():
            self.load()
            self.execute(reset_env=False)
        else:
            print(f"[SCRIPT] Impossible de recharger (fichier introuvable).")



from direct.task import TaskManagerGlobal

from pathlib import Path
from direct.task import TaskManagerGlobal

from pathlib import Path
from direct.task import TaskManagerGlobal

class ScriptManager:
    def __init__(self, editor_app, editor_camera=None):
        """
        editor_app : instance principale de l'éditeur (ShowBase)
        editor_camera : instance de EditorCamera (optionnelle)
        """
        self.editor_app = editor_app
        self.editor_camera = editor_camera  # <--- ✅ caméra d’édition
        self.scripts = {}
        self._registered_tasks = []

        # --- Contexte partagé avec tous les scripts ---
        self.context = {
            "app": editor_app,
            "base": editor_app,
            "render": editor_app.render,
            "loader": editor_app.loader,
            "console": getattr(editor_app.kivy_ui, "console", None),
            "register_task": self.register_task,
            "editor_camera" : self.editor_camera,
        }




    # -------------------------------------------------------------
    def register_task(self, func, name=None):
        """Permet aux scripts d’enregistrer une tâche Panda3D (TaskManagerGlobal)."""
        taskMgr = TaskManagerGlobal.taskMgr
        name = name or f"script_task_{len(self._registered_tasks)}"
        task = taskMgr.add(func, name)
        self._registered_tasks.append((name, task))
        print(f"[SCRIPT MGR] Task enregistrée : {name}")
        return task

    # -------------------------------------------------------------
    def add_script(self, name: str, path: Path = None, code: str = None):
        """Ajoute un script depuis un fichier ou une chaîne et l’exécute immédiatement."""
        script = Script(path=path, code=code, context=self.context)
        if path:
            script.load()
        script.execute()
        self.scripts[name] = script
        print(f"[SCRIPT MGR] Script ajouté : {name}")
        return script

    # -------------------------------------------------------------
    def run_script(self, path: Path):
        """Charge et exécute un script depuis un fichier immédiatement."""
        name = str(path)
        return self.add_script(name=name, path=path)

    # -------------------------------------------------------------
    def add_inline_script(self, name: str, code: str):
        """Ajoute et exécute un script défini à la volée (non stocké sur disque)."""
        return self.add_script(name=name, code=code)

    # -------------------------------------------------------------
    def call_function(self, name: str, func_name: str, *args, **kwargs):
        """Appelle une fonction d’un script déjà chargé."""
        script = self.scripts.get(name)
        if not script:
            print(f"[SCRIPT MGR] Script introuvable : {name}")
            return None
        return script.call(func_name, *args, **kwargs)

    # -------------------------------------------------------------
    def reload_all(self):
        """Recharge et réexécute tous les scripts."""
        for name, script in self.scripts.items():
            print(f"[SCRIPT MGR] Reload : {name}")
            script.reload()

    # -------------------------------------------------------------
    def clear_tasks(self):
        """Supprime toutes les tâches enregistrées par les scripts."""
        taskMgr = TaskManagerGlobal.taskMgr
        for name, _ in self._registered_tasks:
            taskMgr.remove(name)
            print(f"[SCRIPT MGR] Task supprimée : {name}")
        self._registered_tasks.clear()