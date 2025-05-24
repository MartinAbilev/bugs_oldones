import pygame
from NeuralNetwork import *
import gfx as gx

# Initialize global variables
step = 0
Ann = Ann2()

# Display initial status
gx.status(Ann)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    Ann.annStep()
    gx.clear()
    gx.gloop(Ann)

# Cleanup
pygame.quit()
