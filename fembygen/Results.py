import FreeCAD
import FreeCADGui
import PySide
from PySide2.QtWidgets import  QTableWidgetItem
import matplotlib.pyplot as plt
import os.path
import numpy as np
from fembygen import Common
import glob
import functools
from scipy.stats import pearsonr , f_oneway
from femresult.resulttools import fill_femresult_stats
from FreeCAD.Plot import Plot

def makeResult():
    try:
        obj = FreeCAD.ActiveDocument.Results
        obj.isValid()
    except:
        try:
            obj = FreeCAD.ActiveDocument.addObject(
                "App::DocumentObjectGroupPython", "Results")
            FreeCAD.ActiveDocument.GenerativeDesign.addObject(obj)
        except:
            return None
    Result(obj)
    if FreeCAD.GuiUp:
        ViewProviderResult(obj.ViewObject)
    return obj


class Result:
    """ The CFD Physics Model """

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "Result"
        self.initProperties(obj)
        obj.FEAMetricsAll = []
        obj.FEAMetricsSum = []

    def initProperties(self, obj):
        try:
            obj.addProperty("App::PropertyPythonObject", "FEAMetricsAll", "Base",
                            "All Result lists")
            obj.addProperty("App::PropertyPythonObject", "FEAMetricsSum", "Base",
                            "Summary Result lists")
        except:
            pass


class ResultsCommand():
    """Show results of analysed generations"""

    def GetResources(self):
        return {'Pixmap': os.path.join(FreeCAD.getUserAppDataDir() + 'Mod/FEMbyGEN/fembygen/icons/Results.svg'),  # the name of a svg file available in the resources
                'Accel': "Shift+R",  # a default shortcut (optional)
                'MenuText': "Show Results",
                'ToolTip': "Show results of analysed generations"}

    def Activated(self):
        obj = makeResult()
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


class ResultsPanel:
    def __init__(self, object):
        # this will create a Qt widget from our ui file
        guiPath = FreeCAD.getUserAppDataDir() + "Mod/FEMbyGEN/fembygen/ui/Results.ui"
        self.form = FreeCADGui.PySideUic.loadUi(guiPath)
        self.workingDir = '/'.join(
            object.Object.Document.FileName.split('/')[0:-1])
        self.numGenerationsi = Common.checkGenerations(self.workingDir)
        self.obj = object

        self.doc = object.Object.Document
        if self.doc.Results.FEAMetricsAll == []:
            FreeCAD.Console.PrintMessage("Calculating metrics...\n")
            self.calcAndSaveFEAMetrics()
        self.form.arrange.clicked.connect(self.ranking)
        self.form.comboBox_3.currentIndexChanged.connect(self.update_anova_table)
        self.form.comboBox_2.currentIndexChanged.connect(self.plotParetoGraph)
        self.form.comboBox.currentIndexChanged.connect(self.update_table)   
        self.updateResultsTableAll()
        self.updateResultsTableSum()
        self.doc.save()
          
    def updateResultsTableAll(self):
        header = self.doc.Results.FEAMetricsAll[0]
        items = self.doc.Results.FEAMetricsAll[1:]
        stats, numAnalysed = Common.checkAnalyses(self.doc)
        gen, lc = len(stats), len(stats[0])
        index = []
        for i in range(gen):
            for j in range(lc):
                index.append([f"{i+1}.{j+1}"])
        table = np.hstack((index, items))
        table = table.tolist()
        header = ["Gen"]+header

        colours = self.generateColourScalesFromMetrics(
            self.doc.Results.FEAMetricsAll)
        self.tableModel = Common.GenTableModel(
            self.form, table, header, colours)
        self.form.resultsTable_all.setModel(self.tableModel)
        self.form.resultsTable_all.resizeColumnsToContents()
        self.form.resultsTable_all.horizontalHeader().setResizeMode(
            PySide.QtGui.QHeaderView.ResizeToContents)

        self.form.resultsTable_all.clicked.connect(functools.partial(
            Common.showGen, self.form.resultsTable_all, self.doc))
        self.form.resultsTable_all.setMinimumHeight(30+len(index)*31)
        self.form.resultsTable_all.setMaximumHeight(30+len(index)*31)
        self.form.resultsTable_all.setSortingEnabled(True)

    def updateResultsTableSum(self, score=None):
        header = self.doc.Results.FEAMetricsSum[0]
        items = self.doc.Results.FEAMetricsSum[1:]
        stats, numAnalysed = Common.checkAnalyses(self.doc)
        gen, lc = len(stats), len(stats[0])
        index = []
        for i in range(gen):
            index.append([i+1])
        table = np.hstack((index, items))
        table = table.tolist()
        header = ["Gen"]+header

        colours = self.generateColourScalesFromMetrics(
            self.doc.Results.FEAMetricsSum)
        self.tableModel = Common.GenTableModel(
            self.form, table, header, colours, score)
        self.form.resultsTable_sum.setModel(self.tableModel)
        self.form.resultsTable_sum.resizeColumnsToContents()
        self.form.resultsTable_sum.horizontalHeader().setResizeMode(
            PySide.QtGui.QHeaderView.ResizeToContents)

        self.form.resultsTable_sum.clicked.connect(functools.partial(
            Common.showGen, self.form.resultsTable_sum, self.doc))
        self.form.resultsTable_sum.setMinimumHeight(30+gen*31)
        self.form.resultsTable_sum.setMaximumHeight(30+gen*31)
        self.form.resultsTable_sum.setSortingEnabled(True)

    def generateColourScalesFromMetrics(self, table):
        items = np.array(table[1:], dtype=np.dtype("float"))
        width = len(table[0])
        height = len(items)
        colours = [[PySide.QtGui.QColor("white")
                    for x in range(width+1)] for y in range(height)]

        for i in range(width):
            try:
                vals = items[:, i]
            except ValueError:
                FreeCAD.Console.PrintError("Results couldn't converted to the number.\n")

            # Calculate value range to calibrate colour scale
            minVal = min(vals)
            maxVal = max(vals)
            valRange = maxVal - minVal
            for j, value in enumerate(vals):
                try:
                    if value > maxVal:
                        # If value is greater than maximum, set it to full intensity
                        normVal = 1.0
                    else:
                        if valRange != 0:
                            normVal = (value - minVal) / valRange
                        else:
                            normVal = 0

                    col = self.rgb(normVal)
                    colours[j][i+1] = PySide.QtGui.QColor(
                        col[0], col[1], col[2], 255)
                except ValueError:
                    # Item was not a number. Likely a string because an error occurred for analysis in this row
                    # so colour it pink
                    colours[j][i+1] = PySide.QtGui.QColor(230, 184, 184, 255)
                    pass

        return colours

    def rgb(self, normVal):
        mult = 1-normVal
        return int(mult*200), 255, int(mult*200)

    def calcAndSaveFEAMetrics(self):
        master = self.doc
        numGenerations = Common.checkGenerations(self.workingDir)
        if numGenerations > 0:
            header = [["Volume[mm^3]", "Max Stress[MPa]", "Max Disp[mm]", "Mean Stress[MPa]", "Internal Energy[Joule]", "Standard Dev. of En. Den"
                       ]]

            resultAll, resultSum = self.calculateFEAMetric()
            tableAll = header + resultAll
            tableSum = header+resultSum
            master.Results.FEAMetricsAll = tableAll
            master.Results.FEAMetricsSum = tableSum
        FreeCAD.open(master.FileName)

    def calculateFEAMetric(self):
        master = self.doc
        statuses, numgAnly, lc = Common.searchAnalysed(master)
        result = []
        deviation = []

        # Getting the analysis table to read results
        for i, row in enumerate(statuses):
            # open the generation file
            filename = f"Gen{i+1}"
            filePath = self.workingDir + f"/Gen{i+1}/{filename}.FCStd"
            doc = FreeCAD.open(filePath, hidden=True)

            # for each loadcases it's read the results
            results = doc.findObjects('Fem::FemResultObjectPython')
            for j, value in enumerate(row):
                if value == "Analysed":
                    try:
                        resultPath = self.workingDir + f"/Gen{i+1}/loadCase_{j+1}/"
                        mean = np.mean(results[j].vonMises)
                        max = np.max(results[j].vonMises)
                        maxDisp = np.max(results[j].DisplacementLengths)

                        intData, totalInt, volData, totalVol, denData = self.IntEnergyandVolume(
                            resultPath)
                        energyDenStd = np.std(denData)
                        deviation.append(denData)
                        result.append([f"{totalVol:.2e}", f"{max:.2e}", f"{maxDisp:.2e}",
                                       f"{mean:.2e}", f"{totalInt:.2e}", f"{energyDenStd:.2e}"])
                        FreeCAD.Console.PrintMessage(f"Generation {i+1} Analysis {j+1} result values imported\n")
                    except:
                        FreeCAD.Console.PrintError(
                            f"During getting result values of Generation {i+1} Analysis {j+1} problem occured. Please check the generation results by opening Gen{i+1} folder in master file directory.\n")
                        result.append([None]*6)
                else:
                    FreeCAD.Console.PrintError(f"Generation {i+1} Loadcase {j+1} couldn't imported\n")
                    result.append([None]*6)

            self.getResultsToMaster(doc, results[0])
            
            FreeCAD.closeDocument(filename)
        result_sum = []
        res = np.array(result, dtype=np.dtype("float"))

        gen = i+1
        lc = j+1
        for k in range(0, gen*lc, lc):
            try:
                volume = res[k, 0]
                internal = np.sum(res[k:k+lc, 1])
                std = np.std(deviation[k:k+lc])
                meanStr = np.mean(res[k:k+lc, 3])
                maxStr = np.max(res[k:k+lc, 4])
                maxdisp = np.max(res[k:k+lc, 5])
                result_sum.append([f"{volume:.2e}", f"{internal:.2e}", f"{std:.2e}",
                                   f"{meanStr:.2e}", f"{maxStr:.2e}", f"{maxdisp:.2e}"])
            except:
                result_sum.append([None]*6)

        return result, result_sum

    def sumResults(self, total, doc):
        """The function is for sum the results objects of Loadcases. By the way optimum model can be selected in a better way.
        Solidworks and Ansys topology optimizations uses similar method.
        https://hawkridgesys.com/blog/solidworks-simulation-multiple-load-cases-for-topology-studies
        https://us.v-cdn.net/6032193/uploads/JE71WKGYSLZ2/image.png

        For this function work, meshes of all Loadcases needs to be same.
        """
        DisplacementLengths = np.zeros(len(total.DisplacementLengths))
        DisplacementVectors = np.zeros((len(total.DisplacementVectors), 3))
        MaxShear = np.zeros(len(total.MaxShear))
        NodeStrainXX = np.zeros(len(total.NodeStrainXX))
        NodeStrainXY = np.zeros(len(total.NodeStrainXY))
        NodeStrainXZ = np.zeros(len(total.NodeStrainXZ))
        NodeStrainYY = np.zeros(len(total.NodeStrainYY))
        NodeStrainYZ = np.zeros(len(total.NodeStrainYZ))
        NodeStrainZZ = np.zeros(len(total.NodeStrainZZ))
        NodeStressXX = np.zeros(len(total.NodeStressXX))
        NodeStressXY = np.zeros(len(total.NodeStressXY))
        NodeStressXZ = np.zeros(len(total.NodeStressXZ))
        NodeStressYY = np.zeros(len(total.NodeStressYY))
        NodeStressYZ = np.zeros(len(total.NodeStressYZ))
        NodeStressZZ = np.zeros(len(total.NodeStressZZ))
        PrincipalMax = np.zeros(len(total.PrincipalMax))
        PrincipalMed = np.zeros(len(total.PrincipalMed))
        PrincipalMin = np.zeros(len(total.PrincipalMin))
        vonMises = np.zeros(len(total.vonMises))
        for obj in doc.Objects:
            if obj.TypeId == 'Fem::FemResultObjectPython':
                DisplacementLengths += np.array(obj.DisplacementLengths)
                DisplacementVectors += np.array(obj.DisplacementVectors)
                MaxShear += np.array(obj.MaxShear)
                NodeStrainXX += np.array(obj.NodeStrainXX)
                NodeStrainXY += np.array(obj.NodeStrainXY)
                NodeStrainXZ += np.array(obj.NodeStrainXZ)
                NodeStrainYY += np.array(obj.NodeStrainYY)
                NodeStrainYZ += np.array(obj.NodeStrainYZ)
                NodeStrainZZ += np.array(obj.NodeStrainZZ)
                NodeStressXX += np.array(obj.NodeStressXX)
                NodeStressXY += np.array(obj.NodeStressXY)
                NodeStressXZ += np.array(obj.NodeStressXZ)
                NodeStressYY += np.array(obj.NodeStressYY)
                NodeStressYZ += np.array(obj.NodeStressYZ)
                NodeStressZZ += np.array(obj.NodeStressZZ)
                PrincipalMax += np.array(obj.PrincipalMax)
                PrincipalMed += np.array(obj.PrincipalMed)
                PrincipalMin += np.array(obj.PrincipalMin)
                vonMises += np.array(obj.vonMises)

        # Assigning summed results to the an object
        total.DisplacementLengths = DisplacementLengths.tolist()  # it includes Vector object, therefore it converted to the list
        vectorized = []
        for i in DisplacementVectors.tolist():
            vectorized.append(FreeCAD.Vector(i))
        total.DisplacementVectors = vectorized
        total.MaxShear = MaxShear.tolist()
        total.NodeStrainXX = NodeStrainXX.tolist()
        total.NodeStrainXY = NodeStrainXY.tolist()
        total.NodeStrainXZ = NodeStrainXZ.tolist()
        total.NodeStrainYY = NodeStrainYY.tolist()
        total.NodeStrainYZ = NodeStrainYZ.tolist()
        total.NodeStrainZZ = NodeStrainZZ.tolist()
        total.NodeStressXX = NodeStressXX.tolist()
        total.NodeStressXY = NodeStressXY.tolist()
        total.NodeStressXZ = NodeStressXZ.tolist()
        total.NodeStressYY = NodeStressYY.tolist()
        total.NodeStressYZ = NodeStressYZ.tolist()
        total.NodeStressZZ = NodeStressZZ.tolist()
        total.PrincipalMax = PrincipalMax.tolist()
        total.PrincipalMed = PrincipalMed.tolist()
        total.PrincipalMin = PrincipalMin.tolist()
        total.vonMises = vonMises.tolist()
        fill_femresult_stats(total)

    def getResultsToMaster(self, doc, object):
        master = self.doc

        try:
            #copy one of the analysis results to clear all values then calculate sum of all results
            object.Label = f"{doc.Name}_Results"
            object.Mesh.Label = f"{doc.Name}_Mesh"
            master.copyObject(object, False)
            master.copyObject(object.Mesh, False)
        except:
            FreeCAD.Console.PrintError(
                f"Results of {doc.Name} is not found in the file. Please check the results by opening the file directly.\n")
            return
        totalResult = master.getObjectsByLabel(f"{doc.Name}_Results")[0]
        resultMesh = master.getObjectsByLabel(f"{doc.Name}_Mesh")[0]

        # to sum up all loadcases result
        self.sumResults(totalResult, doc)

        totalResult.Mesh = resultMesh
        master.Results.addObject(totalResult)

        totalResult.Visibility = False
        resultMesh.Visibility = False

    def IntEnergyandVolume(self, resultPath):
        """to get volume information and internal energy information from dat file"""
        name = glob.glob(resultPath + "*.dat")
        with open(name[0], "r") as datfile:
            text = datfile.read()

        # getting elemental internal energy results
        internal = text.find(" internal energy")
        internalStart = text.find("\n", internal)+2
        internalEnd = text.find(" total internal", internalStart)-1
        intData = np.fromstring(text[internalStart:internalEnd], sep="\n")
        intData = intData.reshape(len(intData)//2, 2)

        # getting total internal energy
        totalIntStart = text.find("\n", internalEnd+1)+1
        totalIntEnd = text.find("volume", totalIntStart)-1
        totalInt = float(text[totalIntStart:totalIntEnd])

        # getting elements volume
        volStart = text.find("\n", totalIntEnd+1)+1
        volEnd = text.find("total volume", totalIntStart)-1
        volData = np.fromstring(text[volStart:volEnd], sep="\n")
        volData = volData.reshape(len(volData)//2, 2)

        # getting total volume
        totalVolStart = text.find("\n", volEnd+1)+1
        totalVolEnd = text.find("internal energy density", totalVolStart)-1
        totalVol = float(text[totalVolStart:totalVolEnd])

        # getting density from file
        denStart = text.find("\n", totalVolEnd+1)+1
        denEnd = -1  # text.find("total volume", totalVolStart)
        denData = np.fromstring(text[denStart:denEnd], sep="\n")
        denData = denData.reshape(len(denData)//3, 3)

        # Joule , Joule, mm^3, mm^3, Joule
        return intData[:, 1]*1000, totalInt*1000, volData[:, 1], totalVol, denData[:, 2]*1000

    def ranking(self):
        """ By using weight of the result, it arranges the results.
        """
        table = np.array(
            self.doc.Results.FEAMetricsSum[1:], dtype=np.dtype("float"))
        volume = float(self.form.volume.toPlainText())
        maxs = float(self.form.maxstress.toPlainText())
        maxd = float(self.form.maxdisplacement.toPlainText())
        means = float(self.form.meanstress.toPlainText())
        intEn = float(self.form.internalenergy.toPlainText())
        std = float(self.form.standarddeviation.toPlainText())
        try:
            assert volume+intEn+std+means+maxs+maxd == 100
            # calculating normalized value of results
            # max result will be 0, min result will be 1
            row, column = table.shape
            normTable = np.zeros((row, column))
            for i in range(column):
                normTable[:, i] = 1-self.normalize(table[:, i])
                
            # Calculating score by using weight and normalized results
            score = volume*normTable[:, 0] + maxs*normTable[:, 1] + maxd*normTable[:, 2] + \
                means*normTable[:, 3] + intEn * \
                normTable[:, 4] + std*normTable[:, 5]
            self.updateResultsTableSum(score)
        except:
            FreeCAD.Console.PrintError('Total weignt needs to be 100\n')


    def corelation(self):
        master = self.doc
        results = np.array(
            master.Results.FEAMetricsSum[1:], dtype=np.dtype("float"))
        parameters1 =   np.array(
            master.Generate.GeneratedParameters, dtype=np.dtype("float"))
        parameterValues = np.transpose(parameters1)
        parameters = master.Generate.ParametersName

        cor_table = [] 
        for index, param in enumerate(parameters):
            row = [param]    
            for j in range(len(results[0])):
                corr, _ = pearsonr(parameterValues[index], [item[j] for item in results])
                row.append(round(corr, 4))
            cor_table.append(row)

        return cor_table

    def update_table(self, index):
        cor_table = self.corelation()
        self.form.tableWidget.setColumnCount(2)
        self.form.tableWidget.setRowCount(len(cor_table))
        self.form.tableWidget.setHorizontalHeaderLabels(["Parameters", "Correlation Coef."])
        
        for i, row in enumerate(cor_table):
            item_param = QTableWidgetItem(row[0]) 
            item_coef = QTableWidgetItem(str(row[index + 1]))  
            self.form.tableWidget.setItem(i, 0, item_param)
            self.form.tableWidget.setItem(i, 1, item_coef)
            item_coef.setToolTip("As this value approaches -1 or 1, the strength of the effect increases - negative effect, + means positive effect.")

    def anova(self):
        master = self.doc
        results = np.array(
            master.Results.FEAMetricsSum[1:], dtype=np.dtype("float"))
        parameters1 = np.array(
            master.Generate.GeneratedParameters, dtype=np.dtype("float"))
        parameterValues = np.transpose(parameters1)
        parameters = master.Generate.ParametersName

        anova_table = []
        for index, param in enumerate(parameters):
            row = [param]    
            unique_values = np.unique(parameterValues[index])
            
            for j in range(len(results[0])):
                # Create groups for ANOVA test
                groups = [results[:, j][parameterValues[index] == value] for value in unique_values]
                FreeCAD.Console.PrintMessage(f"Parameter: {param}, Unique Values: {unique_values}, Groups: {groups}\n")

                # Check if any group is empty
                if any(len(group) == 0 for group in groups):
                    row.append(None)  # Append None or any placeholder for invalid ANOVA result
                
                else:
                    # Perform ANOVA test
                    f_val, _ = f_oneway(*groups)
                    row.append(round(f_val, 4))  # Round the F-value for consistency

            anova_table.append(row)
        
        return anova_table


    def update_anova_table(self, index):
            anova_table= self.anova()
            self.form.tableWidget_2.setColumnCount(2)
            self.form.tableWidget_2.setRowCount(len(anova_table))
            self.form.tableWidget_2.setHorizontalHeaderLabels(["Parameters", "F values"])
            
            for i, row in enumerate(anova_table):
                item_param = QTableWidgetItem(row[0]) 
                item_coef = QTableWidgetItem(str(row[index + 1]))  
                self.form.tableWidget_2.setItem(i, 0, item_param)
                self.form.tableWidget_2.setItem(i, 1, item_coef)       
    

    def calculate_pareto_data(self):
        cor_table = self.corelation()
        Responses_names = ["Volume", "Max Stress", "Max Displacement", "Mean Stress", "Internal Energy", "Standard Dev. of En. Den."]
        Responses = {}
        parameters = [row[0] for row in cor_table]
    
        for i, response_name in enumerate(Responses_names):
            response_values = [abs(row[i + 1]) for row in cor_table]
            Responses[response_name] = np.abs(response_values)

        return Responses, parameters 


    def plotParetoGraph(self, index):
        Responses, parameters = self.calculate_pareto_data()
        response_name = self.form.comboBox_2.itemText(index) if index != 0 else self.form.comboBox_2.currentText()

        response_matrix = Responses[response_name]
        tot_cor = np.sum(response_matrix)
        percentage_effects= [(miktar / tot_cor) * 100 for miktar in response_matrix.flatten()]
        effects_of_parameters= zip(parameters, percentage_effects)
        percentage_rank= sorted(effects_of_parameters, key=lambda x: x[1], reverse=True)
        cumulative_percentage= [sum([x[1] for x in percentage_rank[:i + 1]]) for i in range(len(percentage_rank))]

        fig = Plot.figure(winTitle=f'Pareto Graph - {response_name}')
        ax1 = Plot.axesList()[0]

        ax1.bar([x[0] for x in percentage_rank], [x[1] for x in percentage_rank], color='skyblue')
        ax2 = ax1.twinx()
        ax2.plot([x[0] for x in percentage_rank], cumulative_percentage, color='r', marker='o')

        ax1.set_xlabel('Parameters')
        ax1.set_ylabel('Percentage Effect')
        ax2.set_ylabel('Cumulative Percentage')
        ax2.set_ylim(0, 100)
        ax1.set_ylim(0, 100)
        Plot.plt.show()
        fig.canvas.flush_events()


    def normalize(self, vals):
        """Resuls range can be different. So, the function make results between 0~1 to calculate ranking score.
        """
        minVal = np.min(vals)
        maxVal = np.max(vals)
        valRange = maxVal - minVal
        norm = (vals-minVal)/valRange
        return norm

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


class ViewProviderResult:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(
            FreeCAD.getUserAppDataDir() + 'Mod/FEMbyGEN/fembygen/icons/Results.svg')
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
        taskd = ResultsPanel(vobj)
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        FreeCADGui.Control.closeDialog()
        return

    # FreeCAD < 0.21.2
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
    
    # FreeCAD >= 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


FreeCADGui.addCommand('Results', ResultsCommand())
