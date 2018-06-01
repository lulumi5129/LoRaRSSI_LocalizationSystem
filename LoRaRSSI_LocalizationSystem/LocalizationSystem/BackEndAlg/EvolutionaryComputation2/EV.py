'''
Created on 2018/5/21

@author: Lulumi5129
'''

import yaml
import sys
from random import Random
from .Evaluator import ClusterCenter
from .Population import Population
from .Individual import Individual
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

#EV3 Config class 
class EV3_Config:
    """
    EV3 configuration class
    """
    # class variables
    sectionName='EV3'
    options={'populationSize': (int,True),
             'generationCount': (int,True),
             'randomSeed': (int,True),
             'crossoverFraction': (float,True),
             'fitnessMethod': (str,True),
             'loopMethod': (str,True),
             'nodelimit': (list,True),
             'loopCount': (int,True),
             'printData': (bool,True),
             'plot': (bool,True),
             'PlotLineCircle': (bool,True)}
     
    #constructor
    def __init__(self, inFileName):
        #read YAML config and get EV3 section
        infile=open(inFileName,'r')
        ymlcfg=yaml.load(infile)
        infile.close()
        eccfg=ymlcfg.get(self.sectionName,None)
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
                    
        self.setEV3Init()
                    
    def setEV3Init(self):
        EV3.populationSize = self.populationSize
        EV3.generationCount = self.generationCount
        EV3.crossoverFraction = self.crossoverFraction
        EV3.loopCount = self.loopCount
        EV3.randomSeed = self.randomSeed
        EV3.nodelimit = self.nodelimit
        EV3.printData=self.printData
        EV3.plot=self.plot
        EV3.PlotLineCircle=self.PlotLineCircle
        
        m = str(sys.modules[__name__])
        path = m.split('\'')[1:2][0]
        EV3.loopMethod = getattr(self.get_class(path + '.EV3'), self.loopMethod)
        
        path = path.replace('.EV', '')
        EV3.fitnessMethod = getattr(self.get_class(path + '.Evaluator.ClusterCenter'), self.fitnessMethod)
        
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
    
class EV3():
    
    populationSize=None
    generationCount=None
    crossoverFraction=None
    fitnessMethod=None
    randomSeed=None
    loopCount=None
    loopMethod=None
    dimensions=None
    nodelimit=None
    printData=None
    plot=None
    PlotLineCircle=None
    
    #EV3 multi process run main
    @classmethod
    def ev3_multiprocess(cls, settingPath, LS_Obj, target):
        from LocalizationSystem.LocalizationAlg.L3M_System import L3M_Config
        from LocalizationSystem.Node.node import node_Config
        from LocalizationSystem.LocalizationAlg.Localization import Localization_Config
        EV3_Config(settingPath[0])
        L3M_Config(settingPath[1])
        Localization_Config(settingPath[2])
        node_Config(settingPath[3])
        
        return cls.ev3(LS_Obj, target)
    
    #EV3 main
    @classmethod
    def ev3(cls, LS_Obj, target):
        #start random number generators
        uniprng=Random()
        uniprng.seed(cls.randomSeed)
        normprng=Random()
        normprng.seed(cls.randomSeed+101)
        
        #set static params on classes
        # (probably not the most elegant approach, but let's keep things simple...)
        Individual.uniprng=uniprng
        Individual.normprng=normprng
        Individual.fitFunc=cls.fitnessMethod
        Individual.learningRate=0.8
        Individual.anchorValue = LS_Obj.anchorNodeNum
        
        Population.uniprng=uniprng
        Population.nodelimit = cls.nodelimit
        Population.crossoverFraction=cls.crossoverFraction
        
        ClusterCenter.anchorList = LS_Obj.anchorList
        
        realRSSIList = LS_Obj.RSSIDict[target.nodeName]
        noiseList = LS_Obj.noiseDict[target.nodeName]
        RSSIList=[]
        for (realRSSI, noise) in zip(realRSSIList, noiseList) :
            RSSIList.append(realRSSI+noise)
        ClusterCenter.RSSIList = RSSIList
        
        if len(target) == 2 :
            cls.dimensions = '2D'
            Population.individualDimensions=cls.dimensions
        else :
            cls.dimensions = '3D'
            Population.individualDimensions=cls.dimensions
           
        
        for loop in range(cls.loopCount) :
            #create initial Population (random initialization)
            population=Population(cls.populationSize)
        
            #print initial pop stats    
            if cls.printData is True : 
                cls.printStats(population,0, target)
                
            minInd = cls.getminInd(population)
            if loop == 0 :
                if cls.plot is True :
                    fig = plt.figure(figsize=(8,6), dpi=120)
                    if cls.dimensions == '2D' :
                        ax = fig.add_subplot(111)
                    else :
                        ax = fig.add_subplot(111, projection='3d')
                
                    fig.suptitle(target.nodeName + " Localization System Loop_%s"%(str(loop+1)))
    
            if cls.plot is True :
                cls.plotLocalizationSystem(fig, ax, population, 0, 0, LS_Obj, target, minInd)
        
            #evolution main loop
            for i in range(cls.generationCount):
                #create initial offspring population by copying parent pop
                offspring=population.copy()
        
                #select mating pool
                offspring.conductTournament()

                #perform crossover
                offspring.crossover()
        
                #random mutation
                offspring.mutate()
        
                #update fitness values
                offspring.evaluateFitness()        
                
                #survivor selection: elitist truncation using parents+offspring
                population.combinePops(offspring)
                population.truncateSelect(cls.populationSize)
        
                #print population stats    
                if cls.printData :
                    cls.printStats(population,i+1, target)
                minInd = cls.getminInd(population)
                if cls.plot is True :
                    cls.plotLocalizationSystem(fig, ax, population, 0, i+1, LS_Obj, target, minInd)
            
            print('target name %s real coordinate is %s, and estimate coordinate is %s, and estimate noise is %s'%(target.nodeName, str(target.coordinate), str(minInd.coordinate), str(minInd.noiseList)))
            if loop != cls.loopCount-1 :
                maxNoiseAnchor = cls.loopMethod(LS_Obj, RSSIList, minInd)
                print(maxNoiseAnchor)
                del LS_Obj.anchorList[maxNoiseAnchor]
                del RSSIList[maxNoiseAnchor]
                del LS_Obj.distanceDict[target.nodeName][maxNoiseAnchor]
                del LS_Obj.noiseDict[target.nodeName][maxNoiseAnchor]
                del LS_Obj.RSSIDict[target.nodeName][maxNoiseAnchor]
            
                ClusterCenter.RSSIList = RSSIList
                ClusterCenter.anchorList = LS_Obj.anchorList
                Individual.anchorValue = Individual.anchorValue -1
            
        if cls.plot is True : plt.show()
        return (target, minInd)
        
    #Plot some useful coordinate to screen
    @classmethod
    def plotLocalizationSystem(cls, fig, ax, pop, loop, gen, L3M_Obj, target, minInd):
        from itertools import cycle
        import math
        cycol=cycle('bgrcmkyb')
        ax.clear()
        x_anchor = L3M_Obj.getAnchorXList()
        y_anchor = L3M_Obj.getAnchorYList()
        z_anchor=[]
        RSSIList = ClusterCenter.RSSIList
        x_EV3 = pop.getPopulationXList()
        y_EV3 = pop.getPopulationYList()
        z_EV3 = []
    
        if L3M_Obj.Localization_Dimensions == '2D' :
            #plot anchor Circle
            if cls.PlotLineCircle is True :
                for anchor, RSSI, noise in zip(L3M_Obj.anchorList, RSSIList, minInd.noiseList) :
                    ax.add_artist(plt.Circle(anchor.coordinate, anchor.getChannelDistance(RSSI, noise), color=next(cycol), fill=False))
            
            # plot
            ax.scatter(x_anchor, y_anchor, c='b', s=100, marker='^', label='Anchor')
            ax.scatter(target.x, target.y, c='r', s=100, marker='o', label=target.nodeName)
            ax.scatter(L3M_Obj.L3M_CoordinateDict[target.nodeName].x, L3M_Obj.L3M_CoordinateDict[target.nodeName].y, s=80, c='y', marker='o', label='L3M')
            ax.scatter(x_EV3, y_EV3, c='k', s=80, marker='*', label='EV3')
            ax.scatter(minInd.x, minInd.y, c='y', s=80, marker='*', label='EV3_min')
            
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            
            #fig.savefig('C:\\Users\\Lulumi5129\\Desktop\\2D_target\\' + str(target.ID+1) + '\\Gen_' + str(int((gen+1) + (loop*cls.generationCount))) + '.png')
        
        elif len(target.coordinate) == 3 :
            #plot anchor Circle
            if cls.PlotLineCircle is True :
                for anchor, RSSI, noise in zip(L3M_Obj.anchorList, RSSIList, minInd.noiseList) :
                    center = anchor.coordinate
                    radius = anchor.getChannelDistance(RSSI, noise)
                    u = np.linspace(0, 2 * np.pi, 100)
                    v = np.linspace(0, np.pi, 100)
                    x = radius * np.outer(np.cos(u), np.sin(v)) + center[0]
                    y = radius * np.outer(np.sin(u), np.sin(v)) + center[1]
                    z = radius * np.outer(np.ones(np.size(u)), np.cos(v)) + center[2]
                    ax.plot_wireframe(x, y, z, color=next(cycol), rstride=10, cstride=10)
            
            z_EV3 = pop.getPopulationZList()
            z_anchor = L3M_Obj.getAnchorZList()
            # plot
            ax.scatter(x_anchor, y_anchor, z_anchor, c='b', s=100, marker='^', label='Anchor')
            ax.scatter(target.x, target.y, target.z, c='r', s=100, marker='o', label=target.nodeName)
            ax.scatter(L3M_Obj.L3M_CoordinateDict[target.nodeName].x, L3M_Obj.L3M_CoordinateDict[target.nodeName].y, L3M_Obj.L3M_CoordinateDict[target.nodeName].z, s=80, c='y', marker='o', label='L3M')
            ax.scatter(x_EV3, y_EV3, z_EV3, c='k', s=80, marker='*', label='EV3')
            ax.scatter(minInd.x, minInd.y, minInd.z, c='y', s=80, marker='*', label='EV3_min')
            legend = ax.legend(loc='center right', fontsize='x-small', shadow=True)
            legend.get_frame().set_facecolor('#00FFCC')
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.set_zlabel('Z (m)')
            #fig.savefig('C:\\Users\\Lulumi5129\\Desktop\\3D_target\\' + str(target.ID+1) + '\\Gen_' + str(int((gen+1) + (loop*cls.generationCount))) + '.png')
        
        else :
            raise Exception("plot error")
        
        sum = 0
        for index in range(len(minInd.coordinate)) :
            sum += math.pow(minInd.coordinate[index]- target.coordinate[index], 2)
        distance = math.sqrt(sum)
        legend = ax.legend(loc='center right', fontsize='x-small', shadow=True)
        legend.get_frame().set_facecolor('#00FFCC')
        textstr1 = str(target) + ', Gen:' + str(gen) + '\n'
        textstr2 = 'distance between target and EV3 is %4.4f '%(distance) + ' m' + '\n'
        textstr4 = 'distance between target and L3M is %4.4f '%(L3M_Obj.L3M_CoordinateDict[target.nodeName].getDistance(target)) + ' m'
        textstr = textstr1 + textstr2 + textstr4
        textstr = textstr.replace('\t', ' ')
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        if L3M_Obj.Localization_Dimensions == '2D' :
            textbox = ax.text(x=0.05, y=0.95, s=textstr, transform=ax.transAxes, fontsize=10,bbox=props)
        else :
            textbox = ax.text(x=0.05, y=0.95, z=0.95, s=textstr, transform=ax.transAxes, fontsize=10,bbox=props)
        textbox.set_horizontalalignment("left")
        textbox.set_verticalalignment("top")
        ax.grid(True)
        plt.pause(0.05)
        plt.draw()
        
    @classmethod
    def getminInd(cls, pop):
        minval = pop[0].fit
        minInd = pop[0]
        for ind in pop :
            if ind.fit > minval:
                minval = ind.fit
                minInd = ind
                
        return minInd
    
    #Print some useful stats to screen
    @classmethod
    def printStats(cls, pop, gen, _target):
        print('Generation:',gen)
        avgval=0
        minval=pop[0].fit 
        minNoiseList=[]
        minNode = pop[0].coordinate
        mutRate=pop[0].mutRate
        for ind in pop:
            avgval+=ind.fit
            if ind.fit > minval:
                minval=ind.fit
                minNoiseList=ind.noiseList
                mutRate=ind.mutRate
                minNode=ind.coordinate
            print(ind)

        print('Min fitness',minval)
        print('Min noise List',minNoiseList)
        print('MutRate',mutRate)
        print('Avg fitness',avgval/len(pop))
        print('real target Coordinate', _target)
        print('EC estimate Coordinate', minNode)
        
    
    @classmethod
    def loopMethod_1(cls, LS_Obj, RSSIList, minInd):
        maxNoiseAnchor=0
        maxNoise=0
        from LocalizationSystem.Node.node import LogDistanceModel
        for i in range(len(minInd.noiseList)) :
            val=0
            for j in range(len(minInd.coordinate)) :
                val += (LS_Obj.anchorList[i].coordinate[j] - minInd.coordinate[j])**2
            distance = LogDistanceModel.getChannelDistance(RSSIList[i], minInd.noiseList[i])**2
            if abs(val-distance) > maxNoise :
                maxNoiseAnchor = i
                maxNoise = abs(val-distance)
    
        return maxNoiseAnchor
        
    @classmethod
    def loopMethod_2(cls, LS_Obj, RSSIList, minInd):
        avgNoise=0
        for noise in minInd.noiseList : avgNoise += noise
        avgNoise = avgNoise/len(minInd.noiseList)
        maxNoiseAnchor=0
        maxNoise=0
        for i in range(len(minInd.noiseList)) :
            if abs(minInd.noiseList[i]-avgNoise) > maxNoise :
                maxNoiseAnchor = i
                maxNoise = abs(minInd.noiseList[i]-avgNoise)
    
        return maxNoiseAnchor
        
    @classmethod
    def loopMethod_3(cls, LS_Obj, RSSIList, minInd):
        from LocalizationSystem.Node.node import LogDistanceModel
        maxNoiseAnchor=0
        maxNoise=0
        for RSSI,noise,i in zip(RSSIList, minInd.noiseList, range(len(minInd.noiseList))) : 
            distance = LogDistanceModel.getChannelDistance(RSSI, noise)
            if distance > maxNoise :
                maxNoiseAnchor = i
                maxNoise = distance
    
        return maxNoiseAnchor
    
    @classmethod
    def loopMethod_4(cls, LS_Obj, minNode, target):
        estimateNodeList = LS_Obj.L3M_Comb_CoordinateDict[target.nodeName]
        anchorList = LS_Obj.anchorList
        anchorCombDict = LS_Obj.anchorCombDict
        for i in range(len(estimateNodeList)-1) :
            for j in range(len(estimateNodeList)-i-1) :
                if estimateNodeList[j].getDistance(minNode) < estimateNodeList[j+1].getDistance(minNode) :
                    estimateNodeList[j] , estimateNodeList[j+1] = estimateNodeList[j+1],estimateNodeList[j]
        
        dirtyNode = estimateNodeList[0:7]
        anchorCount={}
        for anchor in anchorList :
            anchorCount[anchor.nodeName] = 0
        
        for node in dirtyNode :
            x = anchorCombDict['Comb_' + str(node.ID+1)]
            for i in x :
                anchorCount[i.nodeName] += 1
                
        name=''
        max = 0        
        for key in anchorCount :
            if anchorCount[key] > max : 
                max = anchorCount[key]
                name=key
        
        print('target name %s, delete anchor name is %s'%(target.nodeName, name))
        buffer=[]
        for node in range(len(estimateNodeList)) :
            comblist = anchorCombDict['Comb_' + str(estimateNodeList[node].ID+1)]
            for i in range(len(comblist)) :
                if name == comblist[i].nodeName :
                    buffer.append(node)
                    break
                
        newestimateNodeList=[]
        for node in range(len(estimateNodeList)) :
            if node not in buffer :
                newestimateNodeList.append(estimateNodeList[node])
                
        for anchor in LS_Obj.anchorList :
            if anchor.nodeName == name : 
                del LS_Obj.distanceDict[target.nodeName][LS_Obj.anchorList.index(anchor)]
                LS_Obj.anchorList.remove(anchor)
        
        return newestimateNodeList
    
    
    
    
    
    
    
    
    
    
    
    
    