import FreeCAD
import FreeCADGui
import Fem
import os.path
import shutil
from fembygen import Common
import numpy as np
import multiprocessing.dummy as mp
from multiprocessing import cpu_count
from functools import partial
import subprocess # otomasyon kütüphanesi eklendi

# PY-SIDE UYUMSUZLUK COZUCU arayüzün çökmesini engelliyor
try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide import QtCore, QtGui
    QtWidgets = QtGui

LOCATION = os.path.normpath('Mod/FEMbyGEN/fembygen')

class Generate:
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "Generate"
        self.initProperties(obj)

    def initProperties(self, obj):
        try:
            obj.addProperty("App::PropertyEnumeration", "GenerationMethod", "Base", "Generation Method")
            obj.GenerationMethod = ["Full Factorial Design", "Taguchi Optimization Design",
                                    "Plackett Burman Design", "Box Behnken Design",
                                    "Latin Hyper Cube Design", "Central Composite Design"]
            obj.addProperty("App::PropertyStringList", "ParametersName", "Base", "Generated parameter matrix")
            obj.addProperty("App::PropertyPythonObject", "GeneratedParameters", "Base", "Generated parameter matrix")
            obj.addProperty("App::PropertyInteger", "NumberOfCPU", "Base", "Number of CPU's to use ")
            obj.NumberOfCPU = cpu_count()-1
        except NameError:
            pass

class GenerateCommand():
    def GetResources(self):
        return {'Pixmap': os.path.join(FreeCAD.getUserAppDataDir(), LOCATION, 'icons/Generate.svg'),
                'Accel': "Shift+G", 
                'MenuText': "Generate",
                'ToolTip': "Produce part generations"}

    def Activated(self):
        group, obj = Common.addToDocumentObjectGroup('Part::FeaturePython', 'Generate')
        Generate(obj)
        if FreeCAD.GuiUp:
            ViewProviderGen(obj.ViewObject)    
        FreeCADGui.ActiveDocument.setEdit(obj.ViewObject.Object.Name)   
        return

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

class GeneratePanel():
    def __init__(self, object):
        self.obj = object
        guiPath = os.path.join(FreeCAD.getUserAppDataDir(), LOCATION, 'ui/Generate.ui')
        self.form = FreeCADGui.PySideUic.loadUi(guiPath)

        # Eski surum QtGui yerine QtWidgets kullanilmalidir.
        self.radio_layout = QtWidgets.QHBoxLayout()
        self.radio_group = QtWidgets.QButtonGroup()
        
        self.radio_fem = QtWidgets.QRadioButton("FEM Mesh (Varsayilan)")
        self.radio_fem.setChecked(True) 
        
        self.radio_cfd = QtWidgets.QRadioButton("CFD Mesh")
        
        self.radio_group.addButton(self.radio_fem)
        self.radio_group.addButton(self.radio_cfd)
        
        self.radio_layout.addWidget(self.radio_fem)
        self.radio_layout.addWidget(self.radio_cfd)
        
        try:
            if self.form.layout() is not None:
                try:
                    self.form.layout().insertLayout(1, self.radio_layout)
                except AttributeError:
                    self.form.layout().addLayout(self.radio_layout)
            else:
                layout = QtWidgets.QVBoxLayout(self.form)
                layout.addLayout(self.radio_layout)
        except:
            pass

        self.doc = object.Object.Document
        self.workingDir = os.path.dirname(os.path.normpath(self.doc.FileName))
        Common.setWorkspace(self.doc, self.workingDir)

        index = self.form.selectDesign.findText(self.doc.Generate.GenerationMethod, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.form.selectDesign.setCurrentIndex(index)

        self.resetViewControls()
        self.updateParametersTable()

        self.form.more.setIcon(QtGui.QIcon(':/icons/Std_DlgParameter.svg'))
        self.form.deleteGensButton.setIcon(QtGui.QIcon(':/icons/edit-delete.svg'))

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
                                              "The number of samples to generate for each factor")
                self.doc.Generate.addProperty("App::PropertyEnumeration", "Criterion", "Latin Hyper Cube",
                                              "Criterion")
                self.doc.Generate.Criterion = ["center", "maxmin","centermaximin","correlation","lhsmu"]
                self.doc.Generate.addProperty("App::PropertyInteger", "Iterations", "Latin Hyper Cube",
                                              "The number of iterations in the maximin and correlations algorithms.")
                self.doc.Generate.addProperty("App::PropertyInteger", "RandomState", "Latin Hyper Cube",
                                              "Random state (or seed-number) which controls the seed and random draws")
                self.doc.Generate.addProperty("App::PropertyIntegerList", "CorrelationMatrix", "Latin Hyper Cube",
                                              "Enforce correlation between factors")
            except:
                pass
            settings.show()
            settings.save.clicked.connect(save)

    def meshing(self, mesh, type):
        if type == "Netgen":
            mesh.FemMesh = Fem.FemMesh()  
            mesh.recompute()
        elif type == "Gmsh":
            from femmesh.gmshtools import GmshTools as gt
            mesh.FemMesh = Fem.FemMesh()  
            gmsh_mesh = gt(mesh)
            gmsh_mesh.create_mesh()

    def copy_mesh(self, numgenerations, i):
        docPath = os.path.normpath(self.doc.FileName)
        name = f"Gen{i+1}"
        directory = os.path.join(self.workingDir, name)
        filePath = os.path.join(directory, name+".FCStd")
        
        try: os.mkdir(directory)
        except: pass 
            
        try: FreeCAD.closeDocument(name)
        except: pass

        shutil.copy(docPath, filePath)
        shutil.copy(filePath, filePath+".backup")

        doc = FreeCAD.open(filePath)
        if not doc:
            FreeCAD.Console.PrintError(f"{name} acilamadi!\n")
            return
            
        FreeCAD.setActiveDocument(doc.Name)

        try:
            doc.Parameters.set('C1', 'Value')
            for k in range(self.inumber[0]):
                doc.Parameters.set(f'C{k+2}', f'{numgenerations[i][k]}')
                doc.Parameters.clear(f'D1:D{k+2}')
                doc.Parameters.clear(f'E1:E{k+2}')

            doc.recompute()
            FreeCADGui.updateGui() 
            doc.recompute() 

            is_cfd = self.radio_cfd.isChecked()

            if not is_cfd:
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
                        if obj.TypeId == "Fem::FemAnalysis":  
                            lc += 1
                            if lc > 1:
                                for femobj in obj.Group:
                                    if femobj.TypeId in ['Fem::FemMeshObjectPython', 'Fem::FemMeshShapeNetgenObject']:
                                        doc.removeObject(femobj.Name)
                                obj.addObject(doc.copyObject(mesh, False))
                    except: pass
            else:
                from CfdOF.Mesh import CfdMeshTools
                
                # --- ESKI YOLU HAFIZADAN SILEN KOD---
                for tmp_obj in doc.Objects:
                    if hasattr(tmp_obj, "OutputPath"):
                        tmp_obj.OutputPath = directory
                # --------------------------------------
                
                mesh_bulundu = False
                for obj in doc.Objects:
                    if obj.Name == 'Cut_Mesh' or obj.Label == 'Cut_Mesh':
                        mesh_bulundu = True
                        try:
                            FreeCAD.Console.PrintMessage(f"{name} icin MESH HAZIRLANIYOR...\n")
                            cart_mesh = CfdMeshTools.CfdMeshTools(obj)
                            cart_mesh.mesh_case_dir = os.path.join(directory, "meshCase")
                            
                            if not os.path.exists(cart_mesh.mesh_case_dir): 
                                os.makedirs(cart_mesh.mesh_case_dir)
                                
                            # 1. DOSYALARI OLUSTUR 
                            cart_mesh.writeMesh()
                            
                            # 2. OTOMATIK CALISTIRICI 
                            bat_file = os.path.join(cart_mesh.mesh_case_dir, "Allmesh.bat")
                            if os.path.exists(bat_file):
                                FreeCAD.Console.PrintMessage(f"> {name} Mesh Motoru calistiriliyor, lutfen bekleyin...\n")
                                subprocess.run(bat_file, cwd=cart_mesh.mesh_case_dir, shell=True, check=True)
                                FreeCAD.Console.PrintMessage(f"> {name} Mesh basariyla TAMAMLANDI!\n")
                            else:
                                FreeCAD.Console.PrintError(f"HATA: {name} icinde Allmesh.bat olusamadi!\n")
                                
                        except Exception as mesh_err:
                            FreeCAD.Console.PrintError(f"{name} MESH ATILAMADI: {str(mesh_err)}\n")
                        break
                
                if not mesh_bulundu:
                    FreeCAD.Console.PrintError(f"HATA: {name} icinde 'Cut_Mesh' objesi bulunamadi!\n")
                        
            doc.recompute()
            doc.save()
        finally:
            FreeCAD.closeDocument(doc.Name)

    def generateParts(self):
        master = self.doc
        master.save()  

        paramNames = []
        numberofgen = []
        self.detection = []
        self.inumber = []

        try:
            for i in range(99):
                self.detection.append(master.Parameters.get(f'C{i+2}'))
        except:
            self.inumber.append(i)

        param = []

        for i in range(self.inumber[0]):
            paramNames.append(master.Parameters.get(f'B{i+2}'))
            mins = float(master.Parameters.get(f'C{i+2}'))
            maxs = float(master.Parameters.get(f'D{i+2}'))
            numberofgen = int(master.Parameters.get(f'E{i+2}'))
            param.append(np.linspace(mins, maxs, numberofgen))

        selectedModule = self.form.selectDesign.currentText()
        self.doc.Generate.GenerationMethod = selectedModule

        numgenerations = self.design(selectedModule, param, numberofgen)
        try:
            iterationnumber = len(numgenerations)

            if Common.checkGenerations() > 0:
                self.deleteGenerations()

            progress_bar = FreeCAD.Base.ProgressIndicator()    
            progress_bar.start('Generate parts ...', iterationnumber)
            self.form.progressBar.setValue(0)

            for i in range(iterationnumber):
                try:
                    self.copy_mesh(numgenerations,i)
                except Exception as ex:
                    FreeCAD.Console.PrintWarning(f"Gen{i+1} atlandi: {str(ex)}\n")
                    
                progress_bar.next()
                progress = ((i+1)/iterationnumber) * 100
                self.form.progressBar.setValue(progress)
                QtWidgets.QApplication.processEvents() 
       
            FreeCAD.setActiveDocument(master.Name)
            master.Generate.GeneratedParameters = numgenerations
            master.Generate.ParametersName = paramNames

            self.resetViewControls()
            self.updateParametersTable()
            progress_bar.stop()

            master.save()  
            FreeCAD.Console.PrintMessage("Generation done successfully!\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"Hata Olustu: {str(e)}\n")
        
    def deleteGenerations(self):
        qm = QtWidgets.QMessageBox
        ret = qm.question(None, '', "Are you sure to delete all the earlier generation files?", qm.Yes | qm.No)
        if ret == qm.No:
            FreeCAD.Console.PrintMessage("Nothing Deleted\n")
        else:
            Common.closeGen(0)    
            numGens = Common.checkGenerations(self.workingDir)
            for i in range(1, numGens+1):
                directory = os.path.join(self.workingDir, f"Gen{i}")
                try: shutil.rmtree(directory)
                except: pass
            for l in self.doc.GenerativeDesign.Group:
                if l.Name == "Parameters" or l.Name == "Generate": pass
                elif l.Name == "Results": Common.purge_results(self.doc)
                else: self.doc.removeObject(l.Name)

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
        
        try:
            tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        except AttributeError:
            tableWidget.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        for col in range(tableWidget.columnCount()):
            for row in range(tableWidget.rowCount()):
                item = QtWidgets.QTableWidgetItem(str(parameterValues[row][col]))
                tableWidget.setItem(row, col, item)
        if Common.checkGenerations() > 0:
            tableWidget.itemClicked.connect(
                lambda item: self.form.selectGenBox.setValue(item.row()+1))

    def accept(self):
        if not self.form.checkBoxKeep.isChecked(): Common.closeGen(0)    
        guiDoc = FreeCADGui.getDocument(self.doc)
        guiDoc.resetEdit()    
        self.doc.recompute()

    def reject(self):
        Common.closeGen(0)    
        guiDoc = FreeCADGui.getDocument(self.doc)
        guiDoc.resetEdit()    

    def design(self, method, parameters, numberofgen):
        from fembygen.design import Design, Taguchi
        if method == "Full Factorial Design": return Design.fullfact(parameters)
        elif method == "Plackett Burman Design": return Design.designpb(parameters)
        elif method == "Box Behnken Design":
            try: center = self.doc.Generate.CenterPoints
            except: center = None
            return Design.designboxBen(parameters, center)
        elif method == "Central Composite Design":
            try:
                center = self.doc.Generate.Center; face = self.doc.Generate.Face; alpha = self.doc.Generate.Alpha
            except:
                center = (4, 4); alpha = "orthogonal"; face = "circumscribed"
            return Design.designcentalcom(parameters, center, alpha, face)
        elif method == "Latin Hyper Cube Design":
            try:
                samples = self.doc.Generate.Samples; criterion = self.doc.Generate.Criterion
                iterations = self.doc.Generate.Iterations; random_state = self.doc.Generate.RandomState
                correlation_matrix = self.doc.Generate.CorrelationMatrix
            except:
                samples = None; criterion = None; iterations = None; random_state = None; correlation_matrix = None
            return Design.designlhc(parameters,samples,criterion, iterations, random_state, correlation_matrix)
        elif method == "Taguchi Optimization Design":
            result = Taguchi.Taguchipy(parameters, numberofgen)
            res = result.selection()
            if res is not None: return list(res)

class ViewProviderGen:
    def __init__(self, vobj): vobj.Proxy = self
    def getIcon(self): return os.path.join(FreeCAD.getUserAppDataDir(), LOCATION, 'icons/Generate.svg')
    def attach(self, vobj): self.ViewObject = vobj; self.Object = vobj.Object
    def updateData(self, obj, prop): return
    def onChanged(self, vobj, prop): return
    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        doc.setEdit(vobj.Object.Name)
        return True
    def setEdit(self, vobj, mode):
        taskd = GeneratePanel(vobj)
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

FreeCADGui.addCommand("Generate", GenerateCommand())