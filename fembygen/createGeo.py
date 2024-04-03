import FreeCAD,Part
import FreeCADGui
import os
import ObjectsFem
from fembygen import Topology
from PySide import QtGui, QtCore
import shutil

translate = FreeCAD.Qt.translate

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
            obj.addProperty("App::PropertyPythonObject", "Status", "Analysis", "Analysis Status")
            obj.addProperty("App::PropertyString", "Load_Type", "Analysis", "Load Type")
            obj.addProperty("App::PropertyString", "Bc_Type", "Analysis", "Boundary Condition Type")
            obj.addProperty("App::PropertyFloat", "Offset_Ratio", "Geometry", "Offset Ratio Value(%)")
            obj.Offset_Ratio=10.0
            obj.addProperty("App::PropertyStringList", "Preserve_Bodies", "Object", "Selected Preserve Object")
            obj.Preserve_Bodies=[]
            obj.addProperty("App::PropertyStringList", "Obstacle_Bodies", "Object", "Selected Obstacle Object")
            obj.Obstacle_Bodies=[]

        except:
            pass
class CreateGeoCommand:
    def __init__(self):
        self.createGeoPanel = None
    def GetResources(self):
        return {
            'Pixmap': os.path.join(FreeCAD.getUserAppDataDir(), 'Mod/FEMbyGEN/fembygen/icons/createGeo.svg'),
            'Accel': "Shift+S",
            'MenuText': "Create Geo Generations",
            'ToolTip': "Perform createGeo operations on selected objects"
        }
    def Activated(self):
        makecreateGeo()
        if self.createGeoPanel is None:
            self.createGeoPanel = CreateGeoPanel()
            self.createGeoPanel.show()
        elif self.createGeoPanel is not None:
            self.createGeoPanel.show()

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

class CreateGeoPanel:
    def __init__(self):
        
        self.myNewFreeCADWidget = QtGui.QDockWidget() # create a new dckwidget
        self.mw=FreeCADGui.getMainWindow()
        self.mw.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.myNewFreeCADWidget)
        self.form = FreeCADGui.PySideUic.loadUi(guiPath,self.myNewFreeCADWidget)
        self.selected_objects = []
        self.form.setWindowFlags(self.form.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.doc = FreeCAD.ActiveDocument
        self.guiDoc = FreeCADGui.getDocument(self.doc)
        self.form.SelectMaterial.clicked.connect(self.material) #select material
        self.form.addItem_in_preserve.clicked.connect(self.add_to_preserve) #add item in preserve listwidget
        self.form.remove_in_preserve.clicked.connect(self.remove_to_preserve) #remove item in preserve listwidget
        self.form.addItem_in_obstacle.clicked.connect(self.add_to_obstacle) #add item in obstacle listwidget
        self.form.remove_in_obstacle.clicked.connect(self.remove_to_obstacle) #remove item in obstacle listwidget
        self.form.createGeo.clicked.connect(self.createGeoGenerations) #run creategeo
        self.form.AssignLoad.clicked.connect(self.assign_load)
        self.form.AssignBC.clicked.connect(self.assign_bc)       
        self.form.topology_create.clicked.connect(self.TopologyAdvanced)
        self.form.Run.clicked.connect(self.TopologyBasic)
        self.form.OffsetRatio.textChanged.connect(self.updateOffsetRatioProperty)
        self.form.OffsetRatio.setPlainText(str(self.doc.createGeo.Offset_Ratio))
        self.myNewFreeCADWidget.setObjectName("CreateGeo")
        self.form.obstacle_bodies.setMaximumHeight(30)
        self.form.preserve_bodies.setMaximumHeight(30)
        self.workingDir = '/'.join(
            self.doc.FileName.split('/')[0:-1])
        
    def updateOffsetRatioProperty(self):
        text = self.form.OffsetRatio.toPlainText()
        try:
            value = float(text)
            self.doc.createGeo.Offset_Ratio = value
        except ValueError:
            pass
    #add load in combobox 
    def assign_load(self):
        logger=self.setup_logging()
        if self.form.SelectLoadtype.currentText() == "Force":
            self.doc.createGeo.Load_Type="Force"
            self.force()
        elif self.form.SelectLoadtype.currentText() == "Pressure":
            self.doc.createGeo.Load_Type="Pressure"
            self.pressure()
        logger.info("Load Type: {}".format(self.doc.createGeo.Load_Type))
    #add BC in combobox 
    def assign_bc(self):
        logger=self.setup_logging()
        if self.form.SelectBCtype.currentText() == "Fixed Support":
            self.doc.createGeo.Bc_Type="Fixed Support"
            self.fixed_support()
        elif self.form.SelectBCtype.currentText() == "Displacement":
            self.doc.createGeo.Bc_Type="Displacement"
            self.displacement()
        logger.info("Load Type: {}".format(self.doc.createGeo.Bc_Type))
#///////////////////add-remove selections in Qlistwidget/////////////////////////////////////////////
# Adding to the preserve list widget
    def add_to_preserve(self):
        selection = FreeCADGui.Selection.getSelection()
        if not selection:
            FreeCAD.Console.PrintError(translate("FEMbyGEN","Please Select Body\n"))
            return
        for obj in selection:
            item = QtGui.QListWidgetItem(obj.Label)
            self.form.preserve_bodies.addItem(item)
            font = item.font()
            font_size = font.pointSize()
            item_height = font_size+10 # Calculate the height for the current item
            current_max_height = self.form.preserve_bodies.maximumHeight()
            new_max_height = current_max_height + item_height
            self.form.preserve_bodies.setMaximumHeight(new_max_height)
            #self.doc.createGeo.Preserve_Bodies = self.get_preserve_items()
            

    # Removing from the preserve list widget
    def remove_to_preserve(self):
        if self.form.preserve_bodies.count() == 0:
            FreeCAD.Console.PrintError(translate("FEMbyGEN","Preserve list is empty. Nothing to remove.\n"))
            return

        selected_items = self.form.preserve_bodies.selectedItems()
        if not selected_items:
            FreeCAD.Console.PrintError(translate("FEMbyGEN","Please select items to remove from the Preserve list.\n"))
            return

        for item in selected_items:
            label = item.text()
            if label in self.selected_objects:
                self.selected_objects.remove(label)
            self.form.preserve_bodies.takeItem(self.form.preserve_bodies.row(item))
            font = item.font()
            font_size = font.pointSize()
            item_height = font_size+10 # Calculate the height for the current item
            current_max_height = self.form.preserve_bodies.maximumHeight()
            new_max_height = current_max_height - item_height
            self.form.preserve_bodies.setMaximumHeight(new_max_height)

    # Adding to the obstacle list widget
    def add_to_obstacle(self):
        selection = FreeCADGui.Selection.getSelection()
        if not selection:
            FreeCAD.Console.PrintError(translate("FEMbyGEN","Please Select Body\n"))
            return
        for obj in selection:
            item = QtGui.QListWidgetItem(obj.Label)
            self.form.obstacle_bodies.addItem(item)
            font = item.font()
            font_size = font.pointSize()
            item_height = font_size+10 # Calculate the height for the current item
            current_max_height = self.form.obstacle_bodies.maximumHeight()
            new_max_height = current_max_height + item_height
            self.form.obstacle_bodies.setMaximumHeight(new_max_height)
            #self.doc.createGeo.Obstacle_Bodies = self.get_obstacle_items()
           

    # Removing from the obstacle list widget
    def remove_to_obstacle(self):
        if self.form.obstacle_bodies.count() == 0:
            FreeCAD.Console.PrintError(translate("FEMbyGEN","Obstacle list is empty. Nothing to remove.\n"))
            return

        selected_items = self.form.obstacle_bodies.selectedItems()
        if not selected_items:
            FreeCAD.Console.PrintError(translate("FEMbyGEN","Please select items to remove from the Obstacle list.\n"))
            return

        for item in selected_items:
            label = item.text()
            if label in self.selected_objects:
                self.selected_objects.remove(label)
            self.form.obstacle_bodies.takeItem(self.form.obstacle_bodies.row(item))
            font = item.font()
            font_size = font.pointSize()
            item_height = font_size+10  # Calculate the height for the current item
            current_max_height = self.form.obstacle_bodies.maximumHeight()
            new_max_height = current_max_height - item_height
            self.form.obstacle_bodies.setMaximumHeight(new_max_height)
    def deleteTopology(self):
                try:
                    shutil.rmtree(self.workingDir + f"/TopologyCase_1/")
                    FreeCAD.Console.PrintMessage(translate("FEMbyGEN",
                        self.workingDir + f"/TopologyCase_/ deleted\n"))
                except FileNotFoundError:
                    FreeCAD.Console.PrintError(translate("FEMbyGEN","INFO: TopologyCase_1 "  +
                                               " analysis data not found\n"))
                    pass
                except:
                    FreeCAD.Console.PrintError(translate("FEMbyGEN",
                        "Error while trying to delete analysis folder for generation\n "))

        
#///////////////////////////////////////////////////////////////////////////////////////////// 
    def TopologyAdvanced(self):
        constraint_fixed = self.doc.getObject("ConstraintFixed")
        constraint_force = self.doc.getObject("ConstraintForce")
        constraint_displacement = self.doc.getObject("ConstraintDisplacement")
        constraint_pressure = self.doc.getObject("ConstraintPressure")
        if constraint_fixed is None and constraint_displacement is None:
            FreeCAD.Console.PrintError(translate("FEMbyGEN","Please Select BC type.\n"))
        elif constraint_force is None and constraint_pressure is None:
            FreeCAD.Console.PrintError(translate("FEMbyGEN","Please Select Load type.\n"))
        else:
            Topology.TopologyCommand.Activated(self.doc)
            self.doc.recompute()

    def TopologyBasic(self):
        self.deleteTopology()
        Topology.makeTopology()
        self.doc.Topology.mass_goal_ratio=0.50
        self.doc.Topology.mass_removal_ratio=0.06
        self.doc.Topology.mass_addition_ratio=0.03
        panel=Topology.TopologyPanel(self.doc.Topology)
        panel.accept()
        panel.runOptimization()
        panel.get_case("last")
        self.doc.recompute()


        
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
        force_obj.Force = 1
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
    def get_preserve_items(self):
        added_items_in_preserve = []
        for index in range(self.form.preserve_bodies.count()):
            item = self.form.preserve_bodies.item(index)
            added_items_in_preserve.append(item.text())
        return added_items_in_preserve 
    def get_obstacle_items(self):
        added_items_in_obstacle = []
        for index in range(self.form.obstacle_bodies.count()):
            item = self.form.obstacle_bodies.item(index)
            added_items_in_obstacle.append(item.text())
        return added_items_in_obstacle   


    def setup_logging(self):
        # Set up logging
        import logging
        log_directory = self.workingDir
        log_filename = os.path.join(log_directory, 'createGeoGenerations.log')
        logger = logging.getLogger('createGeoGenerations')
        logger.setLevel(logging.DEBUG)

        try:
            file_handler = logging.FileHandler(log_filename)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            FreeCAD.Console.PrintError(translate("FEMbyGEN",f"Error setting up logging: {str(e)}\n"))
            return logger
        logging.shutdown()
        return logger
    def createGeoGenerations(self):
        # Set up logging

        logger=self.setup_logging()
        if self.form.obstacle_bodies.count() > 0:
                logger.info("Starting createGeoGenerations function")

                # Remove previous log file


                percentage_text = self.form.OffsetRatio.toPlainText()

                try:
                    percentage = float(percentage_text)
                except ValueError:
                    FreeCAD.Console.PrintError(translate("FEMbyGEN","Invalid percentage value! Please enter a valid number.\n"))
                    return

                scale = percentage / 100
                logger.info("Offset Ratio value: {}".format(percentage))

                # Get selected Preserve and Obstacle Bodies
                selected_labels_preserve = self.get_preserve_items()
                part_bodies_preserve = [obj for obj in self.doc.Objects if obj.isDerivedFrom("Part::Feature") and obj.Label in selected_labels_preserve]
                selected_labels_obstacle = self.get_obstacle_items()
                part_bodies_obstacle = [obj for obj in self.doc.Objects if obj.isDerivedFrom("Part::Feature") and obj.Label in selected_labels_obstacle]

                logger.info("Selected Preserve Bodies: {}".format(selected_labels_preserve))
                logger.info("Selected Obstacle Bodies: {}".format(selected_labels_obstacle))

                

                # Hide selected objects
                for hide_obj in part_bodies_preserve + part_bodies_obstacle:
                    hide_obj.ViewObject.Visibility = False

                # Define the multiCuts function
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

                        cutName = baseName + str(i - 1)
                        cut = FreeCAD.ActiveDocument.addObject("Part::Cut", cutName)
                        cut.Base = base
                        cut.Tool = copy
                        cut.Label = "Cut " + str(i - 1) + ", " + baseLabel
                        self.doc.recompute()
                        base = cut
                        cuts.append(cut)
                    base.Label = "Cutted"
                    return cuts

                # Create the union of Preserve Bodies and a bounding box
                shape = Part.makeCompound([Part.Shape(obj.Shape) for obj in part_bodies_preserve + part_bodies_obstacle])
                boundBox_ = shape.BoundBox
                boundBoxLX = boundBox_.XLength
                boundBoxLY = boundBox_.YLength
                boundBoxLZ = boundBox_.ZLength
                boundBoxXMin = boundBox_.XMin
                boundBoxYMin = boundBox_.YMin
                boundBoxZMin = boundBox_.ZMin

                if self.doc.getObject('Analysis'):
                    FreeCAD.Console.PrintError(translate("FEMbyGEN","CreateGeo Already Ran\n"))
                else:
                    box = self.doc.addObject("Part::Box", "MyBox")
                    box.Length = boundBoxLX + 2 * scale * boundBoxLX
                    box.Width = boundBoxLY + 2 * scale * boundBoxLY
                    box.Height = boundBoxLZ
                    box.Placement.Base = FreeCAD.Vector(boundBoxXMin - scale * boundBoxLX,
                                                       boundBoxYMin - scale * boundBoxLY, boundBoxZMin)
                    box.ViewObject.Visibility = False

                    preserve_shapes = [obj.Shape for obj in part_bodies_preserve]
                    preserve_compound = Part.makeCompound(preserve_shapes)
                    union_shape = box.Shape.fuse(preserve_compound)
                    union_object = self.doc.addObject("Part::Feature", "UnionObject")
                    union_object.Shape = union_shape

                    obj_list = multiCuts(union_object, part_bodies_obstacle)
                    for obj in obj_list:
                        self.doc.createGeo.addObject(obj)
                    self.doc.createGeo.addObject(box)
                    import femmesh.gmshtools as gt
                    active_analysis = ObjectsFem.makeAnalysis(self.doc, 'Analysis')
                    solver_obj = ObjectsFem.makeSolverCalculixCcxTools(self.doc)
                    self.doc.createGeo.addObject(active_analysis)
                    self.doc.Analysis.addObject(solver_obj)
                    mesh_obj = ObjectsFem.makeMeshGmsh(self.doc, 'FEMMeshGmsh')
                    self.doc.Analysis.addObject(mesh_obj)
                    mesh_obj.Part = obj_list[-1]  # The number of cutted objects
                    mesher = gt.GmshTools(mesh_obj)
                    mesher.create_mesh()

                    self.doc.recompute()

                    logger.info("Finished createGeoGenerations function")
                    

        else:
                logger.debug("No selected Obstacle Bodies")
                FreeCAD.Console.PrintError(translate("FEMbyGEN","No selected Obstacle Bodies"))
               
                
    def show(self):
        self.myNewFreeCADWidget.setWidget(self.form)
        self.myNewFreeCADWidget.show()
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
       self.myNewFreeCADWidget.setWidget(self.form)
       self.myNewFreeCADWidget.show()
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
