"""Generate the default Best and child network files."""

from NeuralNetwork import *

# Local-space creature sensor/thruster points; the first four are legacy actuators.
poly=[(20,20), (-20,20), (-20,-20), (20,-20),   (0,20), (20,0), (0,-20), (-20,0), (40,40) ]

ann=Ann2()

# The serialized order is hidden nodes, inputs (including velocity), then outputs.
ann.createGrid(3)
ann.createInputs(len(poly)+2)
ann.createOutputs(5)
ann.poly=poly
ann.saveNet("Best")
ann.saveNet("child")
