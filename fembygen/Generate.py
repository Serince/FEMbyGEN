import FreeCAD
import FreeCADGui
import Fem
import os.path
import shutil
from fembygen import Common
import numpy as np
import itertools
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
        FreeCAD.ActiveDocument.Generative_Design.addObject(obj)
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
            obj.addProperty("App::PropertyStringList", "Parameters_Name", "Generations",
                            "Generated parameter matrix")
            obj.addProperty("App::PropertyPythonObject", "Generated_Parameters", "Generations",
                            "Generated parameter matrix")
        except:
            pass


class GenerateCommand():
    """Produce part generations"""

    def GetResources(self):
        return {'Pixmap': os.path.join(FreeCAD.getUserAppDataDir() + 'Mod/FEMbyGEN/fembygen/Generate.svg'),  # the name of a svg file available in the resources
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
        guiPath = FreeCAD.getUserAppDataDir() + "Mod/FEMbyGEN/fembygen/Generate.ui"
        self.form = FreeCADGui.PySideUic.loadUi(guiPath)
        self.workingDir = '/'.join(
            object.Object.Document.FileName.split('/')[0:-1])
        
        # Data variables for parameter table

        self.doc = object.Object.Document
        (paramNames, parameterValues) = Common.checkGenParameters(self.doc)
        self.doc.Generate.Parameters_Name = paramNames
        self.doc.Generate.Generated_Parameters = parameterValues
        # Check if any generations have been made already, and up to what number

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
        self.updateParametersTable()

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
            FreeCAD.Console.PrintError(
                f"Please delete earlier generations: Gen{i+1} already exist in the folder\n")
            self.form.progressBar.setValue(100)
            self.form.progressBar.setStyleSheet(
                "QProgressBar {text-align: center; } QProgressBar::chunk {background-color: #F44336;}")
            self.form.readyLabel.setText("Delete earlier generations")
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
        for l in doc.Generative_Design.Group:
            if l.Name == "Parameters":
                pass
            else:
                doc.removeObject(l.Name)
        doc.removeObject(doc.Generative_Design.Name)
        doc.recompute()

        # getting first analysis meshing object and copy it other loadcases
        for mesh in doc.Objects:
            if mesh.TypeId == 'Fem::FemMeshObjectPython':
                self.meshing(mesh, "Gmsh")
                break
            elif mesh.TypeId == 'Fem::FemMeshShapeNetgenObject':
                self.meshing(mesh, "Netgen")
                break

        # define analysis working directory
        lc = 0
        for obj in doc.Objects:
            try:
                if obj.TypeId == "Fem::FemAnalysis":  # to choose analysis objects
                    lc += 1
                    # copying first loadcase mesh to other loadcases
                    if lc > 1:
                        for femobj in obj.Group:
                            # delete old mesh of loadcase
                            if femobj.TypeId == 'Fem::FemMeshObjectPython' or femobj.TypeId == 'Fem::FemMeshShapeNetgenObject':
                                doc.removeObject(femobj.Name)

                            # setting working directory of loadcase to subfolder of generation folder
                            elif femobj.TypeId == 'Fem::FemSolverObjectPython':
                                femobj.WorkingDir = os.path.join(directory+f"loadCase{lc}")
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
        selectedModule = self.form.selectModuleBox.currentText()
        try:
             numgenerations = self.design(selectedModule,param)
             func = partial(self.copy_mesh, numgenerations)
             iterationnumber = len(numgenerations)
             p = mp.Pool(cpu_count()-1)
             for i, _ in enumerate(p.imap_unordered(func, range(iterationnumber))):
                 # Update progress bar
                 progress = ((i+1)/iterationnumber) * 100
                 self.form.progressBar.setValue(progress)
             p.close()
             p.join()

             # ReActivate document again once finished
             FreeCAD.setActiveDocument(master.Name)
             master.Generate.Generated_Parameters = numgenerations
             master.Generate.Parameters_Name = paramNames
             self.updateParametersTable()

             # Update number of generations produced in window
             numGens = Common.checkGenerations(self.workingDir)
             self.form.numGensLabel.setText(str(numGens) + " generations produced")
             #self.form.readyLabel.setText("Finished")
             self.resetViewControls(numGens)
             self.updateParametersTable()
             master.save()  # too store generated values in generate object
             FreeCAD.Console.PrintMessage("Generation done successfully!\n")
        
        
        except TypeError:
            print("Please install pyDOE2 module")

    def deleteGenerations(self):
        FreeCAD.Console.PrintMessage("Deleting...\n")
        numGens = Common.checkGenerations(self.workingDir)
        for i in range(1, numGens+1):
            # Delete analysis directories
            try:
                shutil.rmtree(self.workingDir + f"/Gen{i}/")
                FreeCAD.Console.PrintMessage(self.workingDir + f"/Gen{i}/ deleted\n")
            except FileNotFoundError:
                FreeCAD.Console.PrintError("INFO: Generation " + str(i) +
                                           " analysis data not found")
                pass
            except:
                FreeCAD.Console.PrintError(
                    "Error while trying to delete analysis folder for generation " + str(i))

        # Delete if earlier generative objects exist
        try:
            for l in self.doc.Generative_Design.Group:
                if l.Name == "Parameters" or l.Name == "Generate":
                    pass
                elif l.Name == "Results":
                    Common.purge_results(self.doc)
                else:
                    self.doc.removeObject(l.Name)
        except:
            pass

        self.doc.Generate.Generated_Parameters = None
        # refreshing the table
        self.resetViewControls(numGens)
        self.updateParametersTable()
        FreeCAD.setActiveDocument(self.doc.Name)

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
        paramNames, parameterValues = Common.checkGenParameters(self.doc)
        # Insert generation number column into table

        paramNames.insert(0, "Gen")
        table = []
        for i in range(1, len(parameterValues)+1):
            table.append([i]+list(parameterValues[i-1]))

        tableModel = Common.GenTableModel(
            self.form, table, paramNames)
        tableModel.layoutChanged.emit()
        self.form.parametersTable.setModel(tableModel)
        self.form.parametersTable.horizontalHeader().setResizeMode(PySide.QtGui.QHeaderView.ResizeToContents)
        self.form.parametersTable.clicked.connect(partial(
            Common.showGen, self.form.parametersTable, self.doc))
        self.form.parametersTable.setMinimumHeight(22+len(parameterValues)*30)
        self.form.parametersTable.setMaximumHeight(22+len(parameterValues)*30)

    def accept(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        doc.Document.recompute()
        Common.showGen("close", self.doc, None)   # closes the gen file If a generated file opened to check before

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        # Common.showGen("close", self.doc, None)   # closes the gen file If a generated file opened to check before
    
    def design(self,method,parameters):
        try:
            from fembygen import Design
            if method == "Plackett Burman Design":
                return Design.designpb(parameters)
            elif method == "Box Behnken Design":
                return Design.designboxBen(parameters)
            elif method == "Full Factorial Design":
                return Design.fullfact2(parameters)
            elif method == "Central Composite Design":
                return Design.designcentalcom(parameters) 
        except ModuleNotFoundError:
            pass


class ViewProviderGen:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(FreeCAD.getUserAppDataDir() + 'Mod/FEMbyGEN/fembygen/Generate.svg')
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
