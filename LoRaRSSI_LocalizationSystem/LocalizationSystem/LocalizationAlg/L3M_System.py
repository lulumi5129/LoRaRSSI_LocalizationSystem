'''
Created on 2018/5/20

@author: Lulumi5129

    This is Localization System L3M, L3M_Comb module,
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

class L3M_Config():
    """
    node configuration class
    """
    # class variables
    sectionName='L3M'
    options={'combValue': (int,True)}
    
    #constructor
    def __init__(self, inFileName):
        #read YAML config and get EV3 section
        infile=open(inFileName,'r')
        self.ymlcfg=yaml.load(infile)
        infile.close()
        
        eccfg=self.ymlcfg.get(self.sectionName,None)
        if eccfg is None: raise Exception('Missing {} section in cfg file'.format(self.sectionName))
         
        #iterate over options
        for opt in self.options:
            if opt in eccfg:
                optval=eccfg[opt]
 
                #verify parameter type
                if type(optval) != self.options[opt][0]:
                    raise Exception('Parameter "{}" has wrong type'.format(opt))
                 
                #create attributes on the fly
                setattr(self,opt,optval)
            else:
                if self.options[opt][1]:
                    raise Exception('Missing mandatory parameter "{}"'.format(opt))
                else:
                    setattr(self,opt,None)
                    
        self.setL3MSys()
        
    def setL3MSys(self):
        L3M.combValue = self.combValue
        
    def get_class(self, kls):
        parts = kls.split('.')
        module = ".".join(parts[:-1])
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)            
        return m
    
    #string representation for class data    
    def __str__(self):
        return str(yaml.dump(self.__dict__))
        
class L3M(Localization):
    """
    L3M System main class
    """
    combValue = None
    
    def __init__(self, targetCoordinateList=None, anchorCoordinateList=None, RSSIDict=None):
        super().__init__(targetCoordinateList, anchorCoordinateList, RSSIDict)
        self.L3M_Coordinate()
        self.L3M_Comb_Coordinate()
        
    
    def L3M_Coordinate(self):
        #get estimate Coordinate
        self.L3M_CoordinateDict = {}
        for target in self.targetList :
            RSSIList = self.RSSIDict[target.nodeName]
            noiseList = self.noiseDict.get(target.nodeName, None)
            theta = self.L3M_Alg(self.anchorList, RSSIList, noiseList)
            coordinate = np.transpose(theta).tolist()[0][:-1]
            
            if self.Localization_Dimensions == '2D' :
                self.L3M_CoordinateDict[target.nodeName] = Node(x=coordinate[0], y=coordinate[1], dimensions='2D', headerName='L3M', ID=0)
            else :
                self.L3M_CoordinateDict[target.nodeName] = Node(x=coordinate[0], y=coordinate[1], z=coordinate[2], dimensions='3D', headerName='L3M', ID=0)
    
    def L3M_Comb_Coordinate(self):
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
                
                theta = self.L3M_Alg(anchorCombList, RSSI, noise)
                coordinate = np.transpose(theta).tolist()[0][:-1]
                
                if self.Localization_Dimensions == '2D' :
                    coordinateList.append(Node(x=coordinate[0], y=coordinate[1], dimensions='2D', headerName=target.nodeName + '_L3M_Comb', ID=index))
                else :
                    coordinateList.append(Node(x=coordinate[0], y=coordinate[1], z=coordinate[2], dimensions='3D', headerName=target.nodeName + '_L3M_Comb', ID=index))
                    
            self.L3M_Comb_CoordinateDict[target.nodeName] = coordinateList
        
    @classmethod
    def L3M_Alg(cls, anchorList, RSSIList, noiseList=None):
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
            #create matrix A
            A_col=[-2*anchor.coordinate[i] for i in range(len(anchor))]
            A_col.append(1)
                
            #create matrix b
            b_col=anchor.getChannelDistance(RSSI, noise)**2 - Ri(anchor)
                
            matrix_A.append(A_col)
            matrix_b.append([b_col])
                
        np_matrix_A = np.array(matrix_A)
        np_matrix_b = np.array(matrix_b)
        np_matrix_A_pinv = np.linalg.pinv(np_matrix_A)
        theta = np.dot(np_matrix_A_pinv, np_matrix_b)
        
        return theta
        
    def getL3M_Comb_XList(self, target):
        return [self.L3M_Comb_CoordinateDict[target.nodeName][i].x for i in range(len(self.L3M_Comb_CoordinateDict[target.nodeName]))]
    
    def getL3M_Comb_YList(self, target):
        return [self.L3M_Comb_CoordinateDict[target.nodeName][i].y for i in range(len(self.L3M_Comb_CoordinateDict[target.nodeName]))]
    
    def getL3M_Comb_ZList(self, target):
        return [self.L3M_Comb_CoordinateDict[target.nodeName][i].z for i in range(len(self.L3M_Comb_CoordinateDict[target.nodeName]))]
    
    def printL3M_Coordinate(self):
        for target in self.L3M_CoordinateDict :
            print('Target Node \"%s\" :\n estimate coordinate'%(target) + str(self.L3M_CoordinateDict[target]))
            
    def printL3M_Comb_Coordinate(self):
        for target in self.L3M_Comb_CoordinateDict :
            print("Target Node \"%s\" :\n estimate coordinate ---"%(target))
            for node, anchor in zip(self.L3M_Comb_CoordinateDict[target], self.anchorCombDict) :
                anchorCombList = [self.anchorCombDict[anchor][i].nodeName for i in range(len(self.anchorCombDict[anchor]))]
                print('\t --' + str(node) + '\t comb Anchor : ' + str(anchorCombList))
                
    def printLocalizationSystemInfo(self):
        self.printTargetNode()
        self.printAnchorNode()
        self.printRSSI()
        self.printChannelDistance()
        self.printL3M_Coordinate()
        self.printL3M_Comb_Coordinate()
        
    
        
        
        
        