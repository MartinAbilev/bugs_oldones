import time 
from shared import *
import sfml as sf
from vmath import *


w = sf.RenderWindow(sf.VideoMode(640, 480), "CYBERMIND v0.1", sf.Style.DEFAULT ,sf.ContextSettings(8, 16, 8, 2, 0) )  
#int depth=0, int stencil=0, int antialiasing=0, int major=2, int minor=0)
#w.window.ContextSettings(8, 16, 4, 2, 0)
#mPos=sf.Vector2(0, 0)


mouseOn=-1

global rButton

cstate=-1
cswitch=0

selected=0
onbutton=0

# declare and load a font
try: font = sf.Font.from_file("arial.ttf")
except IOError: 
        print("font error")
        exit(1)



    

def status(ann):
    print(ann.maxN)
    print(ann.a)
    print(ann.b)
    global cstate
    
        
def clear():
    w.clear() # clear screen
    

        

def circle(pos,r,c):
    g=0
    if c<0:
        g=c*-1
        c=0
    
    if g>255:g=255
        
    
    
    if c>255:c=255
    
    if cDist(pos, mPos)<r:
        #print("colizion "+str(cDist(pos, mPos) ) )
        r-=4
        onmouse=1
    else:
        onmouse=0
    
    crcl=sf.CircleShape()
    
    crcl.radius=r
    crcl.outline_color=sf.Color.RED
    crcl.fill_color=sf.Color(c , g, 0)
    crcl.outline_thickness=1
    crcl.position = (pos.x-crcl.radius, pos.y-crcl.radius)
    crcl.point_count=6
    
    w.draw(crcl)
    return onmouse
        
     
     
def line(frm,to):
        lines = sf.VertexArray(sf.PrimitiveType.LINES_STRIP, 2)
        lines[0].position = ( float(frm.x), float(frm.y) )
        lines[1].position = ( float(to.x), float(to.y) )

        w.draw(lines)
        
        
def square(a, b):
    sq=sf.VertexArray(sf.PrimitiveType.LINES_STRIP, 5)
    sq[0].position = (a.x, a.y)
    sq[1].position = (b.x, a.y)
    sq[2].position = (b.x, b.y)
    sq[3].position = (a.x, b.y)
    sq[4].position = (a.x, a.y)
    
    w.draw(sq)
    
    
    if mPos.x>a.x and mPos.x<b.x and mPos.y>a.y and mPos.y<b.y: return 1
    else: return 0
        







def text(msg,pos,c,s):
    # declare and load a font
    global font 
    
    # create a text
    text = sf.Text(msg)
    text.font = font
    text.character_size = s
    text.style = sf.Text.REGULAR
    text.color = c
    text.position=( sf.Vector2(pos.x+16, pos.y-11) )
    
    w.draw(text)


def button(name, pos):
    global onbutton 
        
    if square(pos, sf.Vector2(pos.x+4*16, pos.y+16))==1: 
        col=sf.Color.RED
        bool= 1
        onbutton=1
    else: 
        col=sf.Color.WHITE
        bool= 0
        
    
    
    offset=sf.Vector2(0, 8)
    text(name, pos+offset, col,16)
    return bool


def gui(ann):
    a=0
    
def gloop(ann):
    global mPos
    global mouseOn
    global cstate 
    global cswitch
    global selected
    global onbutton
    onbutton=0
    
    mPos = sf.Mouse.get_position(w)  
    
    
    
    
    
    
    

    
    for event in w.events:
                # close window: exit
                if type(event) is sf.CloseEvent:
                    w.close()
                if type(event) is sf.ResizeEvent:
                    
                    pos=w.position
                    
                    w.recreate(sf.VideoMode(event.size.x, event.size.y), "CYBERMIND v0.1", sf.Style.DEFAULT ,sf.ContextSettings(8, 16, 8, 2, 0))
                    
                    w.position=pos
                    
                if type(event) is sf.MouseWheelEvent:
                    ann.neurons[mouseOn].out+=event.delta *0.1
    
  
    if not sf.Mouse.is_button_pressed(sf.Mouse.LEFT):mouseOn=-1
    
    
    for neuron in ann.neurons:
        for c in neuron.conection:
            line(neuron.pos, ann.neurons[c.to].pos)    
    
    
    for neuron in ann.neurons:
        
        if circle(neuron.pos, 16, 255*neuron.out)==1:
            mouseOn=neuron.nid
        #text
        text(str( round(neuron.out,3) ) , neuron.pos , sf.Color.RED, 8  )
            
    
    
    #buttons
    bp=10
    if  button("save", sf.Vector2(10, bp) )==1 and sf.Mouse.is_button_pressed(sf.Mouse.LEFT): 
        print("save")
        ann.saveNet()
        time.sleep(1)  

    bp+=30
        
        
    if  button("load", sf.Vector2(10, bp) )==1 and sf.Mouse.is_button_pressed(sf.Mouse.LEFT): 
        print("load")
        ann.loadNet()
        time.sleep(1)  
    bp+=30

    
    if  button("clear", sf.Vector2(10, bp) )==1 and sf.Mouse.is_button_pressed(sf.Mouse.LEFT): 
        print("clear")
        ann.neurons=[]
        ann.maxN=0
    bp+=30
    
    
    if  button("sort", sf.Vector2(10, bp) )==1 and sf.Mouse.is_button_pressed(sf.Mouse.LEFT): 
        ann.sort()
    bp+=30
    
    if  button("train", sf.Vector2(10, bp) )==1 and sf.Mouse.is_button_pressed(sf.Mouse.LEFT): 
        print("Train as ERROR")
    bp+=30
    
    if  button("rand", sf.Vector2(10, bp) )==1 and sf.Mouse.is_button_pressed(sf.Mouse.LEFT): 
        print("randomize veights")
        ann.randomizeWeights()
    bp+=30
    
    if  button("crgrid", sf.Vector2(10, bp) )==1 and sf.Mouse.is_button_pressed(sf.Mouse.LEFT): 
        print("crgrid")
        ann.createGrid(6)
        time.sleep(1.0)
    bp+=30
        
        
            
    #creation      
    if sf.Mouse.is_button_pressed(sf.Mouse.LEFT) and mouseOn==-1 and onbutton ==0:
        print("mouse down")
        
        ann.neurons.append(Neuron(ann.maxN))
        
        ann.neurons[ann.maxN].pos=mPos#!!!!!!!!!!! pec load inga japievieno ci ir max neuroni beigas
        
        ann.maxN+=1
        
        print (str(onbutton))
        
        time.sleep(0.3)  
    
    #moovings
    
    if sf.Mouse.is_button_pressed(sf.Mouse.LEFT) and mouseOn>=0 :
        old =ann.neurons[mouseOn].pos
        ann.neurons[mouseOn].pos=mPos
        
        for ch in ann.neurons[mouseOn].lowest:
            
            distX=ann.neurons[mouseOn].pos-old
            
            #if(ch!=ann.neurons[mouseOn].nid):ann.neurons[ch].pos+=distX
            ann.neurons[ch].pos+=distX
            
        
        
        selected=mouseOn
        
    
    
    #conectings
    if  sf.Mouse.is_button_pressed(sf.Mouse.RIGHT) and mouseOn>=0 and cswitch==0:
        print("right mb pressed on. "+str(mouseOn))
        cstate=mouseOn
        cswitch=1
     
            
    if  not sf.Mouse.is_button_pressed(sf.Mouse.RIGHT) and mouseOn==-1 and cswitch==1 :
        cstate=-1
        cswitch=2
        
    if  sf.Mouse.is_button_pressed(sf.Mouse.RIGHT) and mouseOn>=0 and cswitch==2:
        cstate=-1
        cswitch=0
    
    
    if  sf.Mouse.is_button_pressed(sf.Mouse.RIGHT) and mouseOn>=0 and cstate >=0 and cstate !=mouseOn and cswitch==1 :
        print("right mb pressed on. "+str(mouseOn))
        ann.neurons[mouseOn].conectInToOut(cstate,0,1,0)
        ann.neurons[cstate].child.append(mouseOn)
        ann.neurons[mouseOn].parent.append(cstate)
        ann.sort()
        
        cstate=-1
        cswitch=2
    
        
            
        
        
        
            
    if  cswitch==1:
        line(ann.neurons[cstate].pos, mPos)  
        
    if  cswitch==2 and mouseOn==-1:
        cswitch=0
    
    text("cstate="+str(cstate)+"; cswitch="+str(cswitch)+"; mouseon="+str(mouseOn), sf.Vector2(100,10), sf.Color.WHITE, 18)    

    #draw mouse
    circle(mPos,4, 1.0)
    
        
    
  
      
    w.display() # update the window  