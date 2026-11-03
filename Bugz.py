# Bugz.py
import copy
import pygame
import numpy as np
from Box2D import *
import math
from NeuralNetwork import *

# Initialize Pygame
pygame.init()
w = pygame.display.set_mode((640, 480))
pygame.display.set_caption("BUGZ // NEURAL SWARM")
clock = pygame.time.Clock()  # For frame rate control

# Create background surface for static boundaries
background = pygame.Surface((640, 480))
background.fill((7, 12, 21))
for grid_x in range(25, 500, 25):
    pygame.draw.line(background, (11, 24, 35), (grid_x, 0), (grid_x, 400))
for grid_y in range(25, 400, 25):
    pygame.draw.line(background, (11, 24, 35), (0, grid_y), (500, grid_y))
pygame.draw.rect(background, (20, 190, 185), (1, 1, 498, 398), 2)
for corner_x, corner_y, sign_x, sign_y in (
    (8, 8, 1, 1),
    (492, 8, -1, 1),
    (8, 392, 1, -1),
    (492, 392, -1, -1),
):
    pygame.draw.line(
        background,
        (70, 235, 220),
        (corner_x, corner_y),
        (corner_x + 12 * sign_x, corner_y),
        2,
    )
    pygame.draw.line(
        background,
        (70, 235, 220),
        (corner_x, corner_y),
        (corner_x, corner_y + 12 * sign_y),
        2,
    )

# Load and cache fonts
try:
    font_8 = pygame.font.SysFont("arial", 8)
    font_12 = pygame.font.SysFont("arial", 12)
    ui_font_10 = pygame.font.SysFont("arial", 10)
    ui_font_14 = pygame.font.SysFont("arial", 14, bold=True)
    ui_font_20 = pygame.font.SysFont("arial", 20, bold=True)
except Exception as e:
    print("Font error:", e)
    exit(1)

# Box2D world and global variables
annRecord = 0
cnext = 0
max = 0
lifeTimeRecord = 0
objects = []
radiation = 1.0
radiation_slider_dragging = False
radiation_slider = pygame.Rect(519, 137, 108, 8)
radiation_slider_hitbox = pygame.Rect(510, 116, 121, 40)

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

def uiText(surface, message, position, color, font):
    surface.blit(font.render(message, True, color), position)

def drawDashboard(surface, active_objects, record, mutation_rate):
    panel = pygame.Rect(505, 0, 135, 480)
    pygame.draw.rect(surface, (10, 17, 29), panel)
    pygame.draw.line(surface, (25, 54, 68), (505, 0), (505, 480), 2)
    pygame.draw.line(surface, (24, 37, 53), (518, 48), (627, 48))

    uiText(surface, "BUGZ", (518, 10), (235, 248, 255), ui_font_20)
    uiText(surface, "NEURAL SWARM", (519, 34), (93, 191, 197), ui_font_10)

    status_color = (67, 220, 170) if active_objects else (255, 174, 76)
    status_label = "● LIVE" if active_objects else "● RESPAWNING"
    pygame.draw.rect(surface, (19, 34, 43), (516, 57, 112, 31), border_radius=6)
    uiText(surface, status_label, (523, 66), status_color, ui_font_10)

    pygame.draw.rect(surface, (15, 25, 39), (513, 99, 119, 70), border_radius=8)
    pygame.draw.rect(surface, (28, 57, 70), (513, 99, 119, 70), 1, border_radius=8)
    uiText(surface, "RADIATION", (522, 108), (130, 158, 177), ui_font_10)
    uiText(surface, f"{mutation_rate:.2f}x", (575, 105), (255, 190, 82), ui_font_14)
    pygame.draw.rect(surface, (32, 48, 62), radiation_slider, border_radius=4)
    fill_width = round(radiation_slider.width * mutation_rate / 2)
    if fill_width:
        pygame.draw.rect(
            surface,
            (255, 165, 65),
            (radiation_slider.left, radiation_slider.top, fill_width, radiation_slider.height),
            border_radius=4,
        )
    knob_x = radiation_slider.left + fill_width
    pygame.draw.circle(surface, (255, 239, 205), (knob_x, radiation_slider.centery), 6)
    pygame.draw.circle(surface, (255, 165, 65), (knob_x, radiation_slider.centery), 6, 1)
    uiText(surface, "0x", (520, 149), (114, 139, 158), ui_font_10)
    uiText(surface, "2x", (611, 149), (114, 139, 158), ui_font_10)

    pygame.draw.rect(surface, (15, 25, 39), (513, 180, 119, 83), border_radius=8)
    pygame.draw.rect(surface, (28, 57, 70), (513, 180, 119, 83), 1, border_radius=8)
    uiText(surface, "FIELD STATUS", (522, 189), (130, 158, 177), ui_font_10)
    uiText(surface, "ALIVE", (522, 207), (114, 139, 158), ui_font_10)
    uiText(surface, f"{active_objects:02d}", (582, 202), (90, 232, 198), ui_font_14)
    uiText(surface, "BEST LIFE", (522, 232), (114, 139, 158), ui_font_10)
    uiText(surface, f"{record:05d}", (582, 227), (235, 248, 255), ui_font_14)

    pygame.draw.rect(surface, (15, 25, 39), (513, 274, 119, 119), border_radius=8)
    pygame.draw.rect(surface, (28, 57, 70), (513, 274, 119, 119), 1, border_radius=8)
    uiText(surface, "NEURAL SIGNAL", (522, 283), (130, 158, 177), ui_font_10)
    active_network = next((obj.Ann for obj in objects if obj.death == 0), None)
    if active_network is not None:
        neurons = active_network.neurons[:active_network.hiddenSize]
        for index, neuron in enumerate(neurons[:9]):
            y = 302 + index * 9
            pygame.draw.line(surface, (35, 51, 65), (542, y + 3), (619, y + 3), 3)
            value = neuron.out
            if value < -1:
                value = -1
            elif value > 1:
                value = 1
            center_x = 580
            end_x = round(center_x + value * 37)
            color = (72, 222, 194) if value >= 0 else (255, 112, 133)
            pygame.draw.line(surface, color, (center_x, y + 3), (end_x, y + 3), 3)
            pygame.draw.circle(surface, color, (end_x, y + 3), 2)
    else:
        uiText(surface, "awaiting signal", (522, 316), (94, 117, 137), ui_font_10)

    pygame.draw.line(surface, (24, 37, 53), (518, 407), (627, 407))
    uiText(surface, "LMB  mutate", (519, 417), (151, 174, 192), ui_font_10)
    uiText(surface, "RMB  reset record", (519, 436), (151, 174, 192), ui_font_10)
    uiText(surface, "60 FPS  //  BOX2D", (519, 459), (66, 133, 146), ui_font_10)

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
        self.world = b2World(contactListener=myContactListener(), gravity=(0, 1), doSleep=True)
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
            gr = self.Ann.hiddenSize
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
            gr = self.Ann.hiddenSize
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
                childAnn = copy.deepcopy(self.Ann)
                childAnn.randomizeWeights(radiation)
                childAnn.saveNet("child")
                giveBirth(self)
        else:
            self.body.active = False
            self.time = 0
            self.Ann = []

    def drawThrusterIndicators(self, surface):
        output_start = self.Ann.hiddenSize + len(self.poly) + 2
        for index in range(min(4, len(self.poly))):
            output_index = output_start + index
            if output_index >= len(self.Ann.neurons):
                break

            activation = self.Ann.neurons[output_index].out
            if abs(activation) < 0.05:
                continue

            vertex_x, vertex_y = self.poly[index]
            vector_length = math.hypot(vertex_x, vertex_y)
            if vector_length == 0:
                continue

            direction = 1 if activation > 0 else -1
            start_x = self.centerpos.x + vertex_x
            start_y = self.centerpos.y + vertex_y
            arrow_length = 2 + 6 * min(abs(activation), 1)
            end_x = start_x + direction * vertex_x / vector_length * arrow_length
            end_y = start_y + direction * vertex_y / vector_length * arrow_length
            start = (round(start_x), round(start_y))
            end = (round(end_x), round(end_y))

            angle = math.atan2(end_y - start_y, end_x - start_x)
            arrow_head_length = 3
            base_x = end_x - arrow_head_length * math.cos(angle)
            base_y = end_y - arrow_head_length * math.sin(angle)
            pygame.draw.line(
                surface,
                (255, 255, 0),
                start,
                (round(base_x), round(base_y)),
                1,
            )
            for side in (-1, 1):
                head_x = base_x + side * arrow_head_length / 2 * math.sin(angle)
                head_y = base_y - side * arrow_head_length / 2 * math.cos(angle)
                pygame.draw.line(
                    surface,
                    (255, 255, 0),
                    end,
                    (round(head_x), round(head_y)),
                    1,
                )

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
                obj.Ann.randomizeWeights(radiation)

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

    # Handle input and update creatures
    right_click = pygame.mouse.get_pressed()[2]
    left_click = pygame.mouse.get_pressed()[0]
    if not left_click:
        radiation_slider_dragging = False
    elif radiation_slider_dragging or radiation_slider_hitbox.collidepoint(mouse_pos):
        radiation_slider_dragging = True
        slider_position = (mouse_pos[0] - radiation_slider.left) / radiation_slider.width
        if slider_position < 0:
            slider_position = 0
        elif slider_position > 1:
            slider_position = 1
        radiation = round(slider_position * 2 * 20) / 20
        left_click = False
    elif left_click and mouse_pos[0] >= 505:
        left_click = False
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
                obj.Ann.randomizeWeights(radiation)
        if obj.death == 1:
            obj.body.active = False
            to_remove.append(obj)

    # Release pixel array
    del pixel_array

    for obj in objects:
        if obj.death == 0:
            obj.drawThrusterIndicators(w)

    # Remove dead objects
    for obj in to_remove:
        objects.remove(obj)

    drawDashboard(w, alive, lifeTimeRecord, radiation)
    if mouse_pos[0] < 500 and mouse_pos[1] < 400:
        pygame.draw.circle(w, (70, 235, 220), (int(mPos.x), int(mPos.y)), 4, 1)
        pygame.draw.line(w, (70, 235, 220), (mPos.x - 7, mPos.y), (mPos.x + 7, mPos.y), 1)
        pygame.draw.line(w, (70, 235, 220), (mPos.x, mPos.y - 7), (mPos.x, mPos.y + 7), 1)

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
