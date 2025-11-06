from core.editor_app import EditorApp
from panda3d.core import load_prc_file

load_prc_file("core/config/Config.prc")

if __name__ == "__main__":
    app = EditorApp()
    app.run()
