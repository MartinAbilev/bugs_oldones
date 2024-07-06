import math
import random
import sfml as sf
import time

class vector2d(object):
    def __init__(self, X, Y):
        self.x=X
        self.y=Y


class con:
    def __init__(self,To,v,w,e):
        self.to=To
        self.value=v
        self.weight=w
        self.qErrorDelta=1

class Neuron:
    def __init__(self,Id):
        print("neuron id.."+str(Id) )
        
        self.nid=Id        
        self.pos=vector2d(8,8)
        self.conection=[]
        self.child=[]
        self.parent=[]
        self.lowest=[]        
        self.out=0
        self.onmouse=0
        
    def conectInToOut(self,to,val, weight, error):
        self.conection.append(con(to,val,weight,error) )
    
    def addChild(self, ch):
        self.child.append(ch)
        
    def addParent(self, pr):
        self.parent.append(pr)
        
    def addLowest(self, lo):
        self.lowest.append(lo)
        
    def pos(self,Pos):
        self.pos.Pos
        
    def output(self):
        valueOut=0
        
        for c in self.conection:
            valueOut+=c.weight*c.value#*c.qErrorDelta
        
        
        
        self.out=math.tanh(valueOut*10)
        
        return self.out

class NeuralNetwork:     
    def __init__(self,maxNeurons):
        self.maxN=maxNeurons
        self.a=0
        self.b=6
        
        self.neurons=[]

        for i in range(maxNeurons):
            self.neurons.append(Neuron(i))
            self.maxN+=1
            
    def sort(self):
        print("sorted")

        for n in self.neurons:            
            
            n.lowest=[]
            
            n.lowest.extend(n.child)
            for ch in n.child:
                n.lowest.extend(self.neurons[ch].lowest)
            
            
            if n.nid in n.lowest: n.lowest.remove(n.nid)# nodes id nedriks zemaknozhu saraksta atkartoties
            
            n.lowest = sorted(set(n.lowest))# zemaknozhu saraksta nozhu id nedrikst atkartoties
            
            
    def randomizeWeights(self,factor):
        for neuron in self.neurons:
            for con in neuron.conection:
                con.weight=con.weight+(random.randint(-1.0, 1.0) *factor)
                if con.weight>1:con.weight=1
                if con.weight<-1:con.weight=-1
                
    def saveNet(self):
        f = open('annSaveFile.txt', 'w')
        for neuron in self.neurons:
            f.write("ID----------------------------------------------------\n")
            f.write("%s\n" % neuron.nid )
            f.write("%s," % neuron.pos.x+"%s\n" % neuron.pos.y)
            
            
            for con in neuron.conection:                
                f.write("conected Inputs\n")
                f.write("%s\n" % con.to )
                f.write("%s\n" % con.value)
                f.write("%s\n" % con.weight)
                f.write("%s\n" % con.qErrorDelta)
            
            f.write("child nodes\n")    
            for ch in neuron.child:                
                f.write("%s\n" % ch )
            
            f.write("parent nodes\n")    
            for pr in neuron.parent:                
                f.write("%s\n" % pr ) 
                
            f.write("lowest conected nodes\n")    
            for low in neuron.lowest:                
                f.write("%s\n" % low )  
            
            f.write("end\n")   
            
        f.write("ID----------------------------------------------------\n")#add this for loader to load last neuron     
        f.close()
        
    def loadNet(self):
        self.neurons=[]
        self.maxN
        f = open('annSaveFile.txt', 'r')
        content = f.readlines()
        f.close()
        
        #print(content)
        
        neuronDatta=[]
        neuronStr=[]
        
        for str in content:
            str=str.replace('\n', ' ').replace('\r', '')            
            if "ID" in str:
                neuronDatta.append(neuronStr)
                neuronStr=[]
            
            neuronStr.append(str) 
        neuronDatta.pop(0)
            
        
        
        i=0
        for neuron in neuronDatta:
            self.neurons.append(Neuron(i))
            
            self.neurons[i].id=int(neuron[1])
            
            xy=neuron[2].split(',')
            self.neurons[i].pos=sf.Vector2( float(xy[0]),float(xy[1]) )
            
            
            neuron.pop(0)
            neuron.pop(0)
            neuron.pop(0)
            
            for line in neuron:                
                if "conected Inputs" in line:
                    
                    while not "child nodes" in neuron[0]:
                        neuron.pop(0)
                        a=0
                        conecto=int(neuron[0])
                        neuron.pop(0)
                        val=float(neuron[0])
                        neuron.pop(0)
                        weight=float(neuron[0])
                        neuron.pop(0)
                        error=float(neuron[0])
                        neuron.pop(0)
                        a=0                    
                        self.neurons[i].conectInToOut(conecto,val,weight,error)
                        a=0
                
            a=0
                    
                
                    
            for line in neuron:
                if "child nodes" in line:
                    
                    neuron.pop(0)
                    
                    while not "parent nodes" in neuron[0]:
                        a=0
                        self.neurons[i].addChild( int(neuron[0]) )
                        neuron.pop(0)
                        a=0
                        
            for line in neuron:
                if "parent nodes" in line:
                    neuron.pop(0)
                    while not "lowest conected nodes" in neuron[0]:
                        self.neurons[i].addParent( int(neuron[0]) )
                        neuron.pop(0)
                        a=0
            end=0            
            for line in neuron:
                if "lowest conected nodes" in line:
                    neuron.pop(0)
                    while not "end" in neuron[0]:
                        self.neurons[i].addLowest( int(neuron[0]) )
                        neuron.pop(0)
                        a=0
                        end=1
                    neuron.pop(0)
      
        
            b=0
            i+=1
                
        
        a=0   
        self.maxN=i   
        
    
    def createGrid(self,n):
        a=0
        #radam X
        i=self.maxN
        offsetX=200
        offsetY=100
        for y in range(n):
            for x in range(n):
                self.neurons.append(Neuron(self.maxN))
                self.neurons[self.maxN].pos.x=offsetX+(x*60)
                self.neurons[self.maxN].pos.y=offsetY+(y*60)            
                self.maxN+=1
                
        #conect all to all
        
        for neuron in self.neurons:
            if neuron.nid>=i:
                for con in self.neurons:
                    if con.nid>=i: neuron.conectInToOut(con.nid,0,1,1)
                

class Neuron2:
    def __init__(self,Id):
        self.id=Id
        self.conections=[]
        self.weights=[]
        self.out=0.001
        
        self.pos=vector2d(8,8)
        
        self.child=[]
        self.parent=[]
        self.lowest=[] 
        
        
    def step(self, OutDatta):
        a=0
         
        value=0        
        
        i=0
        for con in self.conections:
            value+=self.weights[i]*OutDatta[con]
            i+=1                
            self.out=math.tanh(value*5)
        OutDatta[self.id]=self.out
        a=0
         
        #print(self.id," ",self.out)  
        a=0
        return OutDatta       

class Ann2:
    #private variables
    def __init__(self):
        a=0
        self.maxN=0
        
        #dna
        self.colorR=255
        self.colorG=0
        self.colorB=0
        
        self.poly=[]
        
        
        #brain
        self.neurons=[]
        self.outDatta=[]

    def setPoly(self, p):
        self.poly=p
    
        
    def annStep(self):
        a=0
        i=0
        #for neuron in self.neurons:
            #self.outDatta[i]=neuron.out
            #i+=1
            
        for neuron in self.neurons:
            self.outDatta=neuron.step(self.outDatta)
        a=0    
            
    def connect(self, inpA, toB, w):
        a=0      
        self.neurons[inpA].conections.append(toB)
        self.neurons[inpA].weights.append(w)
    

            
    def outSet(self,Id,value):
        self.outDatta[Id]=value
        self.neurons[Id].out=value
        
    
    def createGrid(self,n):
        a=0
        #radam X
        i=self.maxN
        offsetX=200
        offsetY=100
        for y in range(n):
            for x in range(n):
                self.neurons.append(Neuron2(self.maxN))
                self.neurons[self.maxN].pos.x=offsetX+(x*60)
                self.neurons[self.maxN].pos.y=offsetY+(y*60)            
                self.maxN+=1
                
        #conect all to all
        
        for neuron in self.neurons:
            if neuron.id>=i:
                for con in self.neurons:
                    if con.id>=i: self.connect(neuron.id,con.id,1)
                    
                    
    def createInputs(self,n):
        a=0
        #radam X
        i=self.maxN
        offsetX=100
        offsetY=100
        for y in range(n):
            for x in range(1):
                self.neurons.append(Neuron2(self.maxN))
                self.neurons[self.maxN].pos.x=offsetX+(x*60)
                self.neurons[self.maxN].pos.y=offsetY+(y*60)            
                self.maxN+=1
                
        #conect all to all
        
        for neuron in self.neurons:
            if neuron.id<i:
                for con in self.neurons:
                    if con.id>=i: self.connect(neuron.id,con.id,1)
                    
                    
    def createOutputs(self,n):
        a=0
        #radam X
        i=self.maxN
        offsetX=200
        offsetY=50
        for y in range(1):
            for x in range(n):
                self.neurons.append(Neuron2(self.maxN))
                self.neurons[self.maxN].pos.x=offsetX+(x*60)
                self.neurons[self.maxN].pos.y=offsetY+(y*60)            
                self.maxN+=1
                
        #conect all to all
        
        for neuron in self.neurons:
            if neuron.id<i:
                for con in self.neurons:
                    if con.id>=i: self.connect(con.id,neuron.id,1)
    
    
    
    
    
    def loadNet(self,fname):
        self.neurons=[]
        self.outDatta=[]
        
        f=open(fname+'DNA.txt', 'r')
        str=f.readlines()
        f.close()
        
        content=[]
        for s in str:
            s=s.replace('\n', ' ').replace('\r', '') 
            content.append(s) 
        scol=content[0].split(',')
        self.colorR=int(scol[0])
        self.colorG=int(scol[1])
        self.colorB=int(scol[2])
        
        str=content
        
        str.pop(0)
        
        for line in str:                
                if "poly" in line:
                    a=0
                    str.pop(0)
                    while not "endPoly" in str[0]:
                        a=0
                        spoly=str[0].split(',')
                        x=float(spoly[0])
                        y=float(spoly[1])
                        p=[(x),(y)]

                        self.poly.append( p ) 
                        str.pop(0)

        
        
        
        
        f = open(fname+'.txt', 'r')
        content = f.readlines()
        f.close()
        
        #print(content)
        
        neuronDatta=[]
        neuronStr=[]
        
        for str in content:
            str=str.replace('\n', ' ').replace('\r', '')            
            if "ID" in str:
                neuronDatta.append(neuronStr)
                neuronStr=[]
            
            neuronStr.append(str) 
        neuronDatta.pop(0)
            
        
        
        i=0
        for neuron in neuronDatta:
            self.neurons.append(Neuron2(i))
            self.outDatta.append(0)
            
            self.neurons[i].id=int(neuron[1])
            
            xy=neuron[2].split(',')
            self.neurons[i].pos=sf.Vector2( float(xy[0]),float(xy[1]) )
            
            
            neuron.pop(0)
            neuron.pop(0)
            neuron.pop(0)
            
            for line in neuron:                
                if "conected Inputs" in line:
                    
                    while not "child nodes" in neuron[0]:
                        neuron.pop(0)
                        a=0
                        conecto=int(neuron[0])
                        neuron.pop(0)
                        val=float(neuron[0])
                        neuron.pop(0)
                        weight=float(neuron[0])
                        neuron.pop(0)
                        error=float(neuron[0])
                        neuron.pop(0)
                        a=0                    
                        self.connect(i, conecto, weight)
                        a=0
                
            a=0
                    
                
                    
            for line in neuron:
                if "child nodes" in line:
                    
                    neuron.pop(0)
                    
                    while not "parent nodes" in neuron[0]:
                        a=0
                        self.neurons[i].child.append ( int(neuron[0]) ) 
                        neuron.pop(0)
                        a=0
                        
            for line in neuron:
                if "parent nodes" in line:
                    neuron.pop(0)
                    while not "lowest conected nodes" in neuron[0]:
                        self.neurons[i].parent.append ( int(neuron[0]) )
                        neuron.pop(0)
                        a=0
            end=0            
            for line in neuron:
                if "lowest conected nodes" in line:
                    neuron.pop(0)
                    while not "end" in neuron[0]:
                        self.neurons[i].lowest.append( int(neuron[0]) )
                        neuron.pop(0)
                        a=0
                        end=1
                    neuron.pop(0)
      
        
            b=0
            i+=1
                
        
        a=0   
        self.maxN=i   
        
        
        
        
    def saveNet(self,fname):
        
        f=open(fname+'DNA.txt', 'w')
        f.write("{0}, {1}, {2}\n".format (self.colorR,self.colorG,self.colorB) )
        f.write("poly\n")
        for poly in self.poly:
            f.write( "{0}, {1}\n".format(poly[0],poly[1]) )
        f.write("endPoly\n")
        f.close()
        
        f = open(fname+'.txt', 'w')
        
        for neuron in self.neurons:
            f.write("ID----------------------------------------------------\n")
            f.write("%s\n" % neuron.id )
            f.write("%s," % neuron.pos.x+"%s\n" % neuron.pos.y)
            
            i=0
            for con in neuron.conections:                
                f.write("conected Inputs\n")
                f.write("%s\n" % con )
                f.write("%s\n" % 0)
                f.write("%s\n" % neuron.weights[i])
                f.write("%s\n" % 666)
                i+=1
                
            
            f.write("child nodes\n")    
            for ch in neuron.child:                
                f.write("%s\n" % ch )
            
            f.write("parent nodes\n")    
            for pr in neuron.parent:                
                f.write("%s\n" % pr ) 
                
            f.write("lowest conected nodes\n")    
            for low in neuron.lowest:                
                f.write("%s\n" % low )  
            
            f.write("end\n")   
            
        f.write("ID----------------------------------------------------\n")#add this for loader to load last neuron     
        f.close()
        

        
    def randomizeDNA(self,factor):
        rnd=random.randint(-100,100)
        self.colorG+=rnd
        if self.colorG>255:self.colorG=255
        if self.colorG<0:self.colorG=0
        

        rnd=random.randint(-100,100)
        self.colorB+=rnd
        if self.colorB>255:self.colorB=255
        if self.colorB<0:self.colorB=0
        
        
        i=0
        for pol in self.poly:
            rnd=random.randint(-1,1)*factor
            L = list(pol)
            L[0]+=rnd
            
            rnd=random.randint(-1,1)*factor
            L[1]+=rnd
            self.poly[i]=L
            i+=1
            
    
    def randomizeWeights(self,factor):

        self.randomizeDNA(0.1)

        
        for neuron in self.neurons:
            i=0
            for weight in neuron.weights:
                neuron.weights[i]+=random.randint(-1.0, 1.0) *factor
                i+=1
                

                
            

        

        
        