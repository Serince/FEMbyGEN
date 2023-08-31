import FreeCAD
import FreeCADGui
import os

LOCATION = 'Mod/FEMbyGEN/fembygen'
MAX_NUM_PARAMETER = 10    # maximum number of parameters

class AliasCommand():
    """Analyse the generated parts"""

    def GetResources(self):
        return {'Pixmap': os.path.join(FreeCAD.getUserAppDataDir(), LOCATION, 'icons/Alias.svg'),
                'Accel': "Shift+A",  # a default shortcut (optional)
                'MenuText': "Set alias",
                'ToolTip': "Set the alias from Parameters Name cells"}

    def Activated(self):
        return AliasPanel()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        doc = FreeCAD.ActiveDocument
        return doc is not None and hasattr(doc, 'Parameters')


class AliasPanel:
    def __init__(self):
        doc = FreeCAD.ActiveDocument
        aliasedNum = 0
        for i in range(MAX_NUM_PARAMETER):
            try:
                doc.Parameters.setAlias(f'C{i+2}', doc.Parameters.get(f'B{i+2}'))
            except:
                pass
            else:
                aliasedNum += 1
        doc.Parameters.recompute()
        FreeCAD.Console.PrintMessage(
            f"{aliasedNum} parameters are aliased and can be used in expressions.\n")


FreeCADGui.addCommand('Alias', AliasCommand())
