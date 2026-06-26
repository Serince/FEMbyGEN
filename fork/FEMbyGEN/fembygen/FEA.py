import FreeCAD
import FreeCADGui
import FemGui
import os
from fembygen import Common
import shutil
import glob
from femtools import ccxtools
import numpy as np
import functools
import traceback

# HATA ÖNLEYİCİ  PySide ve PySide2 Uyumsuzluğunu Çöz
try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:
    import PySide
    from PySide import QtCore, QtGui
    QtWidgets = QtGui


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
    def GetResources(self):
        return {'Pixmap': os.path.join(FreeCAD.getUserAppDataDir() + 'Mod/FEMbyGEN/fembygen/icons/FEA.svg'),
                'Accel': "Shift+A",
                'MenuText': "FEA Generations",
                'ToolTip': "Perform FEA/CFD on generated parts"}

    def Activated(self):
        obj = makeFEA()
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
        return FreeCAD.ActiveDocument is not None


class FEAPanel:
    def __init__(self, object):
        self.obj = object
        self.doc = object.Object.Document
        guiPath = FreeCAD.getUserAppDataDir() + "Mod/FEMbyGEN/fembygen/ui/PerformFEA.ui"
        self.form = FreeCADGui.PySideUic.loadUi(guiPath)
        self.workingDir = '/'.join(
            object.Object.Document.FileName.split('/')[0:-1])
        self.numGenerations = Common.checkGenerations(self.workingDir)
        _, numAnalysed, _ = Common.searchAnalysed(self.doc)

        self.form.genCountLabel.setText(
            "There are " + str(self.numGenerations) + " generations")
        self.form.analysedCountLabel.setText(
            str(numAnalysed) + " successful analyses")
        self.updateAnalysisTable()

        self.form.startFEAButton.clicked.connect(self.FEAGenerations)
        self.form.deleteAnalyses.clicked.connect(self.deleteGenerations)

    def deleteGenerations(self):
        FreeCAD.Console.PrintMessage("Deleting analyses...\n")
        numGens = Common.checkGenerations(self.workingDir)
        for i in range(1, numGens+1):
            lcases = glob.glob(self.workingDir + f"/Gen{i}/loadCase*")
            for j in lcases:
                try:
                    shutil.rmtree(j)
                    FreeCAD.Console.PrintMessage(f"{j} deleted\n")
                except FileNotFoundError:
                    pass

        try:
            Common.purge_results(self.doc)
        except:
            pass
        self.doc.FEA.Status = []
        self.doc.FEA.NumberOfAnalysis = 0
        self.doc.FEA.NumberOfLoadCase = 0
        self.updateAnalysisTable()

    def FEAGenerations(self):
        FreeCAD.Console.PrintMessage("Analysis starting...\n")
        
        # ---  PROXY KOPMASINI ENGELLE ---
        # Dosyalar açılmadan ÖNCE modülü yüklüyoruz ki objeler 'NoneType' olmasın
        try:
            import CfdOF
            from CfdOF import CfdTools, CfdConsoleProcess
            from CfdOF.Solve import CfdCaseWriterFoam, CfdRunnableFoam
        except ImportError:
            pass

        for i in range(self.numGenerations):
            partName = f"Gen{i+1}"
            directory = self.workingDir + f"/Gen{i+1}"
            filePath = directory + f"/{partName}.FCStd"
            
            # --- GİZLİ (HIDDEN) AÇMAYI İPTAL ET ---
            # CfdOF arayüze ihtiyaç duyar. hidden=True yaparsak çöker.
            try:
                Gen_Doc = FreeCAD.open(filePath) 
            except:
                FreeCAD.Console.PrintError(f"HATA: {partName} acilamadi!\n")
                continue

            FreeCAD.setActiveDocument(partName)

            lc = 0
            is_cfd = False
            for obj in Gen_Doc.Objects:
                try:
                    if obj.TypeId == "Fem::FemAnalysis": 
                        lc += 1
                        FemGui.setActiveAnalysis(obj)
                        analysisfolder = os.path.join(directory, f"loadCase_{lc}")
                        if not os.path.exists(analysisfolder):
                            os.mkdir(analysisfolder)
                        self.performFEA(Gen_Doc, obj, analysisfolder)
                    
                    elif obj.Name.startswith("CfdAnalysis") or (hasattr(obj, "Proxy") and "CfdAnalysis" in type(obj.Proxy).__name__):
                        is_cfd = True
                except:
                    pass

            if is_cfd or hasattr(Gen_Doc, "CfdAnalysis"):
                self.performCFD(Gen_Doc, partName, directory)

            FreeCAD.closeDocument(partName)

            progress = ((i+1)/self.numGenerations) * 100
            self.form.progressBar.setValue(progress)
            QtWidgets.QApplication.processEvents()

        (statuses, numAnalysed, numLoadCase) = Common.searchAnalysed(self.doc)
        self.doc.FEA.Status = statuses
        self.doc.FEA.NumberOfAnalysis = numAnalysed
        self.doc.FEA.NumberOfLoadCase = numLoadCase
        FreeCAD.setActiveDocument(self.doc.Name)
        self.doc.save()
        self.updateAnalysisTable()

    def performCFD(self, doc, name, directory):
        try:
            from CfdOF import CfdTools, CfdConsoleProcess
            from CfdOF.Solve import CfdCaseWriterFoam, CfdRunnableFoam

            FreeCAD.Console.PrintMessage(f"\n--- {name} CFD Motoru Atesleniyor (OpenFOAM) ---\n")

            analysis_obj = None
            solver_obj = None
            
            for obj in doc.Objects:
                if obj.Name.startswith("CfdAnalysis") or (hasattr(obj, "Proxy") and "CfdAnalysis" in type(obj.Proxy).__name__):
                    analysis_obj = obj
                if obj.Name.startswith("CfdSolver") or (hasattr(obj, "Proxy") and "Solver" in type(obj.Proxy).__name__):
                    solver_obj = obj

            if not analysis_obj or not solver_obj:
                FreeCAD.Console.PrintError(f"HATA: {name} icinde CfdAnalysis veya CfdSolver bulunamadi!\n")
                return

            # ------
            # Eğer ana dosyada silinmiş sınır şartlarından kalan 'None' kalıntılar varsa temizle
            if hasattr(analysis_obj, "Group"):
                temiz_grup = []
                for g_obj in analysis_obj.Group:
                    # Obje gerçekten varsa ve bir ismi (Label) varsa gruba dahil et
                    if g_obj is not None and hasattr(g_obj, "Label"):
                        temiz_grup.append(g_obj)
                analysis_obj.Group = temiz_grup
            # ----------------------------------------

            # Eski yolu hafızadan zorla sil
            analysis_obj.OutputPath = directory
            doc.recompute()

            # OpenFOAM dosyalarını yaz
            solver_obj.Proxy.case_writer = CfdCaseWriterFoam.CfdCaseWriterFoam(analysis_obj)
            solver_obj.Proxy.case_writer.writeCase()

            solver_dir = os.path.abspath(os.path.join(CfdTools.getOutputPath(analysis_obj), solver_obj.InputCaseName))

            # Çözücü Komutunu Al ve Çalıştır
            s_run = CfdRunnableFoam.CfdRunnableFoam(analysis_obj, solver_obj)
            cmd_s = s_run.getSolverCmd(solver_dir)
            env = CfdTools.getRunEnvironment()

            if cmd_s:
                s_proc = CfdConsoleProcess.CfdConsoleProcess(stdout_hook=s_run.processOutput)
                s_proc.start(cmd_s, env_vars=env, working_dir=solver_dir)
                s_proc.waitForFinished()
                FreeCAD.Console.PrintMessage(f"--- {name} CFD Analizi Basariyla TAMAMLANDI! ---\n\n")
            else:
                FreeCAD.Console.PrintError(f"HATA: {name} cozucu komutu alinamadi!\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"CFD HATA ({name}): {str(e)}\n")
            traceback.print_exc()

    def performFEA(self, doc, Analysis, Directory):
        doc.recompute()
        try:
            fea=ccxtools.FemToolsCcx(Analysis)
        except:
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
            self.outputs(Directory)
            fea.ccx_run()
            fea.load_results()
        else:
            FreeCAD.Console.PrintError("Houston, we have a problem! {}\n".format(message))

        doc.save()

    def updateAnalysisTable(self):
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
                    white = QtGui.QColor("white")
                    colours[i, 0] = white
                    if value == "Analysed":
                        colours[i, j + 1] = QtGui.QColor(114, 242, 73, 255)
                    elif value == "Not analysed":
                        colours[i, j + 1] = QtGui.QColor(207, 184, 12, 255)
                    elif value == "Failed":
                        colours[i, j + 1] = QtGui.QColor(250, 100, 100, 255)
            table = table.tolist()
            colours = colours.tolist()
        except:
            table = []
            colours = []
            gen = 0
            
        tableModel = Common.GenTableModel(self.form, table, header, colours=colours)
        tableModel.layoutChanged.emit()
        self.form.tableView.setModel(tableModel)
        self.form.tableView.clicked.connect(functools.partial(Common.showGen, self.form.tableView, self.doc))
        
        try:
            self.form.tableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        except AttributeError:
            self.form.tableView.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            
        self.form.tableView.setMinimumHeight(22+gen*30)
        self.form.tableView.setMaximumHeight(22+gen*30)

    def outputs(self, directory):
        name = glob.glob(directory+"/*.inp")
        if not name: return
        with open(name[0], "r") as old:
            text = old.read()
            end_loc = text.find("RF\n")
            outputs = "\n*EL PRINT, ELSET=Eall, TOTALS=YES \nELSE, EVOL, ENER\n"
            newText = text[:end_loc+3] + outputs + text[end_loc+3:]

        with open(name[0], "w") as new:
            new.write(newText)

    def accept(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        doc.Document.recompute()
        Common.showGen("close", self.doc, None)

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()


class ViewProviderFEA:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return os.path.join(FreeCAD.getUserAppDataDir() + 'Mod/FEMbyGEN/fembygen/icons/FEA.svg')

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
        taskd = FEAPanel(vobj)
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        FreeCADGui.Control.closeDialog()
        return

    def __getstate__(self): return None
    def __setstate__(self, state): return None
    def dumps(self): return None
    def loads(self, state): return None


FreeCADGui.addCommand('FEA', FEACommand())