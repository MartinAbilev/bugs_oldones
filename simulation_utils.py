import math

import pygame


class vector2d:
    def __init__(self, X, Y):
        self.x = X
        self.y = Y

    def __add__(self, other):
        return vector2d(self.x + other.x, self.y + other.y)


def dcircle(surface, pos, angle, radius, red, green, blue):
    pygame.draw.circle(surface, (red, green, blue), (pos.x, pos.y), radius)
    pygame.draw.circle(surface, (255, 0, 0), (pos.x, pos.y), radius, 1)


def rotate_polygon(polygon, theta):
    theta = math.radians(theta)
    return [
        (
            corner[0] * math.cos(theta) - corner[1] * math.sin(theta),
            corner[0] * math.sin(theta) + corner[1] * math.cos(theta),
        )
        for corner in polygon
    ]
