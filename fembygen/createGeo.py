import FreeCAD,Part
import FreeCADGui
import os
from fembygen import Common,ObjectsFem
from PySide2.QtWidgets import QListWidgetItem
App=FreeCAD



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


class createGeoCommand():
    """Perform createGeo on generated parts"""

    def GetResources(self):
        return {'Pixmap': os.path.join(FreeCAD.getUserAppDataDir() + 'Mod/FEMbyGEN/fembygen/icons/createGeo.svg'),  # the name of a svg file available in the resources
                'Accel': "Shift+G",  # a default shortcut (optional)
                'MenuText': "createGeo Generations",
                'ToolTip': "Perform createGeo on generated parts"}
    def Activated(self):
        obj = makecreateGeo()
        try:
            doc = FreeCADGui.getDocument(obj.ViewObject.Object.Document)
            if not doc.getInEdit():
                doc.setEdit(obj.ViewObject.Object.Name)
            else:
                FreeCAD.Console.PrintError('Existing task dialog already open\n')
            return
        except:
            FreeCAD.Console.PrintError('Make sure that you are working on the master file. Close the generated file\n')

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return FreeCAD.ActiveDocument is not None

class createGeoPanel:
    def __init__(self, vobj):
        self.vobj = vobj  # Store vobj as an instance variable
        # this will create a Qt widget from our ui file
        guiPath = FreeCAD.getUserAppDataDir() + "Mod/FEMbyGEN/fembygen/ui/createGeo.ui"
        self.form = FreeCADGui.PySideUic.loadUi(guiPath)
        self.doc = FreeCAD.ActiveDocument
        self.guiDoc= FreeCADGui.getDocument(self.doc)
        if self.doc:
            part_bodies = [obj for obj in self.doc.Objects if obj.isDerivedFrom("Part::Feature")]
            for body in part_bodies:
                item = QListWidgetItem(body.Label)
                self.form.adding_tree.addItem(item)  
                
        self.form.run.clicked.connect(self.createGeoGenerations)
        self.form.selectMaterial.clicked.connect(self.material)
        self.form.selectDisplacment.clicked.connect(self.displacment)
        self.form.force.clicked.connect(self.force)
    def displacment(self):
        self.doc.addObject("Fem::ConstraintDisplacement","ConstraintDisplacement")
        self.doc.ConstraintDisplacement.Scale = 1
        self.doc.createGeo.addObject(App.activeDocument().ConstraintDisplacement)
        for amesh in self.doc.Objects:
            if "ConstraintDisplacement" == amesh.Name:
                amesh.ViewObject.Visibility = True
            elif "Mesh" in amesh.TypeId:
                aparttoshow = amesh.Name.replace("_Mesh","")
                for apart in App.activeDocument().Objects:
                    if aparttoshow == apart.Name:
                        apart.ViewObject.Visibility = True
                amesh.ViewObject.Visibility = False
            
        self.guiDoc.setEdit(self.doc.ActiveObject.Name)
       
    
    def material(self):
        obj=ObjectsFem.makeMaterialSolid(self.doc)
        self.doc.createGeo.addObject(obj)
        self.guiDoc.setEdit(self.doc.ActiveObject.Name)
    def force(self):
        self.doc.addObject("Fem::ConstraintForce","ConstraintForce")
        self.doc.ConstraintForce.Force = 1.0
        self.doc.ConstraintForce.Reversed = False
        self.doc.ConstraintForce.Scale = 1
        self.doc.createGeo.addObject(App.activeDocument().ConstraintForce)
        for amesh in self.doc.Objects:
            if "ConstraintForce" == amesh.Name:
                amesh.ViewObject.Visibility = True
            elif "Mesh" in amesh.TypeId:
                aparttoshow = amesh.Name.replace("_Mesh","")
                for apart in App.activeDocument().Objects:
                    if aparttoshow == apart.Name:
                        apart.ViewObject.Visibility = True
                amesh.ViewObject.Visibility = False
        self.guiDoc.setEdit(self.doc.ActiveObject.Name)
  
    def createGeoGenerations(self):
            percentage_text = self.form.offsetRatio.toPlainText()
            doc = App.ActiveDocument
            try:
                percentage = float(percentage_text)
            except ValueError:
                App.Console.PrintError("Invalid percentage value! Please enter a valid number.\n")
                return
    
            scale = percentage / 100
    
            selected_items = self.form.adding_tree.selectedItems()  # Get selected items from QListWidget
            selected_labels = [item.text() for item in selected_items]  # Get labels of selected items
    
            part_bodies = [obj for obj in doc.Objects if obj.isDerivedFrom("Part::Feature") and obj.Label in selected_labels]
    
            if not part_bodies:
                App.Console.PrintError("No valid objects selected!\n")
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
            
                    copy = self.doc.copyObject(o)
                    copy.Label = "copy, " + o.Label
            
                    cutName = baseName + str(i-1)
                    cut = self.doc.addObject("Part::Cut", cutName)
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
            box = doc.addObject("Part::Box", "MyBox")
            box.Length = boundBoxLX + 2 * scale * boundBoxLX
            box.Width = boundBoxLY + 2 * scale * boundBoxLY
            box.Height = boundBoxLZ
            box.Placement.Base = App.Vector(boundBoxXMin - scale * boundBoxLX, boundBoxYMin - scale * boundBoxLY, boundBoxZMin)
            obj_list = multiCuts(box, part_bodies)
            for obj in obj_list:
                self.doc.createGeo.addObject(obj)
            self.doc.recompute()



    def accept(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        doc.Document.recompute()
        # closes the gen file If a generated file opened to check before
        Common.showGen("close", self.doc.createGeo, None)

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        # closes the gen file If a generated file opened to check before
        # Common.showGen("close", self.doc, None)


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
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Existing task dialog already open\n')
        return True

    def setEdit(self, vobj, mode):
        taskd = createGeoPanel(vobj)
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        FreeCADGui.Control.closeDialog()
        return

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


FreeCADGui.addCommand('createGeo', createGeoCommand())
