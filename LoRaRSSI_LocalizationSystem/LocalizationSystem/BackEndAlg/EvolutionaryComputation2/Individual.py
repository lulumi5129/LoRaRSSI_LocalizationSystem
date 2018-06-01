#
# Individual.py
#
#

import math
from LocalizationSystem.Node.node import Node
from LocalizationSystem.Node.node import channelNoise

#Base class for all individual types
#
class Individual(Node):
    """
    Individual
    """
    minMutRate=1e-100
    maxMutRate=1
    learningRate=None
    uniprng=None
    normprng=None
    fitFunc=None
    anchorValue=None

    def __init__(self, _dimensions, _ID):
        super().__init__(dimensions=_dimensions, headerName='EV3_2', ID=_ID)
        self.noiseList = [ channelNoise.noiseMethod() for i in range(self.anchorValue)]
        self.fit = self.__class__.fitFunc(self)
        self.mutRate=self.uniprng.uniform(0.9,0.1) #use "normalized" sigma
        self.setXYZ()
            
    def mutateMutRate(self):
        self.mutRate=self.mutRate*math.exp(self.learningRate*self.normprng.normalvariate(0,1))
        if self.mutRate < self.minMutRate: self.mutRate=self.minMutRate
        if self.mutRate > self.maxMutRate: self.mutRate=self.maxMutRate
            
    def evaluateFitness(self):
        if self.fit == None: self.fit=self.__class__.fitFunc(self)
        
    def crossover(self, other):
        #perform crossover "in-place"
        for i in range(self.anchorValue):
            if self.uniprng.random() < 0.5:
                tmp=self.noiseList[i]
                self.noiseList[i]=other.noiseList[i]
                other.noiseList[i]=tmp
                        
        self.setXYZ()
        other.setXYZ()
        self.fit=None
        other.fit=None
        
    def mutate(self):
        self.mutateMutRate() #update mutation rate
        
        for i in range(self.anchorValue):
            if self.uniprng.random() < self.mutRate:
                self.noiseList[i]=channelNoise.noiseMethod()
        
        self.setXYZ()
        self.fit=None
        
    def __str__(self):
        return super().__str__() + '\t' + str(self.noiseList) +'\t%0.8e'%self.fit+'\t'+'%0.8e'%self.mutRate
