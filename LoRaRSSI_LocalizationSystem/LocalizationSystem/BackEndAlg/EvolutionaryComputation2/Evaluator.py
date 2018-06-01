
import math
import numpy as np
from LocalizationSystem.LocalizationAlg.L3M_System import L3M

class ClusterCenter:
    anchorList=None
    RSSIList=None
        
    @classmethod  
    def fitnessFunc(cls, ind):
        #get estimate coordinate
        ind.coordinate = cls.getCoordinate(ind)
        
        #get distance
        distanceList=[]
        for i in range(len(ind.noiseList)) :
            distance = ind.getChannelDistance(cls.RSSIList[i], ind.noiseList[i])
            distanceList.append(distance)
            
        #Let all circle cross on the one point
        fit = 0
        for (distance, anchor) in zip(distanceList, cls.anchorList) :
            center = 0
            for i in range(len(anchor)) :
                center += (anchor.coordinate[i] - ind.coordinate[i])**2
                
            fit += abs(center - distance**2)
            
        totaldistance = 0
        for RSSI,noise in zip(cls.RSSIList, ind.noiseList) :
            totaldistance += ind.getChannelDistance(RSSI, noise)**2
            
        fit += totaldistance
            
        return fit
    
    @classmethod
    def getCoordinate(cls, ind):
        #get estimate coordinate
        theta = L3M.L3M_Alg(cls.anchorList, cls.RSSIList, ind.noiseList)
        coordinate = np.transpose(theta).tolist()[0][:-1]
        
        return coordinate
        