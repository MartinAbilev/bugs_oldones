"""Launch the standalone neural-network editor on the saved Best network."""

import pygame
from NeuralNetwork import *
import gfx as gx

# Initialize global variables
step = 0  # Editor frame counter retained for compatibility with the legacy UI.
Ann = Ann2()  # Network currently being edited.
Ann.loadNet('Best')
clock = pygame.time.Clock()  # Caps editor updates to reduce idle CPU usage.

# Display initial status
gx.status(Ann)

# Main loop
running = True  # Set false when the editor window receives QUIT.
while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False

    Ann.annStep()
    gx.clear()
    gx.gloop(Ann, events)
    clock.tick(60)

# Cleanup
pygame.quit()
