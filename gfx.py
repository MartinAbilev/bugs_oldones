import math

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
pygame.display.set_caption("BUGZ // NEURAL LAB")
background = pygame.Surface((640, 480))
background.fill((7, 12, 21))
for grid_x in range(25, 505, 25):
    pygame.draw.line(background, (11, 24, 35), (grid_x, 0), (grid_x, 480))
for grid_y in range(25, 480, 25):
    pygame.draw.line(background, (11, 24, 35), (0, grid_y), (505, grid_y))
pygame.draw.rect(background, (20, 190, 185), (1, 1, 502, 478), 2)
pygame.draw.rect(background, (10, 17, 29), (505, 0, 135, 480))
pygame.draw.line(background, (25, 54, 68), (505, 0), (505, 480), 2)

# Load font
try:
    font = pygame.font.SysFont("arial", 16)
    ui_font_9 = pygame.font.SysFont("arial", 9)
    ui_font_10 = pygame.font.SysFont("arial", 10)
    ui_font_12 = pygame.font.SysFont("arial", 12, bold=True)
    ui_font_18 = pygame.font.SysFont("arial", 18, bold=True)
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
create_neuron_type = 0

# Helper function to calculate distance (replacing vmath.cDist if needed)
def cDist(pos1, pos2):
    return ((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2) ** 0.5

def status(ann):

    global cstate

def clear():
    w.blit(background, (0, 0))

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

def text(msg, pos, c, s):
    text_font = font if s == 16 else ui_font_9 if s <= 10 else ui_font_10
    text_surface = text_font.render(msg, True, c)
    w.blit(text_surface, (pos.x + 16, pos.y - 11))

def drawButton(name, rect, mouse_pos):
    hovered = rect.collidepoint(mouse_pos)
    fill = (28, 57, 70) if hovered else (15, 25, 39)
    edge = (70, 220, 205) if hovered else (35, 75, 88)
    pygame.draw.rect(w, fill, rect, border_radius=5)
    pygame.draw.rect(w, edge, rect, 1, border_radius=5)
    label = ui_font_9.render(name, True, (225, 242, 245) if hovered else (157, 190, 200))
    w.blit(label, label.get_rect(center=rect.center))
    return hovered

def drawThrusterDirection(ann, output_index):
    output_start = ann.hiddenSize + len(ann.poly) + 2
    if output_index == 4:
        return

    neuron = ann.neurons[output_start + output_index]
    if output_index < 4 and output_index < len(ann.poly):
        direction_x, direction_y = ann.poly[output_index]
    else:
        direction_x = neuron.pos.x - 320
        direction_y = neuron.pos.y - 240

    direction_length = (direction_x ** 2 + direction_y ** 2) ** 0.5
    if direction_length == 0:
        return

    activation = neuron.out
    if abs(activation) >= 0.05 and activation < 0:
        direction_x = -direction_x
        direction_y = -direction_y
    direction_x /= direction_length
    direction_y /= direction_length

    start_x = neuron.pos.x + direction_x * 18
    start_y = neuron.pos.y + direction_y * 18
    end_x = start_x + direction_x * 11
    end_y = start_y + direction_y * 11
    angle = math.atan2(direction_y, direction_x)
    pygame.draw.line(
        w,
        (255, 220, 90),
        (round(start_x), round(start_y)),
        (round(end_x), round(end_y)),
        2,
    )
    for side in (-1, 1):
        head_x = end_x - 4 * math.cos(angle) + side * 2 * math.sin(angle)
        head_y = end_y - 4 * math.sin(angle) - side * 2 * math.cos(angle)
        pygame.draw.line(
            w,
            (255, 220, 90),
            (round(end_x), round(end_y)),
            (round(head_x), round(head_y)),
            2,
        )

def createNeuronAt(ann, position, neuron_type):
    if neuron_type == 0:
        neuron = ann.insertNeuron(ann.hiddenSize, neuron_type, position)
        ann.hiddenSize += 1
        return neuron

    if neuron_type == 1:
        extent = max(
            40,
            max(
                (abs(float(coordinate)) for point in ann.poly for coordinate in point),
                default=0,
            ),
        )
        point = [
            (position.x - 320) * extent / 185,
            (position.y - 240) * extent / 185,
        ]
        sensor_index = ann.hiddenSize + len(ann.poly)
        ann.poly.append(point)
        neuron = ann.insertNeuron(sensor_index, neuron_type, position)
        ann.syncMorphologyPositions()
        return neuron

    output_start = ann.hiddenSize + len(ann.poly) + 2
    if len(ann.neurons) - output_start == 4:
        ann.insertNeuron(
            len(ann.neurons),
            2,
            vector2d(320, 240),
        )
    return ann.insertNeuron(len(ann.neurons), neuron_type, position)

def gui(ann):
    pass  # Placeholder if needed

def gloop(ann, events):
    global w, mPos, mouseOn, cstate, cswitch, selected, onbutton, create_neuron_type
    onbutton = 0

    mouse_pos = pygame.mouse.get_pos()
    mPos = vector2d(mouse_pos[0], mouse_pos[1])

    for event in events:
        if event.type == pygame.VIDEORESIZE:
            w = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            pygame.display.set_caption("BUGZ // NEURAL LAB")
        if event.type == pygame.MOUSEWHEEL:
            if mouseOn >= 0:
                ann.neurons[mouseOn].out += event.y * 0.1

    left_down = pygame.mouse.get_pressed()[0]
    right_down = pygame.mouse.get_pressed()[2]
    left_clicks = [
        event.pos
        for event in events
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
    ]

    if not left_down:
        mouseOn = -1

    # Keep graph drawing out of the dashboard region.
    w.set_clip(pygame.Rect(0, 0, 505, 480))
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

    for index, neuron in enumerate(ann.neurons):
        if drawNeuron(neuron.pos, 16, neuron.out, neuronShape(ann, index)):
            mouseOn = neuron.id
        text(str(round(neuron.out, 3)), neuron.pos, (255, 0, 0), 8)
        output_start = ann.hiddenSize + len(ann.poly) + 2
        if index >= output_start:
            drawThrusterDirection(ann, index - output_start)

    if mouseOn == -1 and any(pos[0] < 505 for pos in left_clicks):
        createNeuronAt(ann, vector2d(mouse_pos[0], mouse_pos[1]), create_neuron_type)

    if left_down and mouseOn >= 0 and mouse_pos[0] < 505:
        old = ann.neurons[mouseOn].pos
        ann.neurons[mouseOn].pos = vector2d(mPos.x, mPos.y)
        moveCreaturePoint(ann, mouseOn)
        distX = vector2d(mPos.x - old.x, mPos.y - old.y)
        for child in ann.neurons[mouseOn].lowest:
            ann.neurons[child].pos = vector2d(
                ann.neurons[child].pos.x + distX.x,
                ann.neurons[child].pos.y + distX.y,
            )
        selected = mouseOn

    w.set_clip(None)
    pygame.draw.rect(w, (15, 25, 39), (513, 57, 119, 53), border_radius=8)
    pygame.draw.rect(w, (28, 57, 70), (513, 57, 119, 53), 1, border_radius=8)
    uiText = ui_font_18.render("BUGZ", True, (235, 248, 255))
    w.blit(uiText, (522, 8))
    w.blit(ui_font_9.render("NEURAL LAB  //  EDITOR", True, (93, 191, 197)), (522, 34))
    active_color = (67, 220, 170) if ann.neurons else (255, 174, 76)
    active_label = "● NETWORK READY" if ann.neurons else "● EMPTY NETWORK"
    w.blit(ui_font_9.render(active_label, True, active_color), (520, 67))
    connection_count = sum(len(neuron.conections) for neuron in ann.neurons)
    w.blit(ui_font_9.render(f"{len(ann.neurons):02d} NODES", True, (220, 235, 240)), (520, 85))
    w.blit(ui_font_9.render(f"{connection_count:03d} LINKS", True, (112, 160, 175)), (575, 85))

    pygame.draw.line(w, (24, 37, 53), (518, 122), (627, 122))
    w.blit(ui_font_9.render("NODE LEGEND", True, (130, 158, 177)), (520, 130))
    pygame.draw.circle(w, (72, 222, 194), (525, 153), 4)
    w.blit(ui_font_9.render("HIDDEN", True, (176, 199, 207)), (535, 148))
    pygame.draw.polygon(w, (255, 190, 82), [(580, 149), (585, 157), (575, 157)])
    w.blit(ui_font_9.render("SENSOR", True, (176, 199, 207)), (588, 148))
    pygame.draw.rect(w, (255, 112, 133), (521, 169, 8, 8))
    w.blit(ui_font_9.render("THRUSTER", True, (176, 199, 207)), (535, 168))
    w.blit(ui_font_9.render("EDGE BRIGHTNESS = WEIGHT", True, (95, 130, 146)), (520, 190))
    pygame.draw.line(w, (24, 37, 53), (518, 207), (627, 207))
    w.blit(ui_font_9.render("NETWORK TOOLS", True, (130, 158, 177)), (520, 215))

    button_specs = [
        ("SAVE", pygame.Rect(516, 235, 53, 25)),
        ("LOAD", pygame.Rect(574, 235, 53, 25)),
        ("SORT", pygame.Rect(516, 266, 53, 25)),
        ("RAND", pygame.Rect(574, 266, 53, 25)),
        ("CLEAR", pygame.Rect(516, 297, 53, 25)),
        ("GRID", pygame.Rect(574, 297, 53, 25)),
    ]
    for label, rect in button_specs:
        drawButton(label, rect, mouse_pos)

    w.blit(ui_font_9.render("CREATE NODE TYPE", True, (130, 158, 177)), (520, 330))
    creation_specs = [
        ("HIDDEN", 0, pygame.Rect(516, 347, 111, 23)),
        ("SENSOR", 1, pygame.Rect(516, 375, 111, 23)),
        ("THRUSTER", 2, pygame.Rect(516, 403, 111, 23)),
    ]
    for label, neuron_type, rect in creation_specs:
        drawButton(label, rect, mouse_pos)
        if create_neuron_type == neuron_type:
            pygame.draw.rect(w, (70, 220, 205), rect, 2, border_radius=5)

    save_clicked = any(rect.collidepoint(pos) for pos in left_clicks for label, rect in button_specs if label == "SAVE")
    load_clicked = any(rect.collidepoint(pos) for pos in left_clicks for label, rect in button_specs if label == "LOAD")
    sort_clicked = any(rect.collidepoint(pos) for pos in left_clicks for label, rect in button_specs if label == "SORT")
    rand_clicked = any(rect.collidepoint(pos) for pos in left_clicks for label, rect in button_specs if label == "RAND")
    clear_clicked = any(rect.collidepoint(pos) for pos in left_clicks for label, rect in button_specs if label == "CLEAR")
    grid_clicked = any(rect.collidepoint(pos) for pos in left_clicks for label, rect in button_specs if label == "GRID")
    for _, neuron_type, rect in creation_specs:
        if any(rect.collidepoint(pos) for pos in left_clicks):
            create_neuron_type = neuron_type

    if save_clicked:
        ann.saveNet('Best')
        ann.loadNet('Best')
    if load_clicked:
        ann.loadNet('Best')
    if sort_clicked:
        ann.sort()
    if rand_clicked:
        ann.randomizeWeights(0.1)
    if clear_clicked:
        ann.neurons = []
        ann.maxN = 0
        ann.hiddenSize = 0
        ann.poly = []
    if grid_clicked:
        ann.createGrid(6)

    if right_down and mouseOn >= 0 and cswitch == 0:
        cstate = mouseOn
        cswitch = 1

    if not right_down and mouseOn == -1 and cswitch == 1:
        cstate = -1
        cswitch = 2

    if right_down and mouseOn >= 0 and cswitch == 2:
        cstate = -1
        cswitch = 0

    if right_down and mouseOn >= 0 and cstate >= 0 and cstate != mouseOn and cswitch == 1:
        ann.connect(mouseOn, cstate, 1)
        ann.neurons[cstate].child.append(mouseOn)
        ann.neurons[mouseOn].parent.append(cstate)
        cstate = -1
        cswitch = 2

    if cswitch == 1:
        line(ann.neurons[cstate].pos, mPos)

    if cswitch == 2 and mouseOn == -1:
        cswitch = 0

    if mouse_pos[0] < 505:
        pygame.draw.circle(w, (70, 235, 220), (int(mPos.x), int(mPos.y)), 4, 1)
        pygame.draw.line(w, (70, 235, 220), (mPos.x - 7, mPos.y), (mPos.x + 7, mPos.y), 1)
        pygame.draw.line(w, (70, 235, 220), (mPos.x, mPos.y - 7), (mPos.x, mPos.y + 7), 1)

    pygame.display.flip()
