'''
Created on 2018/5/20

@author: Lulumi5129

    This is Localization System L4M, L4M_Comb module,
    Use node class implement Localization System to 
    find the estimate Coordinate(or comb)
    
    Use :
        distance : Euclidean_distance
        channel model : LogDistanceModel
'''
from ..Node.node import Node
from .Localization import Localization
import yaml
import numpy as np
import math
from itertools import combinations
from .L3M_System import L3M
        
class L4M(L3M):
    """
    L4M System main class
    """
    
    def __init__(self, targetCoordinateList=None, anchorCoordinateList=None, RSSIDict=None):
        super().__init__(targetCoordinateList, anchorCoordinateList, RSSIDict)
        self.L4M_Coordinate()
        self.L4M_Comb_Coordinate()
        
    
    def L4M_Coordinate(self):
        #get estimate Coordinate
        self.L3M_CoordinateDict = {}
        for target in self.targetList :
            RSSIList = self.RSSIDict[target.nodeName]
            noiseList = self.noiseDict.get(target.nodeName, None)
            theta = self.L4M_Alg(self.anchorList, RSSIList, noiseList)
            coordinate = np.transpose(theta).tolist()[0]
            
            if self.Localization_Dimensions == '2D' :
                self.L3M_CoordinateDict[target.nodeName] = Node(x=coordinate[0], y=coordinate[1], dimensions='2D', headerName='L3M', ID=0)
            else :
                self.L3M_CoordinateDict[target.nodeName] = Node(x=coordinate[0], y=coordinate[1], z=coordinate[2], dimensions='3D', headerName='L3M', ID=0)
    
    def L4M_Comb_Coordinate(self):
        #get anchor comb List
        self.anchorCombDict = {}
        anchorCombList = list(combinations(self.anchorList, self.combValue))
        
        for Comb in range(len(anchorCombList)) :
            self.anchorCombDict['Comb_' + str(Comb+1)] = anchorCombList[Comb]
        
        #get estimate Coordinate(comb)
        self.L3M_Comb_CoordinateDict = {}
        for target in self.targetList :
            RSSIList = self.RSSIDict[target.nodeName]
            noiseList = self.noiseDict.get(target.nodeName, None)
            coordinateList = []
            for (Comb, index) in zip(self.anchorCombDict, range(len(self.anchorCombDict))) :
                anchorCombList = self.anchorCombDict[Comb]
                RSSI = [RSSIList[anchorCombList[i].ID] for i in range(len(anchorCombList))]
                if noiseList is not None : 
                    noise = [noiseList[anchorCombList[i].ID] for i in range(len(anchorCombList))]
                else :
                    noise = None
                
                theta = self.L4M_Alg(anchorCombList, RSSI, noise)
                coordinate = np.transpose(theta).tolist()[0]
                
                if self.Localization_Dimensions == '2D' :
                    coordinateList.append(Node(x=coordinate[0], y=coordinate[1], dimensions='2D', headerName=target.nodeName + '_L3M_Comb', ID=index))
                else :
                    coordinateList.append(Node(x=coordinate[0], y=coordinate[1], z=coordinate[2], dimensions='3D', headerName=target.nodeName + '_L3M_Comb', ID=index))
                    
            self.L3M_Comb_CoordinateDict[target.nodeName] = coordinateList
        
    @classmethod
    def L4M_Alg(cls, anchorList, RSSIList, noiseList=None):
        #
        #            |-2*x1 -2*y1 1 |                | 10**((2/n)*(Z0 - Z1)) - R1 |        | x |
        #matrix A =  |-2*x2 -2*y2 1 |  matrix b =    | 10**((2/n)*(Z0 - Z2)) - R2 | theta =| y |
        #            |  .     .   . |                |           .                |        | R |
        #            |-2*xn -2*yn 1 |                | 10**((2/n)*(Z0 - Zn)) - Rn |
        #
        #   Z0=PLog_distance_model_P_Zero, n=Log_distance_model_n
        #   Zn=Pt(dBm) + Pr(dBm), and Pr is RSSI, Pt=Log_distance_model_Pt
        #   Rn = estimate distance between anchor_i and target
        #   x and y is target estimate coordinate, R is target estimate distance
        #   theta = matrix A(pseudo inverse) * matrix b
        #   matrix A(pseudo inverse)= ((A(transpose)*A)**(-1)) * A(transpose)
        #
        #
        def Ri(anchorNode):
            addsum = 0
            for i in range(len(anchorNode)) : addsum += math.pow(anchorNode.coordinate[i], 2)
            return addsum
        
        matrix_A=[]
        matrix_b=[]
        
        if noiseList is None : noiseList = [0 for i in range(len(RSSIList))]
        
        # create matrix A and matrix b
        for (anchor, RSSI, noise) in zip(anchorList, RSSIList, noiseList) :
            if anchor.ID > 0 :
                #create matrix A
                A_col=[-2*(anchorList[0].coordinate[i] - anchor.coordinate[i]) for i in range(len(anchor))]
                
                #create matrix b
                b_col=anchorList[0].getChannelDistance(RSSIList[0], noiseList[0])**2 - anchor.getChannelDistance(RSSI, noise)**2 - (Ri(anchorList[0]) - Ri(anchor))
                
                matrix_A.append(A_col)
                matrix_b.append([b_col])
                
        np_matrix_A = np.array(matrix_A)
        np_matrix_b = np.array(matrix_b)
        np_matrix_A_pinv = np.linalg.pinv(np_matrix_A)
        theta = np.dot(np_matrix_A_pinv, np_matrix_b)
        
        return theta
        
    
        
        
        
        