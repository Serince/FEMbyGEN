import FreeCAD
import FreeCADGui
import Fem
import os.path
import shutil
from fembygen import Common
import numpy as np
from PySide import QtCore, QtGui    # FreeCAD's PySide!
import multiprocessing.dummy as mp
from multiprocessing import cpu_count
from functools import partial

translate = FreeCAD.Qt.translate
def QT_TRANSLATE_NOOP(context, text):
    return text
import FreeCADGui
import os
FreeCADGui.addLanguagePath(os.path.join(FreeCAD.getUserAppDataDir(),"\Mod\FEMbyGEN\fembygen\translations"))
FreeCADGui.updateLocale()

LOCATION = os.path.normpath('Mod/FEMbyGEN/fembygen')

def makeGenerate():
    """Creating generate in combo view """
    try:
        obj = FreeCAD.ActiveDocument.Generate
        obj.isValid()
    except:
        obj = FreeCAD.ActiveDocument.addObject(
            "Part::FeaturePython", "Generate")
        FreeCAD.ActiveDocument.GenerativeDesign.addObject(obj)
    Generate(obj)
    if FreeCAD.GuiUp:
        ViewProviderGen(obj.ViewObject)
    return obj


class Generate:
    """Part generations"""

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "Generate"
        self.initProperties(obj)

    def initProperties(self, obj):
        try:
            obj.addProperty("App::PropertyEnumeration", "GenerationMethod", "Base",
                            "Generation Method")
            obj.GenerationMethod = ["Full Factorial Design", "Taguchi Optimization Design",
                                    "Plackett Burman Design", "Box Behnken Design",
                                    "Latin Hyper Cube Design", "Central Composite Design"]
            obj.addProperty("App::PropertyStringList", "ParametersName", "Base",
                            "Generated parameter matrix")
            obj.addProperty("App::PropertyPythonObject", "GeneratedParameters", "Base",
                            "Generated parameter matrix")
            obj.addProperty("App::PropertyInteger", "NumberOfCPU", "Base",
                            "Number of CPU's to use ")
            obj.NumberOfCPU = cpu_count()-1
        except:
            pass


class GenerateCommand():
    """Produce part generations"""

    def GetResources(self):
        return {'Pixmap': os.path.join(FreeCAD.getUserAppDataDir(), LOCATION, 'icons/Generate.svg'),
                'Accel': "Shift+G",  # a default shortcut (optional)
                'MenuText': QT_TRANSLATE_NOOP("CommandName","Generate"),
                'ToolTip': QT_TRANSLATE_NOOP("CommandName","Produce part generations")}

    def Activated(self):
        obj = makeGenerate()
        doc = FreeCADGui.ActiveDocument
        if not doc.getInEdit():
            doc.setEdit(obj.ViewObject.Object.Name)
        else:
            FreeCAD.Console.PrintError(translate("FEMbyGEN",'Existing task dialog already open\n'))
        return

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return FreeCAD.ActiveDocument is not None


class GeneratePanel():
    def __init__(self, object):

        self.obj = object
        # this will create a Qt widget from our ui file
        guiPath = os.path.join(FreeCAD.getUserAppDataDir(), LOCATION, 'ui/Generate.ui')
        self.form = FreeCADGui.PySideUic.loadUi(guiPath)
        self.doc = object.Object.Document
        self.workingDir = os.path.dirname(os.path.normpath(self.doc.FileName))
        Common.setWorkspace(self.doc, self.workingDir)

        index = self.form.selectDesign.findText(
            self.doc.Generate.GenerationMethod, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.form.selectDesign.setCurrentIndex(index)

        # Check if any generations have been made already, and up to what number
        self.resetViewControls()
        self.updateParametersTable()

        self.form.more.setIcon(QtGui.QIcon(':/icons/Std_DlgParameter.svg'))
        self.form.deleteGensButton.setIcon(QtGui.QIcon(':/icons/edit-delete.svg'))

        # Connect the signal procedures
        self.form.selectDesign.currentTextChanged.connect(self.designChanged)
        self.form.more.clicked.connect(self.more)
        self.form.generateButton.clicked.connect(self.generateParts)
        self.form.selectGenBox.valueChanged.connect(self.viewGeneration)
        self.form.nextGen.clicked.connect(self.form.selectGenBox.stepUp)
        self.form.previousGen.clicked.connect(self.form.selectGenBox.stepDown)
        self.form.deleteGensButton.clicked.connect(self.deleteGenerations)

    def designChanged(self, text):
        if text in ["Box Behnken Design", "Central Composite Design", "Latin Hyper Cube Design"]:
            self.form.more.setEnabled(True)
        else:
            self.form.more.setEnabled(False)

    def more(self):
        """Input screens for methods"""
        path = os.path.join(FreeCAD.getUserAppDataDir(), LOCATION, 'ui')
        method = self.form.selectDesign.currentText()
        if method == "Box Behnken Design":
            def save():
                self.doc.Generate.CenterPoints = int(settings.center.text())
                settings.close()

            settings = FreeCADGui.PySideUic.loadUi(os.path.join(path, 'more_box_behnken.ui'))
            try:
                settings.center.setText(str(self.doc.Generate.CenterPoints))
            except:
                pass

            try:
                self.doc.Generate.addProperty("App::PropertyInteger", "CenterPoints", "Box Behnken",
                                              "The number of center points to include")
            except:
                pass
            settings.show()
            settings.save.clicked.connect(save)

        elif method == "Central Composite Design":
            def save():
                import ast
                self.doc.Generate.Center = ast.literal_eval(settings.center.text())
                self.doc.Generate.Alpha = settings.alpha.currentText()
                self.doc.Generate.Face = settings.face.currentText()
                settings.close()
            settings = FreeCADGui.PySideUic.loadUi(os.path.join(path, 'more_composite.ui'))
            settings.show()
            try:
                settings.center.setText(str(self.doc.Generate.Center))
                index_alpha = settings.alpha.findText(self.doc.Generate.Alpha, QtCore.Qt.MatchFixedString)
                if index_alpha >= 0:
                    settings.alpha.setCurrentIndex(index_alpha)
                index_face = settings.face.findText(self.doc.Generate.Face, QtCore.Qt.MatchFixedString)
                if index_face >= 0:
                    settings.face.setCurrentIndex(index_face)
            except:
                pass

            try:
                self.doc.Generate.addProperty("App::PropertyIntegerList", "Center", "Central Composite",
                                              "Number of center array")
                self.doc.Generate.addProperty("App::PropertyEnumeration", "Alpha", "Central Composite",
                                              "The effect of alpha has on the variance")
                self.doc.Generate.Alpha = ["orthogonal", "rotatable"]
                self.doc.Generate.addProperty("App::PropertyEnumeration", "Face", "Central Composite",
                                              "The relation between the start points and the corner (factorial) points.")
                self.doc.Generate.Face = ["circumscribed", "inscribed", "faced"]
            except:
                pass
            settings.show()
            settings.save.clicked.connect(save)

        elif method == "Latin Hyper Cube Design":
            def save():
                import ast
                self.doc.Generate.Samples = int(settings.samples.text())
                self.doc.Generate.Criterion = settings.criterion.currentText()
                self.doc.Generate.Iterations = int(settings.iterations.text())
                self.doc.Generate.RandomState = int(settings.randomstate.text())
                corrmat=settings.correlationmatrix.text()
                if corrmat != "None":
                    self.doc.Generate.CorrelationMatrix=ast.literal_eval(corrmat)
                settings.close()
            settings = FreeCADGui.PySideUic.loadUi(os.path.join(path, 'more_lhs.ui'))
            settings.samples.setText(str(len(self.doc.Generate.ParametersName)))
            settings.show()
            try:
                settings.samples.setText(str(self.doc.Generate.Samples))
                index = settings.criterion.findText(self.doc.Generate.Criterion, QtCore.Qt.MatchFixedString)
                if index >= 0:
                    settings.criterion.setCurrentIndex(index)
                settings.iterations.setText(str(self.doc.Generate.Iterations))
                settings.randomstate.setText(str(self.doc.Generate.RandomState))
                settings.correlationmatrix.setText(str(self.doc.Generate.CorrelationMatrix))
            except:
                pass

            try:
                self.doc.Generate.addProperty("App::PropertyInteger", "Samples", "Latin Hyper Cube",
                                              "The number of samples to generate for each factor (Default: number of parameters)")
                self.doc.Generate.addProperty("App::PropertyEnumeration", "Criterion", "Latin Hyper Cube",
                                              "Criterion")
                self.doc.Generate.Criterion = ["center", "maxmin","centermaximin","correlation","lhsmu"]
                self.doc.Generate.addProperty("App::PropertyInteger", "Iterations", "Latin Hyper Cube",
                                              "The number of iterations in the maximin and correlations algorithms.")
                self.doc.Generate.addProperty("App::PropertyInteger", "RandomState", "Latin Hyper Cube",
                                              "Random state (or seed-number) which controls the seed and random draws")
                self.doc.Generate.addProperty("App::PropertyIntegerList", "CorrelationMatrix", "Latin Hyper Cube",
                                              "Enforce correlation between factors (only used in lhsmu)")
            except:
                pass
            settings.show()
            settings.save.clicked.connect(save)

    def meshing(self, mesh, type):
        # Remeshing new generation
        if type == "Netgen":
            mesh.FemMesh = Fem.FemMesh()  # cleaning old meshes
            mesh.recompute()
        elif type == "Gmsh":
            from femmesh.gmshtools import GmshTools as gt
            mesh.FemMesh = Fem.FemMesh()  # cleaning old meshes
            gmsh_mesh = gt(mesh)
            gmsh_mesh.create_mesh()

    def copy_mesh(self, numgenerations, i):
        docPath = os.path.normpath(self.doc.FileName)
        name = f"Gen{i+1}"
        directory = os.path.join(self.workingDir, name)
        filePath = os.path.join(directory, name+".FCStd")
        
        # Regenerate the part and save generation as FreeCAD doc
        try:
            os.mkdir(directory)
        except:
            FreeCAD.Console.PrintWarning(translate("FEMbyGEN",f"Keeping existing {name}\n"))
            return
        shutil.copy(docPath, filePath)
        shutil.copy(filePath, filePath+".backup")

        doc = FreeCAD.open(filePath, hidden=True)

        # Produce parameters sheet for new geometry
        doc.Parameters.set('C1', 'Value')
        for k in range(self.inumber[0]):
            doc.Parameters.set(
                f'C{k+2}', f'{numgenerations[i][k]}')
            doc.Parameters.clear(f'D1:D{k+2}')
            doc.Parameters.clear(f'E1:E{k+2}')

        # Removing generative design container in the file
        for l in doc.GenerativeDesign.Group:
            if l.Name == "Parameters":
                pass
            else:
                doc.removeObject(l.Name)
        doc.removeObject(doc.GenerativeDesign.Name)
        doc.recompute()

        # getting first analysis meshing object and copy it other loadcases
        for mesh in doc.Objects:
            if mesh.TypeId == 'Fem::FemMeshObjectPython':
                self.meshing(mesh, "Gmsh")
                break
            elif mesh.TypeId == 'Fem::FemMeshShapeNetgenObject':
                self.meshing(mesh, "Netgen")
                break

        lc = 0
        for obj in doc.Objects:
            try:
                if obj.TypeId == "Fem::FemAnalysis":  # to choose analysis objects
                    lc += 1
                    # copying first loadcase mesh to other loadcases
                    if lc > 1:
                        for femobj in obj.Group:
                            # delete old mesh of second or later analysis
                            if femobj.TypeId in ['Fem::FemMeshObjectPython', 'Fem::FemMeshShapeNetgenObject']:
                                doc.removeObject(femobj.Name)

                        # copying same mesh to other loadcases
                        obj.addObject(doc.copyObject(mesh, False))
            except:
                # after deleting mesh elements, for loop counts it again and it is not exist as object anymore
                pass

        doc.recompute()
        doc.save()
        FreeCAD.closeDocument(name)

    def generateParts(self):
        master = self.doc
        master.save()  # saving the prepared masterfile

        # Getting spreadsheet from FreeCAD
        paramNames = []
        numberofgen = []
        self.detection = []
        self.inumber = []

        # Getting number of parameters
        try:
            for i in range(99):
                self.detection.append(master.Parameters.get(f'C{i+2}'))
        except:
            self.inumber.append(i)

        param = []

        #  Getting data from Spreadsheet
        for i in range(self.inumber[0]):
            paramNames.append(master.Parameters.get(f'B{i+2}'))
            mins = float(master.Parameters.get(f'C{i+2}'))
            maxs = float(master.Parameters.get(f'D{i+2}'))
            numberofgen = int(master.Parameters.get(f'E{i+2}'))
            param.append(np.linspace(mins, maxs, numberofgen))

        # Combination of all parameters
        selectedModule = self.form.selectDesign.currentText()
        self.doc.Generate.GenerationMethod = selectedModule

        numgenerations = self.design(selectedModule, param, numberofgen)
        iterationnumber = len(numgenerations)

        # delete earlier generations files before
        if Common.checkGenerations() > 0:
            self.deleteGenerations()

        # Progress bars
        progress_bar = FreeCAD.Base.ProgressIndicator()    # FreeCAD's progress bar
        progress_bar.start('Generate parts ...', iterationnumber)
        self.form.progressBar.setValue(1)

        func = partial(self.copy_mesh, numgenerations)
        p = mp.Pool(self.doc.Generate.NumberOfCPU)
        for i, _ in enumerate(p.imap_unordered(func, range(iterationnumber))):
            # Update progress bar
            progress_bar.next()
            progress = ((i+1)/iterationnumber) * 100
            self.form.progressBar.setValue(progress)
        p.close()
        p.join()

        # ReActivate document again once finished
        FreeCAD.setActiveDocument(master.Name)
        master.Generate.GeneratedParameters = numgenerations
        master.Generate.ParametersName = paramNames

        # Update number of generations produced in window
        self.resetViewControls()
        self.updateParametersTable()
        progress_bar.stop()

        master.save()  # too store generated values in generate object
        FreeCAD.Console.PrintMessage(translate("FEMbyGEN","Generation done successfully!\n"))
        Common.openGen(1)

    def deleteGenerations(self):
        qm = QtGui.QMessageBox
        ret = qm.question(None, '',
                          "Are you sure to delete all the earlier generation files?",
                          qm.Yes | qm.No)
        if ret == qm.No:
            FreeCAD.Console.PrintMessage(translate("FEMbyGEN","Nothing Deleted\n"))
        else:
            Common.closeGen(0)    # close all generations

            # Delete analysis directories
            numGens = Common.checkGenerations(self.workingDir)
            for i in range(1, numGens+1):
                directory = os.path.join(self.workingDir, f"Gen{i}")
                try:
                    shutil.rmtree(directory)
                except FileNotFoundError:
                    FreeCAD.Console.PrintError(translate("FEMbyGEN",f"Generation {i} analysis data not found\n"))
                except Exception:
                    FreeCAD.Console.PrintError(translate("FEMbyGEN",
                        f"Error while trying to delete analysis folder for generation {i}\n"))
                else:
                    FreeCAD.Console.PrintMessage(translate("FEMbyGEN",directory + " deleted\n"))

            # Delete if earlier generative objects exist
            for l in self.doc.GenerativeDesign.Group:
                if l.Name == "Parameters" or l.Name == "Generate":
                    pass
                elif l.Name == "Results":
                    Common.purge_results(self.doc)
                else:
                    self.doc.removeObject(l.Name)

            self.doc.Generate.GeneratedParameters = None
            self.resetViewControls()
            self.updateParametersTable()
            FreeCAD.setActiveDocument(self.doc.Name)

    def viewGeneration(self, value):
        keep = self.form.checkBoxKeep.isChecked()
        Common.viewGen(value, keep)
        self.form.parametersTable.selectRow(value-1)

    def resetViewControls(self):
        numGens = Common.checkGenerations()

        enable = True if numGens > 0 else False
        self.form.selectGenBox.setEnabled(enable)
        self.form.nextGen.setEnabled(enable)
        self.form.previousGen.setEnabled(enable)

        self.form.numGensLabel.setText(f"{numGens} generations produced")
        self.form.selectGenBox.setRange(1, numGens)

    def updateParametersTable(self):
        paramNames = self.doc.Generate.ParametersName
        parameterValues = self.doc.Generate.GeneratedParameters
        tableWidget = self.form.parametersTable
        
        if parameterValues == None:
            tableWidget.setEnabled(False)
            return

        tableWidget.setEnabled(True)
        tableWidget.setColumnCount(len(paramNames))
        tableWidget.setRowCount(len(parameterValues))
        tableWidget.setHorizontalHeaderLabels(paramNames)
        tableWidget.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)

        for col in range(tableWidget.columnCount()):
            for row in range(tableWidget.rowCount()):
                item = QtGui.QTableWidgetItem(str(parameterValues[row][col]))
                tableWidget.setItem(row, col, item)
        if Common.checkGenerations() > 0:
            tableWidget.itemClicked.connect(
                lambda item: self.form.selectGenBox.setValue(item.row()+1))

    def accept(self):
        """Qt convenience function: Ok pressed"""
        if not self.form.checkBoxKeep.isChecked():
            Common.closeGen(0)    # close all generations
        guiDoc = FreeCADGui.getDocument(self.doc)
        guiDoc.resetEdit()    # close dialog
        self.doc.recompute()

    def reject(self):
        """Qt convenience function: Cancel pressed"""
        Common.closeGen(0)    # close all generations
        guiDoc = FreeCADGui.getDocument(self.doc)
        guiDoc.resetEdit()    # close dialog

    def design(self, method, parameters, numberofgen):
        from fembygen.design import Design, Taguchi
        if method == "Full Factorial Design":
            return Design.fullfact(parameters)
        elif method == "Plackett Burman Design":
            return Design.designpb(parameters)
        elif method == "Box Behnken Design":
            try:
                center = self.doc.Generate.CenterPoints
            except:
                center = None
            return Design.designboxBen(parameters, center)
        elif method == "Central Composite Design":
            try:
                center = self.doc.Generate.Center
                face = self.doc.Generate.Face
                alpha = self.doc.Generate.Alpha
            except:
                center = (4, 4)
                alpha = "orthogonal"
                face = "circumscribed"
            return Design.designcentalcom(parameters, center, alpha, face)
        elif method == "Latin Hyper Cube Design":
            try:
                samples = self.doc.Generate.Samples
                criterion = self.doc.Generate.Criterion
                iterations = self.doc.Generate.Iterations
                random_state = self.doc.Generate.RandomState
                correlation_matrix = self.doc.Generate.CorrelationMatrix
            except:
                samples = None
                criterion = None
                iterations = None
                random_state = None
                correlation_matrix = None
            return Design.designlhc(parameters,samples,criterion, iterations, random_state, correlation_matrix)
        elif method == "Taguchi Optimization Design":
            result = Taguchi.Taguchipy(parameters, numberofgen)
            res = result.selection()
            return list(res)


class ViewProviderGen:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(FreeCAD.getUserAppDataDir(), LOCATION, 'icons/Generate.svg')
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
        taskd = GeneratePanel(vobj)
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


FreeCADGui.addCommand('Generate', GenerateCommand())
