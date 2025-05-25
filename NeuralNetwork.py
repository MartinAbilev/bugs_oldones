import math
import random
import json

class vector2d(object):
    def __init__(self, X, Y):
        self.x = X
        self.y = Y

class Neuron2:
    def __init__(self, Id):
        self.id = Id
        self.type = 0
        self.conections = []
        self.weights = []
        self.out = 0.001
        self.pos = vector2d(8, 8)
        self.child = []
        self.parent = []
        self.lowest = []

    def step(self, Neurons):
        value = 0
        i = 0
        for con in self.conections:
            value += self.weights[i] * Neurons[con].out
            i += 1
        self.out = math.tanh(value * 5)
        Neurons[self.id].out = self.out
        return Neurons

class Ann2:
    def __init__(self):
        self.maxN = 0
        self.colorR = 255
        self.colorG = 0
        self.colorB = 0
        self.poly = []
        self.neurons = []

    def setPoly(self, p):
        self.poly = p

    def annStep(self):
        for neuron in self.neurons:
            self.neurons = neuron.step(self.neurons)

    def connect(self, inpA, toB, w):
        self.neurons[inpA].conections.append(toB)
        self.neurons[inpA].weights.append(w)

    def outSet(self, Id, value):
        self.neurons[Id].out = value

    # the sequence how nns are creted important grid inputs and outputs !!!
    def createGrid(self, n):
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

    def loadNet(self, fname):
        self.neurons = []
        with open(fname + '.json', 'r') as f:
            data = json.load(f)

        # Load colors
        self.colorR = data['colorR']
        self.colorG = data['colorG']
        self.colorB = data['colorB']

        # Load poly
        self.poly = [[float(p[0]), float(p[1])] for p in data['poly']]

        # Load neurons
        for neuron_data in data['neurons']:
            neuron = Neuron2(neuron_data['id'])
            neuron.pos = vector2d(float(neuron_data['pos']['x']), float(neuron_data['pos']['y']))
            neuron.conections = neuron_data['conections']
            neuron.weights = neuron_data['weights']
            neuron.child = neuron_data['child']
            neuron.parent = neuron_data['parent']
            neuron.lowest = neuron_data['lowest']
            self.neurons.append(neuron)

        self.maxN = len(self.neurons)

    def saveNet(self, fname):
        # Prepare data structure for JSON
        data = {
            'colorR': self.colorR,
            'colorG': self.colorG,
            'colorB': self.colorB,
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
        rnd = random.randint(-100, 100)
        self.colorG += rnd
        if self.colorG > 255:
            self.colorG = 255
        if self.colorG < 0:
            self.colorG = 0
        rnd = random.randint(-100, 100)
        self.colorB += rnd
        if self.colorB > 255:
            self.colorB = 255
        if self.colorB < 0:
            self.colorB = 0
        i = 0
        for pol in self.poly:
            rnd = random.randint(-1, 1) * factor
            L = list(pol)
            L[0] += rnd
            rnd = random.randint(-1, 1) * factor
            L[1] += rnd
            self.poly[i] = L
            i += 1

    def randomizeWeights(self, factor):
        self.randomizeDNA(0.1)
        for neuron in self.neurons:
            i = 0
            for weight in neuron.weights:
                neuron.weights[i] += random.randint(-1, 1) * factor
                i += 1
