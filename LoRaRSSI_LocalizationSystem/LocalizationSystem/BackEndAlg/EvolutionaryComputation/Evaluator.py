
import math

class ClusterCenter:
    coordinateCluster=None
        
    @classmethod  
    def fitnessFunc(cls, centerNode):
        totalDistance = 0
        for clusterNode in cls.coordinateCluster:
            totalDistance += centerNode.getDistance(clusterNode)
            
        return totalDistance
        