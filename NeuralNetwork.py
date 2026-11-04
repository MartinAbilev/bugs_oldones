import math
import random
import json

class vector2d(object):
    """Simple mutable coordinate used for editor neuron positions."""

    def __init__(self, X, Y):
        """Store x/y coordinates."""
        self.x = X
        self.y = Y

class Neuron2:
    """A weighted neural node plus its editor position and relationship metadata."""

    def __init__(self, Id):
        """Initialize an unconnected node with neutral activation."""
        self.id = Id
        self.type = 0  # 0 hidden, 1 input/sensor, 2 output.
        self.hiddenSize = 0
        self.conections = []  # Source node indices, paired by position with weights.
        self.weights = []
        self.out = 0.001
        self.pos = vector2d(8, 8)
        self.child = []
        self.parent = []
        self.lowest = []

    def step(self, Neurons):
        """Update this node from the current outputs of its connected sources."""
        neuron_outputs = [neuron.out for neuron in Neurons]
        self.out = self.activation(neuron_outputs)
        Neurons[self.id].out = self.out
        return Neurons

    def activation(self, neuron_outputs, source_limit=None):
        """Apply weighted tanh activation, optionally excluding later-layer sources."""
        value = 0
        for index, con in enumerate(self.conections):
            if source_limit is None or 0 <= con < source_limit:
                value += self.weights[index] * neuron_outputs[con]
        return math.tanh(value * 5)

class Ann2:
    """Neural network, including node layers and creature morphology."""

    def __init__(self):
        """Create an empty network with default creature colors."""
        self.maxN = 0
        self.hiddenSize = 0  # Hidden nodes occupy the first hiddenSize entries.
        self.colorR = 255
        self.colorG = 0
        self.colorB = 0
        self.poly = []  # Sensor/thruster morphology points used by the simulation.
        self.neurons = []

    def setPoly(self, p):
        """Replace the creature's local-space morphology points."""
        self.poly = p

    def annStep(self):
        """Evaluate hidden nodes first, then outputs, using the fixed layer layout."""
        hidden_end = min(max(self.hiddenSize, 0), len(self.neurons))
        # Two extra input slots after morphology sensors carry angular/linear velocity.
        sensor_end = min(hidden_end + len(self.poly) + 2, len(self.neurons))
        previous_outputs = [neuron.out for neuron in self.neurons]

        hidden_outputs = [
            neuron.activation(previous_outputs, sensor_end)
            for neuron in self.neurons[:hidden_end]
        ]
        for neuron, output in zip(self.neurons[:hidden_end], hidden_outputs):
            neuron.out = output

        layer_outputs = [neuron.out for neuron in self.neurons]
        for neuron in self.neurons[sensor_end:]:
            neuron.out = neuron.activation(layer_outputs, sensor_end)

    def connect(self, inpA, toB, w):
        """Add a weighted source-to-target link using the legacy connection layout."""
        self.neurons[inpA].conections.append(toB)
        self.neurons[inpA].weights.append(w)

    def connectAllToAll(self):
        """Replace links with all source-to-hidden/output links at unit weight."""
        neuron_count = len(self.neurons)
        hidden_end = min(max(self.hiddenSize, 0), neuron_count)
        source_end = min(hidden_end + len(self.poly) + 2, neuron_count)

        for neuron in self.neurons:
            neuron.conections = []
            neuron.weights = []
            neuron.parent = []
            neuron.child = []
            neuron.lowest = []

        for target_index in list(range(hidden_end)) + list(range(source_end, neuron_count)):
            target = self.neurons[target_index]
            for source_index in range(source_end):
                target.conections.append(source_index)
                target.weights.append(1.0)
                target.parent.append(source_index)
                self.neurons[source_index].child.append(target_index)

    def insertNeuron(self, index, neuron_type, position):
        """Insert a node into its layer and shift existing node references."""
        neuron = Neuron2(index)
        neuron.type = neuron_type
        neuron.pos = vector2d(float(position.x), float(position.y))

        for existing in self.neurons:
            existing.conections = [
                connection + 1 if connection >= index else connection
                for connection in existing.conections
            ]
            for relation_name in ("child", "parent", "lowest"):
                relations = getattr(existing, relation_name)
                setattr(
                    existing,
                    relation_name,
                    [relation + 1 if relation >= index else relation for relation in relations],
                )

        self.neurons.insert(index, neuron)
        for neuron_id, existing in enumerate(self.neurons):
            existing.id = neuron_id
        self.maxN = len(self.neurons)
        return neuron

    def outSet(self, Id, value):
        """Set a node's externally supplied input value."""
        self.neurons[Id].out = value

    # the sequence how nns are creted important grid inputs and outputs !!!
    def createGrid(self, n):
        """Append an n-by-n hidden layer and fully connect the new hidden nodes."""
        self.hiddenSize = n * n
        i = self.maxN
        offsetX = 200
        offsetY = 200
        for y in range(n):
            for x in range(n):
                self.neurons.append(Neuron2(self.maxN))
                self.neurons[self.maxN].pos.x = offsetX + (x * 60)
                self.neurons[self.maxN].pos.y = offsetY + (y * 60)
                self.neurons[self.maxN].type = 0
                self.maxN += 1
        for neuron in self.neurons:
            if neuron.id >= i:
                for con in self.neurons:
                    if con.id >= i:
                        self.connect(neuron.id, con.id, 1)

    def createInputs(self, n):
        """Append n input nodes and connect them to the existing hidden layer."""
        i = self.maxN
        offsetX = 100
        offsetY = 100
        print('Creating inputs.', n)
        for y in range(n):
            for x in range(1):
                self.neurons.append(Neuron2(self.maxN))
                self.neurons[self.maxN].pos.x = offsetX + (x * 60)
                self.neurons[self.maxN].pos.y = offsetY + (y * 60)
                self.neurons[self.maxN].type = 1
                self.maxN += 1
        for neuron in self.neurons:
            if neuron.id < i: # so its all hiden ones starting from 0..gr
                for con in self.neurons:
                    if con.id >= i: # to its all ones starting from inputs
                        print('input conected', neuron.id, con.id)
                        # input appended as to every hoden con
                        self.connect(neuron.id, con.id, 1)

    def createOutputs(self, n):
        """Append n output nodes and connect them to existing nodes."""
        i = self.maxN
        offsetX = 200
        offsetY = 50
        for y in range(1):
            for x in range(n):
                self.neurons.append(Neuron2(self.maxN))
                self.neurons[self.maxN].pos.x = offsetX + (x * 60)
                self.neurons[self.maxN].pos.y = offsetY + (y * 60)
                self.neurons[self.maxN].type = 2
                self.maxN += 1
        for neuron in self.neurons:
            if neuron.id < i: # so every  nuron starting from 0..out
                for con in self.neurons:
                    if con.id >= i: # to its all ones starting from outputs
                        print('output conected', con.id, neuron.id)
                        # so every nuron is appended to out con
                        self.connect(con.id, neuron.id, 1)

    def sort(self, neuron_type=None):
        """Arrange the selected layer: hidden nodes in a grid, inputs/outputs around it."""
        neuron_count = len(self.neurons)
        hidden_count = min(max(self.hiddenSize, 0), neuron_count)
        input_count = min(len(self.poly) + 2, neuron_count - hidden_count)
        output_start = hidden_count + input_count

        center_x = 320
        center_y = 240
        columns = math.ceil(math.sqrt(hidden_count)) if hidden_count else 0
        rows = math.ceil(hidden_count / columns) if columns else 0
        spacing = 48

        if neuron_type in (None, 0):
            for index in range(hidden_count):
                row = index // columns
                row_start = row * columns
                row_length = min(columns, hidden_count - row_start)
                column = index - row_start
                self.neurons[index].pos = vector2d(
                    center_x + (column - (row_length - 1) / 2) * spacing,
                    center_y + (row - (rows - 1) / 2) * spacing,
                )

        if neuron_type in (None, 1):
            # Keep the input layer readable without changing the creature morphology.
            for index in range(input_count):
                angle = -math.pi / 2 + 2 * math.pi * index / max(input_count, 1)
                self.neurons[hidden_count + index].pos = vector2d(
                    center_x + 185 * math.cos(angle),
                    center_y + 185 * math.sin(angle),
                )

        if neuron_type in (None, 2):
            max_poly_extent = max(
                40,
                max(
                    (abs(float(coordinate)) for point in self.poly for coordinate in point),
                    default=0,
                ),
            )
            output_scale = 225 / max_poly_extent
            output_count = neuron_count - output_start
            mapped_output_count = min(4, len(self.poly))
            for index in range(output_count):
                neuron = self.neurons[output_start + index]
                if index < mapped_output_count:
                    x, y = self.poly[index]
                    neuron.pos = vector2d(
                        center_x + float(x) * output_scale,
                        center_y + float(y) * output_scale,
                    )
                else:
                    extra_index = index - mapped_output_count
                    extra_count = output_count - mapped_output_count
                    angle = -math.pi / 2 + 2 * math.pi * extra_index / max(extra_count, 1)
                    neuron.pos = vector2d(
                        center_x + 225 * math.cos(angle),
                        center_y + 225 * math.sin(angle),
                    )

    def loadNet(self, fname):
        """Load a network JSON file and discard output links to invalid later layers."""
        self.neurons = []
        with open(fname + '.json', 'r') as f:
            data = json.load(f)

        # Load colors
        self.colorR = data['colorR']
        self.colorG = data['colorG']
        self.colorB = data['colorB']

        # hiddenSize
        self.hiddenSize = data['hiddenSize']

        # Load poly
        self.poly = [[float(p[0]), float(p[1])] for p in data['poly']]

        # Load neurons
        for neuron_data in data['neurons']:
            neuron = Neuron2(neuron_data['id'])
            neuron.type = neuron_data['type']
            neuron.pos = vector2d(float(neuron_data['pos']['x']), float(neuron_data['pos']['y']))
            neuron.conections = neuron_data['conections']
            neuron.weights = neuron_data['weights']
            neuron.child = neuron_data['child']
            neuron.parent = neuron_data['parent']
            neuron.lowest = neuron_data['lowest']
            self.neurons.append(neuron)

        self.maxN = len(self.neurons)
        output_start = min(self.hiddenSize + len(self.poly) + 2, self.maxN)
        for neuron in self.neurons[output_start:]:
            connections = [
                (source, weight)
                for source, weight in zip(neuron.conections, neuron.weights)
                if 0 <= source < output_start
            ]
            neuron.conections = [source for source, _ in connections]
            neuron.weights = [weight for _, weight in connections]

    def saveNet(self, fname):
        """Serialize morphology, node metadata, positions, and links to JSON."""
        # Prepare data structure for JSON
        data = {
            'colorR': self.colorR,
            'colorG': self.colorG,
            'colorB': self.colorB,
            'hiddenSize': self.hiddenSize,
            'poly': [[float(p[0]), float(p[1])] for p in self.poly],
            'neurons': []
        }

        # Serialize neuron data
        for neuron in self.neurons:
            neuron_data = {
                'id': neuron.id,
                'type': neuron.type,
                'pos': {'x': float(neuron.pos.x), 'y': float(neuron.pos.y)},
                'conections': neuron.conections,
                'weights': neuron.weights,
                'child': neuron.child,
                'parent': neuron.parent,
                'lowest': neuron.lowest
            }
            data['neurons'].append(neuron_data)

        # Write to JSON file
        with open(fname + '.json', 'w') as f:
            json.dump(data, f, indent=4)

    def randomizeDNA(self, factor):
        """Mutate creature colors and morphology, then refresh editor marker positions."""
        self.colorG = max(0, min(255, round(self.colorG + random.randint(-100, 100) * factor)))
        self.colorB = max(0, min(255, round(self.colorB + random.randint(-100, 100) * factor)))
        i = 0
        for pol in self.poly:
            rnd = random.randint(-1, 1) * factor
            L = list(pol)
            L[0] += rnd
            rnd = random.randint(-1, 1) * factor
            L[1] += rnd
            self.poly[i] = L
            i += 1
        self.syncMorphologyPositions()

    def syncMorphologyPositions(self):
        """Keep sensor markers and morphology-backed thruster markers aligned."""
        center_x = 320
        center_y = 240
        max_poly_extent = max(
            40,
            max(
                (abs(float(coordinate)) for point in self.poly for coordinate in point),
                default=0,
            ),
        )
        sensor_start = self.hiddenSize
        output_start = min(sensor_start + len(self.poly) + 2, len(self.neurons))

        for index, (x, y) in enumerate(self.poly):
            sensor_index = sensor_start + index
            if sensor_index < len(self.neurons):
                self.neurons[sensor_index].pos = vector2d(
                    center_x + float(x) * 185 / max_poly_extent,
                    center_y + float(y) * 185 / max_poly_extent,
                )

            output_index = output_start + index
            if index < 4 and output_index < len(self.neurons):
                self.neurons[output_index].pos = vector2d(
                    center_x + float(x) * 225 / max_poly_extent,
                    center_y + float(y) * 225 / max_poly_extent,
                )

    def randomizeWeights(self, factor):
        """Mutate morphology and connection weights in proportion to factor."""
        if factor <= 0:
            return

        self.randomizeDNA(factor)
        for neuron in self.neurons:
            i = 0
            for weight in neuron.weights:
                neuron.weights[i] += random.randint(-1, 1) * factor
                i += 1
