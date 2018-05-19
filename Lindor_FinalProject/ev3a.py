#
# ev3a.py: An elitist (mu+mu) generational-with-overlap EA
#
#
# To run: python ev3a.py --input ev3_example.cfg
#         python ev3a.py --input my_params.cfg
#
# Basic features of ev3a:
#   - Supports self-adaptive mutation
#   - Uses binary tournament selection for mating pool
#   - Uses elitist truncation selection for survivors
#   - Supports IntegerVector and Multivariate Individual types
#

import optparse
import sys
import yaml
import math
from random import Random
from Population import *
import matplotlib.pyplot as plt
from multiprocessing import Pool
import time
from L3M_System import *
from L3M_equation import L3M_Equation
from mpl_toolkits.mplot3d import Axes3D
from test.libregrtest.save_env import multiprocessing

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
             'poolEvaluator': (bool,True),
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
     
    #string representation for class data    
    def __str__(self):
        return str(yaml.dump(self.__dict__))
         
#Print some useful stats to screen
def plotLocalizationSystem(fig, ax, pop, loopCount, totalGen, gen, estimateNodeList, anchorList, target, minNode, L3MNode):
    ax.clear()
    x_EV3=[]
    y_EV3=[]
    z_EV3=[]
    x_EC=[]
    y_EC=[]
    z_EC=[]
    x_anchor=[]
    y_anchor=[]
    z_anchor=[]
    x_target=[]
    y_target=[]
    z_target=[]
    
    if len(target.coordinate) == 2 :
        for ind in pop :
            x_EV3.append(ind.state.coordinate[0])
            y_EV3.append(ind.state.coordinate[1])

        for estimateNode in estimateNodeList :
            x_EC.append(estimateNode.coordinate[0])
            y_EC.append(estimateNode.coordinate[1])
    
        for anchor in anchorList :
            x_anchor.append(anchor.coordinate[0])
            y_anchor.append(anchor.coordinate[1])
    
        x_target.append(target.coordinate[0])
        y_target.append(target.coordinate[1])
        
        ax.scatter(x_anchor, y_anchor, c='b', s=100, marker='^', label='anchor')
        ax.scatter(x_target, y_target, c='r', s=100, marker='o', label='Real Target')
        ax.scatter(L3MNode.coordinate[0], L3MNode.coordinate[1], s=100, c='y', marker='o', label='L3M Target')
        ax.scatter(x_EC, y_EC, c='g', marker='x', label='estimate Target')
        ax.scatter(x_EV3, y_EV3, c='k', marker='*', label='EV3 Target')
        legend = ax.legend(loc='center right', fontsize='x-small', shadow=True)
        legend.get_frame().set_facecolor('#00FFCC')
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        textstr1 = str(target.NodeID) + ' [%4.2f,%4.2f]'%(target.coordinate[0],target.coordinate[1]) + '\n'
        textstr2 = str(minNode.NodeID) + ' [%4.2f,%4.2f]'%(minNode.coordinate[0],minNode.coordinate[1]) + '\n'
        textstr3 = 'distance with minNode is %4.4f '%(L3M_Equation.Euclidean_distance(minNode, target)) + ' m\n'
        textstr4 = 'distance with L3MNode is %4.4f '%(L3M_Equation.Euclidean_distance(L3MNode, target)) + ' m'
        textstr = textstr1 + textstr2 + textstr3 + textstr4
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        textbox = ax.text(x=0.05, y=0.95, s=textstr, transform=ax.transAxes, fontsize=10,bbox=props)
        textbox.set_horizontalalignment("left")
        textbox.set_verticalalignment("top")
        #fig.savefig('C:\\Users\\Lulumi5129\\Desktop\\' + str(target.NodeID) + '\\Gen_' + str(int((gen+1) + (loopCount*totalGen))) + '.png')
        ax.grid(True)
        plt.pause(0.05)
        plt.draw()
        
    elif len(target.coordinate) == 3 :
        #plt.figure().add_subplot(111, projection='3d')
        
        for ind in pop :
            x_EV3.append(ind.state.coordinate[0])
            y_EV3.append(ind.state.coordinate[1])
            z_EV3.append(ind.state.coordinate[2])

        for estimateNode in estimateNodeList :
            x_EC.append(estimateNode.coordinate[0])
            y_EC.append(estimateNode.coordinate[1])
            z_EC.append(estimateNode.coordinate[2])
    
        for anchor in anchorList :
            x_anchor.append(anchor.coordinate[0])
            y_anchor.append(anchor.coordinate[1])
            z_anchor.append(anchor.coordinate[2])
    
        x_target.append(target.coordinate[0])
        y_target.append(target.coordinate[1])
        z_target.append(target.coordinate[2])
        
        ax.scatter(x_anchor, y_anchor, z_anchor, c='b', s=100, marker='^', label='anchor')
        ax.scatter(x_target, y_target, z_target, c='r', s=100, marker='o', label='Real Target')
        ax.scatter(L3MNode.coordinate[0], L3MNode.coordinate[1], L3MNode.coordinate[2], s=100, c='y', marker='o', label='L3M Target')
        ax.scatter(x_EC, y_EC, z_EC, c='g', marker='o', label='estimate Target')
        ax.scatter(x_EV3, y_EV3, z_EV3, c='k', marker='*', label='EV3 Target')
        legend = ax.legend(loc='center right', fontsize='x-small', shadow=True)
        legend.get_frame().set_facecolor('#00FFCC')
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        textstr1 = str(target.NodeID) + ' [%4.2f,%4.2f,%4.2f]'%(target.coordinate[0],target.coordinate[1],target.coordinate[2]) + '\n'
        textstr2 = str(minNode.NodeID) + ' [%4.2f,%4.2f,%4.2f]'%(minNode.coordinate[0],minNode.coordinate[1],minNode.coordinate[2]) + '\n'
        textstr3 = 'distance with minNode is %4.4f '%(L3M_Equation.Euclidean_distance(minNode, target)) + ' m\n'
        textstr4 = 'distance with L3MNode is %4.4f '%(L3M_Equation.Euclidean_distance(L3MNode, target)) + ' m'
        textstr = textstr1 + textstr2 + textstr3 + textstr4
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        textbox = ax.text(x=0.05, y=0.95, z=0.05, s=textstr, transform=ax.transAxes, fontsize=10,bbox=props)
        textbox.set_horizontalalignment("left")
        textbox.set_verticalalignment("top")
        
        #fig.savefig('C:\\Users\\Lulumi5129\\Desktop\\' + str(target.NodeID) + '\\Gen_' + str(int((gen+1) + (loopCount*totalGen))) + '.png')
        ax.grid(True)
        plt.pause(0.05)
        plt.draw()
        
    else :
        raise Exception("plot error")

#Print some useful stats to screen
def printStats(pop, gen, _target):
    print('Generation:',gen)
    avgval=0
    minval=pop[0].fit 
    mutRate=pop[0].mutRate
    minNode=None
    for ind in pop:
        avgval+=ind.fit
        if ind.fit > minval:
            minval=ind.fit
            mutRate=ind.mutRate
            minNode=ind.state
        print(ind)

    print('Min fitness',minval)
    print('MutRate',mutRate)
    print('Avg fitness',avgval/len(pop))
    print('real target Coordinate', _target)
    print('EC estimate Coordinate', minNode)
    print('distance between EC Node and real node', L3M_Equation.Euclidean_distance(minNode, _target), end='')
    print(' m')
    
    return minNode
    

#L3M
def L3M(L3M_cfg):
    #set static params on L3M
    L3MSys.L3MSys_setting(L3M_cfg)
    
    
    
    #create anchor node list
    #
    # list = [[x,y],[x,y],[x,y]...], index 0 = anchor_1
    if L3M_cfg.L3MSys_Dimensions == '2D' :
        anchorList = L3MSys.CreateNodeList('anchor', NodeXList=L3M_cfg.anchorNode_X_List, NodeYList=L3M_cfg.anchorNode_Y_List)    
    elif L3M_cfg.L3MSys_Dimensions == '3D' :
        anchorList = L3MSys.CreateNodeList('anchor', NodeXList=L3M_cfg.anchorNode_X_List, NodeYList=L3M_cfg.anchorNode_Y_List, NodeZList=L3M_cfg.anchorNode_Z_List)    
    else :
        raise Exception('L3MSys_Dimensions must be 2D or 3D')
    
    #print anchor node list
    for node in anchorList : print(node)    
    
    #create target node list
    #
    # list = [[x,y],[x,y],[x,y]...], index 0 = target_1
    if L3M_cfg.L3MSys_Dimensions == '2D' :
        targetList = L3MSys.CreateNodeList('target', NodeXList=L3M_cfg.targetNode_X_List, NodeYList=L3M_cfg.targetNode_Y_List)    
    elif L3M_cfg.L3MSys_Dimensions == '3D' :
        targetList = L3MSys.CreateNodeList('target', NodeXList=L3M_cfg.targetNode_X_List, NodeYList=L3M_cfg.targetNode_Y_List, NodeZList=L3M_cfg.targetNode_Z_List)    
    else :
        raise Exception('L3MSys_Dimensions must be 2D or 3D')
    
    #print target node list
    for node in targetList : print(node)
    
    #print Real distance Dict between anchor and target
    #
    # Dict = {'Target_1':[d11, d12, d13], 'Target_2':[d21, d22, d23]...}
    Real_distance_Dict={}
    for target in targetList :
        Real_distance=[]
        print("TargetNode name \"%s\" :\nReal distance between ---"%(target.NodeID))
        for anchor in anchorList :
            print("\t --%s : %8.4f m"%(anchor.NodeID, anchor.distance(target)))
            Real_distance.append(anchor.distance(target))
        
        Real_distance_Dict[target.NodeID] = Real_distance
    
    #get pseudo RSSI dict and noise dict between anchor and target  
    # 
    #  pseudo RSSI Dict  = {'Target_1':[R11, R12, R13], 'Target_2':[R21, R22, R23]...}
    #  pseudo noise Dict = {'Target_1':[n11, n12, n13], 'Target_2':[n21, n22, n23]...}
    (pseudoRSSIDict, noiseDict) = L3MSys.getPsudoRSSIValue(anchorList, targetList)
    
    #print RSSI between anchor and target
    for target in pseudoRSSIDict :
        print("TargetNode name \"%s\" :\nRSSI between ---"%(target))
        for anchor in range(len(pseudoRSSIDict[target])) :
            print("\t --anchor %d : %9.4f dBm \tnoise = %8.4f dBm"%(anchor, pseudoRSSIDict[target][anchor], noiseDict[target][anchor]))
            
    #get psudo distance between anchor and target
    #
    # Dict = {'Target_1':[d11, d12, d13], 'Target_2':[d21, d22, d23]...}
    pseudoDistanceDict = L3MSys.getEstimateDistance(pseudoRSSIDict)
    
    #print estimate distance between anchor and target
    for target in pseudoDistanceDict :
        print("TargetNode name \"%s\" :\nestimate RSSI between ---"%(target))
        for anchor in range(len(pseudoDistanceDict[target])) :
            print("\t -- anchor %d : %9.4f m \tReal distance = %8.4f m \tnoise = %8.4f dBm"%(anchor, pseudoDistanceDict[target][anchor], Real_distance_Dict[target][anchor], noiseDict[target][anchor]))
    
    #get estimate coordinate Dict
    #
    # Dict = {'Target_1' : [x,y], 'Target_2' : [x,y]...}
    estimateCoordinateDict = L3MSys.L3M_estimateCoordinate(targetList, anchorList, pseudoRSSIDict)
    
    #print Target estimate coordinate 
    for key in estimateCoordinateDict :
        print("TargetNode name \"%s\" :\nestimate Coordinate List , Total have %d---"%(key, len(estimateCoordinateDict[key])))
        print('\t --Count %3d : '%(1), estimateCoordinateDict[key])
        
    #get Target possible estimate coordinate Dict use comb 
    #
    # Dict = {'Target_1' : [[x1,y1], [x2,y2],...], 'Target_2' : [[x1,y1], [x2,y2],...], ...}
    estimateCoordinateCombDict = L3MSys.L3MC_estimateCoordinate(targetList, anchorList, pseudoRSSIDict)
    
    #print Target possible estimate coordinate 
    for key in estimateCoordinateCombDict :
        print("TargetNode name \"%s\" :\nestimate Coordinate List , Total %d---"%(key, len(estimateCoordinateCombDict[key])))
        for i in range(len(estimateCoordinateCombDict[key])) :
            print('\t --Count %3d : '%(i+1), estimateCoordinateCombDict[key][i])
            
    #Creat Target possible estimate coordinate Node struct
    #
    # Dict = {'Target_1' : [en1, en2], 'Target_2' : [en1, en2], ...} for "en1" is class.Node
    estimateNodeDict={}
    for key in estimateCoordinateCombDict :
        estimateNodeDict[key] = L3MSys.CreateestimateNodeList(estimateCoordinateCombDict[key])
    
    #Creat L3M Target estimate coordinate Node struct
    #
    # Dict = {'Target_1' : L3MNode1, 'Target_2' : L3MNode2, ...} for "L3MNode1" is class.Node
    L3MNodeDict={}
    for key in estimateCoordinateDict :
        L3MNodeDict[key] = L3MSys.CreateestimateNodeList_L3M(estimateCoordinateDict[key])
    
    
    return (estimateNodeDict, anchorList, targetList, L3MNodeDict)     

def loopMethod_1(estimateNodeList, minNode):
    for i in range(len(estimateNodeList)) :
        for j in range(len(estimateNodeList)-1) :
            if estimateNodeList[j].distance(minNode) < estimateNodeList[j+1].distance(minNode) :
                estimateNodeList[j] , estimateNodeList[j+1] = estimateNodeList[j+1],estimateNodeList[j]
        
    if len(estimateNodeList[0].coordinate) == 2 :
        estimateNodeList[0].coordinate[0] = (estimateNodeList[0].coordinate[0]+ minNode.coordinate[0])/2
        estimateNodeList[0].coordinate[1] = (estimateNodeList[1].coordinate[1]+ minNode.coordinate[1])/2
            
    elif len(estimateNodeList[0].coordinate) == 3 :
        estimateNodeList[0].coordinate[0] = (estimateNodeList[0].coordinate[0]+ minNode.coordinate[0])/2
        estimateNodeList[0].coordinate[1] = (estimateNodeList[1].coordinate[1]+ minNode.coordinate[1])/2
        estimateNodeList[0].coordinate[2] = (estimateNodeList[2].coordinate[2]+ minNode.coordinate[2])/2
    else :
        raise Exception("2D 3D error")
    
    return estimateNodeList

def loopMethod_2(estimateNodeList, minNode):
    for i in range(len(estimateNodeList)) :
        for j in range(len(estimateNodeList)-1) :
            if estimateNodeList[j].distance(minNode) < estimateNodeList[j+1].distance(minNode) :
                estimateNodeList[j] , estimateNodeList[j+1] = estimateNodeList[j+1],estimateNodeList[j]
        
    estimateNodeList[0].coordinate = minNode.coordinate
    
    return estimateNodeList

def loopMethod_3(estimateNodeList, minNode):
    for i in range(len(estimateNodeList)) :
        for j in range(len(estimateNodeList)-1) :
            if estimateNodeList[j].distance(minNode) < estimateNodeList[j+1].distance(minNode) :
                estimateNodeList[j] , estimateNodeList[j+1] = estimateNodeList[j+1],estimateNodeList[j]
        
    del estimateNodeList[0]
    
    return estimateNodeList

def ev3(inputFileName, estimateNodeList, anchorList, target, L3MNode):
    #Get EV3 config params
    EV3_cfg=EV3_Config(inputFileName)
        
    #print config params
    #print(EV3_cfg)
        
    #Get EV3 config params
    L3M_cfg=L3M_Config(inputFileName)
    #set static params on L3M
    L3MSys.L3MSys_setting(L3M_cfg)
    
    #start random number generators
    uniprng=Random()
    uniprng.seed(EV3_cfg.randomSeed)
    normprng=Random()
    normprng.seed(EV3_cfg.randomSeed+101)
    
    
    #set static params on classes
    # (probably not the most elegant approach, but let's keep things simple...)
    Individual.uniprng=uniprng
    Individual.normprng=normprng
    Population.uniprng=uniprng
    Population.crossoverFraction=EV3_cfg.crossoverFraction
    Individual.fitFunc=L3M_Equation.Euclidean_distance_fitnessFunc
    Individual.learningRate=0.5
    Population.individualType=L3MIndividual
    
    L3MIndividual.nodeGenCls=L3MSys.CreateEV3Node  
    loopCount = EV3_cfg.loopCount
    #loopCount = 1
    
    for loop in range(loopCount) :
        Individual.estimateNodeList=estimateNodeList
        #create initial Population (random initialization)
        population=Population(EV3_cfg.populationSize)
        
        #print initial pop stats    
        minNode = printStats(population,0, target)
        if loop == 0 :
            fig = plt.figure(figsize=(8,6), dpi=120)
            if len(target.coordinate) == 2 :
                ax = fig.add_subplot(111)
            elif len(target.coordinate) == 3 :
                ax = fig.add_subplot(111, projection='3d')
            else :
                raise Exception("plot error")
        fig.suptitle(target.NodeID + " Localization System Loop" + str(loop+1))
    
        plotLocalizationSystem(fig, ax, population, 0, EV3_cfg.generationCount, 0, estimateNodeList, anchorList, target, minNode, L3MNode)
        
        #evolution main loop
        for i in range(EV3_cfg.generationCount):
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
            population.truncateSelect(EV3_cfg.populationSize)
        
            #print population stats    
            minNode = printStats(population,i+1, target)
            plotLocalizationSystem(fig, ax, population, loop, EV3_cfg.generationCount, i+1, estimateNodeList, anchorList, target, minNode, L3MNode)
        
        estimateNodeList = loopMethod_3(estimateNodeList, minNode)
        del population
        
    plt.show()
    
#
# Main entry point
#
def main(argv=None):
    if argv is None:
        argv = sys.argv
        
    try:
        #
        # get command-line options
        #
        parser = optparse.OptionParser()
        parser.add_option("-i", "--input", action="store", dest="inputFileName", help="input filename", default=None)
        parser.add_option("-q", "--quiet", action="store_true", dest="quietMode", help="quiet mode", default=False)
        parser.add_option("-d", "--debug", action="store_true", dest="debugMode", help="debug mode", default=False)
        (options, args) = parser.parse_args(argv)
        
        #validate options
        if options.inputFileName is None:
            raise Exception("Must specify input file name using -i or --input option.")
        
        #Get EV3 config params
        EV3_cfg=EV3_Config(options.inputFileName)
        
        #print config params
        print(EV3_cfg)
        
        #Get EV3 config params
        L3M_cfg=L3M_Config(options.inputFileName)
        
        #print config params
        print(L3M_cfg)
        
        #run L3M
        (estimateNodeDict, anchorList, targetList, L3MNodeDict) = L3M(L3M_cfg)  
        
        #run EV3 
        for target in targetList :
            p = multiprocessing.Process(target=ev3, args=(options.inputFileName, estimateNodeDict[target.NodeID], anchorList, target, L3MNodeDict[target.NodeID][0],))
            p.start()
            #ev3(EV3_cfg, estimateNodeDict[target.NodeID], anchorList, target)
        
        p.join()
        
        if not options.quietMode:                    
            print('EV3 Completed!')    
        
    except Exception as info:
        if 'options' in vars() and options.debugMode:
            from traceback import print_exc
            print_exc()
        else:
            print(info)
    

if __name__ == '__main__':
    cmd=['ev3a.py', '-i', 'EV_LocalizationSystem.cfg']
    main(cmd)
    
