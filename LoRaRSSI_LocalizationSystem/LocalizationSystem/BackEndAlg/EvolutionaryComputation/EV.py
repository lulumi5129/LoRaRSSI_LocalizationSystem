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
             'loopCount': (int,True)}
     
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
        
        cls.ev3(LS_Obj, target)
    
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
        Individual.learningRate=0.5
        
        Population.uniprng=uniprng
        Population.nodelimit = cls.nodelimit
        Population.crossoverFraction=cls.crossoverFraction
        
        if len(target) == 2 :
            cls.dimensions = '2D'
            Population.individualDimensions=cls.dimensions
        else :
            cls.dimensions = '3D'
            Population.individualDimensions=cls.dimensions
        
        for loop in range(cls.loopCount) :
            ClusterCenter.coordinateCluster=LS_Obj.L3M_Comb_CoordinateDict[target.nodeName]
            
            #create initial Population (random initialization)
            population=Population(cls.populationSize)
        
            #print initial pop stats    
            #cls.printStats(population,0, target)
            minNode = cls.getminNode(population)
            if loop == 0 :
                fig = plt.figure(figsize=(8,6), dpi=120)
                if cls.dimensions == '2D' :
                    ax = fig.add_subplot(111)
                else :
                    ax = fig.add_subplot(111, projection='3d')
                
            fig.suptitle(target.nodeName + " Localization System Loop" + str(loop+1))
    
            cls.plotLocalizationSystem(fig, ax, population, 0, 0, LS_Obj, target, minNode)
        
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
                #cls.printStats(population,i+1, target)
                minNode = cls.getminNode(population)
                cls.plotLocalizationSystem(fig, ax, population, loop, i+1, LS_Obj, target, minNode)
            
            LS_Obj.L3M_Comb_CoordinateDict[target.nodeName] = cls.loopMethod(LS_Obj, minNode, target)
            del population
        
        plt.show()
        
    #Plot some useful coordinate to screen
    @classmethod
    def plotLocalizationSystem(cls, fig, ax, pop, loop, gen, L3M_Obj, target, minNode):
        from itertools import cycle
        cycol=cycle('bgrcmkyb')
        ax.clear()
        x_EV3 = pop.getPopulationXList()
        y_EV3 = pop.getPopulationYList()
        z_EV3=[]
        x_L3M_Comb = L3M_Obj.getL3M_Comb_XList(target)
        y_L3M_Comb = L3M_Obj.getL3M_Comb_YList(target)
        z_L3M_Comb=[]
        x_anchor = L3M_Obj.getAnchorXList()
        y_anchor = L3M_Obj.getAnchorYList()
        z_anchor=[]
    
        if L3M_Obj.Localization_Dimensions == '2D' :
            #plot anchor Circle
            for anchor, distance in zip(L3M_Obj.anchorList, L3M_Obj.distanceDict[target.nodeName]) :
                ax.add_artist(plt.Circle(anchor.coordinate, distance, color=next(cycol), fill=False))
            
            # plot
            ax.scatter(x_anchor, y_anchor, c='b', s=100, marker='^', label='Anchor')
            ax.scatter(target.x, target.y, c='r', s=100, marker='o', label=target.nodeName)
            ax.scatter(L3M_Obj.L3M_CoordinateDict[target.nodeName].x, L3M_Obj.L3M_CoordinateDict[target.nodeName].y, s=80, c='y', marker='o', label='L3M')
            ax.scatter(x_L3M_Comb, y_L3M_Comb, c='g', marker='o', label='L3M_Comb')
            ax.scatter(x_EV3, y_EV3, c='k', marker='*', label='EV3')
            
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            
            #fig.savefig('C:\\Users\\Lulumi5129\\Desktop\\2D_target\\' + str(target.ID+1) + '\\Gen_' + str(int((gen+1) + (loop*cls.generationCount))) + '.png')
        
        elif len(target.coordinate) == 3 :
            #plot anchor Circle
            for anchor, distance in zip(L3M_Obj.anchorList, L3M_Obj.distanceDict[target.nodeName]) :
                center = anchor.coordinate
                radius = distance
                u = np.linspace(0, 2 * np.pi, 100)
                v = np.linspace(0, np.pi, 100)
                x = radius * np.outer(np.cos(u), np.sin(v)) + center[0]
                y = radius * np.outer(np.sin(u), np.sin(v)) + center[1]
                z = radius * np.outer(np.ones(np.size(u)), np.cos(v)) + center[2]
                ax.plot_wireframe(x, y, z, color=next(cycol), rstride=10, cstride=10)
            
            z_EV3 = pop.getPopulationZList()
            z_L3M_Comb = L3M_Obj.getL3M_Comb_ZList(target)
            z_anchor = L3M_Obj.getAnchorZList()
            # plot
            ax.scatter(x_anchor, y_anchor, z_anchor, c='b', s=100, marker='^', label='Anchor')
            ax.scatter(target.x, target.y, target.z, c='r', s=100, marker='o', label=target.nodeName)
            ax.scatter(L3M_Obj.L3M_CoordinateDict[target.nodeName].x, L3M_Obj.L3M_CoordinateDict[target.nodeName].y, L3M_Obj.L3M_CoordinateDict[target.nodeName].z, s=80, c='y', marker='o', label='L3M')
            ax.scatter(x_L3M_Comb, y_L3M_Comb, z_L3M_Comb, c='g', marker='o', label='L3M_Comb')
            ax.scatter(x_EV3, y_EV3, z_EV3, c='k', marker='*', label='EV3')
            legend = ax.legend(loc='center right', fontsize='x-small', shadow=True)
            legend.get_frame().set_facecolor('#00FFCC')
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.set_zlabel('Z (m)')
            #fig.savefig('C:\\Users\\Lulumi5129\\Desktop\\3D_target\\' + str(target.ID+1) + '\\Gen_' + str(int((gen+1) + (loop*cls.generationCount))) + '.png')
        
        else :
            raise Exception("plot error")
        
        legend = ax.legend(loc='center right', fontsize='x-small', shadow=True)
        legend.get_frame().set_facecolor('#00FFCC')
        textstr1 = str(target) + ', Gen:' + str(gen) + '\n'
        textstr2 = str(minNode) + '\n'
        textstr3 = 'distance between target and EV3 is %4.4f '%(minNode.getDistance(target)) + ' m\n'
        textstr4 = 'distance between target and L3M is %4.4f '%(L3M_Obj.L3M_CoordinateDict[target.nodeName].getDistance(target)) + ' m'
        textstr = textstr1 + textstr2 + textstr3 + textstr4
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
    def getminNode(cls, pop):
        avgval=0
        minval=pop[0].fit 
        minNode = pop[0]
        mutRate=pop[0].mutRate
        for ind in pop:
            avgval+=ind.fit
            if ind.fit > minval:
                minval=ind.fit
                mutRate=ind.mutRate
                minNode=ind
                
        return minNode
    
    #Print some useful stats to screen
    @classmethod
    def printStats(cls, pop, gen, _target):
        print('Generation:',gen)
        avgval=0
        minval=pop[0].fit 
        minNode = pop[0]
        mutRate=pop[0].mutRate
        for ind in pop:
            avgval+=ind.fit
            if ind.fit > minval:
                minval=ind.fit
                mutRate=ind.mutRate
                minNode=ind
            print(ind)

        print('Min fitness',minval)
        print('MutRate',mutRate)
        print('Avg fitness',avgval/len(pop))
        print('real target Coordinate', _target)
        print('EC estimate Coordinate', minNode)
        print('distance between EC Node and real node', minNode.getDistance(_target), end='')
        print(' m')
    
    @classmethod
    def loopMethod_1(cls, LS_Obj, minNode, target):
        estimateNodeList = LS_Obj.L3M_Comb_CoordinateDict[target.nodeName]
        for i in range(len(estimateNodeList)-1) :
            for j in range(len(estimateNodeList)-i-1) :
                if estimateNodeList[j].getDistance(minNode) < estimateNodeList[j+1].getDistance(minNode) :
                    estimateNodeList[j] , estimateNodeList[j+1] = estimateNodeList[j+1],estimateNodeList[j]
        
        if len(estimateNodeList[0]) == 2 :
            estimateNodeList[0].x = (estimateNodeList[0].x+ minNode.x)/2
            estimateNodeList[0].y = (estimateNodeList[1].y+ minNode.y)/2
            
        else :
            estimateNodeList[0].x = (estimateNodeList[0].x+ minNode.x)/2
            estimateNodeList[0].y = (estimateNodeList[1].y+ minNode.y)/2
            estimateNodeList[0].z = (estimateNodeList[1].z+ minNode.z)/2
    
        return estimateNodeList
        
    @classmethod
    def loopMethod_2(cls, LS_Obj, minNode, target):
        estimateNodeList = LS_Obj.L3M_Comb_CoordinateDict[target.nodeName]
        for i in range(len(estimateNodeList)-1) :
            for j in range(len(estimateNodeList)-i-1) :
                if estimateNodeList[j].getDistance(minNode) < estimateNodeList[j+1].getDistance(minNode) :
                    estimateNodeList[j] , estimateNodeList[j+1] = estimateNodeList[j+1],estimateNodeList[j]
        
        estimateNodeList[0].coordinate = minNode.coordinate
    
        return estimateNodeList
        
    @classmethod
    def loopMethod_3(cls, LS_Obj, minNode, target):
        estimateNodeList = LS_Obj.L3M_Comb_CoordinateDict[target.nodeName]
        for i in range(len(estimateNodeList)-1) :
            for j in range(len(estimateNodeList)-i-1) :
                if estimateNodeList[j].getDistance(minNode) < estimateNodeList[j+1].getDistance(minNode) :
                    estimateNodeList[j] , estimateNodeList[j+1] = estimateNodeList[j+1],estimateNodeList[j]
        
        del estimateNodeList[0]
    
        return estimateNodeList
    
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
            if anchor.nodeName == name : LS_Obj.anchorList.remove(anchor)
        
        return newestimateNodeList
    
    
    
    
    
    
    
    
    
    
    
    
    