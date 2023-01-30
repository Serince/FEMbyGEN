import numpy as np

def design_L4(parameter):
        variables=parameter
        # L4: https://www.itl.nist.gov/div898/software/dataplot/dex/L4.DATşğ
        
        matrix = np.zeros((4,3))
        # Row 1
        matrix[0,0] = variables[0][0]
        matrix[0,1] = variables[1][0]    
        matrix[0,2] = variables[2][0]
        # Row 2
        matrix[1,0] = variables[0][0]
        matrix[1,1] = variables[1][1]    
        matrix[1,2] = variables[2][1]
        # Row 3
        matrix[2,0] = variables[0][1]
        matrix[2,1] = variables[1][0]    
        matrix[2,2] = variables[2][1]
        # Row 4
        matrix[3,0] = variables[0][1]
        matrix[3,1] = variables[1][1]    
        matrix[3,2] = variables[2][0]
        matrix=matrix.tolist()    
        return matrix
        
       
    
def design_L9(parameter):
        variables=parameter
        # L9: https://www.itl.nist.gov/div898/software/dataplot/dex/L9.DAT
        matrix = np.zeros((9,4))
        # Row 1 : 1,1,1,1
        matrix[0,0] = variables[0][0]
        matrix[0,1] = variables[1][0]    
        matrix[0,2] = variables[2][0]
        matrix[0,3] = variables[3][0]
        # Row 2 : 1,2,2,2
        matrix[1,0] = variables[0][0]
        matrix[1,1] = variables[1][1]    
        matrix[1,2] = variables[2][1]
        matrix[1,3] = variables[3][1]
        # Row 3 : 1,3,3,3
        matrix[2,0] = variables[0][0]
        matrix[2,1] = variables[1][2]    
        matrix[2,2] = variables[2][2]
        matrix[2,3] = variables[3][2]
        # Row 4 : 2,1,2,3
        matrix[3,0] = variables[0][1]
        matrix[3,1] = variables[1][0]    
        matrix[3,2] = variables[2][1]
        matrix[3,3] = variables[3][2]
        # Row 5 : 2,2,3,1
        matrix[4,0] = variables[0][1]
        matrix[4,1] = variables[1][1]    
        matrix[4,2] = variables[2][2]
        matrix[4,3] = variables[3][0]
        # Row 6 : 2,3,1,2
        matrix[5,0] = variables[0][1]
        matrix[5,1] = variables[1][2]    
        matrix[5,2] = variables[2][0]
        matrix[5,3] = variables[3][1]
        # Row 7 : 3,1,3,2
        matrix[6,0] = variables[0][2]
        matrix[6,1] = variables[1][0]    
        matrix[6,2] = variables[2][2]
        matrix[6,3] = variables[3][1]
       # Row 8 : 3,2,1,3
        matrix[7,0] = variables[0][2]
        matrix[7,1] = variables[1][1]    
        matrix[7,2] = variables[2][0]
        matrix[7,3] = variables[3][2]
        # Row 9 : 3,3,2,1
        matrix[8,0] = variables[0][2]
        matrix[8,1] = variables[1][2]    
        matrix[8,2] = variables[2][1]
        matrix[8,3] = variables[3][0]
        matrix=matrix.tolist()
        return matrix
        
        
def design_L8(parameter):
        variables=parameter
        # L8: https://www.itl.nist.gov/div898/software/dataplot/dex/L8.DAT
        matrix = np.zeros((8,7))
        # Row 1 : 1,1,1,1,1,1,1
        matrix[0,0] = variables[0][0]
        matrix[0,1] = variables[1][0]    
        matrix[0,2] = variables[2][0]
        matrix[0,3] = variables[3][0]
        matrix[0,4] = variables[4][0]
        matrix[0,5] = variables[5][0]
        matrix[0,6] = variables[6][0]
        # Row 2 : 1,1,1,2,2,2,2
        matrix[1,0] = variables[0][0]
        matrix[1,1] = variables[1][0]    
        matrix[1,2] = variables[2][0]
        matrix[1,3] = variables[3][1]
        matrix[1,4] = variables[4][1]
        matrix[1,5] = variables[5][1]
        matrix[1,6] = variables[6][1]
        # Row 3 : 1,2,2,1,1,2,2
        matrix[2,0] = variables[0][0]
        matrix[2,1] = variables[1][1]    
        matrix[2,2] = variables[2][1]
        matrix[2,3] = variables[3][0]
        matrix[2,4] = variables[4][0]
        matrix[2,5] = variables[5][1]
        matrix[2,6] = variables[6][1]
        # Row 4 : 1,2,2,2,2,1,1
        matrix[3,0] = variables[0][0]
        matrix[3,1] = variables[1][1]    
        matrix[3,2] = variables[2][1]
        matrix[3,3] = variables[3][1]
        matrix[3,4] = variables[4][1]
        matrix[3,5] = variables[5][0]
        matrix[3,6] = variables[6][0]
        # Row 5 : 2,1,2,1,2,1,2
        matrix[4,0] = variables[0][1]
        matrix[4,1] = variables[1][0]    
        matrix[4,2] = variables[2][1]
        matrix[4,3] = variables[3][0]
        matrix[4,4] = variables[4][1]
        matrix[4,5] = variables[5][0]
        matrix[4,6] = variables[6][1]
        # Row 6 : 2,1,2,2,1,2,1
        matrix[5,0] = variables[0][1]
        matrix[5,1] = variables[1][0]    
        matrix[5,2] = variables[2][1]
        matrix[5,3] = variables[3][1]
        matrix[5,4] = variables[4][0]
        matrix[5,5] = variables[5][1]
        matrix[5,6] = variables[6][0]
        # Row 7 : 2,2,1,1,2,2,1
        matrix[6,0] = variables[0][1]
        matrix[6,1] = variables[1][1]    
        matrix[6,2] = variables[2][0]
        matrix[6,3] = variables[3][0]
        matrix[6,4] = variables[4][1]
        matrix[6,5] = variables[5][1]
        matrix[6,6] = variables[6][0]
       # Row 8 : 2,2,1,2,1,1,2
        matrix[7,0] = variables[0][1]
        matrix[7,1] = variables[1][1]    
        matrix[7,2] = variables[2][0]
        matrix[7,3] = variables[3][1]
        matrix[7,4] = variables[4][0]
        matrix[7,5] = variables[5][0]
        matrix[7,6] = variables[6][1]
        matrix=matrix.tolist()
        return matrix
        
def design_L12(parameter):
        variables=parameter
        # L12: https://www.york.ac.uk/depts/maths/tables/l12.gif
        matrix = np.zeros((12,11))
        # Row 1 :   1,1,1     1,1,1   1,1,1   1,1
        matrix[0,0] = variables[0][0]
        matrix[0,1] = variables[1][0]
        matrix[0,2] = variables[2][0]
        matrix[0,3] = variables[3][0]
        matrix[0,4] = variables[4][0]
        matrix[0,5] = variables[5][0]
        matrix[0,6] = variables[6][0]
        matrix[0,7] = variables[7][0]
        matrix[0,8] = variables[8][0]
        matrix[0,9] = variables[9][0]
        matrix[0,10] = variables[10][0]
        # Row 2 :   1,1,1     1,1,2   2,2,2   2,2
        matrix[1,0] = variables[0][0]
        matrix[1,1] = variables[1][0]
        matrix[1,2] = variables[2][0]
        matrix[1,3] = variables[3][0]
        matrix[1,4] = variables[4][0]
        matrix[1,5] = variables[5][1]
        matrix[1,6] = variables[6][1]
        matrix[1,7] = variables[7][1]
        matrix[1,8] = variables[8][1]
        matrix[1,9] = variables[9][1]
        matrix[1,10] = variables[10][1]
        # Row 3 :   1,1,2     2,2,1   1,1,2   2,2
        matrix[2,0] = variables[0][0]
        matrix[2,1] = variables[1][0]
        matrix[2,2] = variables[2][1]
        matrix[2,3] = variables[3][1]
        matrix[2,4] = variables[4][1]
        matrix[2,5] = variables[5][0]
        matrix[2,6] = variables[6][0]
        matrix[2,7] = variables[7][0]
        matrix[2,8] = variables[8][1]
        matrix[2,9] = variables[9][1]
        matrix[2,10] = variables[10][1]
        # Row 4 :   1,2,1     2,2,1   2,2,1   1,2
        matrix[3,0] = variables[0][0]
        matrix[3,1] = variables[1][1]    
        matrix[3,2] = variables[2][0]
        matrix[3,3] = variables[3][1]
        matrix[3,4] = variables[4][1]
        matrix[3,5] = variables[5][0]
        matrix[3,6] = variables[6][1]
        matrix[3,7] = variables[7][1]
        matrix[3,8] = variables[8][0]
        matrix[3,9] = variables[9][0]
        matrix[3,10] = variables[10][1]
        # Row 5 :   1,2,2     1,2,2   1,2,1   2,1
        matrix[4,0] = variables[0][0]
        matrix[4,1] = variables[1][1]    
        matrix[4,2] = variables[2][1]
        matrix[4,3] = variables[3][0]
        matrix[4,4] = variables[4][1]
        matrix[4,5] = variables[5][1]
        matrix[4,6] = variables[6][0]
        matrix[4,7] = variables[7][1]
        matrix[4,8] = variables[8][0]
        matrix[4,9] = variables[9][1]
        matrix[4,10] = variables[10][0]
        # Row 6 :   1,2,2     2,1,2   2,1,2   1,1
        matrix[5,0] = variables[0][0]
        matrix[5,1] = variables[1][1]    
        matrix[5,2] = variables[2][1]
        matrix[5,3] = variables[3][1]
        matrix[5,4] = variables[4][0]
        matrix[5,5] = variables[5][1]
        matrix[5,6] = variables[6][1]
        matrix[5,7] = variables[7][0]
        matrix[5,8] = variables[8][1]
        matrix[5,9] = variables[9][0]
        matrix[5,10] = variables[10][0]
       # Row 7 :   2,1,2     2,1,1   2,2,1   2,1
        matrix[6,0] = variables[0][1]
        matrix[6,1] = variables[1][0]    
        matrix[6,2] = variables[2][1]
        matrix[6,3] = variables[3][1]
        matrix[6,4] = variables[4][0]
        matrix[6,5] = variables[5][0]
        matrix[6,6] = variables[6][1]
        matrix[6,7] = variables[7][1]
        matrix[6,8] = variables[8][0]
        matrix[6,9] = variables[9][1]
        matrix[6,10] = variables[10][0]
        # Row 8 :   2,1,2     1,2,2   2,1,1   1,2
        matrix[7,0] = variables[0][1]
        matrix[7,1] = variables[1][0]    
        matrix[7,2] = variables[2][1]
        matrix[7,3] = variables[3][0]
        matrix[7,4] = variables[4][1]
        matrix[7,5] = variables[5][1]
        matrix[7,6] = variables[6][1]
        matrix[7,7] = variables[7][0]
        matrix[7,8] = variables[8][0]
        matrix[7,9] = variables[9][0]
        matrix[7,10] = variables[10][1]
        # Row 9 :   2,1,1     2,2,2   1,2,2   1,1
        matrix[8,0] = variables[0][1]
        matrix[8,1] = variables[1][0]    
        matrix[8,2] = variables[2][0]
        matrix[8,3] = variables[3][1]
        matrix[8,4] = variables[4][1]
        matrix[8,5] = variables[5][1]
        matrix[8,6] = variables[6][0]
        matrix[8,7] = variables[7][1]
        matrix[8,8] = variables[8][1]
        matrix[8,9] = variables[9][0]
        matrix[8,10] = variables[10][0]
        # Row 10 :   2,2,2     1,1,1   1,2,2   1,2
        matrix[9,0] = variables[0][1]
        matrix[9,1] = variables[1][1]    
        matrix[9,2] = variables[2][1]
        matrix[9,3] = variables[3][0]
        matrix[9,4] = variables[4][0]
        matrix[9,5] = variables[5][0]
        matrix[9,6] = variables[6][0]
        matrix[9,7] = variables[7][1]
        matrix[9,8] = variables[8][1]
        matrix[9,9] = variables[9][0]
        matrix[9,10] = variables[10][1]
        # Row 11 :   2,2,1     2,1,2   1,1,1   2,2
        matrix[10,0] = variables[0][1]
        matrix[10,1] = variables[1][1]    
        matrix[10,2] = variables[2][0]
        matrix[10,3] = variables[3][1]
        matrix[10,4] = variables[4][0]
        matrix[10,5] = variables[5][1]
        matrix[10,6] = variables[6][0]
        matrix[10,7] = variables[7][0]
        matrix[10,8] = variables[8][0]
        matrix[10,9] = variables[9][1]
        matrix[10,10] = variables[10][1]
        # Row 12 :   2,2,1     1,2,1   2,1,2   2,1
        matrix[11,0] = variables[0][1]
        matrix[11,1] = variables[1][1]    
        matrix[11,2] = variables[2][0]
        matrix[11,3] = variables[3][0]
        matrix[11,4] = variables[4][1]
        matrix[11,5] = variables[5][0]
        matrix[11,6] = variables[6][1]
        matrix[11,7] = variables[7][0]
        matrix[11,8] = variables[8][1]
        matrix[11,9] = variables[9][1]
        matrix[11,10] = variables[10][0]
        matrix=matrix.tolist()
        return matrix
def design_L16b(parameter):
        variables=parameter
        # L16b (1): https://www.york.ac.uk/depts/maths/tables/l16b.htm
        # L16b (2): https://www.itl.nist.gov/div898/software/dataplot/dex/L16B.DAT 
        matrix = np.zeros((16,5))
        # Row 1 : 1,1,1,1,1
        matrix[0,0] = variables[0][0]
        matrix[0,1] = variables[1][0]    
        matrix[0,2] = variables[2][0]
        matrix[0,3] = variables[3][0]
        matrix[0,4] = variables[4][0]
        # Row 2 : 1,2,2,2,2
        matrix[1,0] = variables[0][0]
        matrix[1,1] = variables[1][1]    
        matrix[1,2] = variables[2][1]
        matrix[1,3] = variables[3][1]
        matrix[1,4] = variables[4][1]
        # Row 3 : 1,3,3,3,3
        matrix[2,0] = variables[0][0]
        matrix[2,1] = variables[1][2]    
        matrix[2,2] = variables[2][2]
        matrix[2,3] = variables[3][2]
        matrix[2,4] = variables[4][2]
        # Row 4 : 1,4,4,4,4
        matrix[3,0] = variables[0][0]
        matrix[3,1] = variables[1][3]    
        matrix[3,2] = variables[2][3]
        matrix[3,3] = variables[3][3]
        matrix[3,4] = variables[4][3]
        # Row 5 : 2,1,2,3,4
        matrix[4,0] = variables[0][1]
        matrix[4,1] = variables[1][0]    
        matrix[4,2] = variables[2][1]
        matrix[4,3] = variables[3][2]
        matrix[4,4] = variables[4][3]
        # Row 6 : 2,2,1,4,3
        matrix[5,0] = variables[0][1]
        matrix[5,1] = variables[1][1]    
        matrix[5,2] = variables[2][0]
        matrix[5,3] = variables[3][3]
        matrix[5,4] = variables[4][2]
        # Row 7 : 2,3,4,1,2
        matrix[6,0] = variables[0][1]
        matrix[6,1] = variables[1][2]    
        matrix[6,2] = variables[2][3]
        matrix[6,3] = variables[3][0]
        matrix[6,4] = variables[4][1]
        # Row 8 : 2,4,3,2,1
        matrix[7,0] = variables[0][1]
        matrix[7,1] = variables[1][3]    
        matrix[7,2] = variables[2][2]
        matrix[7,3] = variables[3][1]
        matrix[7,4] = variables[4][0]
        # Row 9 : 3,1,3,4,2
        matrix[8,0] = variables[0][2]
        matrix[8,1] = variables[1][0]    
        matrix[8,2] = variables[2][2]
        matrix[8,3] = variables[3][3]
        matrix[8,4] = variables[4][1]
        # Row 10 : 3,2,4,3,1
        matrix[9,0] = variables[0][2]
        matrix[9,1] = variables[1][1]    
        matrix[9,2] = variables[2][3]
        matrix[9,3] = variables[3][2]
        matrix[9,4] = variables[4][0]
        # Row 11 : 3,3,1,2,4
        matrix[10,0] = variables[0][2]
        matrix[10,1] = variables[1][2]    
        matrix[10,2] = variables[2][0]
        matrix[10,3] = variables[3][1]
        matrix[10,4] = variables[4][3]
        # Row 12 : 3,4,2,1,3
        matrix[11,0] = variables[0][2]
        matrix[11,1] = variables[1][3]    
        matrix[11,2] = variables[2][1]
        matrix[11,3] = variables[3][0]
        matrix[11,4] = variables[4][2]
        # Row 13 : 4,1,4,2,3
        matrix[12,0] = variables[0][3]
        matrix[12,1] = variables[1][0]    
        matrix[12,2] = variables[2][3]
        matrix[12,3] = variables[3][1]
        matrix[12,4] = variables[4][2]
        # Row 14 : 4,2,3,1,4
        matrix[13,0] = variables[0][3]
        matrix[13,1] = variables[1][1]    
        matrix[13,2] = variables[2][2]
        matrix[13,3] = variables[3][0]
        matrix[13,4] = variables[4][3]
        # Row 15 : 4,3,2,4,1
        matrix[14,0] = variables[0][3]
        matrix[14,1] = variables[1][2]    
        matrix[14,2] = variables[2][1]
        matrix[14,3] = variables[3][3]
        matrix[14,4] = variables[4][0]
        # Row 16 : 4,4,1,3,2
        matrix[15,0] = variables[0][3]
        matrix[15,1] = variables[1][3]    
        matrix[15,2] = variables[2][0]
        matrix[15,3] = variables[3][2]
        matrix[15,4] = variables[4][1]
        matrix=matrix.tolist()
        return matrix
                                         

    



