import FreeCAD
import FreeCADGui
from fembygen import Common

MAX_NUM_PARAMETER = 10    # maximum number of parameters


class InitiateCommand():
    """Create parameter spreadsheet"""

    def GetResources(self):
        return {'Pixmap': ':/icons/Spreadsheet.svg',
                'Accel': "Shift+N",  # a default shortcut (optional)
                'MenuText': "Initiate",
                'ToolTip': "Create parameter spreadsheet"}

    def Activated(self):
        group, obj = Common.addToDocumentObjectGroup('Spreadsheet::Sheet', 'Parameters')
        return InitiatePanel()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return FreeCAD.ActiveDocument is not None


class InitiatePanel:
    def __init__(self):
        """Create parameter spreadsheet"""
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
    """Placeholder of the custom Viewprovider"""
    
    def __init__(self, vobj):
        vobj.Proxy = self


FreeCADGui.addCommand('Initiate', InitiateCommand())
