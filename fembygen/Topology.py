import FreeCAD
import FreeCADGui
import os
from PySide import QtGui, QtCore
from femtools import ccxtools
import datetime
import webbrowser
from fembygen.topology import beso_main
from fembygen import Common
import FemGui
import glob
import shutil
from multiprocessing import cpu_count

translate = FreeCAD.Qt.translate
def QT_TRANSLATE_NOOP(context, text):
    return text
import FreeCADGui
import os
FreeCADGui.addLanguagePath(os.path.join(FreeCAD.getUserAppDataDir(),"\Mod\FEMbyGEN\fembygen\translations"))
FreeCADGui.updateLocale()

def makeTopology():
    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    try:
        FreeCAD.ActiveDocument.Generate
        obj = FreeCAD.ActiveDocument.addObject(
            "App::DocumentObjectGroupPython", "Topology")
        FreeCAD.ActiveDocument.GenerativeDesign.addObject(obj)
        TopologyLink(obj)
        if FreeCAD.GuiUp:
            ViewProviderLink(obj.ViewObject)
        return obj
    except:
        obj = FreeCAD.ActiveDocument.addObject(
            "App::DocumentObjectGroupPython", "Topology")
        Topology(obj)
        if FreeCAD.GuiUp:
            ViewProviderGen(obj.ViewObject)
        return obj


class TopologyLink:
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "Topology_Link"
        self.initProperties(obj)

    def initProperties(self, obj):
        obj.addProperty("App::PropertyString", "Path", "Base",
                        "Path of the file")


class Topology:
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "Topology"
        self.initProperties(obj)

    def initProperties(self, obj):

        obj.addProperty("App::PropertyFloat", "mass_addition_ratio", "Mass",
                        "The ratio to add mass between iterations ")
        obj.mass_addition_ratio = 0.015
        obj.addProperty("App::PropertyFloat", "mass_removal_ratio", "Mass",
                        "The ratio to add mass between iterations ")
        obj.mass_removal_ratio = 0.03
        obj.addProperty("App::PropertyInteger", "LastState", "Results",
                        "Last state")

        obj.addProperty("App::PropertyFile", "path_calculix", "Base", "Path to CalculiX")

        obj.addProperty("App::PropertyPythonObject", "combobox", "Base", "List of fem analysis")
        obj.combobox = []

        obj.addProperty("App::PropertyPath", "path", "Base", "Path")

        obj.addProperty("App::PropertyString", "file_name", "Base", "File Name")

        obj.addProperty("App::PropertyPythonObject", "domain_offset", "Domain", "Domain Offset")
        obj.domain_offset = {}

        obj.addProperty("App::PropertyPythonObject", "domain_orientation", "Domain", "Domain Orientation")
        obj.domain_orientation = {}

        obj.addProperty("App::PropertyPythonObject", "domain_FI", "Domain", "Domain FI")
        obj.domain_FI = {}

        obj.addProperty("App::PropertyPythonObject", "domain_same_state", "Domain", "Domain Same State")
        obj.domain_same_state = {}

        obj.addProperty("App::PropertyFile", "continue_from", "Base", "Continue From")
        obj.continue_from = ''

        obj.addProperty("App::PropertyPythonObject", "filter_list", "Base", "Filter List")

        obj.addProperty("App::PropertyPythonObject", "Gen_filled")
        obj.Gen_filled = False

        obj.addProperty("App::PropertyInteger", "cpu_cores", "Base", "CPU Cores")
        obj.cpu_cores = cpu_count()

        obj.addProperty("App::PropertyFloat", "FI_violated_tolerance", "Base", "FI Violated Tolerance")
        obj.FI_violated_tolerance = 1.0

        obj.addProperty("App::PropertyFloat", "decay_coefficient", "Base", "Decay Coefficient")
        obj.decay_coefficient = -0.2

        obj.addProperty("App::PropertyBool", "shells_as_composite", "Base", "Shells as Composite")
        obj.shells_as_composite = False

        obj.addProperty("App::PropertyEnumeration", "reference_points", "Base", "Reference Points")
        obj.reference_points = ["integration points", "nodes"]

        obj.addProperty("App::PropertyEnumeration", "reference_value", "Base", "Reference Value")
        obj.reference_value = ['max', 'average']

        obj.addProperty("App::PropertyBool", "sensitivity_averaging", "Base", "Sensitivity Averaging")
        obj.sensitivity_averaging = False

        obj.addProperty("App::PropertyBool", "compensate_state_filter", "Base", "Compensate State Filter")
        obj.compensate_state_filter = False

        obj.addProperty("App::PropertyIntegerList", "steps_superposition", "Base", "Steps Superposition")
        obj.steps_superposition = []

        obj.addProperty("App::PropertyString", "iterations_limit", "Base", "Iterations Limit")
        obj.iterations_limit = 'auto'

        obj.addProperty("App::PropertyFloat", "tolerance", "Base", "Tolerance")
        obj.tolerance = 1e-3

        obj.addProperty("App::PropertyStringList", "displacement_graph", "Base", "Displacement Graph")
        obj.displacement_graph = []

        obj.addProperty("App::PropertyInteger", "save_iteration_results", "Base", "Save Iteration Results")
        obj.save_iteration_results = 1

        obj.addProperty("App::PropertyString", "save_solver_files", "Base", "Save Solver Files")
        obj.save_solver_files = ''

        obj.addProperty("App::PropertyEnumeration", "save_resulting_format", "Base", "Save Resulting Format")
        obj.save_resulting_format = [["inp"], ["vtk"], ["inp", "vtk"]]

        obj.addProperty("App::PropertyPythonObject", "domain_optimized", "Domain", "Domain Optimized")
        obj.domain_optimized = {}

        obj.addProperty("App::PropertyPythonObject", "domain_density", "Domain", "Domain Density")
        obj.domain_density = {}
        obj.addProperty("App::PropertyPythonObject", "domain_thickness", "Domain", "Domain Density")
        obj.domain_thickness = {}
        obj.addProperty("App::PropertyFloat", "stress_limit", "Base", "Stress Limit")

        obj.addProperty("App::PropertyPythonObject", "domain_material", "Domain", "Domain Material")
        obj.domain_material = {}

        obj.addProperty("App::PropertyInteger", "Number_of_Domains", "Domain", "Number of domains")
        obj.Number_of_Domains = 1

        obj.addProperty("App::PropertyFloat", "mass_goal_ratio", "Mass", "Mass Goal Ratio")
        obj.mass_goal_ratio=0.75

        obj.addProperty("App::PropertyString", "optimization_base", "Base", "Optimization Base")


        obj.addProperty("App::PropertyEnumeration", "ratio_type", "Base", "Ratio Type")
        obj.ratio_type = ['relative', 'absolute']
        obj.addProperty("App::PropertyPythonObject", "Generations")
        obj.Generations = []


class TopologyCommand():

    def GetResources(self):
        return {'Pixmap': os.path.join(FreeCAD.getUserAppDataDir() + 'Mod/FEMbyGEN/fembygen/icons/Topology.svg'),  # the name of a svg file available in the resources
                'Accel': "Shift+T",  # a default shortcut (optional)
                'MenuText': QT_TRANSLATE_NOOP("CommandName","Topology"),
                'ToolTip':  QT_TRANSLATE_NOOP("CommandName","Opens Topology gui")}

    def Activated(self):

        obj = makeTopology()
        doc = FreeCADGui.ActiveDocument
        if not doc.getInEdit() and obj is not None:
            doc.setEdit(obj.ViewObject.Object.Name)  
        else:
            FreeCAD.Console.PrintError(translate("FEMbyGEN",'Existing task dialog already open')+"\n")
        return
    

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return FreeCAD.ActiveDocument is not None


class TopologyMasterPanel(QtGui.QWidget):
    def __init__(self, object):
        self.obj = object
        guiPath = FreeCAD.getUserAppDataDir() + "Mod/FEMbyGEN/fembygen/ui/Beso_GenSelect.ui"
        self.form = FreeCADGui.PySideUic.loadUi(guiPath)
        self.workingDir = '/'.join(
            object.Document.FileName.split('/')[0:-1])
        self.doc = object.Document
        self.form.getGen.clicked.connect(self.openGeneration)

        numAnalysis = self.doc.FEA.NumberOfAnalysis
        LC = self.doc.FEA.NumberOfLoadCase
        numGens = numAnalysis//LC
        self.form.selectGen.clear()
        for i in range(1, numGens+1):
            self.form.selectGen.addItem(f"Gen{i}")

    def openGeneration(self):
        # ose old opened generations
        # Common.showGen("close",self.doc,1)

        # get selected generations
        gen = self.form.selectGen.currentIndex()+1

        # open selected generation file to make topology optimizations
        partName = f"Gen{gen}"
        filePath = os.path.join(self.workingDir, f"Gen{gen}/Gen{gen}.FCStd")
        self.obj.Label = partName+"_Topology"
        self.obj.Path = filePath
        self.accept()
        Gen_Doc = FreeCAD.open(filePath)
        FreeCAD.setActiveDocument(partName)
        obj = makeTopology()

        # hide all mesh files to show results at the end of the topology
        for mesh in Gen_Doc.Objects:
            if mesh.TypeId == 'Fem::FemMeshObjectPython' or mesh.TypeId == 'Fem::FemMeshShapeNetgenObject' or 'Fem::FemPostPipeline':
                mesh.Visibility = False

        Gen_Doc.Topology.ViewObject.doubleClicked()

    def accept(self):
        doc = FreeCADGui.getDocument(self.doc)
        doc.resetEdit()
        doc.Document.recompute()
        FreeCADGui.Control.closeDialog()

    def reject(self):
        doc = FreeCADGui.getDocument(self.doc)
        doc.resetEdit()


class TopologyPanel(QtGui.QWidget):
    def __init__(self, object):
        self.obj = object
        guiPath = FreeCAD.getUserAppDataDir() + "Mod/FEMbyGEN/fembygen/ui/Beso.ui"
        self.form = FreeCADGui.PySideUic.loadUi(guiPath)
        self.workingDir = '/'.join(
            object.Document.FileName.split('/')[0:-1])
        self.doc = object.Document

        self.getAnalysis()
        self.form.iterationSlider.sliderMoved.connect(self.massratio)

        if self.doc.Topology.Number_of_Domains == 1:
            self.domains1()
        elif self.doc.Topology.Number_of_Domains == 2:
            self.domains2()
        elif self.doc.Topology.Number_of_Domains == 3:
            self.domains3()
        
        self.form.addButton_1.clicked.connect(self.addDomain)
        self.form.remButton_1.clicked.connect(self.remDomain)
        self.form.addButton_2.clicked.connect(self.addDomain)
        self.form.remButton_2.clicked.connect(self.remDomain)

        # adding constraint for mass goal ratio between 0.0 - 1.0
        self.form.validator = QtGui.QDoubleValidator(0, 1, 2)
        self.form.massGoalRatio.setValidator(self.form.validator)
        self.form.massGoalRatio.textEdited.connect(self.validator)
        self.form.massGoalRatio.setText(str(self.doc.Topology.mass_goal_ratio))
        self.form.selectFilter_2.currentIndexChanged.connect(self.filterType2)
        self.form.selectFilter_3.currentIndexChanged.connect(self.filterType3)
        self.form.filterRange_2.currentIndexChanged.connect(self.filterRange2)
        self.form.filterRange_3.currentIndexChanged.connect(self.filterRange2)


        self.form.selectLC.currentIndexChanged.connect(self.selectFile) # select generated analysis file
        self.form.selectMaterial_1.currentIndexChanged.connect(
            self.selectMaterial1)  # select domain by material object comboBox 1
        self.form.selectMaterial_2.currentIndexChanged.connect(
            self.selectMaterial2)  # select domain by material object comboBox 2
        self.form.selectMaterial_3.currentIndexChanged.connect(
            self.selectMaterial3)  # select domain by material object comboBox 3

        self.form.selectFilter_1.currentIndexChanged.connect(
            self.filterType1)  # select filter type comboBox 1 (simple,casting)
        self.form.selectFilter_2.currentIndexChanged.connect(
            self.filterType2)  # select filter type comboBox 2 (simple,casting)
        self.form.selectFilter_3.currentIndexChanged.connect(
            self.filterType3)  # select filter type comboBox 3 (simple,casting)

        self.form.filterRange_1.currentIndexChanged.connect(
            self.filterRange1)  # select filter range comboBox 1 (auto,manual)
        self.form.filterRange_2.currentIndexChanged.connect(
            self.filterRange2)  # select filter range comboBox 2 (auto,manual)
        self.form.filterRange_3.currentIndexChanged.connect(
            self.filterRange3)  # select filter range comboBox 3 (auto,manual)

        self.form.results.clicked.connect(lambda: self.get_case("last"))  # show results
        self.form.runOpt.clicked.connect(self.runOptimization)  # run optimization button
        self.form.openExample.clicked.connect(self.openExample)  # example button, opens examples on beso github
        self.form.confComments.clicked.connect(self.openConfComments)  # opens config comments on beso github
        self.form.openLog.clicked.connect(self.openLog) # opens log file


    def validator(self):
        text = self.form.massGoalRatio.text()
        if text:
            number = float(text)
            if number > 1:
                self.form.massGoalRatio.setText("1")
            elif number < 0:
                self.form.massGoalRatio.setText("0")

    def getAnalysisObjects(self, analysis):
        materials = []
        thicknesses = []
        for obj in analysis.Group:
            if obj.TypeId == "App::MaterialObjectPython":
                materials.append(obj)
            elif obj.Name[:17] == "ElementGeometry2D":
                thicknesses.append(obj)
        return materials, thicknesses

    def addDomain(self):
        self.doc.Topology.Number_of_Domains
        self.doc.Topology.Number_of_Domains += 1
        if self.doc.Topology.Number_of_Domains == 1:
            self.domains1()
        elif self.doc.Topology.Number_of_Domains == 2:
            self.domains2()
        elif self.doc.Topology.Number_of_Domains == 3:
            self.domains3()

    def remDomain(self):
        self.doc.Topology.Number_of_Domains
        self.doc.Topology.Number_of_Domains -= 1

        if self.doc.Topology.Number_of_Domains == 1:
            self.domains1()
        elif self.doc.Topology.Number_of_Domains == 2:
            self.domains2()
        elif self.doc.Topology.Number_of_Domains == 3:
            self.domains3()

    def domains1(self):
        if not self.doc.Topology.combobox[0][3]:
            self.form.thicknessObject_1.setVisible(False)
            self.form.labelThickness.setVisible(False)
        self.form.domain_2.setVisible(False)
        self.form.domain_3.setVisible(False)
        self.form.selectMaterial_2.setVisible(False)
        self.form.selectMaterial_3.setVisible(False)
        self.form.thicknessObject_2.setVisible(False)
        self.form.thicknessObject_3.setVisible(False)
        self.form.asDesign_checkbox_2.setVisible(False)
        self.form.asDesign_checkbox_3.setVisible(False)
        self.form.stressLimit_2.setVisible(False)
        self.form.stressLimit_3.setVisible(False)
        self.form.filter_2.setVisible(False)
        self.form.filter_3.setVisible(False)
        self.form.selectFilter_2.setVisible(False)
        self.form.selectFilter_3.setVisible(False)
        self.form.filterRange_2.setVisible(False)
        self.form.filterRange_3.setVisible(False)
        self.form.range_2.setVisible(False)
        self.form.range_3.setVisible(False)
        self.form.directionVector_2.setVisible(False)
        self.form.directionVector_3.setVisible(False)
        self.form.domainList_2.setVisible(False)
        self.form.domainList_3.setVisible(False)
        self.form.remButton_1.setVisible(False)
        self.form.remButton_2.setVisible(False)
        self.form.addButton_2.setVisible(False)
        self.form.addButton_1.setVisible(True)
        self.form.domainList_1.clear()
        self.form.domainList_1.addItems(["All Defined", "Domain 1"])
        self.form.domainList_1.setCurrentRow(0)

    def domains2(self):
        if not self.doc.Topology.combobox[0][3]:
            self.form.thicknessObject_1.setVisible(False)
            self.form.thicknessObject_2.setVisible(False)
            self.form.labelThickness.setVisible(False)
        else:
            self.form.thicknessObject_1.setVisible(True)
            self.form.thicknessObject_2.setVisible(True)
            self.form.labelThickness.setVisible(True)
        self.form.domain_2.setVisible(True)
        self.form.domain_3.setVisible(False)
        self.form.selectMaterial_2.setVisible(True)
        self.form.selectMaterial_3.setVisible(False)
        self.form.thicknessObject_3.setVisible(False)
        self.form.asDesign_checkbox_2.setVisible(True)
        self.form.asDesign_checkbox_3.setVisible(False)
        self.form.stressLimit_2.setVisible(True)
        self.form.stressLimit_3.setVisible(False)
        self.form.filter_2.setVisible(True)
        self.form.filter_3.setVisible(False)
        self.form.selectFilter_2.setVisible(True)
        self.form.selectFilter_3.setVisible(False)
        self.form.filterRange_2.setVisible(True)
        self.form.filterRange_3.setVisible(False)
        self.form.range_2.setVisible(True)
        self.form.range_3.setVisible(False)
        self.form.directionVector_2.setVisible(True)
        self.form.directionVector_3.setVisible(False)
        self.form.domainList_2.setVisible(True)
        self.form.domainList_3.setVisible(False)
        self.form.remButton_1.setVisible(True)
        self.form.remButton_2.setVisible(False)
        self.form.addButton_2.setVisible(True)
        self.form.addButton_1.setVisible(False)
        self.form.domainList_1.clear()
        self.form.domainList_1.addItems(["All Defined", "Domain 1", "Domain 2"])
        self.form.domainList_1.setCurrentRow(0)
        self.form.domainList_2.clear()
        self.form.domainList_2.addItems(["All Defined", "Domain 1", "Domain 2"])
        self.form.domainList_2.setCurrentRow(0)

    def domains3(self):
        if not self.doc.Topology.combobox[0][3]:
            self.form.thicknessObject_1.setVisible(False)
            self.form.thicknessObject_2.setVisible(False)
            self.form.thicknessObject_3.setVisible(False)
            self.form.labelThickness.setVisible(False)
        else:
            self.form.thicknessObject_1.setVisible(True)
            self.form.thicknessObject_2.setVisible(True)
            self.form.thicknessObject_3.setVisible(True)
            self.form.labelThickness.setVisible(True)
        self.form.domain_2.setVisible(True)
        self.form.domain_3.setVisible(True)
        self.form.selectMaterial_2.setVisible(True)
        self.form.selectMaterial_3.setVisible(True)
        self.form.asDesign_checkbox_2.setVisible(True)
        self.form.asDesign_checkbox_3.setVisible(True)
        self.form.stressLimit_2.setVisible(True)
        self.form.stressLimit_3.setVisible(True)
        self.form.filter_2.setVisible(True)
        self.form.filter_3.setVisible(True)
        self.form.selectFilter_2.setVisible(True)
        self.form.selectFilter_3.setVisible(True)
        self.form.filterRange_2.setVisible(True)
        self.form.filterRange_3.setVisible(True)
        self.form.range_2.setVisible(True)
        self.form.range_3.setVisible(True)
        self.form.directionVector_2.setVisible(True)
        self.form.directionVector_3.setVisible(True)
        self.form.domainList_2.setVisible(True)
        self.form.domainList_3.setVisible(True)
        self.form.remButton_1.setVisible(False)
        self.form.remButton_2.setVisible(True)
        self.form.addButton_2.setVisible(False)
        self.form.addButton_1.setVisible(False)
        self.form.domainList_1.clear()
        self.form.domainList_1.addItems(["All Defined", "Domain 1", "Domain 2", "Domain 3"])
        self.form.domainList_1.setCurrentRow(0)
        self.form.domainList_2.clear()
        self.form.domainList_2.addItems(["All Defined", "Domain 1", "Domain 2", "Domain 3"])
        self.form.domainList_2.setCurrentRow(0)
        self.form.domainList_3.clear()
        self.form.domainList_3.addItems(["All Defined", "Domain 1", "Domain 2", "Domain 3"])
        self.form.domainList_3.setCurrentRow(0)

    def selectFile(self):

        case_number = self.form.selectLC.currentIndex()
        path = self.doc.Topology.combobox[case_number][1]
        self.form.fileName.setText(path)

        #clear old definitions
        for k in range(1, 4):
                getattr(self.form, f"selectMaterial_{k}").clear()
                getattr(self.form, f"thicknessObject_{k}").clear()

        for i in self.doc.Topology.combobox[case_number][2]:
            for j in range(1, 4):
                getattr(self.form, f"selectMaterial_{j}").addItem(i.Name)

        for i in self.doc.Topology.combobox[case_number][3]:
            for j in range(1, 4):
                getattr(self.form, f"thicknessObject_{j}").addItem(i.Name)

    def getAnalysis(self):
        comboBoxItems = []
        self.doc.Topology.combobox = []
        self.form.selectLC.clear()

        if self.doc.Topology.combobox:
            for i in self.doc.Topology.combobox:
                self.form.selectLC.addItem(i[0])
                self.selectFile()
            return
        lc = 0
        print(self.doc.Name)
        for obj in self.doc.Objects:
            try:
                if obj.TypeId == "Fem::FemAnalysis":  # to choose analysis objects
                    lc += 1
                    FemGui.setActiveAnalysis(obj)
                    analysisfolder = os.path.join(
                        self.workingDir + f"/TopologyCase_{lc}")
                    try:
                        os.mkdir(analysisfolder)
                        try:
                            fea = ccxtools.FemToolsCcx(analysis=obj)
                        except:

                            import ObjectsFem
                            obj.addObject(ObjectsFem.makeSolverCalculixCcxTools(self.doc))
                            fea = ccxtools.FemToolsCcx(analysis=obj)

                        fea.setup_working_dir(analysisfolder)
                        fea.update_objects()
                        fea.setup_ccx()

                        fea.purge_results()
                        fea.write_inp_file()
                        material, thickness = self.getAnalysisObjects(obj)
                        inppath = glob.glob(analysisfolder+"/*.inp")[0]
                        comboBoxItems.append([obj.Name, inppath, material, thickness])
                        self.form.selectLC.addItem(obj.Name)
                    except:
                        try:
                            for i in self.doc.Topology.combobox:
                                self.form.selectLC.addItem(i[0])
                            self.selectFile()
                            return
                        except:
                            FreeCAD.Console.PrintMessage(translate("FEMbyGEN","Target path has previous files. Old files are deleted."))
                            folders = glob.glob(self.workingDir + "/TopologyCase*")

                            for i in folders:
                                shutil.rmtree(i)

                            self.getAnalysis()

                            return
            except:
                # it counts deleted objects and gives error.
                pass

        self.doc.Topology.combobox = comboBoxItems
        self.selectFile()

    def setFilter(self):
        self.doc.Topology.filter_list=[]
        for i in range(1, self.doc.Topology.Number_of_Domains+1):
            filter = getattr(self.form, f"selectFilter_{i}").currentText()
            if getattr(self.form, f"filterRange_{i}").currentText() == "auto":
                Range = "auto"
            elif getattr(self.form, f"filterRange_{i}").currentText() == "manual":
                Range = float(getattr(self.form, f"range_{i}").text())
            direction = getattr(self.form, f"directionVector_{i}").text()
            selection = [item.text() for item in getattr(self.form, f"domainList_{i}").selectedItems()]

            filter_domains = []
            if "All defined" not in selection:
                if "Domain 1" in selection:
                    filter_domains.append(elset)
                if "Domain 2" in selection:
                    filter_domains.append(elset1)
                if "Domain 3" in selection:
                    filter_domains.append(elset2)
            if filter == "simple":
                self.doc.Topology.filter_list.append(['simple', Range])
                for dn in filter_domains:
                    self.doc.Topology.filter_list[-1].append(dn)
            elif filter == "casting":
                self.doc.Topology.filter_list.append(['casting', Range, f"({direction})"])
                for dn in filter_domains:
                    self.doc.Topology.filter_list[-1].append(dn)

    def setConfig(self):
        self.doc.Topology.file_name = os.path.split(self.form.fileName.text())[1]
        self.doc.Topology.path = os.path.split(self.form.fileName.text())[0]

        global elset2
        global elset
        global elset1
        elset2 = ""
        elset = ""
        elset1 = ""
        fea = ccxtools.FemToolsCcx()
        fea.setup_ccx()
        self.doc.Topology.path_calculix = fea.ccx_binary

        self.doc.Topology.optimization_base = self.form.optBase.currentText()  # stiffness,heat
        for case in range(len(self.doc.Topology.combobox)):
            for i in range(self.doc.Topology.Number_of_Domains):
                analysis = self.doc.Topology.combobox[case][0]

                elset_id = getattr(self.form, f"selectMaterial_{i+1}").currentIndex()
                thickness_id = getattr(self.form, f"thicknessObject_{i+1}").currentIndex()

                #except first domain there is a None option in combobox.So, index is one more
                # if i>0:
                #     elset_id -=1
                #     thickness_id -=1
                if thickness_id > -1:
                    elset_name = self.doc.Topology.combobox[case][2][elset_id].Name + \
                        self.doc.Topology.combobox[case][3][thickness_id].Name
                else:  # 0 means None thickness selected
                    elset_name = self.doc.Topology.combobox[case][2][elset_id].Name + "Solid"
                modulus = float(self.doc.Topology.combobox[case][2]
                                [elset_id].Material["YoungsModulus"].split()[0])  # MPa
                if self.doc.Topology.combobox[case][2][elset_id].Material["YoungsModulus"].split()[1] != "MPa":
                    raise Exception(" units not recognised in " + self.doc.Topology.combobox[elset_id][2])
                poisson = float(self.doc.Topology.combobox[case][2][elset_id].Material["PoissonRatio"].split()[0])
                try:
                    density = float(self.doc.Topology.combobox[case][2][elset_id].Material["Density"].split()[
                        0]) * 1e-12  # kg/m3 -> t/mm3
                    self.doc.Topology.domain_density[analysis] = {elset_name: [density*1e-6, density]}
                    if self.doc.Topology.combobox[case][2][elset_id].Material["Density"].split()[1] not in ["kg/m^3", "kg/m3"]:
                        raise Exception(" units not recognised in " + self.doc.Topology.combobox[elset_id][2])
                except KeyError:
                    self.doc.Topology.domain_density[analysis] = {elset_name: [0, 0]}
                try:
                    conductivity = float(
                        self.doc.Topology.combobox[case][2][elset_id].Material["ThermalConductivity"].split()[0])  # W/m/K
                    if self.doc.Topology.combobox[case][2][elset_id].Material["ThermalConductivity"].split()[1] != "W/m/K":
                        raise Exception(" units not recognised in " +
                                        self.doc.Topology.combobox[case][2][elset_id].Name)
                except KeyError:
                    conductivity = 0.
                try:
                    if self.doc.Topology.combobox[case][2][elset_id].Material["ThermalExpansionCoefficient"].split()[1] == "um/m/K":
                        expansion = float(self.doc.Topology.combobox[case][2][elset_id].Material["ThermalExpansionCoefficient"].split()[
                            0]) * 1e-6  # um/m/K -> mm/mm/K
                    elif self.doc.Topology.combobox[case][2][elset_id].Material["ThermalExpansionCoefficient"].split()[1] == "m/m/K":
                        expansion = float(self.doc.Topology.combobox[case][2][elset_id].Material["ThermalExpansionCoefficient"].split()[
                            0])  # m/m/K -> mm/mm/K
                    else:
                        raise Exception(" units not recognised in " +
                                        self.doc.Topology.combobox[case][2][elset_id].Name)
                except KeyError:
                    expansion = 0.
                try:
                    specific_heat = float(self.doc.Topology.combobox[case][2][elset_id].Material["SpecificHeat"].split()[
                        0]) * 1e6  # J/kg/K -> mm^2/s^2/K
                    if self.doc.Topology.combobox[case][2][elset_id].Material["SpecificHeat"].split()[1] != "J/kg/K":
                        raise Exception(" units not recognised in " +
                                        self.doc.Topology.combobox[case][2][elset_id].Name)
                except KeyError:
                    specific_heat = 0.
                if thickness_id > -1:
                    thickness = float(str(self.doc.Topology.combobox[case][3][thickness_id].Thickness).split()[0])  # mm
                    if str(self.doc.Topology.combobox[case][3][thickness_id].Thickness).split()[1] != "mm":
                        raise Exception(" units not recognised in " +
                                        self.doc.Topology.combobox[case][3][thickness_id].Name)
                else:
                    thickness = 0
                optimized = self.form.asDesign_checkbox_1.isChecked()
                if self.form.stressLimit_1.text():
                    von_mises = float(self.form.stressLimit_1.text())
                else:
                    von_mises = 0.

        #         if self.doc.Topology.Number_of_Domains == 2:
        #             elset_id1 = self.form.selectMaterial_2.currentIndex() - 1
        #             thickness_id1 = self.form.thicknessObject_2.currentIndex() - 1

        #             if elset_id1 != -1:
        #                 if thickness_id1 > -1:
        #                     elset1 = self.doc.Topology.combobox[case][elset_id1].Name + self.thicknesses[thickness_id1].Name
        #                 else:  # 0 means None thickness selected
        #                     elset1 = self.materials[elset_id1].Name + "Solid"
        #                 modulus1 = float(self.materials[elset_id1].Material["YoungsModulus"].split()[0])  # MPa
        #                 if self.materials[elset_id1].Material["YoungsModulus"].split()[1] != "MPa":
        #                     raise Exception(" units not recognised in " + self.materials[elset_id1].Name)
        #                 poisson1 = float(self.materials[elset_id1].Material["PoissonRatio"].split()[0])
        #                 try:
        #                     density1 = float(self.materials[elset_id1].Material["Density"].split()[0]) * 1e-12  # kg/m3 -> t/mm3
        #                     if self.materials[elset_id1].Material["Density"].split()[1] not in ["kg/m^3", "kg/m3"]:
        #                         raise Exception(" units not recognised in " + self.materials[elset_id1].Name)
        #                 except KeyError:
        #                     density1 = 0.
        #                 try:
        #                     conductivity1 = float(self.materials[elset_id1].Material["ThermalConductivity"].split()[0])  # W/m/K
        #                     if self.materials[elset_id1].Material["ThermalConductivity"].split()[1] != "W/m/K":
        #                         raise Exception(" units not recognised in " + self.materials[elset_id1].Name)
        #                 except KeyError:
        #                     conductivity1 = 0.
        #                 try:
        #                     if self.materials[elset_id1].Material["ThermalExpansionCoefficient"].split()[1] == "um/m/K":
        #                         expansion1 = float(self.materials[elset_id1].Material["ThermalExpansionCoefficient"].split()[
        #                             0]) * 1e-6  # um/m/K -> mm/mm/K
        #                     elif self.materials[elset_id1].Material["ThermalExpansionCoefficient"].split()[1] == "m/m/K":
        #                         expansion1 = float(self.materials[elset_id1].Material["ThermalExpansionCoefficient"].split()[
        #                             0])  # m/m/K -> mm/mm/K
        #                     else:
        #                         raise Exception(" units not recognised in " + self.materials[elset_id1].Name)
        #                 except KeyError:
        #                     expansion1 = 0.
        #                 try:
        #                     specific_heat1 = float(self.materials[elset_id1].Material["SpecificHeat"].split()[
        #                         0]) * 1e6  # J/kg/K -> mm^2/s^2/K
        #                     if self.materials[elset_id1].Material["SpecificHeat"].split()[1] != "J/kg/K":
        #                         raise Exception(" units not recognised in " + self.materials[elset_id1].Name)
        #                 except KeyError:
        #                     specific_heat1 = 0.
        #                 if thickness_id1 > -1:
        #                     thickness1 = str(self.thicknesses[thickness_id1].Thickness).split()[0]  # mm
        #                     if str(self.thicknesses[thickness_id1].Thickness).split()[1] != "mm":
        #                         raise Exception(" units not recognised in " + self.thicknesses[thickness_id1].Name)
        #                 else:
        #                     thickness1 = 0.
        #                 optimized1 = self.form.asDesign_checkbox_2.isChecked()
        #                 if self.form.stressLimit_2.text():
        #                     von_mises1 = float(self.form.stressLimit_2.text())
        #                 else:
        #                     von_mises1 = 0.
        # if self.doc.Topology.Number_of_Domains == 3:
        #     elset_id1 = self.form.selectMaterial_2.currentIndex() - 1
        #     thickness_id1 = self.form.thicknessObject_2.currentIndex() - 1

        #     if elset_id1 != -1:
        #         if thickness_id1 > -1:
        #             elset1 = self.materials[elset_id1].Name + self.thicknesses[thickness_id1].Name
        #         else:  # 0 means None thickness selected
        #             elset1 = self.materials[elset_id1].Name + "Solid"
        #         modulus1 = float(self.materials[elset_id1].Material["YoungsModulus"].split()[0])  # MPa
        #         if self.materials[elset_id1].Material["YoungsModulus"].split()[1] != "MPa":
        #             raise Exception(" units not recognised in " + self.materials[elset_id1].Name)
        #         poisson1 = float(self.materials[elset_id1].Material["PoissonRatio"].split()[0])
        #         try:
        #             density1 = float(self.materials[elset_id1].Material["Density"].split()[0]) * 1e-12  # kg/m3 -> t/mm3
        #             if self.materials[elset_id1].Material["Density"].split()[1] not in ["kg/m^3", "kg/m3"]:
        #                 raise Exception(" units not recognised in " + self.materials[elset_id1].Name)
        #         except KeyError:
        #             density1 = 0.
        #         try:
        #             conductivity1 = float(self.materials[elset_id1].Material["ThermalConductivity"].split()[0])  # W/m/K
        #             if self.materials[elset_id1].Material["ThermalConductivity"].split()[1] != "W/m/K":
        #                 raise Exception(" units not recognised in " + self.materials[elset_id1].Name)
        #         except KeyError:
        #             conductivity1 = 0.
        #         try:
        #             if self.materials[elset_id1].Material["ThermalExpansionCoefficient"].split()[1] == "um/m/K":
        #                 expansion1 = float(self.materials[elset_id1].Material["ThermalExpansionCoefficient"].split()[
        #                     0]) * 1e-6  # um/m/K -> mm/mm/K
        #             elif self.materials[elset_id1].Material["ThermalExpansionCoefficient"].split()[1] == "m/m/K":
        #                 expansion1 = float(self.materials[elset_id1].Material["ThermalExpansionCoefficient"].split()[
        #                     0])  # m/m/K -> mm/mm/K
        #             else:
        #                 raise Exception(" units not recognised in " + self.materials[elset_id1].Name)
        #         except KeyError:
        #             expansion1 = 0.
        #         try:
        #             specific_heat1 = float(self.materials[elset_id1].Material["SpecificHeat"].split()[
        #                 0]) * 1e6  # J/kg/K -> mm^2/s^2/K
        #             if self.materials[elset_id1].Material["SpecificHeat"].split()[1] != "J/kg/K":
        #                 raise Exception(" units not recognised in " + self.materials[elset_id1].Name)
        #         except KeyError:
        #             specific_heat1 = 0.
        #         if thickness_id1 > -1:
        #             thickness1 = str(self.thicknesses[thickness_id1].Thickness).split()[0]  # mm
        #             if str(self.thicknesses[thickness_id1].Thickness).split()[1] != "mm":
        #                 raise Exception(" units not recognised in " + self.thicknesses[thickness_id1].Name)
        #         else:
        #             thickness1 = 0.
        #         optimized1 = self.form.asDesign_checkbox_2.isChecked()
        #         if self.form.stressLimit_2.text():
        #             von_mises1 = float(self.form.stressLimit_2.text())
        #         else:
        #             von_mises1 = 0.

        #     elset_id2 = self.form.selectMaterial_3.currentIndex() - 1
        #     thickness_id2 = self.form.thicknessObject_3.currentIndex() - 1
        #     if elset_id2 != -1:
        #         if thickness_id2 > -1:
        #             elset2 = self.materials[elset_id2].Name + self.thicknesses[thickness_id2].Name
        #         else:  # 0 means None thickness selected
        #             elset2 = self.materials[elset_id2].Name + "Solid"
        #         modulus2 = float(self.materials[elset_id2].Material["YoungsModulus"].split()[0])  # MPa
        #         if self.materials[elset_id2].Material["YoungsModulus"].split()[1] != "MPa":
        #             raise Exception(" units not recognised in " + self.materials[elset_id2].Name)
        #         poisson2 = float(self.materials[elset_id2].Material["PoissonRatio"].split()[0])
        #         try:
        #             density2 = float(self.materials[elset_id2].Material["Density"].split()[0]) * 1e-12  # kg/m3 -> t/mm3
        #             if self.materials[elset_id2].Material["Density"].split()[1] not in ["kg/m^3", "kg/m3"]:
        #                 raise Exception(" units not recognised in " + self.materials[elset_id2].Name)
        #         except KeyError:
        #             density2 = 0.
        #         try:
        #             conductivity2 = float(self.materials[elset_id2].Material["ThermalConductivity"].split()[0])  # W/m/K
        #             if self.materials[elset_id2].Material["ThermalConductivity"].split()[1] != "W/m/K":
        #                 raise Exception(" units not recognised in " + self.materials[elset_id2].Name)
        #         except KeyError:
        #             conductivity2 = 0.
        #         try:
        #             if self.materials[elset_id2].Material["ThermalExpansionCoefficient"].split()[1] == "um/m/K":
        #                 expansion2 = float(self.materials[elset_id2].Material["ThermalExpansionCoefficient"].split()[
        #                     0]) * 1e-6  # um/m/K -> mm/mm/K
        #             elif self.materials[elset_id2].Material["ThermalExpansionCoefficient"].split()[1] == "m/m/K":
        #                 expansion2 = float(self.materials[elset_id2].Material["ThermalExpansionCoefficient"].split()[
        #                     0])  # m/m/K -> mm/mm/K
        #             else:
        #                 raise Exception(" units not recognised in " + self.materials[elset_id2].Name)
        #         except KeyError:
        #             expansion2 = 0.
        #         try:
        #             specific_heat2 = float(self.materials[elset_id2].Material["SpecificHeat"].split()[
        #                 0]) * 1e6  # J/kg/K -> mm^2/s^2/K
        #             if self.materials[elset_id2].Material["SpecificHeat"].split()[1] != "J/kg/K":
        #                 raise Exception(" units not recognised in " + self.materials[elset_id2].Name)
        #         except KeyError:
        #             specific_heat2 = 0.
        #         if thickness_id2 > -1:
        #             thickness2 = str(self.thicknesses[thickness_id2].Thickness).split()[0]  # mm
        #             if str(self.thicknesses[thickness_id2].Thickness).split()[1] != "mm":
        #                 raise Exception(" units not recognised in " + self.thicknesses[thickness_id2].Name)
        #         else:
        #             thickness2 = 0.
        #         optimized2 = self.form.asDesign_checkbox_3.isChecked()
        #         if self.form.stressLimit_3.text():
        #             von_mises2 = float(self.form.stressLimit_3.text())
        #         else:
                    # von_mises2 = 0.

            self.doc.Topology.domain_material[analysis] = {elset_name: [
                modulus, poisson, density, conductivity, expansion, specific_heat]}

            self.doc.Topology.domain_optimized[analysis] = {elset_name: optimized}
            if thickness:
                self.doc.Topology.domain_thickness[analysis] = {elset_name: [thickness, thickness]}
            if von_mises:
                self.doc.Topology.domain_FI[analysis] = {elset_name: [[('stress_von_Mises', von_mises * 1e6)],
                                                                      [('stress_von_Mises', von_mises)]]}
        self.doc.Topology.mass_goal_ratio = float(self.form.massGoalRatio.text())
        FreeCAD.Console.PrintMessage(translate("FEMbyGEN","Config file created\n"))

    def massratio(self, slider_position):
        if slider_position == 0:
            self.doc.Topology.mass_addition_ratio = 0.01
            self.doc.Topology.mass_removal_ratio = 0.02
        if slider_position == 1:
            self.doc.Topology.mass_addition_ratio = 0.015
            self.doc.Topology.mass_removal_ratio = 0.03
        if slider_position == 2:
            self.doc.Topology.mass_addition_ratio = 0.03
            self.doc.Topology.mass_removal_ratio = 0.06

    def runOptimization(self):
        # Run optimization
        self.setConfig()
        self.setFilter()
        analysis = self.form.selectLC.currentText()
        topologyObject = beso_main.BesoMain(analysis)
        topologyObject.main()
        FreeCADGui.runCommand('Std_ActivatePrevWindow')
        FreeCAD.setActiveDocument(self.doc.Name)
        
         
    # Uncomment the following line if needed
    # self.get_case("last")

    def get_case(self, numberofcase):
        lastcase = self.doc.Topology.LastState
        if not numberofcase:
            FreeCAD.Console.PrintError(translate("FEMbyGEN","The simulations are not completed\n"))
            return
        elif numberofcase == "last":
            numberofcase = lastcase
        mw = FreeCADGui.getMainWindow()
        evaluation_bar = QtGui.QToolBar()
        try:
            mw.removeToolBar(mw.findChild(QtGui.QToolBar, "Evaluation"))
        except:
            pass
        from functools import partial
        get_result = partial(Common.get_results_fc, self.doc)
        slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        slider.setGeometry(10, mw.height()-50, mw.width()-50, 50)
        slider.setMinimum(1)
        slider.setMaximum(lastcase)
        slider.setValue(numberofcase)
        slider.setTickPosition(QtGui.QSlider.TicksBelow)
        slider.setTickInterval(1)
        slider.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        slider.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        slider.sliderMoved.connect(get_result)
        button = QtGui.QPushButton("Animation")
        button.setGeometry(50, 100, 100, 30)
        timer = QtCore.QTimer()
        def start_auto_slider(s):
            button.setEnabled(False)  # Disable the button during automation
            timer.start(500)  # Trigger the auto_slide method every 100 milliseconds
        def auto_slide():
            current_value = slider.value()
            max_value = slider.maximum()

            if current_value < max_value:
                slider.setValue(current_value + 1)
                get_result(slider.value())
            else:
                timer.stop()  
                button.setEnabled(True)  
        button.clicked.connect(start_auto_slider) 
        timer.timeout.connect(auto_slide)
        closebutton = QtGui.QPushButton("")
        pix = QtGui.QStyle.SP_TitleBarCloseButton
        icon = closebutton.style().standardIcon(pix)
        closebutton.setIcon(icon)
        closebutton.clicked.connect(evaluation_bar.close)
        evaluation_bar.addWidget(button)
        evaluation_bar.addWidget(slider)
        evaluation_bar.addWidget(closebutton)
        evaluation_bar.setObjectName("Evaluation")
        mw.addToolBar(QtCore.Qt.ToolBarArea.BottomToolBarArea, evaluation_bar)
        get_result(lastcase)
    def openExample(self):
        webbrowser.open_new_tab("https://github.com/fandaL/beso/wiki/Example-4:-GUI-in-FreeCAD")

    def openConfComments(self):
        webbrowser.open_new_tab("https://github.com/fandaL/beso/blob/master/beso_conf.py")

    def openLog(self):
        """Open log file"""
        if self.form.fileName.text() in ["None analysis file selected", ""]:
            FreeCAD.Console.PrintMessage(translate("FEMbyGEN","None analysis file selected"))
        else:
            log_file = os.path.normpath(self.form.fileName.text()[:-4] + ".log.fcmacro")
            FreeCADGui.insert(log_file, "Log File")

    def selectMaterial1(self):
        if self.form.selectMaterial_1.currentText() == "None":
            self.form.thicknessObject_1.setEnabled(False)
            self.form.asDesign_checkbox_1.setEnabled(False)
            self.form.stressLimit_1.setEnabled(False)
        else:
            self.form.thicknessObject_1.setEnabled(True)
            self.form.asDesign_checkbox_1.setEnabled(True)
            self.form.stressLimit_1.setEnabled(True)

    def selectMaterial2(self):
        if self.form.selectMaterial_2.currentText() == "None":
            self.form.thicknessObject_2.setEnabled(False)
            self.form.asDesign_checkbox_2.setEnabled(False)
            self.form.stressLimit_2.setEnabled(False)
        else:
            self.form.thicknessObject_2.setEnabled(True)
            self.form.asDesign_checkbox_2.setEnabled(True)
            self.form.stressLimit_2.setEnabled(True)

    def selectMaterial3(self):
        if self.form.selectMaterial_3.currentText() == "None":
            self.form.thicknessObject_3.setEnabled(False)
            self.form.asDesign_checkbox_3.setEnabled(False)
            self.form.stressLimit_3.setEnabled(False)
        else:
            self.form.thicknessObject_3.setEnabled(True)
            self.form.asDesign_checkbox_3.setEnabled(True)
            self.form.stressLimit_3.setEnabled(True)

    def filterRange1(self):
        if self.form.filterRange_1.currentText() == "auto":
            self.form.range_1.setEnabled(False)  # range as mm
        elif self.form.filterRange_1.currentText() == "manual":
            self.form.range_1.setEnabled(True)

    def filterRange2(self):
        if self.form.filterRange_2.currentText() == "auto":
            self.form.range_2.setEnabled(False)
        elif self.form.filterRange_2.currentText() == "manual":
            self.form.range_2.setEnabled(True)

    def filterRange3(self):
        if self.form.filterRange_3.currentText() == "auto":
            self.form.range_3.setEnabled(False)
        elif self.form.filterRange_3.currentText() == "manual":
            self.form.range_3.setEnabled(True)

    def filterType1(self):
        if self.form.selectFilter_1.currentText() == "None":
            self.form.filterRange_1.setEnabled(False)
            self.form.range_1.setEnabled(False)
            self.form.directionVector_1.setEnabled(False)
            self.form.domainList_1.setEnabled(False)
        elif self.form.selectFilter_1.currentText() == "casting":
            self.form.filterRange_1.setEnabled(True)
            if self.form.filterRange_1.currentText() == "manual":
                self.form.range_1.setEnabled(True)
            self.form.directionVector_1.setEnabled(True)
            self.form.domainList_1.setEnabled(True)
        else:
            self.form.filterRange_1.setEnabled(True)
            if self.form.filterRange_1.currentText() == "manual":
                self.form.range_1.setEnabled(True)
            self.form.directionVector_1.setEnabled(False)
            self.form.domainList_1.setEnabled(True)
    def filterType2(self):
        if self.form.selectFilter_2.currentText() == "None":
            self.form.filterRange_2.setEnabled(False)
            self.form.range_2.setEnabled(False)
            self.form.directionVector_2.setEnabled(False)
            self.form.domainList_2.setEnabled(False)
        elif self.form.selectFilter_2.currentText() == "casting":
            self.form.filterRange_2.setEnabled(True)
            if self.form.filterRange_2.currentText() == "manual":
                self.form.range_2.setEnabled(True)
            self.form.directionVector_2.setEnabled(True)
            self.form.domainList_2.setEnabled(True)
        else:
            self.form.filterRange_2.setEnabled(True)
            if self.form.filterRange_2.currentText() == "manual":
                self.form.range_2.setEnabled(True)
            self.form.directionVector_2.setEnabled(False)
            self.form.domainList_2.setEnabled(True)

    def filterType3(self):
        if self.form.selectFilter_3.currentText() == "None":
            self.form.filterRange_3.setEnabled(False)
            self.form.range_3.setEnabled(False)
            self.form.directionVector_3.setEnabled(False)
            self.form.domainList_3.setEnabled(False)
        elif self.form.selectFilter_3.currentText() == "casting":
            self.form.filterRange_3.setEnabled(True)
            if self.form.filterRange_3.currentText() == "manual":
                self.form.range_3.setEnabled(True)
            self.form.directionVector_3.setEnabled(True)
            self.form.domainList_3.setEnabled(True)
        else:
            self.form.filterRange_3.setEnabled(True)
            if self.form.filterRange_3.currentText() == "manual":
                self.form.range_3.setEnabled(True)
            self.form.directionVector_3.setEnabled(False)
            self.form.domainList_3.setEnabled(True)

    def accept(self):
        doc = FreeCADGui.getDocument(self.doc)
        doc.resetEdit()
        doc.Document.recompute()

    def reject(self):
        doc = FreeCADGui.getDocument(self.doc)
        doc.resetEdit()

class ViewProviderGen:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(FreeCAD.getUserAppDataDir() + 'Mod/FEMbyGEN/fembygen/icons/Topology.svg')
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
            FreeCAD.Console.PrintError(translate("FEMbyGEN",'Existing task dialog already open\n'))
        return True

    def setEdit(self, vobj, mode):
        taskd = TopologyPanel(vobj.Object)
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


class ViewProviderLink:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(FreeCAD.getUserAppDataDir() + 'Mod/FEMbyGEN/fembygen/icons/Topology.svg')
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        return

    def doubleClicked(self, vobj):
        doc = FreeCAD.openDocument(vobj.Object.Path)
        guiDoc = FreeCADGui.getDocument(doc)
        if not guiDoc.getInEdit():
            guiDoc.setEdit(doc.Topology)
        else:
            FreeCAD.Console.PrintError(translate("FEMbyGEN",'Existing task dialog already open\n'))
        return True

    def setEdit(self, vobj, mode):
        taskd = TopologyMasterPanel(vobj.Object)
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


FreeCADGui.addCommand('Topology', TopologyCommand())
