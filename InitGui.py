import FreeCAD
import FreeCADGui

translate = FreeCAD.Qt.translate
def QT_TRANSLATE_NOOP(context, text):
    return text
import FreeCADGui
import os
FreeCADGui.addLanguagePath(os.path.join(FreeCAD.getUserAppDataDir(),"\Mod\FEMbyGEN\fembygen\translations"))
FreeCADGui.updateLocale()

class FEMbyGEN(Workbench):
    "FEMbyGEN workbench object"

    def __init__(self):
        self.__class__.Icon = FreeCAD.getUserAppDataDir() + "Mod/FEMbyGEN/fembygen/icons/icon.svg"
        self.__class__.MenuText = "FEMbyGEN"
        self.__class__.ToolTip = "Parametric FEM analysis"

        from PySide import QtCore
        ICONS_PATH = FreeCAD.getUserAppDataDir() + "Mod/FEMbyGEN/fembygen/icons/"
        QtCore.QDir.addSearchPath("icons", ICONS_PATH)

    def Initialize(self):
        """This function is executed when FreeCAD starts"""

        from fembygen import Initiate, Alias, Generate, FEA, createGeo, Results, Topology
        self.list = ["Initiate", "Alias", "Generate", "FEA", "createGeo", "Results",
                     "Topology"]  # A list of command names created in the line above

        self.appendToolbar("Commands", self.list)  # creates a new toolbar with your commands
        self.appendMenu("FEMbyGEN", self.list)  # creates a new menu

    def Activated(self):
        """This function is executed when the workbench is activated"""
        return

    def Deactivated(self):
        """This function is executed when the workbench is deactivated"""
        return

    def ContextMenu(self, recipient):
        """This is executed whenever the user right-clicks on screen"""
        # "recipient" will be either "view" or "tree"
        self.appendContextMenu("My commands", self.list)  # add commands to the context menu

    def GetClassName(self):
        # This function is mandatory if this is a full python workbench
        # This is not a template, the returned string should be exactly "Gui::PythonWorkbench"
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(FEMbyGEN())
