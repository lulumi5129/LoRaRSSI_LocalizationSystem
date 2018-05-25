'''
Created on 2018/5/19

@author: Lulumi5129 by NCHU EE Lab 610

    This is Localization System basic module,
    create node structure to implement Localization System,
    and other algorithm.
'''

import random
import math
import yaml
import sys

#node Config class 
class node_Config:
    """
    node configuration class
    """
    # class variables
     
    #constructor
    def __init__(self, inFileName):
        #read YAML config and get EV3 section
        infile=open(inFileName,'r')
        self.ymlcfg=yaml.load(infile)
        infile.close()
        
        self.setNodeInit()
        self.set_node_Method_Init()
        self.set_LogDistanceModel_Init()
        self.set_channelNoise_Init()
                    
    def setNodeInit(self):
        sectionName='Node'
        options={'X_Axis_Limit': (list,True),
                 'Y_Axis_Limit': (list,True),
                 'Z_Axis_Limit': (list,True)}
        
        eccfg=self.ymlcfg.get(sectionName,None)
        if eccfg is None: raise Exception('Missing {} section in cfg file'.format(sectionName))
         
        #iterate over options
        for opt in options:
            if opt in eccfg:
                optval=eccfg[opt]
 
                #verify parameter type
                if type(optval) != options[opt][0]:
                    raise Exception('Parameter "{}" has wrong type'.format(opt))
                 
                #create attributes on the fly
                setattr(self,opt,optval)
            else:
                if options[opt][1]:
                    raise Exception('Missing mandatory parameter "{}"'.format(opt))
                else:
                    setattr(self,opt,None)
                    
        #setting params to class
        Node.X_Axis_Limit = self.X_Axis_Limit
        Node.Y_Axis_Limit = self.Y_Axis_Limit
        Node.Z_Axis_Limit = self.Z_Axis_Limit
                    
    def set_node_Method_Init(self):
        sectionName='node_Method'
        options={'nodeRandomSeed': (int,True),
                 'distanceEquation': (str,True),
                 'channelModel': (str,True)}
        
        eccfg=self.ymlcfg.get(sectionName,None)
        if eccfg is None: raise Exception('Missing {} section in cfg file'.format(sectionName))
         
        #iterate over options
        for opt in options:
            if opt in eccfg:
                optval=eccfg[opt]
 
                #verify parameter type
                if type(optval) != options[opt][0]:
                    raise Exception('Parameter "{}" has wrong type'.format(opt))
                 
                #create attributes on the fly
                setattr(self,opt,optval)
            else:
                if options[opt][1]:
                    raise Exception('Missing mandatory parameter "{}"'.format(opt))
                else:
                    setattr(self,opt,None)
                    
        #setting params to class
        prng = random.Random()
        prng.seed(self.nodeRandomSeed)
        node_Method.nodeRandom = prng
        m = str(sys.modules[__name__])
        path = m.split('\'')[1:2][0]
        node_Method.distanceEquation = getattr(self.get_class(path + '.node_Method'), self.distanceEquation)
        node_Method.channelModel = self.get_class(path + '.' + str(self.channelModel))
        
    def set_LogDistanceModel_Init(self):
        sectionName='LogDistanceModel'
        options={'zeroPoint': (float,True),
                 'n': (float,True),
                 'transmitPower': (float,True),
                 'modelRandom': (str,True)}
        
        eccfg=self.ymlcfg.get(sectionName,None)
        if eccfg is None: raise Exception('Missing {} section in cfg file'.format(sectionName))
         
        #iterate over options
        for opt in options:
            if opt in eccfg:
                optval=eccfg[opt]
 
                #verify parameter type
                if type(optval) != options[opt][0]:
                    raise Exception('Parameter "{}" has wrong type'.format(opt))
                 
                #create attributes on the fly
                setattr(self,opt,optval)
            else:
                if options[opt][1]:
                    raise Exception('Missing mandatory parameter "{}"'.format(opt))
                else:
                    setattr(self,opt,None)
                    
        #setting params to class
        LogDistanceModel.zeroPoint = self.zeroPoint
        LogDistanceModel.n = self.n
        LogDistanceModel.transmitPower =self.transmitPower
        m = str(sys.modules[__name__])
        path = m.split('\'')[1:2][0]
        LogDistanceModel.modelRandom = self.get_class(path + '.' + str(self.modelRandom))
        
    def set_channelNoise_Init(self):
        sectionName='channelNoise'
        options={'noiseRandomSeed': (int,True),
                 'noiseMethod': (str,True),
                 'noiseLimit': (list,True)}
        
        eccfg=self.ymlcfg.get(sectionName,None)
        if eccfg is None: raise Exception('Missing {} section in cfg file'.format(sectionName))
         
        #iterate over options
        for opt in options:
            if opt in eccfg:
                optval=eccfg[opt]
 
                #verify parameter type
                if type(optval) != options[opt][0]:
                    raise Exception('Parameter "{}" has wrong type'.format(opt))
                 
                #create attributes on the fly
                setattr(self,opt,optval)
            else:
                if options[opt][1]:
                    raise Exception('Missing mandatory parameter "{}"'.format(opt))
                else:
                    setattr(self,opt,None)
                    
        #setting params to class
        prng = random.Random()
        prng.seed(self.noiseRandomSeed)
        channelNoise.noiseRandom = prng
        m = str(sys.modules[__name__])
        path = m.split('\'')[1:2][0]
        channelNoise.noiseMethod = getattr(self.get_class(path + '.channelNoise'), self.noiseMethod)
        channelNoise.noiseLimit = self.noiseLimit
     
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

class Node():
    '''
    create 2D or 3D node structure
    
    x, y, z must be int or float
    dimensions must be '2D' or '3D'
    nodeID must be int
    '''
    
    X_Axis_Limit=None
    Y_Axis_Limit=None
    Z_Axis_Limit=None

    def __init__(self, x=None, y=None, z=None, dimensions=None, headerName=None, ID=None):
        '''
        Constructor
        '''
        
        if headerName is None and ID is None :
            raise Exception('Must be specify your \'nodeID\' and \'nodeHeaderName\'.')
        else :
            self.nodeName = str(headerName) + '_' + str(ID+1)
            self.ID = ID
            
        if dimensions != '2D' and dimensions != '3D' :
            raise Exception('node \'dimensions\' Must be specify \'2D\' or \'3D\'.')
        else :
            self.nodeDimensions = dimensions
            
        if x is None or y is None :
            self.x = node_Method.genRandomCoordinate(self.X_Axis_Limit)
            self.y = node_Method.genRandomCoordinate(self.Y_Axis_Limit)
        else :
            self.x = x
            self.y = y
        
        if self.nodeDimensions == '3D' and z is None:
            self.z = node_Method.genRandomCoordinate(self.Z_Axis_Limit)
        elif self.nodeDimensions == '3D':
            self.z = z
            
        self.coordinate = self.getCoordinate()
            
    def __str__(self):
        msg1 = ('['+', '.join(['%.2f']*len(self.coordinate))+']') % tuple(self.coordinate)
        return 'Node ' + self.nodeName + '-->\t' + 'coordinate: ' + msg1
    
    def __len__(self):
        return len(self.coordinate)
    
    def getCoordinate(self):
        coordinate=[]
        
        if self.nodeDimensions == '2D' :
            coordinate = [self.x, self.y]
        else :
            coordinate = [self.x, self.y, self.z]
            
        return coordinate
    
    def setXYZ(self):
        if self.nodeDimensions == '2D' :
            self.x = self.coordinate[0]
            self.y = self.coordinate[1]
        else :
            self.x = self.coordinate[0]
            self.y = self.coordinate[1]
            self.z = self.coordinate[2]
    
    def getDistance(self, other):
        if self and other is not None : return node_Method.distanceEquation(self, other)
        
    def getChannelRSSI(self, other):
        if self and other is not None : return node_Method.getChannelRSSI(self, other)
        
    def getChannelDistance(self, other):
        if self and other is not None : return node_Method.getChannelDistance(self, other)
        
    def getChannelDistance_noNoise(self, other):
        if self and other is not None : return node_Method.getChannelDistance_noNoise(self, other)
    
class node_Method():
    
    nodeRandom=None
    distanceEquation=None
    channelModel=None
    
    @classmethod
    def genRandomCoordinate(cls, limit):
        return cls.nodeRandom.uniform(limit[0], limit[1])
    
    #####################################
    ########## Distance Equation ########
    #####################################
    @classmethod
    def Euclidean_distance(cls, selfNode, otherNode):
        sum = 0
        if selfNode.nodeDimensions != otherNode.nodeDimensions :
            raise Exception('Euclidean_distance Error : not same dimensions!')
        else :
            for index in range(len(selfNode)) :
                sum += math.pow(selfNode.coordinate[index]- otherNode.coordinate[index], 2)
            distance = math.sqrt(sum)
            
        return distance
    
    @classmethod
    def Euclidean_distance_nosqrt(cls, selfNode, otherNode):
        distance = 0
        if selfNode.nodeDimensions != otherNode.nodeDimensions :
            raise Exception('Euclidean_distance Error : not same dimensions!')
        else :
            for index in range(len(selfNode)) :
                distance += math.pow(selfNode.coordinate[index]- otherNode.coordinate[index], 2)
                
        return distance
    
    #####################################
    ########## Channel Model ############
    #####################################
    @classmethod
    def getChannelRSSI(cls, selfNode, otherNode):
        return cls.channelModel.getChannelRSSI(selfNode, otherNode)
        
    @classmethod
    def getChannelDistance(cls, selfNode, otherNode):
        return cls.channelModel.getChannelDistance(selfNode, otherNode)
    
    @classmethod
    def getChannelDistance_noNoise(cls, selfNode, otherNode):
        return cls.channelModel.getChannelDistance_noNoise(selfNode, otherNode)
        
class LogDistanceModel():
    
    zeroPoint=None # it mean 1m of receive power
    n=None         # environment factor
    transmitPower=None
    modelRandom=None
    
    @classmethod
    def getChannelRSSI(cls, selfNode, otherNode):
        # Calculation Real distance between 2 node
        distance = selfNode.getDistance(otherNode)
        
        # Calculation receive single strength
        # RSSI= p0 - 10nlog(d) - pt - noise
        realRSSI=cls.zeroPoint - 10*cls.n*math.log10(distance) - cls.transmitPower
        noise = channelNoise.noiseMethod(selfNode, otherNode)
        
        return realRSSI, noise
    
    @classmethod
    def getChannelDistance(cls, selfNode, otherNode):
        # get Real RSSI and noise
        (realRSSI, noise) = cls.getChannelRSSI(selfNode, otherNode)
        
        # Calculation distance
        # d = 10**((1/10*n)*(P0 - Pr - Pt - noise))
        distance = 10**((1/(10*cls.n)) * (cls.zeroPoint - cls.transmitPower - realRSSI - noise))
        
        return distance, noise
    
    @classmethod
    def getChannelDistance_noNoise(cls, selfNode, otherNode):
        # get Real RSSI and noise
        (realRSSI, noise) = cls.getChannelRSSI(selfNode, otherNode)
        
        # Calculation distance
        # d = 10**((1/10*n)*(P0 - Pr - Pt - noise))
        distance = 10**((1/(10*cls.n)) * (cls.zeroPoint - cls.transmitPower - realRSSI))
        
        return distance
    
class channelNoise():
    
    noiseRandom=None
    noiseMethod=None
    noiseLimit=None
    
    @classmethod
    def normalNoise(cls, selfNode=None, otherNode=None):
        return cls.noiseRandom.uniform(cls.noiseLimit[0], cls.noiseLimit[1])



















    