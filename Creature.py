import pygame
import numpy as np
from Box2D import *
import time
import math
from shared import *

# Initialize Pygame
pygame.init()
w = pygame.display.set_mode((640, 480))
pygame.display.set_caption("My first Pygame Window - or not ?")
clock = pygame.time.Clock()  # For frame rate control

# Create background surface for static boundaries
background = pygame.Surface((640, 480))
background.fill((0, 0, 0))
# Draw boundaries once
pygame.draw.rect(background, (255, 0, 0), (0, 0, 500, 5), 1)
pygame.draw.rect(background, (255, 0, 0), (0, 400, 500, 5), 1)
pygame.draw.rect(background, (255, 0, 0), (0, 0, 5, 400), 1)
pygame.draw.rect(background, (255, 0, 0), (500, 0, 5, 400), 1)

# Load and cache fonts
try:
    font_8 = pygame.font.SysFont("arial", 8)
    font_12 = pygame.font.SysFont("arial", 12)
except Exception as e:
    print("Font error:", e)
    exit(1)

# Box2D world and global variables
annRecord = 0
cnext = 0
max = 0
gr = 3 * 3
lifeTimeRecord = 0
objects = []

# Vector2d class to replace sf.Vector2
class vector2d(object):
    def __init__(self, X, Y):
        self.x = X
        self.y = Y

    def __add__(self, other):
        return vector2d(self.x + other.x, self.y + other.y)

# Text rendering with cached fonts
def text(surface, msg, pos, c, size):
    font = font_8 if size == 8 else font_12
    text_surface = font.render(msg, True, c)
    surface.blit(text_surface, (pos.x, pos.y - 11))

# Box2D contact listener
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

        if not actorA == "as" and not actorB == "as":
            for obj in objects:
                if obj.oId == actorA:
                    obj.lives -= 1
            for obj in objects:
                if obj.oId == actorB:
                    obj.lives -= 1

    def EndContact(self, contact):
        pass

    def PreSolve(self, contact, oldManifold):
        pass

    def PostSolve(self, contact, impulse):
        pass

# Physics world
class mworld:
    def __init__(self):
        self.world = b2World(contactListener=myContactListener(), gravity=(0, -1), doSleep=True)
        self.timeStep = 1.0 / 60
        self.ground_body = self.world.CreateStaticBody(position=(0, 0), shapes=b2PolygonShape(box=(500, 5)))
        self.ground_body.userData = "passive"
        self.ground_body = self.world.CreateStaticBody(position=(0, 400), shapes=b2PolygonShape(box=(500, 5)))
        self.ground_body.userData = "passive"
        self.ground_body = self.world.CreateStaticBody(position=(0, 0), shapes=b2PolygonShape(box=(5, 500)))
        self.ground_body.userData = "passive"
        self.ground_body = self.world.CreateStaticBody(position=(500, 0), shapes=b2PolygonShape(box=(5, 500)))
        self.ground_body.userData = "passive"

wrld = mworld()

# Drawing functions
def dcircle(surface, pos, angle, r, R, G, B):
    pygame.draw.circle(surface, (R, G, B), (pos.x, pos.y), r)
    pygame.draw.circle(surface, (255, 0, 0), (pos.x, pos.y), r, 1)

def line(surface, frm, to):
    pygame.draw.line(surface, (255, 255, 255), (frm.x, frm.y), (to.x, to.y))

# Polygon rotation
def rotatePolygon(polygon, theta):
    theta = math.radians(theta)
    rotatedPolygon = []
    for corner in polygon:
        rotatedPolygon.append((
            corner[0] * math.cos(theta) - corner[1] * math.sin(theta),
            corner[0] * math.sin(theta) + corner[1] * math.cos(theta)
        ))
    return rotatedPolygon

# Object class
class objectA:
    def __init__(self, Pos, rot, World, id, load):
        self.oId = id
        self.death = 0
        self.Ann = Ann2()
        self.Ann.loadNet(load)
        self.step = 0
        self.time = 0
        self.lives = 3
        self.birthTimer = 0
        self.r = 10
        self.centerpos = 0
        self.body = World.world.CreateDynamicBody(position=Pos)
        self.body.userData = id
        circle = b2CircleShape(radius=self.r)
        self.poly = self.Ann.poly
        self.box = self.body.CreateFixture(shape=circle, density=1, friction=0.8, restitution=0.2)
        self.body.angularDamping = 0.99

    def angle(self):
        return math.degrees(self.body.angle)

    def AnnStep(self):
        self.Ann.annStep()

    def readColor(self, pixel_array, centerpos2, p):
        f = 1.2
        x = int(centerpos2.x + (self.poly[p][0] * f))
        y = int(centerpos2.y + (self.poly[p][1] * f))
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x >= 640:
            x = 639
        if y >= 480:
            y = 479
        try:
            color = pixel_array[x, y]
            return type('Color', (), {'r': color[0], 'g': color[1], 'b': color[2]})
        except:
            return type('Color', (), {'r': 0, 'g': 0, 'b': 0})

    def sense(self, pixel_array):
        if self.death == 0:
            pos2 = vector2d(self.body.position.x + self.r, self.body.position.y + self.r)
            centerpos2 = vector2d(pos2.x - self.r, pos2.y - self.r)
            colors = []
            for i in range(len(self.poly)):
                colors.append(self.readColor(pixel_array, centerpos2, i))
            global gr
            for i in range(len(self.poly)):
                self.Ann.outSet(i + gr, colors[i].r)
            self.Ann.outSet(len(self.poly) + gr, self.body.angularVelocity)
            self.Ann.outSet(len(self.poly) + 1 + gr, (self.body.linearVelocity.x + self.body.linearVelocity.y) / 2)
            plen = len(self.poly)
            self.AnnStep()
            power = 100
            self.truster(
                self.Ann.neurons[plen + 2 + gr].out * power,
                self.Ann.neurons[plen + 3 + gr].out * power,
                self.Ann.neurons[plen + 4 + gr].out * power,
                self.Ann.neurons[plen + 5 + gr].out * power,
                self.Ann.neurons[plen + 6 + gr].out * power
            )
            global lifeTimeRecord, annRecord, cnext, alive
            if self.time > lifeTimeRecord:
                lifeTimeRecord = self.time
                annRecord = self.Ann
                if alive <= 1:
                    cnext = 1
                if alive > 25:
                    cnext = 1
                if alive > 5:
                    self.death = 1
            self.time += 1

    def draw(self, surface):
        if self.lives <= 0:
            self.death = 1
        if self.death == 0:
            r = self.r
            pos = vector2d(self.body.position.x + r, self.body.position.y + r)
            self.centerpos = vector2d(pos.x - r, pos.y - r)
            rot = self.angle()
            self.poly = self.Ann.poly
            self.poly = rotatePolygon(self.poly, rot)
            global gr
            dcircle(surface, pos, rot, self.r, 255, self.Ann.colorG, self.Ann.colorB)
            dcircle(surface, vector2d(self.centerpos.x + 2, self.centerpos.y + 2), rot, 2, 0, 255, 0)
            for i in range(len(self.poly)):
                dcircle(
                    surface,
                    vector2d(self.centerpos.x + self.poly[i][0] + 2, self.centerpos.y + self.poly[i][1] + 2),
                    rot, 2, 0, self.Ann.neurons[i + gr].out, 0
                )
            self.birthTimer += 1
            if self.birthTimer > 300:
                self.birthTimer = 0
                childAnn = self.Ann
                childAnn.randomizeWeights(0.1)
                childAnn.saveNet("child")
                giveBirth(self)
        else:
            self.body.active = False
            self.time = 0
            self.Ann = []

    def truster(self, a, b, c, d, r):
        trustVector = b2Vec2(self.poly[0])
        trustCenter = b2Vec2(self.centerpos.x, self.centerpos.y)
        self.body.ApplyAngularImpulse(r, wake=True)
        self.body.ApplyLinearImpulse(trustVector * a, trustCenter, wake=True)
        trustVector = b2Vec2(self.poly[1])
        self.body.ApplyLinearImpulse(trustVector * b, trustCenter, wake=True)
        trustVector = b2Vec2(self.poly[2])
        self.body.ApplyLinearImpulse(trustVector * c, trustCenter, wake=True)
        trustVector = b2Vec2(self.poly[3])
        self.body.ApplyLinearImpulse(trustVector * d, trustCenter, wake=True)

# Initialize objects
for y in range(1):
    for x in range(3):
        objects.append(objectA(b2Vec2(50 + (x * 50), 50 + (y * 50)), 45, wrld, max, "Best"))
        max += 1

def giveBirth(parentAnn):
    global max, objects
    max += 1
    objects.append(objectA(b2Vec2(random.randint(10, 400), 200), 45, wrld, max, "child"))

def createNext():
    global max, objects, annRecord
    annRecord.saveNet("Best")
    for y in range(1):
        for x in range(6):
            objects.append(objectA(b2Vec2(50 + (x * 50), random.randint(10, 350)), 45, wrld, max, "Best"))
            max += 1
    for obj in objects:
        if obj.death == 0:
            if obj.oId <= max + 3:
                obj.Ann.randomizeWeights(1)

# Main game loop
running = True
alive = 0
mPos = vector2d(0, 0)
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update mouse position
    mouse_pos = pygame.mouse.get_pos()
    mPos = vector2d(mouse_pos[0], mouse_pos[1])

    # Clear screen and draw background
    w.blit(background, (0, 0))

    # Draw mouse
    dcircle(w, mPos, 0, 30, 255, 0, 0)

    # Handle input and update creatures
    right_click = pygame.mouse.get_pressed()[2]
    left_click = pygame.mouse.get_pressed()[0]
    if right_click:
        lifeTimeRecord = 0

    # Draw creatures (first pass to ensure correct pixel data)
    alive = 0
    for obj in objects:
        if obj.death == 0:
            obj.draw(w)
            alive += 1

    # Capture pixel array for color sensing
    pixel_array = pygame.surfarray.pixels3d(w)

    # Update creatures and remove dead ones
    to_remove = []
    for obj in objects:
        if obj.death == 0:
            obj.sense(pixel_array)
            if left_click:
                obj.Ann.randomizeWeights(0.1)
        if obj.death == 1:
            obj.body.active = False
            to_remove.append(obj)

    # Release pixel array
    del pixel_array

    # Remove dead objects
    for obj in to_remove:
        objects.remove(obj)

    # Draw text overlays
    text(w, str(lifeTimeRecord), vector2d(505, 10), (255, 0, 0), 8)
    i = 0
    for obj in objects:
        text(w, f"{obj.time} lives={obj.lives}", vector2d(505, 20 + (i * 10)), (0, 255, 0), 8)
        i += 1
        if obj.death == 0:
            j = 0
            for neuron in obj.Ann.neurons:
                color = neuron.out
                cr = 0
                cg = 0
                if color > 0:
                    cg = int(color * 255)
                if color < 0:
                    cr = int(color * 255) * -1
                if cr > 255:
                    cr = 255
                if cg > 255:
                    cg = 255
                text(
                    w,
                    f"  {round(neuron.out, 2):.2f}   ",
                    vector2d(j * (500 / len(obj.Ann.neurons)), 400 + (i * 10)),
                    (cr, cg, 100), 8
                )
                j += 1

    # Update physics
    wrld.world.Step(wrld.timeStep, 32, 32)
    wrld.world.ClearForces()

    # Update display
    pygame.display.flip()

    # Check for next generation
    if alive <= 0 or cnext == 1:
        cnext = 0
        createNext()

    # Cap frame rate
    clock.tick(60)

# Cleanup
pygame.quit()
