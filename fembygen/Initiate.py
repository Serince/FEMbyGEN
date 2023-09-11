import FreeCAD
import FreeCADGui


def makeInitiate():
    try:
        group = FreeCAD.ActiveDocument.Generative_Design
        group.isValid()
    except:
        doc = FreeCAD.ActiveDocument
        group = FreeCAD.ActiveDocument.addObject(
            "App::DocumentObjectGroupPython", "Generative Design")
        parameter = doc.addObject('Spreadsheet::Sheet', 'Parameters')
        group.addObject(parameter)
    Initiate(group)
    if FreeCAD.GuiUp:
        ViewProviderIni(group.ViewObject)
    return group


class Initiate:
    """ Initiate """

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "Initiate"
        self.initProperties(obj)

    def initProperties(self, obj):
        pass


class InitiateCommand():
    """Analyse the generated parts"""

    def GetResources(self):
        return {'Pixmap': FreeCAD.getUserAppDataDir() +'Mod/FEMbyGEN/fembygen/Initiate.svg',  # the name of a svg file available in the resources
                'Accel': "Shift+N",  # a default shortcut (optional)
                'MenuText': "Initiate",
                'ToolTip': "Initialise the generation process"}

    def Activated(self):
        makeInitiate()
        return InitiatePanel()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return FreeCAD.ActiveDocument is not None


class InitiatePanel:
    def __init__(self):
        # create a group
        # group = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython", "Generative Design")
        # Add spreatsheet
        doc = FreeCAD.ActiveDocument
        self.paramsheet = doc.Parameters
        # Spreadsheet editing
        for i in range(10):
            self.paramsheet.set(f'A{i+2}', f'{i+1}.Parameter')
            self.paramsheet.setStyle(f'A{i+2}:A{i+2}', 'bold', 'add')

        self.paramsheet.set('B1', 'Parameter Name')
        self.paramsheet.set('C1', 'Min Value')
        self.paramsheet.set('D1', 'Max Value')
        self.paramsheet.set('E1', 'Number of Generations')
        self.paramsheet.setStyle('B1:E1', 'bold', 'add')
        self.paramsheet.setForeground(
            'A2:A100', (1.000000, 0.000000, 0.000000, 1.000000))
        self.paramsheet.setForeground(
            'B1:E1', (0.000000, 0.501961, 0.000000, 1.000000))
        self.paramsheet.setAlignment('C2:E100', 'left|vcenter|vimplied')
        doc.recompute()


class ViewProviderIni:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = FreeCAD.getUserAppDataDir() + "Mod/FEMbyGEN/icon.svg"
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        return

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


FreeCADGui.addCommand('Initiate', InitiateCommand())
