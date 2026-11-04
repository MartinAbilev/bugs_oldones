import math

import pygame


class vector2d:
    """Minimal mutable x/y point shared by drawing and creature code."""

    def __init__(self, X, Y):
        """Initialize a point with screen/world coordinates."""
        self.x = X
        self.y = Y

    def __add__(self, other):
        """Return the component-wise sum as a new point."""
        return vector2d(self.x + other.x, self.y + other.y)


def dcircle(surface, pos, angle, radius, red, green, blue):
    """Draw a filled creature marker with the simulation's red outline."""
    pygame.draw.circle(surface, (red, green, blue), (pos.x, pos.y), radius)
    pygame.draw.circle(surface, (255, 0, 0), (pos.x, pos.y), radius, 1)


def rotate_polygon(polygon, theta):
    """Rotate local polygon coordinates by an angle in degrees."""
    theta = math.radians(theta)
    return [
        (
            corner[0] * math.cos(theta) - corner[1] * math.sin(theta),
            corner[0] * math.sin(theta) + corner[1] * math.cos(theta),
        )
        for corner in polygon
    ]
