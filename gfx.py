import time
import pygame
from NeuralNetwork import *  # Assuming this includes Neuron, NeuralNetwork, etc.

# Define vector2d class to replace sf.Vector2
class vector2d(object):
    def __init__(self, X, Y):
        self.x = X
        self.y = Y

# Initialize Pygame
pygame.init()
w = pygame.display.set_mode((640, 480))
pygame.display.set_caption("CYBERMIND v0.1")

# Load font
try:
    font = pygame.font.SysFont("arial", 16)
except Exception as e:
    print("Font error:", e)
    exit(1)

# Global variables
mouseOn = -1
cstate = -1
cswitch = 0
selected = 0
onbutton = 0
mPos = vector2d(0, 0)

# Helper function to calculate distance (replacing vmath.cDist if needed)
def cDist(pos1, pos2):
    return ((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2) ** 0.5

def status(ann):

    global cstate

def clear():
    w.fill((0, 0, 0))  # Clear screen with black

def circle(pos, r, c):
    global mPos
    g = 0
    if c < 0:
        g = c * -1
        c = 0
    if g > 255:
        g = 255
    if c > 255:
        c = 255

    if cDist(pos, mPos) < r:
        r -= 4
        onmouse = 1
    else:
        onmouse = 0

    pygame.draw.circle(w, (c, g, 0), (pos.x, pos.y), r)
    pygame.draw.circle(w, (255, 0, 0), (pos.x, pos.y), r, 1)  # Outline
    return onmouse

def line(frm, to):
    pygame.draw.line(w, (255, 255, 255), (frm.x, frm.y), (to.x, to.y))

def square(a, b):
    rect = pygame.Rect(a.x, a.y, b.x - a.x, b.y - a.y)
    pygame.draw.rect(w, (255, 255, 255), rect, 1)
    if a.x < mPos.x < b.x and a.y < mPos.y < b.y:
        return 1
    return 0

def text(msg, pos, c, s):
    global font
    font_size = s
    text_font = pygame.font.SysFont("arial", font_size)
    text_surface = text_font.render(msg, True, c)
    w.blit(text_surface, (pos.x + 16, pos.y - 11))

def button(name, pos):
    global onbutton
    pos_b = vector2d(pos.x + 4 * 16, pos.y + 16)
    if square(pos, pos_b) == 1:
        col = (255, 0, 0)  # Red
        bool_val = 1
        onbutton = 1
    else:
        col = (255, 255, 255)  # White
        bool_val = 0
    offset = vector2d(0, 8)
    text(name, vector2d(pos.x + offset.x, pos.y + offset.y), col, 16)
    return bool_val

def gui(ann):
    pass  # Placeholder if needed

def gloop(ann):
    global mPos, mouseOn, cstate, cswitch, selected, onbutton
    onbutton = 0

    # Update mouse position
    mouse_pos = pygame.mouse.get_pos()
    mPos = vector2d(mouse_pos[0], mouse_pos[1])

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.VIDEORESIZE:
            w = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            pygame.display.set_caption("CYBERMIND v0.1")
        if event.type == pygame.MOUSEWHEEL:
            if mouseOn >= 0:
                ann.neurons[mouseOn].out += event.y * 0.1

    # Reset mouseOn if left mouse button is not pressed
    if not pygame.mouse.get_pressed()[0]:
        mouseOn = -1

    # Draw connections
    for neuron in ann.neurons:
        for c in neuron.conections:
            line(neuron.pos, ann.neurons[c].pos)

    # Draw neurons and text
    for neuron in ann.neurons:
        if circle(neuron.pos, 16, 255 * neuron.out) == 1:
            mouseOn = neuron.id
        text(str(round(neuron.out, 3)), neuron.pos, (255, 0, 0), 8)

    # Draw buttons
    bp = 10
    if button("save", vector2d(10, bp)) == 1 and pygame.mouse.get_pressed()[0]:
        print("save")
        ann.saveNet()
        time.sleep(1)
    bp += 30

    if button("load", vector2d(10, bp)) == 1 and pygame.mouse.get_pressed()[0]:
        print("load")
        ann.loadNet('Best')
        time.sleep(1)
    bp += 30

    if button("clear", vector2d(10, bp)) == 1 and pygame.mouse.get_pressed()[0]:
        print("clear")
        ann.neurons = []
        ann.maxN = 0
    bp += 30

    if button("sort", vector2d(10, bp)) == 1 and pygame.mouse.get_pressed()[0]:
        ann.sort()
    bp += 30

    if button("train", vector2d(10, bp)) == 1 and pygame.mouse.get_pressed()[0]:
        print("Train as ERROR")
    bp += 30

    if button("rand", vector2d(10, bp)) == 1 and pygame.mouse.get_pressed()[0]:
        print("randomize weights")
        ann.randomizeWeights(0.1)
    bp += 30

    if button("crgrid", vector2d(10, bp)) == 1 and pygame.mouse.get_pressed()[0]:
        print("crgrid")
        ann.createGrid(6)
        time.sleep(1.0)
    bp += 30

    # Create new neuron
    if pygame.mouse.get_pressed()[0] and mouseOn == -1 and onbutton == 0:
        print("mouse down")
        ann.neurons.append(Neuron2(ann.maxN))
        ann.neurons[ann.maxN].pos = vector2d(mPos.x, mPos.y)
        ann.maxN += 1
        time.sleep(0.3)

    # Move neurons
    if pygame.mouse.get_pressed()[0] and mouseOn >= 0:
        old = ann.neurons[mouseOn].pos
        ann.neurons[mouseOn].pos = vector2d(mPos.x, mPos.y)
        distX = vector2d(mPos.x - old.x, mPos.y - old.y)
        for ch in ann.neurons[mouseOn].lowest:
            ann.neurons[ch].pos = vector2d(
                ann.neurons[ch].pos.x + distX.x,
                ann.neurons[ch].pos.y + distX.y
            )
        selected = mouseOn

    # Handle connections
    if pygame.mouse.get_pressed()[2] and mouseOn >= 0 and cswitch == 0:
        print("right mb pressed on. " + str(mouseOn))
        cstate = mouseOn
        cswitch = 1

    if not pygame.mouse.get_pressed()[2] and mouseOn == -1 and cswitch == 1:
        cstate = -1
        cswitch = 2

    if pygame.mouse.get_pressed()[2] and mouseOn >= 0 and cswitch == 2:
        cstate = -1
        cswitch = 0

    if pygame.mouse.get_pressed()[2] and mouseOn >= 0 and cstate >= 0 and cstate != mouseOn and cswitch == 1:
        print("right mb pressed on. " + str(mouseOn))
        ann.connect(mouseOn, cstate, 1)
        ann.neurons[cstate].child.append(mouseOn)
        ann.neurons[mouseOn].parent.append(cstate)
        # ann.sort()
        cstate = -1
        cswitch = 2

    if cswitch == 1:
        line(ann.neurons[cstate].pos, mPos)

    if cswitch == 2 and mouseOn == -1:
        cswitch = 0

    # Draw status text
    text("cstate=" + str(cstate) + "; cswitch=" + str(cswitch) + "; mouseon=" + str(mouseOn), vector2d(100, 10), (255, 255, 255), 18)

    # Draw mouse cursor
    circle(mPos, 4, 1.0)

    pygame.display.flip()  # Update the display
