import FreeCAD, FreeCADGui


class FEMbyGEN(Workbench):
    MenuText = "FEMbyGEN"
    ToolTip = "Parametric FEM analysis"
    Icon = FreeCAD.getUserAppDataDir() + "Mod/FEMbyGEN/icon.svg"

    def Initialize(self):
        """This function is executed when FreeCAD starts"""

        from fembygen import Initiate, Alias, Generate, FEA,createGeo, Results, Topology
        FreeCADGui.addIconPath(FreeCAD.getUserAppDataDir() + "Mod/FEMbyGEN/fembygen/icons/")

        self.list = ["Initiate", "Alias","Generate", "FEA","createGeo", "Results", "Topology"]  # A list of command names created in the line above

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
