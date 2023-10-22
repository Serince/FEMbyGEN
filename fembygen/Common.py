import FreeCAD
import PySide
import os.path
import numpy as np
import operator
import glob
import Fem
import FreeCADGui as Gui


def checkGenerations(workingDir):
    numGens = 1
    # workingDir = '/'.join(master.FileName.split('/')[0:-1])
    while os.path.isdir(workingDir + "/Gen" + str(numGens)):
        numGens += 1
    return numGens-1


def purge_results(doc):
    from femtools.femutils import is_of_type
    analysis = doc.Results
    for m in analysis.Group:
        if m.isDerivedFrom("Fem::FemResultObject"):
            if m.Mesh and is_of_type(m.Mesh, "Fem::MeshResult"):
                analysis.Document.removeObject(m.Mesh.Name)
            analysis.Document.removeObject(m.Name)
    analysis.Document.recompute()
    # result mesh
    for m in analysis.Group:
        if is_of_type(m, "Fem::MeshResult"):
            analysis.Document.removeObject(m.Name)
    analysis.Document.recompute()
    # dat text object
    for m in analysis.Group:
        if is_of_type(m, "App::TextDocument") and m.Name.startswith("ccx_dat_file"):
            analysis.Document.removeObject(m.Name)
    analysis.Document.recompute()
    doc.removeObject("Results")


def searchAnalysed(master):
    numAnalysed = 0
    statuses = []
    workingDir = '/'.join(master.FileName.split('/')[0:-1])
    numGenerations = checkGenerations(workingDir)
    for i in range(1, numGenerations+1):
        # Checking the loadcases in generated file
        lc = 0
        lcStatus = []
        for obj in master.Objects:
            if obj.TypeId == "Fem::FemAnalysis":  # to choose analysis objects
                lc += 1
                analysisfolder = os.path.join(
                    workingDir + f"/Gen{i}/loadCase_{lc}/")
                print("analysisfolder", analysisfolder)
                try:
                    # This returns an exception if analysis failed for this .frd file, because there is no results data
                    FRDPath = glob.glob(analysisfolder + "*.frd")[0]
                    print("frdpadh", FRDPath)
                    try:
                        with open(FRDPath, "r") as file:
                            file.readline().decode().strip()
                    except:
                        status = "Failed"
                except:
                    status = "Not analysed"
                else:
                    status = "Analysed"
                    numAnalysed += 1
                try:
                    lcStatus.append(status)
                except:
                    FreeCAD.Console.PrintError("Analysis not found.\n")
        statuses.append(lcStatus)
    return (statuses, numAnalysed, lc)


def checkAnalyses(master):
    statuses = master.FEA.Status
    numAnalysed = master.FEA.NumberOfAnalysis

    return (statuses, numAnalysed)



def showGen(table, master, item):
    global old
    old = FreeCAD.ActiveDocument.Name
    if old[:3] == "Gen" and old[3:4].isnumeric():
        FreeCAD.closeDocument(old)
    if table == "close":
        FreeCAD.setActiveDocument(master.Name)
        return

    index = table.model().index(item.row(), 0)
    index = int(float(index.data()))
    # Open the generation
    workingDir = '/'.join(master.FileName.split('/')[0:-1])
    docPath = workingDir + \
        f"/Gen{index}/Gen{index}.FCStd"
    docName = f"Gen{index}"
    FreeCAD.open(docPath)
    FreeCAD.setActiveDocument(docName)



def get_results_fc(doc, case):
    import os
    import femmesh.femmesh2mesh
    import Mesh
    file_path = doc.Topology.path
    file = os.path.join(file_path, "topology_iterations", "file" + str(case).zfill(3))
    result_state0 = f"{file}_state0"
    result_state1 = f"{file}_state1"
    # Hide all previous mesh objects
    meshes = doc.findObjects('Mesh::Feature') 
    for mesh in meshes:
        mesh.Visibility = False
    for obj in doc.Topology.Group:
        obj.Visibility = False
    # If the file is already imported, open it
    if doc.getObject(os.path.split(file)[1]):
        doc.getObject(os.path.split(file)[1]).Visibility = True
    else:
        state = FreeCAD.ActiveDocument.addObject(
            "App::DocumentObjectGroupPython", os.path.split(file)[1])
        Fem.insert(f"{result_state0}.inp", doc.Name)
        Fem.insert(f"{result_state1}.inp", doc.Name)
        Gui.getDocument(doc).getObject(os.path.split(result_state0)[1]).ShapeColor = (1., 0., 0.)
        Gui.getDocument(doc).getObject(os.path.split(result_state0)[1]).Transparency = 80
        Gui.getDocument(doc).getObject(os.path.split(result_state0)[1]).LineWidth = 0.1
        Gui.getDocument(doc).getObject(os.path.split(result_state1)[1]).ShapeColor = (0., 1., 0.)
        state.addObject(doc.getObject(os.path.split(result_state0)[1]))
        state.addObject(doc.getObject(os.path.split(result_state1)[1]))
        femmesh_object=doc.getObject(os.path.split(result_state1)[1])
        out_mesh = femmesh.femmesh2mesh.femmesh_2_mesh(femmesh_object.FemMesh)
        mesh_filename = f"Smooth{case:03}"
        Mesh.show(Mesh.Mesh(out_mesh), mesh_filename)
        obj=doc.getObject(mesh_filename)
        state.addObject(obj)
        obj.Mesh.smooth("Laplace", 10, 0.6307, 0.0424)
        doc.Topology.addObject(state)
    state1 = doc.getObject(os.path.split(result_state0)[1])
    state2 = doc.getObject(os.path.split(result_state1)[1])

    if state1 is not None:
        state1.Visibility = False

    if state2 is not None:
        state2.Visibility = False

class GenTableModel(PySide.QtCore.QAbstractTableModel):
    def __init__(self, parent, itemList, header, colours=None, score=None, *args):

        PySide.QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.itemList = []
        for i in itemList:
            self.itemList.append(list(i))

        self.header = header[:]
        height = len(itemList)
        width = len(header)
        defaultColour = PySide.QtGui.QColor("white")

        if colours == None:
            self.colours = [
                [defaultColour for x in range(width)] for y in range(height)]
        else:
            self.colours = colours[:]
        self.score = score

    def updateColours(self, colours):
        for i, row in enumerate(colours):
            self.colours[i][1:] = row

    def updateData(self, table):
        for i, row in enumerate(table):
            self.itemList[i][1:] = row

    def updateHeader(self, header):
        self.header[1:] = header

    def rowCount(self, parent):
        return len(self.itemList)

    def columnCount(self, parent):
        return len(self.header)

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role == PySide.QtCore.Qt.BackgroundRole:
            # Return colour
            return self.colours[index.row()][index.column()]
        elif role == PySide.QtCore.Qt.DisplayRole:
            return str(self.itemList[index.row()][index.column()])

    def headerData(self, col, orientation, role):
        if orientation == PySide.QtCore.Qt.Horizontal and role == PySide.QtCore.Qt.DisplayRole:
            return self.header[col]
        return None

    def sort(self, col, order):
        """sort table by given column number col"""
        self.layoutAboutToBeChanged.emit()
        if isinstance(self.score, np.ndarray):
            self.itemList = [c for _, c in sorted(
                zip(self.score, self.itemList))]
            self.colours = [c for _, c in sorted(
                zip(self.score, self.colours))]
        else:
            self.itemList = sorted(self.itemList, key=operator.itemgetter(col))
            self.colours = [c for _, c in sorted(
                zip(self.itemList, self.colours))]

        if order != PySide.QtCore.Qt.DescendingOrder:
            self.itemList.reverse()
        self.layoutChanged.emit()