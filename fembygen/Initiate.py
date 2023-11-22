import FreeCAD
import FreeCADGui
import os

LOCATION = 'Mod/FEMbyGEN/fembygen'
MAX_NUM_PARAMETER = 10    # maximum number of parameters

def makeInitiate():
    """Initiate group"""
    doc = FreeCAD.ActiveDocument
    try:
        group = doc.GenerativeDesign
        group.isValid()
    except:
        group = doc.addObject(
            'App::DocumentObjectGroupPython', 'GenerativeDesign')
    try:
        parameter = doc.Parameters
        parameter.isValid()
    except:
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
        return {'Pixmap': os.path.join(FreeCAD.getUserAppDataDir(), LOCATION, 'icons/Initiate.svg'),
                'Accel': "Shift+N",  # a default shortcut (optional)
                'MenuText': "Initiate",
                'ToolTip': "Initialise and create parameter spreadsheet"}

    def Activated(self):
        makeInitiate()
        return InitiatePanel()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return FreeCAD.ActiveDocument is not None


class InitiatePanel:
    def __init__(self):
        """Create a group with parameter spreadsheet"""
        doc = FreeCAD.ActiveDocument
        guidoc = FreeCADGui.ActiveDocument
        self.paramsheet = self.spreadsheetTemplate(doc.Parameters)
        doc.Parameters.recompute()
        guidoc.setEdit(guidoc.Parameters)    # open spreadsheet

    def spreadsheetTemplate(self, sheet):
        """Spreadsheet editing"""
        pal = FreeCADGui.getMainWindow().palette()    # get colors from theme color palette
        backColor = pal.background().color().getRgbF()
        textColor = pal.text().color().getRgbF()
        for i in range(MAX_NUM_PARAMETER):
            sheet.set(f'A{i+2}', f'{i+1}')    # parameter number

        sheet.set('A1', 'Parameter Number')
        sheet.set('B1', 'Name')
        sheet.set('C1', 'Min Value')
        sheet.set('D1', 'Max Value')
        sheet.set('E1', 'Number of Generations')
        sheet.setStyle('A1:E1', 'bold')    # head
        sheet.setBackground('A1:E1', backColor)    # label columns
        sheet.setForeground('A1:E1', textColor)
        sheet.setBackground(f'A2:A{MAX_NUM_PARAMETER+1}', backColor)
        sheet.setForeground(f'A2:A{MAX_NUM_PARAMETER+1}', textColor)
        return sheet


class ViewProviderIni:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(FreeCAD.getUserAppDataDir(), LOCATION, 'icons/Initiate.svg')
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
