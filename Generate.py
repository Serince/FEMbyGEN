import FreeCAD
import FreeCADGui
import Fem
import os.path
import shutil
from fembygen import Common
import numpy as np
import PySide
import multiprocessing.dummy as mp
from multiprocessing import cpu_count
from functools import partial


def makeGenerate():
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
    """ Finite Element Analysis """

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
        return {'Pixmap': os.path.join(FreeCAD.getUserAppDataDir() + 'Mod/FEMbyGEN/fembygen/icons/Generate.svg'),  # the name of a svg file available in the resources
                'Accel': "Shift+G",  # a default shortcut (optional)
                'MenuText': "Generate",
                'ToolTip': "Produce part generations"}

    def Activated(self):
        obj = makeGenerate()
        doc = FreeCADGui.ActiveDocument
        if not doc.getInEdit():
            doc.setEdit(obj.ViewObject.Object.Name)
        else:
            FreeCAD.Console.PrintError('Existing task dialog already open\n')
        return

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return FreeCAD.ActiveDocument is not None


class GeneratePanel():
    def __init__(self, object):

        self.obj = object
        # this will create a Qt widget from our ui file
        guiPath = FreeCAD.getUserAppDataDir() + "Mod/FEMbyGEN/fembygen/ui/Generate.ui"
        self.form = FreeCADGui.PySideUic.loadUi(guiPath)
        self.workingDir = '/'.join(
            object.Object.Document.FileName.split('/')[0:-1])

        # Data variables for parameter table

        self.doc = object.Object.Document
        # (paramNames, parameterValues) = Common.checkGenParameters(self.doc)
        # self.doc.Generate.ParametersName = paramNames
        # self.doc.Generate.GeneratedParameters = parameterValues
        index = self.form.selectDesign.findText(self.doc.Generate.GenerationMethod, PySide.QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.form.selectDesign.setCurrentIndex(index)
        # Check if any generations have been made already, and up to what number
        close = partial(Common.showGen,"close", self.doc)
        self.form.selectDesign.currentTextChanged.connect(close)
        numGens = Common.checkGenerations(self.workingDir)
        self.resetViewControls(numGens)

        self.form.numGensLabel.setText(f"{numGens} generations produced")

        self.selectedGen = -1

        # Connect the button procedures
        self.form.generateButton.clicked.connect(self.generateParts)
        self.form.viewGenButton.clicked.connect(self.viewGeneration)
        self.form.deleteGensButton.clicked.connect(self.deleteGenerations)
        self.form.nextGen.clicked.connect(lambda: self.nextG(numGens))
        self.form.previousGen.clicked.connect(
            lambda: self.previousG(numGens))

        pix = PySide.QtWidgets.QStyle.SP_FileDialogDetailedView
        icon = self.form.more.style().standardIcon(pix)
        self.form.more.setIcon(icon)
        self.form.more.clicked.connect(self.more)
        self.updateParametersTable()

    def more(self):
        """I will write here a detailed inputs screens for methods"""
        path = FreeCAD.getUserAppDataDir() + "Mod/FEMbyGEN/fembygen/ui/"
        method = self.form.selectDesign.currentText()
        if method == "Full Factorial Design":
            pass
        elif method == "Plackett Burman Design":
            pass
        elif method == "Box Behnken Design":
            def save():
                self.doc.Generate.CenterPoints = int(settings.center.text())
                settings.close()

            settings = FreeCADGui.PySideUic.loadUi(path+"more_box_behnken.ui")
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
            settings = FreeCADGui.PySideUic.loadUi(path+"more_composite.ui")
            settings.show()
            try:
                settings.center.setText(str(self.doc.Generate.Center))
                index_alpha = settings.alpha.findText(self.doc.Generate.Alpha, PySide.QtCore.Qt.MatchFixedString)
                if index_alpha >= 0:
                    settings.alpha.setCurrentIndex(index_alpha)
                index_face = settings.face.findText(self.doc.Generate.Face, PySide.QtCore.Qt.MatchFixedString)
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
            settings = FreeCADGui.PySideUic.loadUi(path+"more_lhs.ui")
            settings.samples.setText(str(len(self.doc.Generate.ParametersName)))
            settings.show()
            try:
                settings.samples.setText(str(self.doc.Generate.Samples))
                index = settings.criterion.findText(self.doc.Generate.Criterion, PySide.QtCore.Qt.MatchFixedString)
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
        elif method == "Taguchi Optimization Design":
            pass

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
        docPath = self.doc.FileName
        # Regenerate the part and save generation as FreeCAD doc
        try:
            os.mkdir(self.workingDir + f"/Gen{i+1}")
        except:
            FreeCAD.Console.PrintError(f"Please delete earlier generations folders...\n")
            return

        filename = f"Gen{i+1}.FCStd"
        directory = self.workingDir + f"/Gen{i+1}/"
        filePath = directory + filename
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
                            if femobj.TypeId == 'Fem::FemMeshObjectPython' or femobj.TypeId == 'Fem::FemMeshShapeNetgenObject':
                                doc.removeObject(femobj.Name)

                        # copying same mesh to other loadcases
                        obj.addObject(doc.copyObject(mesh, False))
            except:
                # after deleting mesh elements, for loop counts it again and it is not exist as object anymore
                pass

        doc.recompute()
        doc.save()
        FreeCAD.closeDocument(filename[:-6])

    def generateParts(self):
        master = self.doc
        master.save()  # saving the prepared masterfile
        docPath = master.FileName

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

        self.form.progressBar.setStyleSheet(
            'QProgressBar {text-align: center; } QProgressBar::chunk {background-color: #009688;}')
        # Combination of all parameters
        selectedModule = self.form.selectDesign.currentText()
        self.doc.Generate.GenerationMethod = selectedModule

        numgenerations = self.design(selectedModule, param, numberofgen)

        numGens = Common.checkGenerations(self.workingDir)  # delete earlier generations files before
        if numGens > 0:
            self.deleteGenerations()

        func = partial(self.copy_mesh, numgenerations)
        iterationnumber = len(numgenerations)
        p = mp.Pool(self.doc.Generate.NumberOfCPU)
        for i, _ in enumerate(p.imap_unordered(func, range(iterationnumber))):
            # Update progress bar
            progress = ((i+1)/iterationnumber) * 100
            self.form.progressBar.setValue(progress)
        p.close()
        p.join()

        # ReActivate document again once finished
        FreeCAD.setActiveDocument(master.Name)
        master.Generate.GeneratedParameters = numgenerations
        master.Generate.ParametersName = paramNames
        self.updateParametersTable()

        # Update number of generations produced in window
        numGens = Common.checkGenerations(self.workingDir)
        self.form.numGensLabel.setText(
            str(numGens) + " generations produced")
        self.resetViewControls(numGens)
        self.updateParametersTable()
        master.save()  # too store generated values in generate object
        FreeCAD.Console.PrintMessage("Generation done successfully!\n")

    def deleteGenerations(self):
        qm = PySide.QtWidgets.QMessageBox
        ret = qm.question(None, '', "Are you sure to delete all the earlier generation files?", qm.Yes | qm.No)

        if ret == qm.Yes:

            FreeCAD.Console.PrintMessage("Deleting...\n")

            numGens = Common.checkGenerations(self.workingDir)
            for i in range(1, numGens+1):
                # Delete analysis directories
                try:
                    shutil.rmtree(self.workingDir + f"/Gen{i}/")
                    FreeCAD.Console.PrintMessage(
                        self.workingDir + f"/Gen{i}/ deleted\n")
                except FileNotFoundError:
                    FreeCAD.Console.PrintError("INFO: Generation " + str(i) +
                                               " analysis data not found\n")
                    pass
                except:
                    FreeCAD.Console.PrintError(
                        "Error while trying to delete analysis folder for generation\n " + str(i))

            # Delete if earlier generative objects exist
            try:
                for l in self.doc.GenerativeDesign.Group:
                    if l.Name == "Parameters" or l.Name == "Generate":
                        pass
                    elif l.Name == "Results":
                        Common.purge_results(self.doc)
                    else:
                        self.doc.removeObject(l.Name)
            except:
                pass

            self.doc.Generate.GeneratedParameters = None
            # refreshing the table
            self.resetViewControls(numGens)
            self.updateParametersTable()
            FreeCAD.setActiveDocument(self.doc.Name)
        else:
            qm.information(None, '', "Nothing Changed")
            FreeCAD.Console.PrintMessage("Nothing Deleted\n")

    def nextG(self, numGens):
        index = self.form.selectGenBox.currentIndex()
        if index >= numGens-1:
            index = -1
        self.form.selectGenBox.setCurrentIndex(index+1)
        self.viewGeneration()

    def previousG(self, numGens):
        index = self.form.selectGenBox.currentIndex()
        if index <= 0:
            index = numGens
        self.form.selectGenBox.setCurrentIndex(index-1)
        self.viewGeneration()

    def viewGeneration(self):
        # Close the generation that the user might be viewing previously
        if self.selectedGen > 0:
            docName = f"Gen{self.selectedGen}"
            FreeCAD.closeDocument(docName)

        # Find which generation is selected in the combo box
        self.selectedGen = self.form.selectGenBox.currentText()
        self.selectedGen = int(str(self.selectedGen).split()[-1])

        # Open the generation
        docPath = self.workingDir + \
            f"/Gen{self.selectedGen}/Gen{self.selectedGen}.FCStd"
        docName = f"Gen{self.selectedGen}"
        FreeCAD.open(docPath)
        # FreeCAD.setActiveDocument(docName)

    def resetViewControls(self, numGens):
        comboBoxItems = []

        if numGens > 0:
            self.form.viewGenButton.setEnabled(True)
            self.form.selectGenBox.setEnabled(True)
            self.form.nextGen.setEnabled(True)
            self.form.previousGen.setEnabled(True)

            for i in range(1, numGens+1):
                comboBoxItems.append("Generation " + str(i))

            self.form.selectGenBox.clear()
            self.form.selectGenBox.addItems(comboBoxItems)
        else:
            self.form.viewGenButton.setEnabled(False)
            self.form.selectGenBox.setEnabled(False)
            self.form.nextGen.setEnabled(False)
            self.form.previousGen.setEnabled(False)
            self.form.selectGenBox.clear()

    def updateParametersTable(self):
        paramNames = self.doc.Generate.ParametersName
        parameterValues = self.doc.Generate.GeneratedParameters
        if parameterValues == None:
            paramNames = [""]
            parameterValues = []
        # Insert generation number column into table

        paramNames.insert(0, "Gen")
        table = []
        for i in range(1, len(parameterValues)+1):
            table.append([i]+list(parameterValues[i-1]))

        tableModel = Common.GenTableModel(
            self.form, table, paramNames)
        tableModel.layoutChanged.emit()
        self.form.parametersTable.setModel(tableModel)
        self.form.parametersTable.horizontalHeader().setResizeMode(
            PySide.QtWidgets.QHeaderView.ResizeToContents)
        self.form.parametersTable.clicked.connect(partial(
            Common.showGen, self.form.parametersTable, self.doc))
        self.form.parametersTable.setMinimumHeight(22+len(parameterValues)*30)
        self.form.parametersTable.setMaximumHeight(22+len(parameterValues)*30)

    def accept(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        doc.Document.recompute()
        # closes the gen file If a generated file opened to check before
        Common.showGen("close", self.doc, None)

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        # Common.showGen("close", self.doc, None)   # closes the gen file If a generated file opened to check before

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
        icon_path = os.path.join(
            FreeCAD.getUserAppDataDir() + 'Mod/FEMbyGEN/fembygen/icons/Generate.svg')
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
