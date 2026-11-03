import math

import pygame
from Box2D import b2CircleShape, b2Vec2

from NeuralNetwork import Ann2
from simulation_utils import dcircle, rotate_polygon, vector2d


class Creature:
    def __init__(
        self,
        position,
        world,
        creature_id,
        network_file,
        on_lifetime_update,
        on_birth,
    ):
        self.oId = creature_id
        self.death = 0
        self.Ann = Ann2()
        self.Ann.loadNet(network_file)
        self.step = 0
        self.time = 0
        self.lives = 3
        self.birthTimer = 0
        self.r = 10
        self.centerpos = 0
        self.on_lifetime_update = on_lifetime_update
        self.on_birth = on_birth
        self.body = world.world.CreateDynamicBody(position=position)
        self.body.userData = creature_id
        self.poly = self.Ann.poly
        self.box = self.body.CreateFixture(
            shape=b2CircleShape(radius=self.r),
            density=1,
            friction=0.8,
            restitution=0.2,
        )
        self.body.angularDamping = 0.99

    def angle(self):
        return math.degrees(self.body.angle)

    def ann_step(self):
        self.Ann.annStep()

    def read_color(self, pixel_array, center, point_index):
        x = int(center.x + self.poly[point_index][0] * 1.2)
        y = int(center.y + self.poly[point_index][1] * 1.2)
        x = max(0, min(639, x))
        y = max(0, min(479, y))
        try:
            color = pixel_array[x, y]
            return color[0]
        except Exception:
            return 0

    def sense(self, pixel_array, alive_count):
        if self.death != 0:
            return

        center = vector2d(self.body.position.x, self.body.position.y)
        colors = [
            self.read_color(pixel_array, center, index)
            for index in range(len(self.poly))
        ]
        hidden_size = self.Ann.hiddenSize
        for index, value in enumerate(colors):
            self.Ann.outSet(index + hidden_size, value)
        self.Ann.outSet(
            len(self.poly) + hidden_size,
            self.body.angularVelocity,
        )
        self.Ann.outSet(
            len(self.poly) + 1 + hidden_size,
            (self.body.linearVelocity.x + self.body.linearVelocity.y) / 2,
        )

        output_start = len(self.poly) + 2 + hidden_size
        self.ann_step()
        power = 100
        self.truster(
            *(self.Ann.neurons[output_start + index].out * power for index in range(5))
        )
        self.on_lifetime_update(self, alive_count)
        self.time += 1

    def draw(self, surface):
        if self.lives <= 0:
            self.death = 1
        if self.death != 0:
            self.body.active = False
            self.time = 0
            self.Ann = []
            return

        position = vector2d(
            self.body.position.x + self.r,
            self.body.position.y + self.r,
        )
        self.centerpos = vector2d(position.x - self.r, position.y - self.r)
        self.poly = rotate_polygon(self.Ann.poly, self.angle())
        hidden_size = self.Ann.hiddenSize
        dcircle(surface, position, self.angle(), self.r, 255, self.Ann.colorG, self.Ann.colorB)
        dcircle(
            surface,
            vector2d(self.centerpos.x + 2, self.centerpos.y + 2),
            self.angle(),
            2,
            0,
            255,
            0,
        )
        for index, point in enumerate(self.poly):
            dcircle(
                surface,
                vector2d(self.centerpos.x + point[0] + 2, self.centerpos.y + point[1] + 2),
                self.angle(),
                2,
                0,
                self.Ann.neurons[index + hidden_size].out,
                0,
            )

        self.birthTimer += 1
        if self.birthTimer > 300:
            self.birthTimer = 0
            self.on_birth(self)

    def draw_thruster_indicators(self, surface):
        output_start = self.Ann.hiddenSize + len(self.poly) + 2
        for index in range(min(4, len(self.poly))):
            output_index = output_start + index
            if output_index >= len(self.Ann.neurons):
                break

            activation = self.Ann.neurons[output_index].out
            if abs(activation) < 0.05:
                continue

            vertex_x, vertex_y = self.poly[index]
            vector_length = math.hypot(vertex_x, vertex_y)
            if vector_length == 0:
                continue

            direction = 1 if activation > 0 else -1
            start_x = self.centerpos.x + vertex_x
            start_y = self.centerpos.y + vertex_y
            arrow_length = 2 + 6 * min(abs(activation), 1)
            end_x = start_x + direction * vertex_x / vector_length * arrow_length
            end_y = start_y + direction * vertex_y / vector_length * arrow_length
            start = (round(start_x), round(start_y))
            end = (round(end_x), round(end_y))

            angle = math.atan2(end_y - start_y, end_x - start_x)
            arrow_head_length = 3
            base_x = end_x - arrow_head_length * math.cos(angle)
            base_y = end_y - arrow_head_length * math.sin(angle)
            pygame.draw.line(
                surface,
                (255, 255, 0),
                start,
                (round(base_x), round(base_y)),
                1,
            )
            for side in (-1, 1):
                head_x = base_x + side * arrow_head_length / 2 * math.sin(angle)
                head_y = base_y - side * arrow_head_length / 2 * math.cos(angle)
                pygame.draw.line(
                    surface,
                    (255, 255, 0),
                    end,
                    (round(head_x), round(head_y)),
                    1,
                )

    def truster(self, a, b, c, d, rotation):
        trust_center = b2Vec2(self.centerpos.x, self.centerpos.y)
        self.body.ApplyAngularImpulse(rotation, wake=True)
        for index, activation in enumerate((a, b, c, d)):
            trust_vector = b2Vec2(self.poly[index])
            self.body.ApplyLinearImpulse(
                trust_vector * activation,
                trust_center,
                wake=True,
            )
