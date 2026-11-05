import numpy as np  
import FreeCAD  
import itertools
from PySide import QtGui  
from fembygen import Common
import pyDOE3

class Taguchipy():
    def __init__(self, param, numberofgen):
        self.variables = param
        self.numberofgen = numberofgen

    def selection(self):
        self.FACTORS = len(self.variables)
        self.LEVELS = self.numberofgen

        try:
            tg = pyDOE3.taguchi_design(self.FACTORS, self.LEVELS)
            row, column = tg.shape
            for c in range(column):
                for r in range(row):
                    idx = int(tg[r, c])
                    if idx < len(self.variables[c]):
                        tg[r, c] = self.variables[c][idx]
                    else:
                        tg[r, c] = self.variables[c][-1]
            
            self.matrix = tg.tolist()
            return self.matrix
            
        except Exception as e:
            qm = QtGui.QMessageBox
            ret = qm.critical(None, 'Attention',
                            "There are no suitable parameters for Taguchi.\n",
                            qm.Ok)

            qm.information(None, 'Information',
                        "You can explore suitable parameters for Taguchi at the following link:\n"
                        "https://www.york.ac.uk/depts/maths/tables/orthogonal.htm\n\n"
                        "Alternatively, you may consider using another experimental design method.",
                        qm.Ok)

            FreeCAD.Console.PrintWarning(f"There are no suitable parameters for Taguchi.\n")
            return None
class Signal():
    def smaller_best(self, focused_res):
        n = np.size(focused_res)
        focused_res = np.array(focused_res).astype(float)
        squaring = focused_res ** 2
        return -10 * np.log10(np.sum(squaring) / n)
    def larger_best(self, focused_res):
        n = np.size(focused_res)
        focused_res = np.array(focused_res).astype(float)
        squaring = (1 / focused_res) ** 2
        return -10 * np.log10(np.sum(squaring) / n)
    def optimal_best(self, focused_res):
        focused_res = np.array(focused_res).astype(float)
        mean = np.mean(focused_res)
        std = np.std(focused_res)
        return 10 * np.log10((mean ** 2) / (std ** 2))
class Sobolpy():
    def __init__(self, param, numberofgen):
        self.variables = param
        self.samples = numberofgen

    def selection(self):
        try:
            sobol = pyDOE3.sobol_sequence(len(self.variables), self.samples)
            row, column = sobol.shape
            for i, param_range in enumerate(self.variables):
                diff = param_range[-1] - param_range[0]
                sobol[:, i] = diff * sobol[:, i] + param_range[0]
            
            self.matrix = sobol.tolist()
            return self.matrix
            
        except Exception as e:
            qm = QtGui.QMessageBox
            qm.critical(None, 'Attention', 
                        "An error occurred while generating the Sobol sequence.\n", 
                        qm.Ok)
            FreeCAD.Console.PrintWarning(f"Sobol sequence error: {str(e)}\n")
            return None


class Morrispy():
    def __init__(self, param, numberofgen):
        self.variables = param
        self.trajectories = numberofgen 
        self.levels = 4

    def selection(self):
        try:
            morris = pyDOE3.morris_sampling(len(self.variables), self.levels, self.trajectories)
            row, column = morris.shape
            for i, param_range in enumerate(self.variables):
                diff = param_range[-1] - param_range[0]
                morris[:, i] = diff * morris[:, i] + param_range[0]
            
            self.matrix = morris.tolist()
            return self.matrix
            
        except Exception as e:
            qm = QtGui.QMessageBox
            qm.critical(None, 'Attention', 
                        "An error occurred while generating Morris sampling.\n", 
                        qm.Ok)
            FreeCAD.Console.PrintWarning(f"Morris sampling error: {str(e)}\n")
            return None


class Optimalpy():
    def __init__(self, param, numberofgen):
        self.variables = param
        self.samples = numberofgen

    def selection(self):
        try:
            candidates = np.array(list(itertools.product(*self.variables)))
            opt = pyDOE3.optimal_design(candidates, self.samples)
            
            self.matrix = opt.tolist()
            return self.matrix
            
        except Exception as e:
            qm = QtGui.QMessageBox
            qm.critical(None, 'Attention', 
                        "An error occurred while generating the Optimal design.\n"
                        "Make sure the sample size is mathematically valid for the candidate pool.", 
                        qm.Ok)
            FreeCAD.Console.PrintWarning(f"Optimal design error: {str(e)}\n")
            return None