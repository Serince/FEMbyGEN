import numpy as np    

def QT_TRANSLATE_NOOP(context, text):
    return text

class Taguchipy():
    def __init__(self,param,numberofgen):
        self.variables=param
        self.numberofgen=numberofgen
    def selection(self):
        self.FACTORS = len(self.variables)
        self.LEVELS=self.numberofgen
        if self.FACTORS == 3 and self.LEVELS == 2:
                    print('Taguchi_L4 is applicable.')
                    return self.design_L4() 
        elif self.FACTORS == 4 and self.LEVELS == 3:
                    print('Taguchi_L9 is applicable.')
                    return self.design_L9()      
        elif self.FACTORS == 7 and self.LEVELS == 2:
                    print('Taguchi_L8 is applicable.')
                    return self.design_L8()
        elif self.FACTORS == 11 and self.LEVELS == 2:
                    print('Taguchi_L12 is applicable.')
                    return self.design_L12()
        elif self.FACTORS == 16 and self.LEVELS == 5:
                    print('Taguchi_L16b is applicable.')
                    return self.design_L16()
        else:
            raise Exception("Taguchi design not available.")
    
    def design_L4(self):
            # L4: https://www.itl.nist.gov/div898/software/dataplot/dex/L4.DATşğ
            self.matrix = np.zeros((4,3))
            # Row 1
            self.matrix[[0],[0]] = self.variables[0][0]
            self.matrix[[0],[1]] = self.variables[1][0]    
            self.matrix[[0],[2]] = self.variables[2][0]
            # Row 2
            self.matrix[[1],[0]] = self.variables[0][0]
            self.matrix[[1],[1]] = self.variables[1][1]    
            self.matrix[[1],[2]] = self.variables[2][1]
            # Row 3
            self.matrix[[2],[0]] = self.variables[0][1]
            self.matrix[[2],[1]] = self.variables[1][0]    
            self.matrix[[2],[2]] = self.variables[2][1]
            # Row 4
            self.matrix[[3],[0]] = self.variables[0][1]
            self.matrix[[3],[1]] = self.variables[1][1]    
            self.matrix[[3],[2]] = self.variables[2][0]
            self.matrix=self.matrix.tolist()
            return self.matrix
                                 
        
    def design_L9(self):
            # L9: https://www.itl.nist.gov/div898/software/dataplot/dex/L9.DAT
            self.matrix = np.zeros((9,4))
            # Row 1 : 1,1,1,1
            self.matrix[[0],[0]] = self.variables[0][0]
            self.matrix[[0],[1]] = self.variables[1][0]    
            self.matrix[[0],[2]] = self.variables[2][0]
            self.matrix[[0],[3]] = self.variables[3][0]
            # Row 2 : 1,2,2,2
            self.matrix[[1],[0]] = self.variables[0][0]
            self.matrix[[1],[1]] = self.variables[1][1]    
            self.matrix[[1],[2]] = self.variables[2][1]
            self.matrix[[1],[3]] = self.variables[3][1]
            # Row 3 : 1,3,3,3
            self.matrix[[2],[0]] = self.variables[0][0]
            self.matrix[[2],[1]] = self.variables[1][2]    
            self.matrix[[2],[2]] = self.variables[2][2]
            self.matrix[[2],[3]] = self.variables[3][2]
            # Row 4 : 2,1,2,3
            self.matrix[[3],[0]] = self.variables[0][1]
            self.matrix[[3],[1]] = self.variables[1][0]    
            self.matrix[[3],[2]] = self.variables[2][1]
            self.matrix[[3],[3]] = self.variables[3][2]
            # Row 5 : 2,2,3,1
            self.matrix[[4],[0]] = self.variables[0][1]
            self.matrix[[4],[1]] = self.variables[1][1]    
            self.matrix[[4],[2]] = self.variables[2][2]
            self.matrix[[4],[3]] = self.variables[3][0]
            # Row 6 : 2,3,1,2
            self.matrix[[5],[0]] = self.variables[0][1]
            self.matrix[[5],[1]] = self.variables[1][2]    
            self.matrix[[5],[2]] = self.variables[2][0]
            self.matrix[[5],[3]] = self.variables[3][1]
            # Row 7 : 3,1,3,2
            self.matrix[[6],[0]] = self.variables[0][2]
            self.matrix[[6],[1]] = self.variables[1][0]    
            self.matrix[[6],[2]] = self.variables[2][2]
            self.matrix[[6],[3]] = self.variables[3][1]
            # Row 8 : 3,2,1,3
            self.matrix[[7],[0]] = self.variables[0][2]
            self.matrix[[7],[1]] = self.variables[1][1]    
            self.matrix[[7],[2]] = self.variables[2][0]
            self.matrix[[7],[3]] = self.variables[3][2]
            # Row 9 : 3,3,2,1
            self.matrix[[8],[0]] = self.variables[0][2]
            self.matrix[[8],[1]] = self.variables[1][2]    
            self.matrix[[8],[2]] = self.variables[2][1]
            self.matrix[[8],[3]] = self.variables[3][0]
            self.matrix=self.matrix.tolist()
            return self.matrix
                                 
        
            
    def design_L8(self):
            # L8: https://www.itl.nist.gov/div898/software/dataplot/dex/L8.DAT
            self.matrix = np.zeros((8,7))
            # Row 1 : 1,1,1,1,1,1,1
            self.matrix[[0],[0]] = self.variables[0][0]
            self.matrix[[0],[1]] = self.variables[1][0]    
            self.matrix[[0],[2]] = self.variables[2][0]
            self.matrix[[0],[3]] = self.variables[3][0]
            self.matrix[[0],[4]] = self.variables[4][0]
            self.matrix[[0],[5]] = self.variables[5][0]
            self.matrix[[0],[6]] = self.variables[6][0]
            # Row 2 : 1,1,1,2,2,2,2
            self.matrix[[1],[0]] = self.variables[0][0]
            self.matrix[[1],[1]] = self.variables[1][0]    
            self.matrix[[1],[2]] = self.variables[2][0]
            self.matrix[[1],[3]] = self.variables[3][1]
            self.matrix[[1],[4]] = self.variables[4][1]
            self.matrix[[1],[5]] = self.variables[5][1]
            self.matrix[[1],[6]] = self.variables[6][1]
            # Row 3 : 1,2,2,1,1,2,2
            self.matrix[[2],[0]] = self.variables[0][0]
            self.matrix[[2],[1]] = self.variables[1][1]    
            self.matrix[[2],[2]] = self.variables[2][1]
            self.matrix[[2],[3]] = self.variables[3][0]
            self.matrix[[2],[4]] = self.variables[4][0]
            self.matrix[[2],[5]] = self.variables[5][1]
            self.matrix[[2],[6]] = self.variables[6][1]
            # Row 4 : 1,2,2,2,2,1,1
            self.matrix[[3],[0]] = self.variables[0][0]
            self.matrix[[3],[1]] = self.variables[1][1]    
            self.matrix[[3],[2]] = self.variables[2][1]
            self.matrix[[3],[3]] = self.variables[3][1]
            self.matrix[[3],[4]] = self.variables[4][1]
            self.matrix[[3],[5]] = self.variables[5][0]
            self.matrix[[3],[6]] = self.variables[6][0]
            # Row 5 : 2,1,2,1,2,1,2
            self.matrix[[4],[0]] = self.variables[0][1]
            self.matrix[[4],[1]] = self.variables[1][0]    
            self.matrix[[4],[2]] = self.variables[2][1]
            self.matrix[[4],[3]] = self.variables[3][0]
            self.matrix[[4],[4]] = self.variables[4][1]
            self.matrix[[4],[5]] = self.variables[5][0]
            self.matrix[[4],[6]] = self.variables[6][1]
            # Row 6 : 2,1,2,2,1,2,1
            self.matrix[[5],[0]] = self.variables[0][1]
            self.matrix[[5],[1]] = self.variables[1][0]    
            self.matrix[[5],[2]] = self.variables[2][1]
            self.matrix[[5],[3]] = self.variables[3][1]
            self.matrix[[5],[4]] = self.variables[4][0]
            self.matrix[[5],[5]] = self.variables[5][1]
            self.matrix[[5],[6]] = self.variables[6][0]
            # Row 7 : 2,2,1,1,2,2,1
            self.matrix[[6],[0]] = self.variables[0][1]
            self.matrix[[6],[1]] = self.variables[1][1]    
            self.matrix[[6],[2]] = self.variables[2][0]
            self.matrix[[6],[3]] = self.variables[3][0]
            self.matrix[[6],[4]] = self.variables[4][1]
            self.matrix[[6],[5]] = self.variables[5][1]
            self.matrix[[6],[6]] = self.variables[6][0]
            # Row 8 : 2,2,1,2,1,1,2
            self.matrix[[7],[0]] = self.variables[0][1]
            self.matrix[[7],[1]] = self.variables[1][1]    
            self.matrix[[7],[2]] = self.variables[2][0]
            self.matrix[[7],[3]] = self.variables[3][1]
            self.matrix[[7],[4]] = self.variables[4][0]
            self.matrix[[7],[5]] = self.variables[5][0]
            self.matrix[[7],[6]] = self.variables[6][1]
            self.matrix=self.matrix.tolist()
            return self.matrix
                                 
            
    def design_L12(self):
            # L12: https://www.york.ac.uk/depts/maths/tables/l12.gif
            self.matrix = np.zeros((12,11))
            # Row 1 :   1,1,1     1,1,1   1,1,1   1,1
            self.matrix[[0],[0]] = self.variables[0][0]
            self.matrix[[0],[1]] = self.variables[1][0]    
            self.matrix[[0],[2]] = self.variables[2][0]
            self.matrix[[0],[3]] = self.variables[3][0]
            self.matrix[[0],[4]] = self.variables[4][0]
            self.matrix[[0],[5]] = self.variables[5][0]
            self.matrix[[0],[6]] = self.variables[6][0]
            self.matrix[[0],[7]] = self.variables[7][0]
            self.matrix[[0],[8]] = self.variables[8][0]
            self.matrix[[0],[9]] = self.variables[9][0]
            self.matrix[[0],[10]] = self.variables[10][0]
            # Row 2 :   1,1,1     1,1,2   2,2,2   2,2
            self.matrix[[1],[0]] = self.variables[0][0]
            self.matrix[[1],[1]] = self.variables[1][0]    
            self.matrix[[1],[2]] = self.variables[2][0]
            self.matrix[[1],[3]] = self.variables[3][0]
            self.matrix[[1],[4]] = self.variables[4][0]
            self.matrix[[1],[5]] = self.variables[5][1]
            self.matrix[[1],[6]] = self.variables[6][1]
            self.matrix[[1],[7]] = self.variables[7][1]
            self.matrix[[1],[8]] = self.variables[8][1]
            self.matrix[[1],[9]] = self.variables[9][1]
            self.matrix[[1],[10]] = self.variables[10][1]
            # Row 3 :   1,1,2     2,2,1   1,1,2   2,2
            self.matrix[[2],[0]] = self.variables[0][0]
            self.matrix[[2],[1]] = self.variables[1][0]    
            self.matrix[[2],[2]] = self.variables[2][1]
            self.matrix[[2],[3]] = self.variables[3][1]
            self.matrix[[2],[4]] = self.variables[4][1]
            self.matrix[[2],[5]] = self.variables[5][0]
            self.matrix[[2],[6]] = self.variables[6][0]
            self.matrix[[2],[7]] = self.variables[7][0]
            self.matrix[[2],[8]] = self.variables[8][1]
            self.matrix[[2],[9]] = self.variables[9][1]
            self.matrix[[2],[10]] = self.variables[10][1]
            # Row 4 :   1,2,1     2,2,1   2,2,1   1,2
            self.matrix[[3],[0]] = self.variables[0][0]
            self.matrix[[3],[1]] = self.variables[1][1]    
            self.matrix[[3],[2]] = self.variables[2][0]
            self.matrix[[3],[3]] = self.variables[3][1]
            self.matrix[[3],[4]] = self.variables[4][1]
            self.matrix[[3],[5]] = self.variables[5][0]
            self.matrix[[3],[6]] = self.variables[6][1]
            self.matrix[[3],[7]] = self.variables[7][1]
            self.matrix[[3],[8]] = self.variables[8][0]
            self.matrix[[3],[9]] = self.variables[9][0]
            self.matrix[[3],[10]] = self.variables[10][1]
            # Row 5 :   1,2,2     1,2,2   1,2,1   2,1
            self.matrix[[4],[0]] = self.variables[0][0]
            self.matrix[[4],[1]] = self.variables[1][1]    
            self.matrix[[4],[2]] = self.variables[2][1]
            self.matrix[[4],[3]] = self.variables[3][0]
            self.matrix[[4],[4]] = self.variables[4][1]
            self.matrix[[4],[5]] = self.variables[5][1]
            self.matrix[[4],[6]] = self.variables[6][0]
            self.matrix[[4],[7]] = self.variables[7][1]
            self.matrix[[4],[8]] = self.variables[8][0]
            self.matrix[[4],[9]] = self.variables[9][1]
            self.matrix[[4],[10]] = self.variables[10][0]
            # Row 6 :   1,2,2     2,1,2   2,1,2   1,1
            self.matrix[[5],[0]] = self.variables[0][0]
            self.matrix[[5],[1]] = self.variables[1][1]    
            self.matrix[[5],[2]] = self.variables[2][1]
            self.matrix[[5],[3]] = self.variables[3][1]
            self.matrix[[5],[4]] = self.variables[4][0]
            self.matrix[[5],[5]] = self.variables[5][1]
            self.matrix[[5],[6]] = self.variables[6][1]
            self.matrix[[5],[7]] = self.variables[7][0]
            self.matrix[[5],[8]] = self.variables[8][1]
            self.matrix[[5],[9]] = self.variables[9][0]
            self.matrix[[5],[10]] = self.variables[10][0]
            # Row 7 :   2,1,2     2,1,1   2,2,1   2,1
            self.matrix[[6],[0]] = self.variables[0][1]
            self.matrix[[6],[1]] = self.variables[1][0]    
            self.matrix[[6],[2]] = self.variables[2][1]
            self.matrix[[6],[3]] = self.variables[3][1]
            self.matrix[[6],[4]] = self.variables[4][0]
            self.matrix[[6],[5]] = self.variables[5][0]
            self.matrix[[6],[6]] = self.variables[6][1]
            self.matrix[[6],[7]] = self.variables[7][1]
            self.matrix[[6],[8]] = self.variables[8][0]
            self.matrix[[6],[9]] = self.variables[9][1]
            self.matrix[[6],[10]] = self.variables[10][0]
            # Row 8 :   2,1,2     1,2,2   2,1,1   1,2
            self.matrix[[7],[0]] = self.variables[0][1]
            self.matrix[[7],[1]] = self.variables[1][0]    
            self.matrix[[7],[2]] = self.variables[2][1]
            self.matrix[[7],[3]] = self.variables[3][0]
            self.matrix[[7],[4]] = self.variables[4][1]
            self.matrix[[7],[5]] = self.variables[5][1]
            self.matrix[[7],[6]] = self.variables[6][1]
            self.matrix[[7],[7]] = self.variables[7][0]
            self.matrix[[7],[8]] = self.variables[8][0]
            self.matrix[[7],[9]] = self.variables[9][0]
            self.matrix[[7],[10]] = self.variables[10][1]
            # Row 9 :   2,1,1     2,2,2   1,2,2   1,1
            self.matrix[[8],[0]] = self.variables[0][1]
            self.matrix[[8],[1]] = self.variables[1][0]    
            self.matrix[[8],[2]] = self.variables[2][0]
            self.matrix[[8],[3]] = self.variables[3][1]
            self.matrix[[8],[4]] = self.variables[4][1]
            self.matrix[[8],[5]] = self.variables[5][1]
            self.matrix[[8],[6]] = self.variables[6][0]
            self.matrix[[8],[7]] = self.variables[7][1]
            self.matrix[[8],[8]] = self.variables[8][1]
            self.matrix[[8],[9]] = self.variables[9][0]
            self.matrix[[8],[10]] = self.variables[10][0]
            # Row 10 :   2,2,2     1,1,1   1,2,2   1,2
            self.matrix[[9],[0]] = self.variables[0][1]
            self.matrix[[9],[1]] = self.variables[1][1]    
            self.matrix[[9],[2]] = self.variables[2][1]
            self.matrix[[9],[3]] = self.variables[3][0]
            self.matrix[[9],[4]] = self.variables[4][0]
            self.matrix[[9],[5]] = self.variables[5][0]
            self.matrix[[9],[6]] = self.variables[6][0]
            self.matrix[[9],[7]] = self.variables[7][1]
            self.matrix[[9],[8]] = self.variables[8][1]
            self.matrix[[9],[9]] = self.variables[9][0]
            self.matrix[[9],[10]] = self.variables[10][1]
            # Row 11 :   2,2,1     2,1,2   1,1,1   2,2
            self.matrix[[10],[0]] = self.variables[0][1]
            self.matrix[[10],[1]] = self.variables[1][1]    
            self.matrix[[10],[2]] = self.variables[2][0]
            self.matrix[[10],[3]] = self.variables[3][1]
            self.matrix[[10],[4]] = self.variables[4][0]
            self.matrix[[10],[5]] = self.variables[5][1]
            self.matrix[[10],[6]] = self.variables[6][0]
            self.matrix[[10],[7]] = self.variables[7][0]
            self.matrix[[10],[8]] = self.variables[8][0]
            self.matrix[[10],[9]] = self.variables[9][1]
            self.matrix[[10],[10]] = self.variables[10][1]
            # Row 12 :   2,2,1     1,2,1   2,1,2   2,1
            self.matrix[[11],[0]] = self.variables[0][1]
            self.matrix[[11],[1]] = self.variables[1][1]    
            self.matrix[[11],[2]] = self.variables[2][0]
            self.matrix[[11],[3]] = self.variables[3][0]
            self.matrix[[11],[4]] = self.variables[4][1]
            self.matrix[[11],[5]] = self.variables[5][0]
            self.matrix[[11],[6]] = self.variables[6][1]
            self.matrix[[11],[7]] = self.variables[7][0]
            self.matrix[[11],[8]] = self.variables[8][1]
            self.matrix[[11],[9]] = self.variables[9][1]
            self.matrix[[11],[10]] = self.variables[10][0]
            self.matrix=self.matrix.tolist()
            return self.matrix
                                 
            
    def design_L16b(self):
            # L16b (1): https://www.york.ac.uk/depts/maths/tables/l16b.htm
            # L16b (2): https://www.itl.nist.gov/div898/software/dataplot/dex/L16B.DAT 
            self.matrix = np.zeros((16,5))
            # Row 1 : 1,1,1,1,1
            self.matrix[[0],[0]] = self.variables[0][0]
            self.matrix[[0],[1]] = self.variables[1][0]    
            self.matrix[[0],[2]] = self.variables[2][0]
            self.matrix[[0],[3]] = self.variables[3][0]
            self.matrix[[0],[4]] = self.variables[4][0]
            # Row 2 : 1,2,2,2,2
            self.matrix[[1],[0]] = self.variables[0][0]
            self.matrix[[1],[1]] = self.variables[1][1]    
            self.matrix[[1],[2]] = self.variables[2][1]
            self.matrix[[1],[3]] = self.variables[3][1]
            self.matrix[[1],[4]] = self.variables[4][1]
            # Row 3 : 1,3,3,3,3
            self.matrix[[2],[0]] = self.variables[0][0]
            self.matrix[[2],[1]] = self.variables[1][2]    
            self.matrix[[2],[2]] = self.variables[2][2]
            self.matrix[[2],[3]] = self.variables[3][2]
            self.matrix[[2],[4]] = self.variables[4][2]
            # Row 4 : 1,4,4,4,4
            self.matrix[[3],[0]] = self.variables[0][0]
            self.matrix[[3],[1]] = self.variables[1][3]    
            self.matrix[[3],[2]] = self.variables[2][3]
            self.matrix[[3],[3]] = self.variables[3][3]
            self.matrix[[3],[4]] = self.variables[4][3]
            # Row 5 : 2,1,2,3,4
            self.matrix[[4],[0]] = self.variables[0][1]
            self.matrix[[4],[1]] = self.variables[1][0]    
            self.matrix[[4],[2]] = self.variables[2][1]
            self.matrix[[4],[3]] = self.variables[3][2]
            self.matrix[[4],[4]] = self.variables[4][3]
            # Row 6 : 2,2,1,4,3
            self.matrix[[5],[0]] = self.variables[0][1]
            self.matrix[[5],[1]] = self.variables[1][1]    
            self.matrix[[5],[2]] = self.variables[2][0]
            self.matrix[[5],[3]] = self.variables[3][3]
            self.matrix[[5],[4]] = self.variables[4][2]
            # Row 7 : 2,3,4,1,2
            self.matrix[[6],[0]] = self.variables[0][1]
            self.matrix[[6],[1]] = self.variables[1][2]    
            self.matrix[[6],[2]] = self.variables[2][3]
            self.matrix[[6],[3]] = self.variables[3][0]
            self.matrix[[6],[4]] = self.variables[4][1]
            # Row 8 : 2,4,3,2,1
            self.matrix[[7],[0]] = self.variables[0][1]
            self.matrix[[7],[1]] = self.variables[1][3]    
            self.matrix[[7],[2]] = self.variables[2][2]
            self.matrix[[7],[3]] = self.variables[3][1]
            self.matrix[[7],[4]] = self.variables[4][0]
            # Row 9 : 3,1,3,4,2
            self.matrix[[8],[0]] = self.variables[0][2]
            self.matrix[[8],[1]] = self.variables[1][0]    
            self.matrix[[8],[2]] = self.variables[2][2]
            self.matrix[[8],[3]] = self.variables[3][3]
            self.matrix[[8],[4]] = self.variables[4][1]
            # Row 10 : 3,2,4,3,1
            self.matrix[[9],[0]] = self.variables[0][2]
            self.matrix[[9],[1]] = self.variables[1][1]    
            self.matrix[[9],[2]] = self.variables[2][3]
            self.matrix[[9],[3]] = self.variables[3][2]
            self.matrix[[9],[4]] = self.variables[4][0]
            # Row 11 : 3,3,1,2,4
            self.matrix[[10],[0]] = self.variables[0][2]
            self.matrix[[10],[1]] = self.variables[1][2]    
            self.matrix[[10],[2]] = self.variables[2][0]
            self.matrix[[10],[3]] = self.variables[3][1]
            self.matrix[[10],[4]] = self.variables[4][3]
            # Row 12 : 3,4,2,1,3
            self.matrix[[11],[0]] = self.variables[0][2]
            self.matrix[[11],[1]] = self.variables[1][3]    
            self.matrix[[11],[2]] = self.variables[2][1]
            self.matrix[[11],[3]] = self.variables[3][0]
            self.matrix[[11],[4]] = self.variables[4][2]
            # Row 13 : 4,1,4,2,3
            self.matrix[[12],[0]] = self.variables[0][3]
            self.matrix[[12],[1]] = self.variables[1][0]    
            self.matrix[[12],[2]] = self.variables[2][3]
            self.matrix[[12],[3]] = self.variables[3][1]
            self.matrix[[12],[4]] = self.variables[4][2]
            # Row 14 : 4,2,3,1,4
            self.matrix[[13],[0]] = self.variables[0][3]
            self.matrix[[13],[1]] = self.variables[1][1]    
            self.matrix[[13],[2]] = self.variables[2][2]
            self.matrix[[13],[3]] = self.variables[3][0]
            self.matrix[[13],[4]] = self.variables[4][3]
            # Row 15 : 4,3,2,4,1
            self.matrix[[14],[0]] = self.variables[0][3]
            self.matrix[[14],[1]] = self.variables[1][2]    
            self.matrix[[14],[2]] = self.variables[2][1]
            self.matrix[[14],[3]] = self.variables[3][3]
            self.matrix[[14],[4]] = self.variables[4][0]
            # Row 16 : 4,4,1,3,2
            self.matrix[[15],[0]] = self.variables[0][3]
            self.matrix[[15],[1]] = self.variables[1][3]    
            self.matrix[[15],[2]] = self.variables[2][0]
            self.matrix[[15],[3]] = self.variables[3][2]
            self.matrix[[15],[4]] = self.variables[4][1]
            self.matrix=self.matrix.tolist()
            return self.matrix
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