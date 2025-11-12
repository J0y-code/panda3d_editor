try:
    from editor_camera import EditorCamera
except ImportError:
    from .editor_camera import EditorCamera

try:
    from core.ui.editor_ui import *
except ImportError:
    from .ui.editor_ui import *

from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import BulletWorld, BulletRigidBodyNode, BulletTriangleMesh, BulletTriangleMeshShape
from core.scripting.scriptmgr import ScriptManager
from panda3d.core import Vec4, Camera, NodePath


class EditorApp(ShowBase):
    def __init__(self):
        super().__init__()

        # --- Nettoyage des DisplayRegions par défaut ---
        # Désactive ou supprime la région par défaut de ShowBase
        '''try:
            default_dr = self.camNode.getDisplayRegion(0)
            default_dr.setActive(False)
        except Exception:
            pass'''

        # (Optionnel : tu peux aussi tout supprimer si Kivy n'est pas encore lancé)
        # self.win.removeAllDisplayRegions()

        # --- Création du viewport 3D principal ---
        x_min, x_max = 1-0.844, 0.844
        y_min, y_max = 0.2675, 0.891
        
        # Crée une DisplayRegion personnalisée pour l’éditeur
        self.viewport_region = self.win.makeDisplayRegion(x_min, x_max, y_min, y_max)
        self.viewport_region.setSort(1)  # après Kivy si besoin
        self.viewport_region.setClearColorActive(True)
        self.viewport_region.setClearColor(Vec4(0.5, 0.5, 0.5, 1))  # fond gris clair
        self.viewport_region.setClearDepthActive(True)

        from panda3d.core import PerspectiveLens

        # Crée une caméra dédiée
        self.editor_cam = Camera('EditorCamera')
        self.cameditor = NodePath(self.editor_cam)
        self.cameditor.reparentTo(self.camera)
        self.viewport_region.setCamera(self.cameditor)

        # Ajuste le lens
        lens = PerspectiveLens()
        # calculer le ratio de la display region
        region_width = (x_max - x_min) * self.win.getXSize()
        region_height = (y_max - y_min) * self.win.getYSize()
        lens.setAspectRatio(region_width / region_height)
        self.editor_cam.setLens(lens)



        # --- Instancie la caméra de l’éditeur ---
        self.editor_camera = EditorCamera(base=self, camera=self.cameditor)
        # View render, as seen by the default camera


        # --- Interface et scripts ---
        self.kivy_ui = EditorUI(panda=self, app=self.render)
        self.scripting = ScriptManager(self, editor_camera=self.editor_camera)
        self.kivy_ui.scripting = self.scripting

        # --- Debug : affiche toutes les DisplayRegions ---
        print("DisplayRegions actives :", self.win.getNumDisplayRegions())
        for i in range(self.win.getNumDisplayRegions()):
            dr = self.win.getDisplayRegion(i)
            print(f"{i} {dr.getDimensions()} active={dr.isActive()} sort={dr.getSort()}")

        # --- Lancer l'interface Kivy ---
        self.kivy_ui.run()
        




if __name__ == "__main__":
    app = EditorApp()
    app.run()
