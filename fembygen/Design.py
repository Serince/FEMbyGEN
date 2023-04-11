import numpy as np
import pyDOE2 as pydoe2
import itertools


def fullfact(A):
    numgenerations = list(itertools.product(*A))
    return numgenerations


def designpb(A):
    pb = pydoe2.pbdesign(len(A))
    row, column = pb.shape
    for c in range(column):

        for r in range(row):
            if pb[r, c] == -1:
                pb[r, c] = A[c][0]
            elif pb[r, c] == 1:
                pb[r, c] = A[c][-1]

    pb = pb.tolist()
    return pb


def designcentalcom(A):
    cc = pydoe2.ccdesign(len(A), alpha="r")
    row, column = cc.shape
    for c in range(column):

        for r in range(row):
            if cc[r, c] == -1:
                cc[r, c] = A[c][0]
            elif cc[r, c] == 0:
                cc[r, c] = (A[c][0]+A[c][-1])/2
            elif cc[r, c] == 1:
                cc[r, c] = A[c][-1]
            else:

                if cc[r, c] < 0:
                    cc[r, c] = (cc[r, c] * (A[c][1] - A[c][0])) + A[c][1]
                elif cc[r, c] > 0:
                    cc[r, c] = (cc[r, c] * (A[c][1] - A[c][0])) + A[c][1]
    cc = cc.tolist()
    return cc


def designboxBen(A):
    bb = pydoe2.bbdesign(len(A))
    row, column = bb.shape
    for c in range(column):

        for r in range(row):

            if bb[r, c] == -1:
                bb[r, c] = A[c][0]
            elif bb[r, c] == 0:
                bb[r, c] = (A[c][0]+A[c][-1])/2
            elif bb[r, c] == 1:
                bb[r, c] = A[c][-1]

            
    
        

    bb = bb.tolist()
    return bb

        

       
 

     
     
