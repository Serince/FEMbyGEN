import FreeCAD
import FreeCADGui


class AliasCommand():
    """Analyse the generated parts"""

    def GetResources(self):
        return {'Pixmap': FreeCAD.getUserAppDataDir() +'Mod/FEMbyGEN/fembygen/Alias.svg',  # the name of a svg file available in the resources
                'Accel': "Shift+A",  # a default shortcut (optional)
                'MenuText': "Alias",
                'ToolTip': "Alias in spreadsheet"}

    def Activated(self):
        return AliasPanel()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True


class AliasPanel:
    def __init__(self):
        for i in range(10):
            try:
                FreeCAD.ActiveDocument.Parameters.setAlias(
                    f'C{i+2}', FreeCAD.ActiveDocument.Parameters.get(f'B{i+2}'))
                FreeCAD.ActiveDocument.Parameters.recompute()
                print("Parameters names and sizes are aliased")
            except:
                pass


FreeCADGui.addCommand('Alias', AliasCommand())
