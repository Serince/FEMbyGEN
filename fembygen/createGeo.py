import FreeCAD,Part
import FreeCADGui
import os
from fembygen import Common, ObjectsFem,Topology
from PySide import QtCore


def makecreateGeo():
    try:
        obj = FreeCAD.ActiveDocument.createGeo
        obj.isValid()
    except:
        try:
            obj = FreeCAD.ActiveDocument.addObject(
                "App::DocumentObjectGroupPython", "createGeo")

        except:
            return None
    createGeo(obj)
    if FreeCAD.GuiUp:
        ViewProvidercreateGeo(obj.ViewObject)
    return obj

class createGeo:
    """createGeo geometry"""

    def __init__(self, obj):

        obj.Proxy = self
        self.Type = "createGeo"
        self.initProperties(obj)

    def initProperties(self, obj):
        try:
            obj.addProperty("App::PropertyPythonObject", "Status", "Base",
                            "Analysis Status")
            obj.addProperty("App::PropertyInteger", "NumberOfAnalysis", "Base",
                            "Number of Analysis")
            obj.addProperty("App::PropertyInteger", "NumberOfLoadCase", "Base",
                            "Number of Load Cases")
        except:
            pass

class CreateGeoCommand:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(FreeCAD.getUserAppDataDir(), 'Mod/FEMbyGEN/fembygen/icons/createGeo.svg'),
            'Accel': "Shift+G",
            'MenuText': "Create Geo Generations",
            'ToolTip': "Perform createGeo operations on selected objects"
        }

    def Activated(self):
        makecreateGeo()
        self.createGeoPanel = CreateGeoPanel()
        self.createGeoPanel.show()

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


class CreateGeoPanel:
    def __init__(self):
        self.form = FreeCADGui.PySideUic.loadUi(guiPath)
        self.selected_objects = []

        self.form.setWindowFlags(self.form.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        self.doc = FreeCAD.ActiveDocument
        self.guiDoc = FreeCADGui.getDocument(self.doc)

        self.form.SelectMaterial.clicked.connect(self.material) #select material
        self.form.addItem.clicked.connect(self.add_selected_objects) #add item in listwidget
        self.form.RemoveObj.clicked.connect(self.remove_selected_object) #remove item in listwidget
        self.form.Run.clicked.connect(self.createGeoGenerations) #run creategeo
        self.form.AssignLoad.clicked.connect(self.assign_load)
        self.form.AssignBC.clicked.connect(self.assign_bc)       
        self.form.topology_create.clicked.connect(self.Topology)

    #add load in combobox 
    def assign_load(self):
        if self.form.SelectLoadtype.currentText() == "Force":
            self.force()
        elif self.form.SelectLoadtype.currentText() == "Pressure":
            self.pressure()
    #add BC in combobox 
    def assign_bc(self):
        if self.form.SelectBCtype.currentText() == "Fixed Support":
            self.fixed_support()
        elif self.form.SelectBCtype.currentText() == "Displacement":
            self.displacement()
          

    # add selections in Qlistwidget
    def add_selected_objects(self):
        selection = FreeCADGui.Selection.getSelection()
        for obj in selection:
            self.selected_objects.append(obj.Label)
            self.form.addingTree.addItem(obj.Label)

    # remove selection in Qlistwidget
    def remove_selected_object(self):
        selected_items = self.form.addingTree.selectedItems()
        for item in selected_items:
            label = item.text()
            if label in self.selected_objects:
                self.selected_objects.remove(label)
            self.form.addingTree.takeItem(self.form.addingTree.row(item))
    def Topology(self):
        topo_obj=Topology.TopologyCommand.Activated(self.doc)
        self.doc.createGeo.addObject(topo_obj)
    def displacement(self):
        displacement_obj = self.doc.addObject("Fem::ConstraintDisplacement", "ConstraintDisplacement")
        displacement_obj.Scale = 1
        self.doc.Analysis.addObject(displacement_obj)
        for amesh in self.doc.Objects:
            if "ConstraintDisplacement" == amesh.Name:
                amesh.ViewObject.Visibility = True
            elif "Mesh" in amesh.TypeId:
                aparttoshow = amesh.Name.replace("_Mesh", "")
                for apart in self.doc.Objects:
                    if aparttoshow == apart.Name:
                        apart.ViewObject.Visibility = True
                amesh.ViewObject.Visibility = False

        self.guiDoc.setEdit(displacement_obj.Name)
    def fixed_support(self):
        fixed_support_obj=self.doc.addObject("Fem::ConstraintFixed","ConstraintFixed")
        fixed_support_obj.Scale = 1
        self.doc.Analysis.addObject(fixed_support_obj)
        for amesh in self.doc.Objects:
            if "ConstraintFixed" == amesh.Name:
                amesh.ViewObject.Visibility = True
            elif "Mesh" in amesh.TypeId:
                aparttoshow = amesh.Name.replace("_Mesh", "")
                for apart in self.doc.Objects:
                    if aparttoshow == apart.Name:
                        apart.ViewObject.Visibility = True
                amesh.ViewObject.Visibility = False
        self.guiDoc.setEdit(fixed_support_obj.Name)
    def material(self):
        obj = ObjectsFem.makeMaterialSolid(self.doc)
        self.doc.Analysis.addObject(obj)
        self.guiDoc.setEdit(obj.Name)

    def force(self):
        force_obj = self.doc.addObject("Fem::ConstraintForce", "ConstraintForce")
        force_obj.Force = 1.0
        force_obj.Reversed = False
        force_obj.Scale = 1
        self.doc.Analysis.addObject(force_obj)
        for amesh in self.doc.Objects:
            if "ConstraintForce" == amesh.Name:
                amesh.ViewObject.Visibility = True
            elif "Mesh" in amesh.TypeId:
                aparttoshow = amesh.Name.replace("_Mesh", "")
                for apart in self.doc.Objects:
                    if aparttoshow == apart.Name:
                        apart.ViewObject.Visibility = True
                amesh.ViewObject.Visibility = False
        self.guiDoc.setEdit(force_obj.Name)
    def pressure(self):
        preassure_obj=self.doc.addObject("Fem::ConstraintPressure","ConstraintPressure")
        preassure_obj.Pressure = 0.1
        preassure_obj.Reversed = False
        preassure_obj.Scale = 1
        self.doc.Analysis.addObject(preassure_obj)
        for amesh in self.doc.Objects:
            if "ConstraintPressure" == amesh.Name:
                amesh.ViewObject.Visibility = True
            elif "Mesh" in amesh.TypeId:
                aparttoshow = amesh.Name.replace("_Mesh", "")
                for apart in self.doc.Objects:
                    if aparttoshow == apart.Name:
                        apart.ViewObject.Visibility = True
                amesh.ViewObject.Visibility = False   

        self.guiDoc.setEdit(preassure_obj.Name)    

    def createGeoGenerations(self):
            percentage_text = self.form.OffsetRatio.toPlainText()
            try:
                percentage = float(percentage_text)
            except ValueError:
                FreeCAD.Console.PrintError("Invalid percentage value! Please enter a valid number.\n")
                return
    
            scale = percentage / 100
    
            selected_items = self.form.addingTree.selectedItems()  # Get selected items from QListWidget
            selected_labels = [item.text() for item in selected_items]  # Get labels of selected items
    
            part_bodies = [obj for obj in self.doc.Objects if obj.isDerivedFrom("Part::Feature") and obj.Label in selected_labels]
  
            if not part_bodies:
                FreeCAD.Console.PrintError("No valid objects selected!\n")
                return
            def multiCuts(base_o, Objects):
                cuts = []
                i = 0
                base = base_o
                baseName = base.Name
                baseLabel = base.Label
                for o in Objects:
                    i = i + 1
                    if i == 0:
                        continue
            
                    copy = FreeCAD.ActiveDocument.copyObject(o)
                    copy.Label = "copy, " + o.Label
            
                    cutName = baseName + str(i-1)
                    cut = FreeCAD.ActiveDocument.addObject("Part::Cut", cutName)
                    cut.Base = base
                    cut.Tool = copy
                    cut.Label = "Cut " + str(i-1) + ", " + baseLabel
            
                    self.doc.recompute()
            
                    base = cut
                    cuts.append(cut)
            
                base.Label = "Cut, " + baseLabel
                return cuts
            shape = Part.makeCompound([Part.Shape(obj.Shape) for obj in part_bodies])
            boundBox_ = shape.BoundBox
            boundBoxLX = boundBox_.XLength
            boundBoxLY = boundBox_.YLength
            boundBoxLZ = boundBox_.ZLength
            boundBoxXMin = boundBox_.XMin
            boundBoxYMin = boundBox_.YMin
            boundBoxZMin = boundBox_.ZMin

            box = self.doc.addObject("Part::Box", "MyBox")
            box.Length = boundBoxLX + 2 * scale * boundBoxLX
            box.Width = boundBoxLY + 2 * scale * boundBoxLY
            box.Height = boundBoxLZ
            box.Placement.Base = FreeCAD.Vector(boundBoxXMin - scale * boundBoxLX, boundBoxYMin - scale * boundBoxLY, boundBoxZMin)
            obj_list = multiCuts(box, part_bodies)
            
            for obj in obj_list:
                FreeCAD.ActiveDocument.createGeo.addObject(obj)
                
            active_analysis=ObjectsFem.makeAnalysis(self.doc, 'Analysis')
            solver_obj=ObjectsFem.makeSolverCalculixCcxTools(self.doc)
            self.doc.createGeo.addObject(active_analysis)
            self.doc.Analysis.addObject(solver_obj)
            import femmesh.gmshtools as gt
            mesh_obj = ObjectsFem.makeMeshGmsh(self.doc, 'FEMMeshGmsh')
            self.doc.Analysis.addObject(mesh_obj)
            mesh_obj.Part = obj_list[len(selected_items)-1] #number of cutted obj
            mesher = gt.GmshTools(mesh_obj)
            mesher.create_mesh()
            self.doc.recompute()

    def show(self):
        self.form.show()
    def close(self):
        self.form.close()
class ViewProvidercreateGeo:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(
            FreeCAD.getUserAppDataDir() + 'Mod/FEMbyGEN/fembygen/icons/createGeo.svg')
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        return 

    def doubleClicked(self, vobj):
       panel = CreateGeoPanel()
       panel.show()
       return True

    def setEdit(self, vobj, mode):
       panel = CreateGeoPanel()
       panel.show()
       return True

    def unsetEdit(self, vobj, mode):
        FreeCADGui.control.closedialog()
        return None

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

# Path to your UI file
guiPath = FreeCAD.getUserAppDataDir() + "/Mod/FEMbyGEN/fembygen/ui/createGeo.ui"
FreeCADGui.addCommand('createGeo', CreateGeoCommand())
