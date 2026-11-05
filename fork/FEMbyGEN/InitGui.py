import FreeCAD
import FreeCADGui

#  Sadece Workbench degil FreeCADGui.Workbench olmali
class FEMbyGEN(FreeCADGui.Workbench):
    "FEMbyGEN workbench object"

    def __init__(self):
        self.icons_path = FreeCAD.getUserAppDataDir() + "Mod/FEMbyGEN/fembygen/icons/"
        self.__class__.Icon = self.icons_path + "icon.svg"
        self.__class__.MenuText = "FEMbyGEN"
        self.__class__.ToolTip = "Parametric FEM analysis"

        from PySide2 import QtCore
        QtCore.QDir.addSearchPath("icons", self.icons_path)

    def Initialize(self):
        from fembygen import Initiate, Alias, Generate, FEA, createGeo, Results, Topology
        self.list = ["Initiate", "Alias", "Generate", "FEA", "createGeo", "Results", "Topology"] 
        self.appendToolbar("Commands", self.list)  
        self.appendMenu("FEMbyGEN", self.list)  

    def Activated(self):
        pass

    def Deactivated(self):
        return

    def ContextMenu(self, recipient):
        self.appendContextMenu("My commands", self.list)  

    def GetClassName(self):
        return "Gui::PythonWorkbench"

FreeCADGui.addWorkbench(FEMbyGEN())