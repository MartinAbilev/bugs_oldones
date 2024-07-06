
from shared import *
#http://www.python-sfml.org/tutorials.html#graphics

print("Ok")
#import Box2D # The main library
from Box2D import * # This maps Box2D.b2Vec2 to vec2 (and so on)
import sfml as sf
import time
import math
w = sf.RenderWindow(sf.VideoMode(640, 480), "My first pySFML Window - or not ?")
renderTexture=sf.RenderTexture(640,480)
texture = renderTexture.texture
simage=texture.to_image()
#box2d world
annRecord=0
cnext=0
max=0
gr=3*3

# declare and load a font
try: font = sf.Font.from_file("arial.ttf")
except IOError: 
        print("font error")
        exit(1)
def text(msg,pos,c,s):
    # declare and load a font
    global font 
    
    # create a text
    text = sf.Text(msg)
    text.font = font
    text.character_size = s
    text.style = sf.Text.REGULAR
    text.color = c
    text.position=( sf.Vector2(pos.x, pos.y-11) )
    
    w.draw(text)

lifeTimeRecord=0

class myContactListener(b2ContactListener):
    def __init__(self):
        b2ContactListener.__init__(self)
    def BeginContact(self, contact):
        
        fixtureA = contact.fixtureA
        bodyA = fixtureA.body
        actorA = bodyA.userData
        
        fixtureB = contact.fixtureB
        bodyB = fixtureB.body
        actorB = bodyB.userData
        

        
        
        if not actorA=="as" and  not actorB=="as":
            
            for obj in objects:
                if obj.oId==actorA: 
                    obj.lives-=1
                    #obj.body.active=0
                    
            for obj in objects:
                if obj.oId==actorB: 
                    obj.lives-=1
                    #obj.body.active=0
                
     
                
        pass
    
    def EndContact(self, contact):
        pass
    def PreSolve(self, contact, oldManifold):
        pass
    def PostSolve(self, contact, impulse):
        pass





class mworld:
    def __init__(self):
        self.world=b2World(contactListener=myContactListener(), gravity=(0,-1),doSleep=True)
        self.timeStep = 1.0 / 60


        self.ground_body=self.world.CreateStaticBody( position=(0,0), shapes=b2PolygonShape(box=(500,5)), )
        self.ground_body.userData = "passive"
        self.ground_body=self.world.CreateStaticBody( position=(0,400), shapes=b2PolygonShape(box=(500,5)), )
        self.ground_body.userData = "passive"

        self.ground_body=self.world.CreateStaticBody( position=(0,0), shapes=b2PolygonShape(box=(5,500)), )
        self.ground_body.userData = "passive"
        self.ground_body=self.world.CreateStaticBody( position=(500,0), shapes=b2PolygonShape(box=(5,500)), )
        self.ground_body.userData = "passive"


   
wrld=mworld()

        

        

def dcircle(pos,angle,r,R,G,B):

    
    '''if cDist(pos, mPos)<r:
        #print("colizion "+str(cDist(pos, mPos) ) )
        r-=4
        onmouse=1
    else:
        onmouse=0
   ''' 
    crcl=sf.CircleShape()
    
    crcl.radius=r
    crcl.outline_color=sf.Color.RED
    #print(R,G,B)
    crcl.fill_color=sf.Color(R , G, B)
    crcl.outline_thickness=1
    crcl.position = (pos.x-crcl.radius, pos.y-crcl.radius)
    #
    crcl.point_count=8
    crcl.origin=(r,r)
    crcl.rotation =angle
    renderTexture.draw(crcl)
    #return onmouse



def line(frm,to):
        lines = sf.VertexArray(sf.PrimitiveType.LINES_STRIP, 2)
        lines[0].position = (frm.x, frm.y)
        lines[1].position = (to.x, to.y)

        w.draw(lines)


def square(pos, angle,size):
    sq=sf.graphics.RectangleShape()
    sx=size.x
    sy=size.y
    sq.size=sf.Vector2(sx, sy)
    sq.fill_color=sf.Color.RED    
    

    
    
    
    #sq.position.x+=size.x
    
    
    
    sq.rotation=angle
    sq.position=pos
    renderTexture.draw(sq)
    
    
    #if mPos.x>a.x and mPos.x<b.x and mPos.y>a.y and mPos.y<b.y: return 1

def rotatePolygon(polygon,theta):
    """Rotates the given polygon which consists of corners represented as (x,y),
    around the ORIGIN, clock-wise, theta degrees"""
    theta = math.radians(theta)
    rotatedPolygon = []
    for corner in polygon :
        rotatedPolygon.append(( corner[0]*math.cos(theta)-corner[1]*math.sin(theta) , corner[0]*math.sin(theta)+corner[1]*math.cos(theta)) )
    return rotatedPolygon


my_polygon = [(0,0),(1,0),(0,1)]
print (rotatePolygon(my_polygon,90))
objects=[]

    
    

    


class objectA:
    
    def __init__(self,Pos, rot, World, id, load):
        #self.size=b2Vec2(10,10)
        self.oId=id
        self.death=0
        self.Ann=Ann2()
        
        self.Ann.loadNet(load)
        self.step=0
        self.time=0
        self.lives=3
        self.birthTimer=0
        
        
        self.r=10
        
        self.centerpos=0
        
        self.body = World.world.CreateDynamicBody(position=Pos)
        self.body.userData = id
        
        circle = b2CircleShape( radius=self.r)
        self.poly=[]
        #self.poly=[(20,20), (-20,20), (-20,-20), (20,-20),   (0,20), (20,0), (0,-20), (-20,0)]
        #self.Ann.poly=self.poly
        self.poly=self.Ann.poly
        
        self.box=self.body.CreateFixture(shape=circle, density=1, friction=0.8, restitution=0.2)
        self.body.angularDamping=0.99
        #self.body.linearDamping=0.999
        
    def angle(self): 
        return math.degrees(self.body.angle)
    
    def AnnStep(self):
        
        self.Ann.annStep()
    
    
    def readColor(self,centerpos2,p ):
        
            f=1.2    
            x=centerpos2.x+(self.poly[p][0]*f)
            y=centerpos2.y+(self.poly[p][1]*f)  
            x=round(x,0)
            y=round(y,0)
            if x<0:x=0
            if y<0:y=0
            return simage[ x,y ]
        
    
    def sense(self):
                #--------------------------------------sense
        if self.death==0:
            x=0
            y=0
            
            pos2=self.body.position+(self.r,self.r)
            centerpos2=pos2+b2Vec2(-self.r,-self.r)
            
            colors=[]
            
            for i in range( len(self.poly) ):
                colors.append( self.readColor(centerpos2, i) )

            
      
            global gr
            for i in range( len(self.poly) ):
                self.Ann.outSet( i+gr, colors[i].r )

            
        
            
            self.Ann.outSet(len(self.poly)+gr, self.body.angularVelocity )
            self.Ann.outSet(len(self.poly)+1+gr, (self.body.linearVelocity.x+self.body.linearVelocity.y)/2 )
            

            plen=len(self.poly)
            #print(self.Ann.neurons[33].out)
            self.AnnStep()
            #print (self.Ann.outDatta[42] ,self.Ann.neurons[43].out,self.Ann.neurons[44].out ,self.Ann.neurons[45].out)
            power=100
            self.truster(self.Ann.neurons[plen+2+gr].out*power, self.Ann.neurons[plen+3+gr].out*power, self.Ann.neurons[plen+4+gr].out*power, self.Ann.neurons[plen+5+gr].out*power, self.Ann.neurons[plen+6+gr].out*power)
            
            
            global lifeTimeRecord
            global annRecord
            global cnext
            global alive
            if self.time>lifeTimeRecord:
                lifeTimeRecord=self.time
                annRecord=self.Ann
                if alive<=1: cnext=1
                if alive>25: cnext=1
                if alive>5:  self.death=1
            self.time+=1
            

          
        
    def draw(self):
        #square(self.body.position, self.angle(), self.size  )    #else: return 0
        
        #if self.time<=1: self.death=1
        
        if self.lives<=0: self.death=1
        
        
        
        if self.death==0:
            r=self.r
        
            pos=self.body.position+(r,r)
            self.centerpos=pos+b2Vec2(-r,-r)
            rot=self.angle()          
            
            
            
            
            
            self.poly=self.Ann.poly
            self.poly=rotatePolygon(self.poly,rot) 
            

        
        
        
            global gr
      
            dcircle(pos, rot, self.r, 255,self.Ann.colorG, self.Ann.colorB)              
            dcircle(self.centerpos+(2,2), rot, 2, 0,255,0)
            
            
            for i in range(len(self.poly)):
                dcircle(self.centerpos+self.poly[i]+(2,2), rot, 2, 0,self.Ann.neurons[i+gr].out,0)

            
            
            self.birthTimer+=1
            if self.birthTimer>300:
                self.birthTimer=0
                childAnn=self.Ann
                childAnn.randomizeWeights(0.1)
                childAnn.saveNet("child")
                giveBirth(self)  
    
            
        else:
            #dcircle(pos, rot, self.r, -200)
            self.body.active=0
            self.time=0
            #self.body.position=(100,100)
            
            self.Ann=[]
           
            
    
     
    def truster(self, a, b ,c ,d ,r):
        
        #print (a, b, c ,d, r)
        trustVector=b2Vec2( self.poly[0])
        trustCenter= b2Vec2(self.centerpos)
        
        self.body.ApplyAngularImpulse( r )
        
        self.body.ApplyLinearImpulse(trustVector*a, trustCenter )
        
        trustVector=b2Vec2( self.poly[1])
        trustCenter= self.centerpos
        self.body.ApplyLinearImpulse(trustVector*b, trustCenter )
        
        trustVector=b2Vec2( self.poly[2])
        trustCenter= self.centerpos
        self.body.ApplyLinearImpulse(trustVector*c, trustCenter )
        
        trustVector=b2Vec2( self.poly[3])
        trustCenter= self.centerpos
        self.body.ApplyLinearImpulse(trustVector*d, trustCenter )
        






for y in range(1):
    for x in range(3):
        objects.append(  objectA(b2Vec2(  50+(x*50),50+(y*50)  ),45, wrld , max,"Best") )
        max+=1

def giveBirth(parentAnn):
    global max
    global objects
    a=0
    max+=1
    objects.append(  objectA(b2Vec2(  random.randint(10, 400.0) ,200  ),45, wrld , max,"child") )  

       

def createNext():
    fitedId=0
    global max
    global objects
  
    annRecord.saveNet("Best")
    #objects=[]


    for y in range(1):
        for x in range(6):
            
            objects.append(  objectA(b2Vec2(  50+(x*50),random.randint(10, 350.0)  ),45, wrld , max,"Best") )
            max+=1
            
        
    
    
    
    for obj in objects:
        if obj.death==0: 
            if obj.oId<=max+3:obj.Ann.randomizeWeights(1)
            
        

            
    
# start the game loop

while w.is_open:
# process events
    mPos = sf.Mouse.get_position(w)  
    for event in w.events:
    # close window: exit
        if type(event) is sf.CloseEvent:
            w.close()
    
    
    
    
    
    square( sf.Vector2(0,0), 0, sf.Vector2(500,5) )
    square( sf.Vector2(0,400), 0, sf.Vector2(500,-5) )
    
    square( sf.Vector2(500,0), 0, sf.Vector2(-5,400) )
    square( sf.Vector2(0,0), 0, sf.Vector2(5,400) )
    
    
    
    alive=0
    dcircle(mPos, 0, 30, 255, 0,0)
    if sf.Mouse.is_button_pressed(sf.Mouse.RIGHT):lifeTimeRecord=0
    for obj in objects:
        
        obj.draw()
        if sf.Mouse.is_button_pressed(sf.Mouse.LEFT):
            
            if obj.death==0: obj.Ann.randomizeWeights(0.1)
        if obj.death==0:
            alive+=1

    
    #square(body.position, math.degrees(body.angle) )        texture = renderTexture.texture
    simage=texture.to_image()
    renderTexture.display()
    texture = renderTexture.texture
    sprite =sf.Sprite(texture)
    for obj in objects:
        obj.sense()
        if obj.death==1:
            obj.body.active=0
            objects.remove(obj)
            
   
   
    
    
    w.draw(sprite)
    text(str(lifeTimeRecord),sf.Vector2(505,10),sf.Color.RED, 8)
    
    i=0
   
    for obj in objects:
         text(str(obj.time)+" lives="+str(obj.lives) ,sf.Vector2(505,20+(i*10) ),sf.Color.GREEN, 8)
         i+=1
         
         if obj.death==0:
             j=0
             for neuron in obj.Ann.neurons:
                 color=neuron.out
                 cr=0
                 cg=0
                 if color>0:cg=int(color*255)
                 if color<0:cr=int(color*255)*-1
                 if cr>255:cr=255
                 if cg>255:cg=255
                 
                 
                 text("  %.2f " % round(neuron.out,2)+"   ",   sf.Vector2( j*(500/len(obj.Ann.neurons) ),400+(i*10) ),sf.Color(cr,cg,100), 8)
                 j+=1
         
    wrld.world.Step(wrld.timeStep, 32, 32)    
    w.display() # update the window
    w.clear() # clear screen
    renderTexture.clear()
    wrld.world.ClearForces()
    #print (alive)    
    if alive<=0 or cnext==1:
        cnext=0
        createNext()
    #time.sleep(0.01)
    

    