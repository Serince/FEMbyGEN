import FreeCAD
import FreeCADGui
import FemGui
import os
from fembygen import Common
import shutil
import os
import PySide
import glob
from femtools import ccxtools
import numpy as np
import functools

translate = FreeCAD.Qt.translate
def QT_TRANSLATE_NOOP(context, text):
    return text
import FreeCADGui
import os
FreeCADGui.addLanguagePath(os.path.join(FreeCAD.getUserAppDataDir(),"\Mod\FEMbyGEN\fembygen\translations"))
FreeCADGui.updateLocale()

def makeFEA():
    try:
        obj = FreeCAD.ActiveDocument.FEA
        obj.isValid()
    except:
        try:
            obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "FEA")
            FreeCAD.ActiveDocument.GenerativeDesign.addObject(obj)
        except:
            return None
    FEA(obj)
    if FreeCAD.GuiUp:
        ViewProviderFEA(obj.ViewObject)
    return obj


class FEA:
    """ Finite Element Analysis """

    def __init__(self, obj):

        obj.Proxy = self
        self.Type = "FEA"
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


class FEACommand():
    """Perform FEA on generated parts"""

    def GetResources(self):
        return {'Pixmap': os.path.join(FreeCAD.getUserAppDataDir() + 'Mod/FEMbyGEN/fembygen/icons/FEA.svg'),  # the name of a svg file available in the resources
                'Accel': "Shift+A",  # a default shortcut (optional)
                'MenuText': QT_TRANSLATE_NOOP("CommandName","FEA Generations"),
                'ToolTip': QT_TRANSLATE_NOOP("CommandName","Perform FEA on generated parts")}

    def Activated(self):
        obj = makeFEA()
        try:
            doc = FreeCADGui.getDocument(obj.ViewObject.Object.Document)
            if not doc.getInEdit():
                doc.setEdit(obj.ViewObject.Object.Name)
            else:
                FreeCAD.Console.PrintError(translate("FEMbyGEN",'Existing task dialog already open\n'))
            return
        except:
            FreeCAD.Console.PrintError(translate("FEMbyGEN",'Make sure that you are working on the master file. Close the generated file\n'))

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return FreeCAD.ActiveDocument is not None


class FEAPanel:
    def __init__(self, object):
        # Creating tree view object
        self.obj = object
        self.doc = object.Object.Document
        # this will create a Qt widget from our ui file
        guiPath = FreeCAD.getUserAppDataDir() + "Mod/FEMbyGEN/fembygen/ui/PerformFEA.ui"
        self.form = FreeCADGui.PySideUic.loadUi(guiPath)
        self.workingDir = '/'.join(
            object.Object.Document.FileName.split('/')[0:-1])
        self.numGenerations = Common.checkGenerations(self.workingDir)
        _, numAnalysed, _ = Common.searchAnalysed(self.doc)

        # Update status labels and table
        self.form.genCountLabel.setText(
            "There are " + str(self.numGenerations) + " generations")
        self.form.analysedCountLabel.setText(
            str(numAnalysed) + " successful analyses")
        self.updateAnalysisTable()

        # Link callback procedures
        self.form.startFEAButton.clicked.connect(self.FEAGenerations)
        self.form.deleteAnalyses.clicked.connect(self.deleteGenerations)

    def deleteGenerations(self):
        FreeCAD.Console.PrintMessage(translate("FEMbyGEN","Deleting...\n"))
        numGens = Common.checkGenerations(self.workingDir)
        for i in range(1, numGens+1):
            lcases = glob.glob(self.workingDir + f"/Gen{i}/loadCase*")
            for j in lcases:
                try:
                    shutil.rmtree(j)
                    FreeCAD.Console.PrintMessage(translate("FEMbyGEN",f"{j} deleted\n"))

                except FileNotFoundError:
                    FreeCAD.Console.PrintError(translate("FEMbyGEN",
                        f"INFO: Generation {j} analysis data not found\n"))
                # Delete if earlier generative objects exist

        try:  # If already results imported, try to delete those
            Common.purge_results(self.doc)
        except:
            pass
        self.doc.FEA.Status = []
        self.doc.FEA.NumberOfAnalysis = 0
        self.doc.FEA.NumberOfLoadCase = 0
        self.updateAnalysisTable()

    def FEAGenerations(self):
        FreeCAD.Console.PrintMessage(translate("FEMbyGEN","Analysis starting\n"))
        for i in range(self.numGenerations):
            # Open generated part
            partName = f"Gen{i+1}"
            filePath = self.workingDir + f"/Gen{i+1}/Gen{i+1}.FCStd"
            Gen_Doc = FreeCAD.open(filePath, hidden=True)
            FreeCAD.setActiveDocument(partName)

            # get the loadcases from the generation file
            lc = 0
            for obj in Gen_Doc.Objects:
                try:
                    if obj.TypeId == "Fem::FemAnalysis":  # to choose analysis objects
                        lc += 1
                        FemGui.setActiveAnalysis(obj)
                        analysisfolder = os.path.join(
                            self.workingDir + f"/Gen{i+1}/loadCase_{lc}")
                        os.mkdir(analysisfolder)
                    # Run FEA solver on generation
                        self.performFEA(Gen_Doc, obj, analysisfolder)
                except:
                    # It counts for deleted objects and gives error.
                    pass

            # Close generated part
            FreeCAD.closeDocument(partName)

            # Update progress bar
            progress = ((i+1)/self.numGenerations) * 100
            self.form.progressBar.setValue(progress)

        (statuses, numAnalysed, numLoadCase) = Common.searchAnalysed(self.doc)
        self.doc.FEA.Status = statuses
        self.doc.FEA.NumberOfAnalysis = numAnalysed
        self.doc.FEA.NumberOfLoadCase = numLoadCase
        FreeCAD.setActiveDocument(self.doc.Name)
        self.doc.save()
        self.updateAnalysisTable()

    def updateAnalysisTable(self):
        # Make a header and table with one more column, because otherwise the table object will split each character
        # into its own cell
        stats, numAnalysed = Common.checkAnalyses(self.doc)
        header = ["Gen"]
        try:
            gen, lc = len(stats), len(stats[0])
            for i in range(lc):
                header.append(f"LoadCase {i+1}")

            index = np.array(range(1, gen+1))[..., None]
            table = np.hstack((index, stats))

            colours = np.empty((gen, lc+1), dtype=np.dtype("object"))

            for i, row in enumerate(stats):
                for j, value in enumerate(row):
                    white = PySide.QtGui.QColor("white")
                    colours[i, 0] = white
                    if value == "Analysed":
                        # green
                        colours[i, j +
                                1] = PySide.QtGui.QColor(114, 242, 73, 255)
                    elif value == "Not analysed":
                        # yellow
                        colours[i, j +
                                1] = PySide.QtGui.QColor(207, 184, 12, 255)
                    elif value == "Failed":
                        # red/pink
                        colours[i, j +
                                1] = PySide.QtGui.QColor(250, 100, 100, 255)
            table = table.tolist()
            colours = colours.tolist()
        except:
            table = []
            colours = []
            gen = 0
        tableModel = Common.GenTableModel(
            self.form, table, header, colours=colours)
        tableModel.layoutChanged.emit()
        self.form.tableView.setModel(tableModel)
        self.form.tableView.clicked.connect(functools.partial(
            Common.showGen, self.form.tableView, self.doc))
        self.form.tableView.horizontalHeader().setResizeMode(
            PySide.QtGui.QHeaderView.ResizeToContents)
        self.form.tableView.setMinimumHeight(22+gen*30)
        self.form.tableView.setMaximumHeight(22+gen*30)

    def outputs(self, directory):
        """ It modifies the inp file to get extra outputs
        such as element volumes and elements internal energies"""

        name = glob.glob(directory+"/*.inp")

        with open(name[0], "r") as old:
            text = old.read()
            end_loc = text.find("RF\n")
            outputs = "\n*EL PRINT, ELSET=Eall, TOTALS=YES \nELSE, EVOL, ENER\n"
            newText = text[:end_loc+3] + outputs + text[end_loc+3:]

        with open(name[0], "w") as new:
            new.write(newText)

    def performFEA(self, doc, Analysis, Directory):
        doc.recompute()
        # run the analysis step by step

        # , solver=doc.SolverCcxTools)
        try:
            fea=ccxtools.FemToolsCcx(Analysis)
        except:
            print(translate("FEMbyGEN","adding"))
            import ObjectsFem
            Analysis.addObject(ObjectsFem.makeSolverCalculixCcxTools(doc))
            fea=ccxtools.FemToolsCcx(Analysis)

        fea.setup_working_dir(Directory)
        fea.update_objects()
        fea.setup_ccx()
        message = fea.check_prerequisites()
        if not message:
            fea.purge_results()
            fea.write_inp_file()
            self.outputs(Directory)  # to get extra information at result file
            fea.ccx_run()
            fea.load_results()
        else:
            FreeCAD.Console.PrintError(translate("FEMbyGEN",
                "Houston, we have a problem! {}\n".format(message)))  # in report view

        # save FEA results
        doc.save()

    def accept(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        doc.Document.recompute()
        # closes the gen file If a generated file opened to check before
        Common.showGen("close", self.doc, None)

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        # closes the gen file If a generated file opened to check before
        # Common.showGen("close", self.doc, None)


class ViewProviderFEA:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(
            FreeCAD.getUserAppDataDir() + 'Mod/FEMbyGEN/fembygen/icons/FEA.svg')
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
        taskd = FEAPanel(vobj)
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


FreeCADGui.addCommand('FEA', FEACommand())
