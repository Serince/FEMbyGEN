import numpy as np
from fembygen.design.pydoe2 import doe_lhs, doe_box_behnken, doe_composite, doe_plackett_burman
import itertools

def QT_TRANSLATE_NOOP(context, text):
    return text

def fullfact(A):
    numgenerations = list(itertools.product(*A))
    return numgenerations


def designlhc(A,samples,criterion, iterations, random_state, correlation_matrix):
    lhc = doe_lhs.lhs(len(A), samples, criterion,iterations, random_state, correlation_matrix)
    row, column = lhc.shape
    for i, param in enumerate(A):
        diff = param[-1]-param[0]
        lhc[:, i] = diff*lhc[:, i]+param[0]

    lhc = lhc.tolist()
    return lhc


def designpb(A):
    pb = doe_plackett_burman.pbdesign(len(A))
    row, column = pb.shape
    for c in range(column):

        for r in range(row):
            if pb[r, c] == -1:
                pb[r, c] = A[c][0]
            elif pb[r, c] == 1:
                pb[r, c] = A[c][-1]

    pb = pb.tolist()
    return pb


def designcentalcom(A, center, alpha, face):
    cc = doe_composite.ccdesign(len(A), center, alpha, face)
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


def designboxBen(A, center=None):
    bb = doe_box_behnken.bbdesign(len(A), center)
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
