#
# Individual.py
#
#

import math

#Base class for all individual types
#
class Individual:
    """
    Individual
    """
    minMutRate=1e-100
    maxMutRate=1
    learningRate=None
    uniprng=None
    normprng=None
    fitFunc=None
    estimateNodeList=None

    def __init__(self):
        self.fit=self.__class__.fitFunc(self.state, self.estimateNodeList)
        self.mutRate=self.uniprng.uniform(0.9,0.1) #use "normalized" sigma
            
    def mutateMutRate(self):
        self.mutRate=self.mutRate*math.exp(self.learningRate*self.normprng.normalvariate(0,1))
        if self.mutRate < self.minMutRate: self.mutRate=self.minMutRate
        if self.mutRate > self.maxMutRate: self.mutRate=self.maxMutRate
            
    def evaluateFitness(self):
        if self.fit == None: self.fit=self.__class__.fitFunc(self.state, self.estimateNodeList)

#A combinatorial integer representation class
#
class L3MIndividual(Individual):
    """
    IntVectorIndividual
    """
    nodeGenCls=None
        
    def __init__(self, _count=None):
        self.state=self.nodeGenCls(_count)
        
        super().__init__() #call base class ctor
        
    def crossover(self, other):
        #perform crossover "in-place"
        for i in range(len(self.state.coordinate)) :
            tmp = (self.state.coordinate[i] + other.state.coordinate[i])/2 
            
            self.state.coordinate[i] += tmp
            other.state.coordinate[i] -= tmp
            
        self.fit=None
        other.fit=None
    
    def mutate(self):
        self.mutateMutRate() #update mutation rate
        
        for i in range(len(self.state.coordinate)) :
            self.state.coordinate[i] = self.state.coordinate[i] * self.mutRate
        
        self.fit=None
            
    def __str__(self):
        return str(self.state)+'\t'+'%0.8e'%self.fit+'\t'+'%0.8e'%self.mutRate
    