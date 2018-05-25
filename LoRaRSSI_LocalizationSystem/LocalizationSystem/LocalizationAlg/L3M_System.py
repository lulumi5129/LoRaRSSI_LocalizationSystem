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

from ..Node.node import Node, node_Config
import yaml
import numpy as np
import math
from itertools import combinations

class L3M_Config():
    """
    node configuration class
    """
    # class variables
    sectionName='L3MSys'
    options={'targetNodeNum': (int,True),
             'specifyTargetNodeValue': (list,False),
             'specifyTarget': (bool,True),
             'anchorNodeNum': (int,True),
             'specifyAnchorNodeValue': (list,False),
             'specifyAnchor': (bool,True),
             'L3M_Sys_Dimensions': (str,True),
             'L3M_Sys_InputType': (str,True),
             'combValue': (int,True)}
    
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
        L3M_Sys.targetNodeNum = self.targetNodeNum
        L3M_Sys.specifyTargetNodeValue = self.specifyTargetNodeValue
        L3M_Sys.specifyTarget = self.specifyTarget
        L3M_Sys.anchorNodeNum = self.anchorNodeNum
        L3M_Sys.specifyAnchorNodeValue = self.specifyAnchorNodeValue
        L3M_Sys.specifyAnchor = self.specifyAnchor
        L3M_Sys.L3M_Sys_Dimensions = self.L3M_Sys_Dimensions
        L3M_Sys.L3M_Sys_InputType = self.L3M_Sys_InputType
        L3M_Sys.combValue = self.combValue
        
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
        
class L3M_Sys():
    """
    L3M System main class
    """
    
    targetNodeNum = None
    specifyTargetNodeValue = None
    specifyTarget = None
    
    anchorNodeNum = None
    specifyAnchorNodeValue = None
    specifyAnchor = None
    
    L3M_Sys_Dimensions = None
    L3M_Sys_InputType = None
    combValue = None
    
    @classmethod
    def L3M_Sys_main(cls):
        if cls.L3M_Sys_InputType == 'pseudo' :
            return cls.L3M_Sys_pseudo()
        elif cls.L3M_Sys_InputType == 'real' :
            return cls.L3M_Sys_real()
        else :
            raise Exception('Your \'L3M_Sys_InputType\' Must be specify \'pseudo\' or \'real\'.')
    
    @classmethod
    def L3M_Sys_real(cls):
        print('real data form database')
    
    @classmethod
    def L3M_Sys_pseudo(cls):
        #create target node list
        targetNodeList = []
        for i in range(cls.targetNodeNum) :
            if cls.specifyTarget is True :
                if cls.L3M_Sys_Dimensions == '2D' :
                    targetNodeList.append(Node(x=cls.specifyTargetNodeValue[i][0], y=cls.specifyTargetNodeValue[i][1], dimensions='2D', headerName='Target', ID=i))
                else :
                    targetNodeList.append(Node(x=cls.specifyTargetNodeValue[i][0], y=cls.specifyTargetNodeValue[i][1], z=cls.specifyTargetNodeValue[i][2], dimensions='3D', headerName='Target', ID=i))
            else:
                if cls.L3M_Sys_Dimensions == '2D' :
                    targetNodeList.append(Node(dimensions='2D', headerName='Target', ID=i))
                else :
                    targetNodeList.append(Node(dimensions='3D', headerName='Target', ID=i))
            
        #create anchor node list
        anchorNodeList = []
        for i in range(cls.anchorNodeNum) :
            if cls.specifyAnchor is True :
                if cls.L3M_Sys_Dimensions == '2D' :
                    anchorNodeList.append(Node(x=cls.specifyAnchorNodeValue[i][0], y=cls.specifyAnchorNodeValue[i][1], dimensions='2D', headerName='Anchor', ID=i))
                else :
                    anchorNodeList.append(Node(x=cls.specifyAnchorNodeValue[i][0], y=cls.specifyAnchorNodeValue[i][1], z=cls.specifyAnchorNodeValue[i][2], dimensions='3D', headerName='Anchor', ID=i))
            else :
                if cls.L3M_Sys_Dimensions == '2D' :
                    anchorNodeList.append(Node(dimensions='2D', headerName='Anchor', ID=i))
                else :
                    anchorNodeList.append(Node(dimensions='3D', headerName='Anchor', ID=i))
            
        #get RSSI and pseudo noise
        realRSSIDict = {}
        noiseDict = {}
        channelDistanceDict = {}
        for target in targetNodeList :
            realRSSIList = []
            noiseList = []
            channelDistanceList = []
            for anchor in anchorNodeList :
                (channelDistance, noise) = target.getChannelDistance(anchor)
                (RSSI, noise1) = target.getChannelRSSI(anchor)
                realRSSIList.append(RSSI)
                noiseList.append(noise)
                channelDistanceList.append(channelDistance)
                
            realRSSIDict[target.nodeName] = realRSSIList
            noiseDict[target.nodeName] = noiseList
            channelDistanceDict[target.nodeName] = channelDistanceList
        
        #get estimate Coordinate
        L3M_CoordinateDict = {}
        for target, i in zip(targetNodeList, range(cls.targetNodeNum)) :
            realRSSIList = realRSSIDict[target.nodeName]
            noiseList = noiseDict[target.nodeName]
            theta = cls.L3M_Alg(anchorNodeList, realRSSIList, noiseList)
            coordinate = np.transpose(theta).tolist()[0][:-1]
            
            if cls.L3M_Sys_Dimensions == '2D' :
                L3M_CoordinateDict[target.nodeName] = Node(x=coordinate[0], y=coordinate[1], dimensions='2D', headerName='L3M', ID=i)
            else :
                L3M_CoordinateDict[target.nodeName] = Node(x=coordinate[0], y=coordinate[1], z=coordinate[2], dimensions='3D', headerName='L3M', ID=i)
        
        #get anchor comb List
        anchorCombDict = {}
        anchorCombList = list(combinations(anchorNodeList, cls.combValue))
        
        for anchorComb in range(len(anchorCombList)) :
            anchorCombDict['Comb_' + str(anchorComb+1)] = anchorCombList[anchorComb]
        
        #get estimate Coordinate(comb)
        L3M_Comb_CoordinateDict = {}
        for index in range(len(targetNodeList)) :
            target = targetNodeList[index]
            noiseList = noiseDict[target.nodeName]
            realRSSIList = realRSSIDict[target.nodeName]
            coordinateList=[]
            for key, i in zip(anchorCombDict, range(len(anchorCombDict))):
                anchorCombList = anchorCombDict[key]
                noise = [noiseList[anchorCombList[i].ID] for i in range(len(anchorCombList))]
                RSSI = [realRSSIList[anchorCombList[i].ID] for i in range(len(anchorCombList))]
                theta = cls.L3M_Alg(anchorCombList, RSSI, noise)
                coordinate = np.transpose(theta).tolist()[0][:-1]
                
                if cls.L3M_Sys_Dimensions == '2D' :
                    coordinateList.append(Node(x=coordinate[0], y=coordinate[1], dimensions='2D', headerName=target.nodeName + '_L3M_Comb', ID=i))
                else :
                    coordinateList.append(Node(x=coordinate[0], y=coordinate[1], z=coordinate[2], dimensions='3D', headerName=target.nodeName + '_L3M_Comb', ID=i))
                
            L3M_Comb_CoordinateDict[target.nodeName] = coordinateList
            
        return (anchorNodeList, targetNodeList, realRSSIDict, channelDistanceDict, noiseDict, L3M_CoordinateDict, anchorCombDict, L3M_Comb_CoordinateDict)
        
    @classmethod
    def L3M_Alg(cls, anchorNodeList, realRSSIList, noiseList=None):
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
        from ..Node.node import LogDistanceModel
        
        def Ri(anchorNode):
            addsum = 0
            for i in range(len(anchorNode)) : addsum += math.pow(anchorNode.coordinate[i], 2)
            return addsum
        
        matrix_A=[]
        matrix_b=[]
        
        # create matrix A and matrix b
        for anchorIndex in range(len(anchorNodeList)) :
            anchor = anchorNodeList[anchorIndex]
            noise = noiseList[anchorIndex]
            RSSI = realRSSIList[anchorIndex]
            
            #create matrix A
            A_col=[-2*anchor.coordinate[i] for i in range(len(anchor))]
            A_col.append(1)
                
            #create matrix b
            Zi = LogDistanceModel.transmitPower + RSSI
            b_col=(10**((2/(10*LogDistanceModel.n))*(LogDistanceModel.zeroPoint - Zi - noise))) - Ri(anchor)
                
            matrix_A.append(A_col)
            matrix_b.append([b_col])
                
        np_matrix_A = np.array(matrix_A)
        np_matrix_b = np.array(matrix_b)
        np_matrix_A_pinv = np.linalg.pinv(np_matrix_A)
        theta = np.dot(np_matrix_A_pinv, np_matrix_b)
        
        return theta
        
    @classmethod
    def printTargetNode(cls, targetNodeList):
        for target in targetNodeList :
            print(target)
            
    @classmethod
    def printAnchorNode(cls, anchorNodeList):
        for anchor in anchorNodeList :
            print(anchor)
    
    @classmethod
    def printChannelDistance(cls, channelDistanceDict, noiseDict):
        for key in channelDistanceDict :
            print("Target Node \"%s\" :\npseudo distance between ---"%(key))
            for index in range(len(channelDistanceDict[key])) :
                print("\t --Anchor %d : %4.4f m \tnoise = %8.4f dBm"%(index+1, channelDistanceDict[key][index], noiseDict[key][index]) )
    
    @classmethod
    def printRealRSSI(cls, realRSSIDict, noiseDict):
        for key in realRSSIDict :
            print("Target Node \"%s\" :\npseudo RSSI between ---"%(key))
            for index in range(len(realRSSIDict[key])) :
                print("\t --Anchor %d : %8.4f dBm \tnoise = %8.4f dBm"%(index+1, realRSSIDict[key][index], noiseDict[key][index]) )
        
    @classmethod
    def printL3M_Coordinate(cls, L3M_CoordinateDict):
        for key in L3M_CoordinateDict :
            print('Target Node \"%s\" :\nestimate coordinate'%(key) + str(L3M_CoordinateDict[key]))
            
    @classmethod
    def printL3M_Comb_Coordinate(cls, L3M_Comb_CoordinateDict, anchorCombDict):
        for key1 in L3M_Comb_CoordinateDict :
            print("Target Node \"%s\" :\nestimate coordinate ---"%(key1))
            for index, key2 in zip(range(len(L3M_Comb_CoordinateDict[key1])), anchorCombDict) :
                anchorCombList = [anchorCombDict[key2][i].nodeName for i in range(len(anchorCombDict[key2]))]
                print('\t --' + str(L3M_Comb_CoordinateDict[key1][index]) + '\t combAnchor : ' + str(anchorCombList))
    
        
        
        
        