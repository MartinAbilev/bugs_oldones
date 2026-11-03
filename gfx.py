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

def drawNeuron(pos, size, value, shape):
    hovered = cDist(pos, mPos) < size
    radius = size - 4 if hovered else size
    center = (int(pos.x), int(pos.y))
    brightness = max(0, min(255, round(255 * abs(value))))
    color = (brightness, 0, 0) if value >= 0 else (0, brightness, 0)

    if shape == "circle":
        pygame.draw.circle(w, color, center, radius)
        pygame.draw.circle(w, (255, 0, 0), center, radius, 1)
    elif shape == "triangle":
        points = [
            (center[0], center[1] - radius),
            (center[0] + radius, center[1] + radius),
            (center[0] - radius, center[1] + radius),
        ]
        pygame.draw.polygon(w, color, points)
        pygame.draw.polygon(w, (255, 0, 0), points, 1)
    else:
        rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
        pygame.draw.rect(w, color, rect)
        pygame.draw.rect(w, (255, 0, 0), rect, 1)

    return hovered

def neuronShape(ann, index):
    if index < ann.hiddenSize:
        return "circle"
    if index < ann.hiddenSize + len(ann.poly) + 2:
        return "triangle"
    return "square"

def moveCreaturePoint(ann, neuron_index):
    sensor_start = ann.hiddenSize
    output_start = sensor_start + len(ann.poly) + 2
    if sensor_start <= neuron_index < sensor_start + len(ann.poly):
        poly_index = neuron_index - sensor_start
        scale = 185
    elif output_start <= neuron_index < output_start + min(4, len(ann.poly)):
        poly_index = neuron_index - output_start
        scale = 225
    else:
        return

    max_extent = max(
        40,
        max(
            (abs(float(coordinate)) for point in ann.poly for coordinate in point),
            default=0,
        ),
    )
    center_x = 320
    center_y = 240
    ann.poly[poly_index] = [
        (ann.neurons[neuron_index].pos.x - center_x) * max_extent / scale,
        (ann.neurons[neuron_index].pos.y - center_y) * max_extent / scale,
    ]

    updated_extent = max(
        40,
        max(
            (abs(float(coordinate)) for point in ann.poly for coordinate in point),
            default=0,
        ),
    )
    for index, (x, y) in enumerate(ann.poly):
        sensor_index = sensor_start + index
        if sensor_index < len(ann.neurons):
            ann.neurons[sensor_index].pos = vector2d(
                center_x + float(x) * 185 / updated_extent,
                center_y + float(y) * 185 / updated_extent,
            )
        thruster_index = output_start + index
        if index < min(4, len(ann.poly)) and thruster_index < len(ann.neurons):
            ann.neurons[thruster_index].pos = vector2d(
                center_x + float(x) * 225 / updated_extent,
                center_y + float(y) * 225 / updated_extent,
            )

def line(frm, to, color=(255, 255, 255)):
    pygame.draw.line(w, color, (frm.x, frm.y), (to.x, to.y))

def connectionColor(weight, min_weight, max_weight):
    if max_weight == min_weight:
        brightness = 255
    else:
        normalized = (weight - min_weight) / (max_weight - min_weight)
        brightness = round(40 + normalized * 215)
    return (brightness, brightness, brightness)

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

def gloop(ann, events):
    global mPos, mouseOn, cstate, cswitch, selected, onbutton
    onbutton = 0

    # Update mouse position
    mouse_pos = pygame.mouse.get_pos()
    mPos = vector2d(mouse_pos[0], mouse_pos[1])

    # Handle events
    for event in events:
        if event.type == pygame.VIDEORESIZE:
            w = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            pygame.display.set_caption("CYBERMIND v0.1")
        if event.type == pygame.MOUSEWHEEL:
            if mouseOn >= 0:
                ann.neurons[mouseOn].out += event.y * 0.1

    # Reset mouseOn if left mouse button is not pressed
    if not pygame.mouse.get_pressed()[0]:
        mouseOn = -1

    # Draw connections with brightness normalized across the network's weights.
    weights = [weight for neuron in ann.neurons for weight in neuron.weights]
    min_weight = min(weights, default=0)
    max_weight = max(weights, default=0)
    for neuron in ann.neurons:
        for index, c in enumerate(neuron.conections):
            weight = neuron.weights[index]
            line(
                neuron.pos,
                ann.neurons[c].pos,
                connectionColor(weight, min_weight, max_weight),
            )

    # Draw hidden neurons as circles, sensors as triangles, and thrusters as squares.
    for index, neuron in enumerate(ann.neurons):
        if drawNeuron(neuron.pos, 16, neuron.out, neuronShape(ann, index)):
            mouseOn = neuron.id
        text(str(round(neuron.out, 3)), neuron.pos, (255, 0, 0), 8)

    # Draw buttons
    bp = 10
    if button("save", vector2d(10, bp)) == 1 and pygame.mouse.get_pressed()[0]:
        print("save")
        ann.saveNet('Best')
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
        moveCreaturePoint(ann, mouseOn)
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
