import FreeCAD
import FreeCADGui

FreeCADGui.addLanguagePath(os.path.join(FreeCAD.getUserAppDataDir(),"\Mod\FEMbyGEN\fembygen\translations"))

translate = FreeCAD.Qt.translate
print(translate("FEMbyGEN","FEMbyGEN Workbench loaded"))
#try101
