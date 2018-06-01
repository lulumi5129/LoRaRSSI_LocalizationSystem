'''
Created on 2018/5/26

@author: Lulumi5129

    This is Localization System 
    Use node class implement Localization System
    
'''

import yaml
from ..Node.node import Node

class Localization_Config():
    """
    node configuration class
    """
    # class variables
    sectionName='Localization'
    options={'targetNodeNum': (int,True),
             'specifyTargetNodeValue': (list,False),
             'specifyTarget': (bool,True),
             'anchorNodeNum': (int,True),
             'specifyAnchorNodeValue': (list,False),
             'specifyAnchor': (bool,True),
             'Localization_Dimensions': (str,True)}
    
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
                    
        self.setLocalization()
        
    def setLocalization(self):
        Localization.targetNodeNum = self.targetNodeNum
        Localization.specifyTargetNodeValue = self.specifyTargetNodeValue
        Localization.specifyTarget = self.specifyTarget
        Localization.anchorNodeNum = self.anchorNodeNum
        Localization.specifyAnchorNodeValue = self.specifyAnchorNodeValue
        Localization.specifyAnchor = self.specifyAnchor
        Localization.Localization_Dimensions = self.Localization_Dimensions
        
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
    
class Localization():
    """
    Localization System class
    """
    
    targetNodeNum = None
    specifyTargetNodeValue = None
    specifyTarget = None
    
    anchorNodeNum = None
    specifyAnchorNodeValue = None
    specifyAnchor = None
    
    Localization_InputType = None
    Localization_Dimensions = None
    
    def __init__(self, targetCoordinateList=None, anchorCoordinateList=None, RSSIDict=None):
        self.targetList = []
        self.anchorList = []
        
        #Use config setting to init Localization System
        if targetCoordinateList is None or anchorCoordinateList is None :
            self.Localization_InputType = 'pseudo'
            #check Localization Dimensions
            if self.Localization_Dimensions != '2D' and self.Localization_Dimensions != '3D' :
                raise Exception('Please setting Localization_Dimensions is 2D or 3D.')
            
            #create target node with specify value
            if self.specifyTarget is True :
                if self.Localization_Dimensions == '2D' :
                    for i in range(self.targetNodeNum) :
                        target = Node(x=self.specifyTargetNodeValue[i][0], y=self.specifyTargetNodeValue[i][1], dimensions=self.Localization_Dimensions, headerName='Target', ID=i)
                        self.targetList.append(target)
                else :
                    for i in range(self.targetNodeNum) :
                        target = Node(x=self.specifyTargetNodeValue[i][0], y=self.specifyTargetNodeValue[i][1], z=self.specifyTargetNodeValue[i][2], dimensions=self.Localization_Dimensions, headerName='Target', ID=i)
                        self.targetList.append(target)
            
            #create target node with random value
            else :
                if self.Localization_Dimensions == '2D' :
                    for i in range(self.targetNodeNum) :
                        target = Node(dimensions=self.Localization_Dimensions, headerName='Target', ID=i)
                        self.targetList.append(target)
                else :
                    for i in range(self.targetNodeNum) :
                        target = Node(dimensions=self.Localization_Dimensions, headerName='Target', ID=i)
                        self.targetList.append(target)
                        
            #create anchor node with specify value
            if self.specifyAnchor is True :
                if self.Localization_Dimensions == '2D' :
                    for i in range(self.anchorNodeNum) :
                        anchor = Node(x=self.specifyAnchorNodeValue[i][0], y=self.specifyAnchorNodeValue[i][1], dimensions=self.Localization_Dimensions, headerName='Anchor', ID=i)
                        self.anchorList.append(anchor)
                else :
                    for i in range(self.anchorNodeNum) :
                        anchor = Node(x=self.specifyAnchorNodeValue[i][0], y=self.specifyAnchorNodeValue[i][1], z=self.specifyAnchorNodeValue[i][2], dimensions=self.Localization_Dimensions, headerName='Anchor', ID=i)
                        self.anchorList.append(anchor)
            
            #create anchor node with random value
            else :
                if self.Localization_Dimensions == '2D' :
                    for i in range(self.anchorNodeNum) :
                        anchor = Node(dimensions=self.Localization_Dimensions, headerName='Anchor', ID=i)
                        self.anchorList.append(anchor)
                else :
                    for i in range(self.anchorNodeNum) :
                        anchor = Node(dimensions=self.Localization_Dimensions, headerName='Anchor', ID=i)
                        self.anchorList.append(anchor)
        
        #Use real data to init Localization System
        else :
            self.Localization_InputType = 'real'
            #set len
            self.targetNodeNum = len(targetCoordinateList)
            self.anchorNodeNum = len(anchorCoordinateList)
            
            if len(targetCoordinateList[0]) != len(anchorCoordinateList[0]) :
                raise Exception('Please setting target and anchor is same Dimensions.')
            
            if len(targetCoordinateList[0]) == 2 :
                self.Localization_Dimensions == '2D'
            elif len(targetCoordinateList[0]) == 3 :
                self.Localization_Dimensions == '3D'
            else :
                raise Exception('Please setting Localization_Dimensions is 2D or 3D.')
            
            #create target node
            if self.Localization_Dimensions == '2D' :
                for i in range(self.targetNodeNum) :
                    target = Node(x=targetCoordinateList[i][0], y=targetCoordinateList[i][1], dimensions=self.Localization_Dimensions, headerName='Target', ID=i)
                    self.targetList.append(target)
            else :
                for i in range(self.targetNodeNum) :
                    target = Node(x=targetCoordinateList[i][0], y=targetCoordinateList[i][1], z=targetCoordinateList[i][2], dimensions=self.Localization_Dimensions, headerName='Target', ID=i)
                    self.targetList.append(target)
                        
            #create anchor node with specify value
            if self.Localization_Dimensions == '2D' :
                for i in range(self.anchorNodeNum) :
                    anchor = Node(x=anchorCoordinateList[i][0], y=anchorCoordinateList[i][1], dimensions=self.Localization_Dimensions, headerName='Anchor', ID=i)
                    self.anchorList.append(anchor)
            else :
                for i in range(self.anchorNodeNum) :
                    anchor = Node(x=anchorCoordinateList[i][0], y=anchorCoordinateList[i][1], z=anchorCoordinateList[i][2], dimensions=self.Localization_Dimensions, headerName='Anchor', ID=i)
                    self.anchorList.append(anchor)
        
        #get real RSSI value
        self.RSSIDict = {}
        self.noiseDict = {}
        if self.Localization_InputType == 'pseudo' :
            for target in self.targetList :
                RSSIList = []
                noiseList = []
                for anchor in self.anchorList :
                    (RSSI, noise) = target.getChannelRSSI(anchor)
                    RSSIList.append(RSSI)
                    noiseList.append(noise)
                    
                self.RSSIDict[target.nodeName] = RSSIList
                self.noiseDict[target.nodeName] = noiseList
                
        else :
            self.RSSIDict = RSSIDict
            
        #get distance value with noise
        self.distanceDict = {}
        for target in self.targetList :
            RSSIList = self.RSSIDict[target.nodeName]
            noiseList = self.noiseDict.get(target.nodeName, None)
            distanceList = []
            for (anchor, RSSI, noise) in zip(self.anchorList, RSSIList, noiseList) :
                distance = target.getChannelDistance(RSSI, noise)
                distanceList.append(distance)
            self.distanceDict[target.nodeName] = distanceList
    
    def printTargetNode(self):
        print('All Target Node :')
        for target in self.targetList :
            print('\t--' + str(target))
            
    def printAnchorNode(self):
        print('All Anchor Node :')
        for anchor in self.anchorList :
            print('\t--' + str(anchor))
            
    def printChannelDistance(self):
        for targetName in self.distanceDict :
            print("Target Node \"%s\" :\n distance between ---"%(targetName))
            distanceList = self.distanceDict[targetName]
            if self.Localization_InputType == 'pseudo' :
                noiseList = self.noiseDict[targetName]
                for (index, distance, noise) in zip(range(self.anchorNodeNum), distanceList, noiseList) :
                    print("\t --Anchor %d : %4.4f m \t noise = %8.4f dBm"%(index+1, distance, noise))
            else :
                for (index, distance) in zip(range(self.anchorNodeNum), distanceList) :
                    print("\t --Anchor %d : %4.4f m"%(index+1, distance))
                    
    def printRSSI(self):
        for targetName in self.RSSIDict :
            print("Target Node \"%s\" :\n RSSI between ---"%(targetName))
            RSSIList = self.RSSIDict[targetName]
            if self.Localization_InputType == 'pseudo' :
                noiseList = self.noiseDict[targetName]
                for (index, RSSI, noise) in zip(range(self.anchorNodeNum), RSSIList, noiseList) :
                    print("\t --Anchor %d : %4.4f dBm \t noise = %8.4f dBm"%(index+1, RSSI, noise))
            else :
                for (index, RSSI) in zip(range(self.anchorNodeNum), RSSIList) :
                    print("\t --Anchor %d : %4.4f dBm"%(index+1, RSSI))
                    
    def getAnchorXList(self):
        return [anchor.x for anchor in self.anchorList]
    
    def getAnchorYList(self):
        return [anchor.y for anchor in self.anchorList]
    
    def getAnchorZList(self):
        return [anchor.z for anchor in self.anchorList]
    
    def getTargetXList(self):
        return [target.x for target in self.targetList]
    
    def getTargetYList(self):
        return [target.y for target in self.targetList]
    
    def getTargetZList(self):
        return [target.z for target in self.targetList]
        
        
        
        
        
        
        
        
        
        
        
        
        
        