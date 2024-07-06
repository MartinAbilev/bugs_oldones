from shared import *
import gfx as gx

step=0

Ann=NeuralNetwork(0)

gx.status(Ann)







def AnnStep():
    global step
    step+=1
    if step>4:
        step=0
        for n in Ann.neurons:
            for c in n.conection:
                c.value=Ann.neurons[c.to].out
                v=n.output()
        
            
    

while gx.w.is_open:    
    
    AnnStep()
        
    gx.clear()
       
    gx.gloop(Ann)
    
    
    a=1
    
