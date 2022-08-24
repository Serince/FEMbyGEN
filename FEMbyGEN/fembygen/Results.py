import FreeCAD
import FreeCADGui
import PySide
import os.path
import numpy as np
from fembygen import Common


class ResultsCommand():
    """Show results of analysed generations"""

    def GetResources(self):
        return {'Pixmap': 'fembygen/Results.svg',  # the name of a svg file available in the resources
                'Accel': "Shift+R",  # a default shortcut (optional)
                'MenuText': "Show Results",
                'ToolTip': "Show results of analysed generations"}

    def Activated(self):
        panel = ResultsPanel()
        FreeCADGui.Control.showDialog(panel)
        """Do something here"""
        return

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True


class ResultsPanel:
    def __init__(self):
        # this will create a Qt widget from our ui file
        try:
            guiPath = FreeCAD.getUserAppDataDir() + "Mod/FEMbyGEN/fembygen/Results.ui"
            self.form = FreeCADGui.PySideUic.loadUi(guiPath)
            self.workingDir = '/'.join(
                FreeCAD.ActiveDocument.FileName.split('/')[0:-1])
            self.numGenerations = Common.checkGenerations()
    
            # If FEAMetrics.npy doesn't exist, try to generate it from scratch
            filePath = self.workingDir + "/FEAMetrics.npy"
            if not os.path.isfile(filePath):
                print("Calculating metrics...")
                Common.calcAndSaveFEAMetrics()
    
            # Load metrics from file
            metrics = np.load(filePath)
            table = metrics.tolist()
    
            # Split into header and table data, then update table
            self.metricNames = table[0]
            self.metrics = table[1:]
    
            # Add configuration controls
            self.addConfigControls()
    
            self.updateResultsTable()
        except:
            print("Please open a master file before open results")
    def accept(self):
        FreeCADGui.Control.closeDialog()


    def updateResultsTable(self):
        header = self.metricNames
        items = self.metrics

        colours = self.generateColourScalesFromMetrics()
        self.tableModel = Common.GenTableModel(
            self.form, items, header, colours)
        self.form.resultsTable.setModel(self.tableModel)
        self.form.resultsTable.resizeColumnsToContents()
        self.form.resultsTable.clicked.connect(Common.showGen)

    def addConfigControls(self):
        self.configControls = []

        for name in self.metricNames:
            # Create instances of controls
            paramCheck = PySide.QtGui.QCheckBox(name, self.form)
            redGreenRadio = PySide.QtGui.QRadioButton(self.form)
            gradientRadio = PySide.QtGui.QRadioButton(self.form)
            radioGroup = PySide.QtGui.QButtonGroup()
            minBox = PySide.QtGui.QDoubleSpinBox(self.form)
            maxBox = PySide.QtGui.QDoubleSpinBox(self.form)

            # Configure control parameters
            paramCheck.setChecked(True)
            minBox.setMaximum(999999.99)
            maxBox.setMaximum(999999.99)
            gradientRadio.setChecked(True)
            radioGroup.addButton(redGreenRadio)
            radioGroup.addButton(gradientRadio)

            (minVal, maxVal) = self.getMetricValueRange(name)
            minBox.setValue(minVal)
            maxBox.setValue(maxVal)

            # Create and link callback functions
            def valueChanged(value):
                colours = self.generateColourScalesFromMetrics()
                self.updateResultsTableColours(colours)
                pass

            minBox.valueChanged.connect(valueChanged)
            maxBox.valueChanged.connect(valueChanged)

            controls = [paramCheck, redGreenRadio,
                        gradientRadio, radioGroup, minBox, maxBox]
            self.configControls.append(controls)

            # Add widgets to form
            configGrid = self.form.configGrid
            numRows = configGrid.rowCount()
            configGrid.addWidget(paramCheck, numRows, 0)
            configGrid.addWidget(redGreenRadio, numRows, 1)
            configGrid.addWidget(gradientRadio, numRows, 2)
            configGrid.addWidget(minBox, numRows, 3)
            configGrid.addWidget(maxBox, numRows, 4)

    def updateResultsTableColours(self, colours):
        self.tableModel.updateColours(colours)
        # self.form.resultsTable.update()
        self.form.resultsTable.activated.emit(1)

    def getMetricValueRange(self, metricName):
        i = self.metricNames.index(metricName)
        height = len(self.metrics)
        # Gather all the values in a column
        values = [self.metrics[y][i] for y in range(height)]

        # Make new column of values that doesn't include numbers
        vals = []
        for item in values:
            try:
                vals.append(float(item))
            except ValueError:
                pass

        # Calculate value range
        minVal = min(vals)
        maxVal = max(vals)
        return (minVal, maxVal)

    def generateColourScalesFromMetrics(self):
        width = len(self.metricNames)
        height = len(self.metrics)
        colours = [[PySide.QtGui.QColor("white")
                    for x in range(width)] for y in range(height)]

        items = self.metrics

        for i in range(width):
            # Gather all the values in a column
            values = [items[y][i] for y in range(height)]

            # Make new column of values that doesn't include numbers
            vals = []
            for item in values:
                try:
                    vals.append(float(item))
                except ValueError:
                    pass

            # Calculate value range
            minVal = self.configControls[i][4].value()
            maxVal = self.configControls[i][5].value()

            # Calculate value range to calibrate colour scale
            valRange = maxVal - minVal

            for j, value in enumerate(values):
                try:
                    value = float(value)
                    if value > maxVal:
                        # If value is greater than maximum, set it to full intensity
                        normVal = 1.0
                    else:
                        if valRange != 0:
                            normVal = (value - minVal) / valRange
                        else:
                            normVal = 0

                    hue = 0.4
                    col = Common.hsvToRgb(hue, normVal, 1.0)
                    col = [int(col[0]*255), int(col[1]*255), int(col[2]*255)]
                    colours[j][i] = PySide.QtGui.QColor(
                        col[0], col[1], col[2], 255)
                except ValueError:
                    # Item was not a number. Likely a string because an error occured for analysis in this row
                    # so colour it pink
                    colours[j][i] = PySide.QtGui.QColor(230, 184, 184, 255)
                    pass

        return colours


FreeCADGui.addCommand('Results', ResultsCommand())
