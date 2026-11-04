import math

import pygame
from NeuralNetwork import *  # Assuming this includes Neuron, NeuralNetwork, etc.

# Define vector2d class to replace sf.Vector2
class vector2d(object):
    """Mutable point used by the editor's node layout and drag handling."""

    def __init__(self, X, Y):
        """Store the point's screen coordinates."""
        self.x = X
        self.y = Y

# Initialize Pygame
pygame.init()
w = pygame.display.set_mode((640, 480))
pygame.display.set_caption("BUGZ // NEURAL LAB")
background = pygame.Surface((640, 480))
background.fill((7, 12, 21))
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

# Editor interaction state: selected node, connection gesture, and cursor position.
mouseOn = -1
cstate = -1
cswitch = 0
selected = 0
onbutton = 0
mPos = vector2d(0, 0)
create_neuron_type = 0  # Node type assigned when the user clicks empty graph space.
view_zoom = 1.0
view_pan = vector2d(0, 0)
last_pan_position = None
drag_node_index = -1
drag_offset = vector2d(0, 0)

# Helper function to calculate distance (replacing vmath.cDist if needed)
def cDist(pos1, pos2):
    """Return Euclidean distance between two editor points."""
    return ((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2) ** 0.5

def graphToScreen(position):
    """Project a saved graph coordinate through the current editor viewport."""
    return vector2d(
        position.x * view_zoom + view_pan.x,
        position.y * view_zoom + view_pan.y,
    )

def screenToGraph(position):
    """Convert a screen point back to a persistent graph coordinate."""
    return vector2d(
        (position.x - view_pan.x) / view_zoom,
        (position.y - view_pan.y) / view_zoom,
    )

def zoomAt(position, wheel_delta):
    """Zoom around the pointer so the graph point under it stays stationary."""
    global view_zoom, view_pan
    graph_position = screenToGraph(position)
    old_zoom = view_zoom
    view_zoom = max(0.25, min(3.0, view_zoom * (1.15 ** wheel_delta)))
    if view_zoom != old_zoom:
        view_pan.x = position.x - graph_position.x * view_zoom
        view_pan.y = position.y - graph_position.y * view_zoom

def status(ann):
    """Compatibility hook retained for the editor entry point."""
    global cstate

def clear():
    """Redraw the editor background and its viewport-transformed graph grid."""
    w.blit(background, (0, 0))
    spacing = 25 * view_zoom
    pygame.draw.rect(w, (11, 24, 35), (0, 0, 505, 480))
    w.set_clip(pygame.Rect(0, 0, 505, 480))
    grid_x = view_pan.x % spacing
    while grid_x < 505:
        pygame.draw.line(w, (11, 24, 35), (round(grid_x), 0), (round(grid_x), 480))
        grid_x += spacing
    grid_y = view_pan.y % spacing
    while grid_y < 480:
        pygame.draw.line(w, (11, 24, 35), (0, round(grid_y)), (505, round(grid_y)))
        grid_y += spacing
    w.set_clip(None)
    pygame.draw.rect(w, (20, 190, 185), (1, 1, 502, 478), 2)

def circle(pos, r, c):
    """Draw the legacy circular node marker and return its hover state."""
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
    """Draw a node using its layer shape and current activation brightness."""
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
    """Return the editor shape implied by the node's hidden/input/output layer."""
    if index < ann.hiddenSize:
        return "circle"
    if index < ann.hiddenSize + len(ann.poly) + 2:
        return "triangle"
    return "square"

def moveCreaturePoint(ann, neuron_index):
    """Update morphology when dragging a sensor or morphology-backed thruster."""
    sensor_start = ann.hiddenSize
    output_start = sensor_start + len(ann.poly) + 2
    if sensor_start <= neuron_index < sensor_start + len(ann.poly):
        poly_index = neuron_index - sensor_start
        scale = 1.2
    elif output_start <= neuron_index < output_start + min(4, len(ann.poly)):
        poly_index = neuron_index - output_start
        scale = 1
    else:
        return

    ann.poly[poly_index] = [
        (ann.neurons[neuron_index].pos.x - 320) / scale,
        (ann.neurons[neuron_index].pos.y - 240) / scale,
    ]
    ann.syncMorphologyPositions()

def line(frm, to, color=(255, 255, 255)):
    """Draw a connection between two editor coordinates."""
    pygame.draw.line(w, color, (frm.x, frm.y), (to.x, to.y))

def connectionColor(weight, min_weight, max_weight):
    """Map a connection weight to a grayscale brightness within the graph range."""
    if max_weight == min_weight:
        brightness = 255
    else:
        normalized = (weight - min_weight) / (max_weight - min_weight)
        brightness = round(40 + normalized * 215)
    return (brightness, brightness, brightness)

def text(msg, pos, c, s):
    """Render a compact label beside a graph node."""
    text_font = font if s == 16 else ui_font_9 if s <= 10 else ui_font_10
    text_surface = text_font.render(msg, True, c)
    w.blit(text_surface, (pos.x + 16, pos.y - 11))

def drawButton(name, rect, mouse_pos):
    """Draw a sidebar button and report whether the pointer is over it."""
    hovered = rect.collidepoint(mouse_pos)
    fill = (28, 57, 70) if hovered else (15, 25, 39)
    edge = (70, 220, 205) if hovered else (35, 75, 88)
    pygame.draw.rect(w, fill, rect, border_radius=5)
    pygame.draw.rect(w, edge, rect, 1, border_radius=5)
    label = ui_font_9.render(name, True, (225, 242, 245) if hovered else (157, 190, 200))
    w.blit(label, label.get_rect(center=rect.center))
    return hovered

def drawThrusterDirection(ann, output_index):
    """Draw the thruster arrow at the same local offset used by the simulation."""
    output_start = ann.hiddenSize + len(ann.poly) + 2
    if output_index == 4:
        return

    neuron = ann.neurons[output_start + output_index]
    output_indices = [
        index for index in range(len(ann.neurons) - output_start) if index != 4
    ]
    vector_by_index = dict(zip(output_indices, ann.thrusterVectors(output_indices)))
    direction_x, direction_y = vector_by_index[output_index]
    direction_length = math.hypot(direction_x, direction_y)
    if direction_length == 0:
        return

    activation = neuron.out
    if activation <= 0:
        direction_x = -direction_x
        direction_y = -direction_y
    vector_x, vector_y = vector_by_index[output_index]
    start = graphToScreen(vector2d(320 + vector_x, 240 + vector_y))
    end = graphToScreen(
        vector2d(
            320 + vector_x + direction_x / direction_length * 8,
            240 + vector_y + direction_y / direction_length * 8,
        )
    )
    color = (255, 220, 90) if abs(activation) >= 0.05 else (90, 150, 170)
    thickness = max(1, round(view_zoom * (2 if abs(activation) >= 0.05 else 1)))
    pygame.draw.line(
        w,
        color,
        (round(start.x), round(start.y)),
        (round(end.x), round(end.y)),
        thickness,
    )
    angle = math.atan2(end.y - start.y, end.x - start.x)
    arrow_head_length = 3 * view_zoom
    for side in (-1, 1):
        head_x = end.x - arrow_head_length * math.cos(angle) + side * arrow_head_length / 2 * math.sin(angle)
        head_y = end.y - arrow_head_length * math.sin(angle) - side * arrow_head_length / 2 * math.cos(angle)
        pygame.draw.line(
            w,
            color,
            (round(end.x), round(end.y)),
            (round(head_x), round(head_y)),
            thickness,
        )

def drawSimulationMorphology(ann):
    """Show the creature body and sensor samples at their simulation coordinates."""
    center = graphToScreen(vector2d(320, 240))
    center_point = (round(center.x), round(center.y))
    radius = max(1, round(10 * view_zoom))
    pygame.draw.circle(
        w,
        (ann.colorR, ann.colorG, ann.colorB),
        center_point,
        radius,
    )
    pygame.draw.circle(
        w,
        (255, 0, 0),
        center_point,
        radius,
        max(1, round(view_zoom)),
    )
    pygame.draw.circle(w, (0, 255, 0), center_point, max(1, round(2 * view_zoom)))

    for index, (x, y) in enumerate(ann.poly):
        sensor = graphToScreen(
            vector2d(320 + float(x) * 1.2, 240 + float(y) * 1.2)
        )
        neuron_index = ann.hiddenSize + index
        activation = ann.neurons[neuron_index].out if neuron_index < len(ann.neurons) else 0
        sensor_point = (round(sensor.x), round(sensor.y))
        pygame.draw.circle(
            w,
            (0, max(0, min(255, round(activation))), 0),
            sensor_point,
            max(1, round(2 * view_zoom)),
        )
        pygame.draw.circle(w, (255, 0, 0), sensor_point, max(1, round(2 * view_zoom)), 1)

def createNeuronAt(ann, position, neuron_type):
    """Insert a node into its layer, adding morphology for sensor nodes."""
    if neuron_type == 0:
        neuron = ann.insertNeuron(ann.hiddenSize, neuron_type, position)
        ann.hiddenSize += 1
        return neuron

    if neuron_type == 1:
        point = [
            (position.x - 320) / 1.2,
            (position.y - 240) / 1.2,
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
    neuron = ann.insertNeuron(len(ann.neurons), neuron_type, position)
    ann.syncMorphologyPositions()
    return neuron

def gui(ann):
    """Legacy UI hook; sidebar rendering is performed directly by gloop."""
    pass  # Placeholder if needed

def gloop(ann, events):
    """Process one frame of editor input and draw the graph and sidebar."""
    global w, mPos, mouseOn, cstate, cswitch, selected, onbutton, create_neuron_type
    global last_pan_position, view_pan, drag_node_index, drag_offset
    onbutton = 0

    mouse_pos = pygame.mouse.get_pos()
    mPos = vector2d(mouse_pos[0], mouse_pos[1])
    middle_down = pygame.mouse.get_pressed()[1]

    for event in events:
        if event.type == pygame.VIDEORESIZE:
            w = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            pygame.display.set_caption("BUGZ // NEURAL LAB")
        if event.type == pygame.MOUSEWHEEL:
            if mouse_pos[0] < 505:
                zoomAt(mPos, event.y)

    if middle_down and last_pan_position is not None:
        view_pan.x += mouse_pos[0] - last_pan_position[0]
        view_pan.y += mouse_pos[1] - last_pan_position[1]
        mouseOn = -1
    last_pan_position = mouse_pos if middle_down else None
    if any(
        event.type == pygame.MOUSEBUTTONUP and event.button == 1
        for event in events
    ):
        drag_node_index = -1
        ann.syncMorphologyPositions()

    left_down = pygame.mouse.get_pressed()[0]
    right_down = pygame.mouse.get_pressed()[2]
    # Use button-down events for one-shot actions; held state is reserved for dragging.
    left_clicks = [
        event.pos
        for event in events
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
    ]

    if not left_down or middle_down:
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
                graphToScreen(neuron.pos),
                graphToScreen(ann.neurons[c].pos),
                connectionColor(weight, min_weight, max_weight),
            )

    drawSimulationMorphology(ann)
    for index, neuron in enumerate(ann.neurons):
        screen_position = graphToScreen(neuron.pos)
        if drawNeuron(screen_position, 16, neuron.out, neuronShape(ann, index)):
            mouseOn = neuron.id
        text(str(round(neuron.out, 3)), screen_position, (255, 0, 0), 8)
        # The simulation's output layer begins after hidden nodes and all sensor inputs.
        output_start = ann.hiddenSize + len(ann.poly) + 2
        if index >= output_start:
            drawThrusterDirection(ann, index - output_start)

    if not middle_down:
        for click_position in left_clicks:
            if click_position[0] < 505 and mouseOn >= 0:
                graph_click = screenToGraph(
                    vector2d(click_position[0], click_position[1])
                )
                node_position = ann.neurons[mouseOn].pos
                drag_node_index = mouseOn
                drag_offset = vector2d(
                    node_position.x - graph_click.x,
                    node_position.y - graph_click.y,
                )

    if not middle_down and mouseOn == -1 and any(pos[0] < 505 for pos in left_clicks):
        createNeuronAt(ann, screenToGraph(mPos), create_neuron_type)

    if left_down and not middle_down and drag_node_index >= 0 and mouse_pos[0] < 505:
        old = ann.neurons[drag_node_index].pos
        graph_mouse_position = screenToGraph(mPos)
        new_position = vector2d(
            graph_mouse_position.x + drag_offset.x,
            graph_mouse_position.y + drag_offset.y,
        )
        ann.neurons[drag_node_index].pos = new_position
        moveCreaturePoint(ann, drag_node_index)
        distX = vector2d(new_position.x - old.x, new_position.y - old.y)
        for child in ann.neurons[drag_node_index].lowest:
            ann.neurons[child].pos = vector2d(
                ann.neurons[child].pos.x + distX.x,
                ann.neurons[child].pos.y + distX.y,
            )
        selected = drag_node_index

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

    all_to_all_button = pygame.Rect(516, 328, 111, 25)
    drawButton("ALL-TO-ALL", all_to_all_button, mouse_pos)

    w.blit(ui_font_9.render("CREATE NODE TYPE", True, (130, 158, 177)), (520, 361))
    creation_specs = [
        ("HIDDEN", 0, pygame.Rect(516, 378, 111, 23)),
        ("SENSOR", 1, pygame.Rect(516, 406, 111, 23)),
        ("THRUSTER", 2, pygame.Rect(516, 434, 111, 23)),
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
    all_to_all_clicked = any(all_to_all_button.collidepoint(pos) for pos in left_clicks)

    if save_clicked:
        ann.saveNet('Best')
        ann.loadNet('Best')
    if load_clicked:
        ann.loadNet('Best')
    if sort_clicked:
        ann.sort(create_neuron_type)
    if rand_clicked:
        ann.randomizeWeights(0.1)
    if clear_clicked:
        ann.neurons = []
        ann.maxN = 0
        ann.hiddenSize = 0
        ann.poly = []
    if grid_clicked:
        ann.createGrid(6)
    if all_to_all_clicked:
        ann.connectAllToAll()

    if not middle_down and right_down and mouseOn >= 0 and cswitch == 0:
        cstate = mouseOn
        cswitch = 1

    if not right_down and mouseOn == -1 and cswitch == 1:
        cstate = -1
        cswitch = 2

    if not middle_down and right_down and mouseOn >= 0 and cswitch == 2:
        cstate = -1
        cswitch = 0

    if not middle_down and right_down and mouseOn >= 0 and cstate >= 0 and cstate != mouseOn and cswitch == 1:
        ann.connect(mouseOn, cstate, 1)
        ann.neurons[cstate].child.append(mouseOn)
        ann.neurons[mouseOn].parent.append(cstate)
        cstate = -1
        cswitch = 2

    if cswitch == 1:
        line(graphToScreen(ann.neurons[cstate].pos), mPos)

    if cswitch == 2 and mouseOn == -1:
        cswitch = 0

    if mouse_pos[0] < 505:
        pygame.draw.circle(w, (70, 235, 220), (int(mPos.x), int(mPos.y)), 4, 1)
        pygame.draw.line(w, (70, 235, 220), (mPos.x - 7, mPos.y), (mPos.x + 7, mPos.y), 1)
        pygame.draw.line(w, (70, 235, 220), (mPos.x, mPos.y - 7), (mPos.x, mPos.y + 7), 1)

    pygame.display.flip()
