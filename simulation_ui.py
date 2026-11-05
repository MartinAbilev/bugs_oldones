import pygame


class SimulationUI:
    """Draw the simulation arena, sidebar dashboard, and neural activity map."""

    def __init__(self):
        """Create cached arena graphics, fonts, and interactive control hitboxes."""
        self.background = pygame.Surface((640, 480))
        self.background.fill((7, 12, 21))
        for grid_x in range(25, 500, 25):
            pygame.draw.line(self.background, (11, 24, 35), (grid_x, 0), (grid_x, 400))
        for grid_y in range(25, 400, 25):
            pygame.draw.line(self.background, (11, 24, 35), (0, grid_y), (500, grid_y))

        self.border_glow = pygame.Surface((640, 480), pygame.SRCALPHA)
        for inset in range(10):
            alpha = round(220 * (1 - inset / 10) ** 1.5)
            pygame.draw.rect(
                self.border_glow,
                (255, 35, 55, alpha),
                (1 + inset, 1 + inset, 498 - inset * 2, 398 - inset * 2),
                1,
            )

        self.font_8 = pygame.font.SysFont("arial", 8)
        self.font_9 = pygame.font.SysFont("arial", 9)
        self.font_10 = pygame.font.SysFont("arial", 10)
        self.font_12 = pygame.font.SysFont("arial", 12)
        self.font_14 = pygame.font.SysFont("arial", 14, bold=True)
        self.font_20 = pygame.font.SysFont("arial", 20, bold=True)
        self.radiation_slider = pygame.Rect(519, 137, 108, 8)  # Visible slider track.
        self.radiation_slider_hitbox = pygame.Rect(510, 116, 121, 40)
        self.pause_button = pygame.Rect(582, 59, 42, 27)
        self.edit_button = pygame.Rect(516, 410, 112, 29)  # Opens the network editor.

    @staticmethod
    def text(surface, message, position, color, font):
        """Render one UI label onto a surface."""
        surface.blit(font.render(message, True, color), position)

    def draw_arena_border(self, surface):
        """Draw the red gradient glow around the arena."""
        surface.blit(self.border_glow, (0, 0))

    @staticmethod
    def draw_sensor_border(surface):
        """Draw a solid-red sensor target over the arena's border area."""
        red = (255, 0, 0)
        pygame.draw.rect(surface, red, (0, 0, 500, 10))
        pygame.draw.rect(surface, red, (0, 390, 500, 10))
        pygame.draw.rect(surface, red, (0, 10, 10, 380))
        pygame.draw.rect(surface, red, (490, 10, 10, 380))

    @staticmethod
    def draw_godhand(surface, position):
        """Draw the red cursor orb that creatures can detect with red sensors."""
        x, y = map(round, position)
        pygame.draw.circle(surface, (255, 45, 65), (x, y), 14, 2)
        pygame.draw.circle(surface, (255, 45, 65), (x, y), 8, 1)
        pygame.draw.circle(surface, (255, 30, 55), (x, y), 4)
        pygame.draw.circle(surface, (255, 220, 220), (x - 1, y - 1), 1)

    def draw_neural_activity(self, surface, objects):
        """Show each living creature's neuron activations in type-colored rows."""
        bounds = pygame.Rect(8, 407, 484, 67)
        pygame.draw.rect(surface, (6, 15, 21), bounds, border_radius=6)
        pygame.draw.rect(surface, (23, 86, 81), bounds, 1, border_radius=6)

        living_creatures = [obj for obj in objects if obj.death == 0]
        self.text(
            surface,
            "NEURAL MAP",
            (16, 411),
            (80, 207, 165),
            self.font_9,
        )
        legend = (
            ("IN", (55, 135, 255)),
            ("HID", (45, 225, 115)),
            ("OUT", (255, 75, 75)),
        )
        legend_x = 338
        for label, color in legend:
            pygame.draw.rect(surface, color, (legend_x, 412, 5, 5))
            self.text(surface, label, (legend_x + 8, 410), color, self.font_9)
            legend_x += 48

        if not living_creatures:
            self.text(surface, "awaiting signal", (16, 438), (94, 117, 137), self.font_9)
            return

        network = living_creatures[0].Ann
        neuron_count = len(network.neurons)
        if neuron_count == 0:
            return

        # Keep network indices intact while displaying inputs, hidden, then outputs.
        hidden_end = min(network.hiddenSize, neuron_count)
        input_end = min(hidden_end + len(network.poly) + 2, neuron_count)
        input_indices = list(range(hidden_end, input_end))
        hidden_indices = list(range(hidden_end))
        output_indices = list(range(input_end, neuron_count))
        display_indices = input_indices + hidden_indices + output_indices
        row_top = 424
        row_height = bounds.bottom - 4 - row_top
        column_width = bounds.width - 12

        pygame.draw.line(
            surface,
            (23, 55, 55),
            (bounds.left + 5, row_top - 2),
            (bounds.right - 5, row_top - 2),
            1,
        )
        for row_index, creature in enumerate(living_creatures):
            y0 = row_top + row_index * row_height // len(living_creatures)
            y1 = row_top + (row_index + 1) * row_height // len(living_creatures)
            if y1 <= y0:
                continue

            for display_index, neuron_index in enumerate(display_indices):
                neuron = creature.Ann.neurons[neuron_index]
                x0 = bounds.left + 6 + display_index * column_width // neuron_count
                x1 = bounds.left + 6 + (display_index + 1) * column_width // neuron_count
                cell_size = max(1, min(x1 - x0, y1 - y0))
                cell_left = x0 + (x1 - x0 - cell_size) // 2
                cell_top = y0 + (y1 - y0 - cell_size) // 2

                if neuron_index < hidden_end:
                    base_color = (45, 225, 115)
                elif neuron_index < input_end:
                    base_color = (55, 135, 255)
                else:
                    base_color = (255, 75, 75)
                activation = min(1.0, abs(float(neuron.out)))
                brightness = 0.3 + activation * 0.7
                color = tuple(round(channel * brightness) for channel in base_color)
                pygame.draw.rect(
                    surface,
                    color,
                    (cell_left, cell_top, cell_size, cell_size),
                )

        for boundary in (len(input_indices), len(input_indices) + len(hidden_indices)):
            if 0 < boundary < neuron_count:
                x = bounds.left + 6 + boundary * column_width // neuron_count
                pygame.draw.line(
                    surface,
                    (130, 170, 170),
                    (x, row_top),
                    (x, bounds.bottom - 4),
                    1,
                )

    def draw_dashboard(
        self,
        surface,
        active_count,
        best_live,
        record,
        mutation_rate,
        objects,
        paused=False,
    ):
        """Render status, mutation controls, lifetime values, and neural signals."""
        text = self.text
        panel = pygame.Rect(505, 0, 135, 480)
        pygame.draw.rect(surface, (10, 17, 29), panel)
        pygame.draw.line(surface, (25, 54, 68), (505, 0), (505, 480), 2)
        pygame.draw.line(surface, (24, 37, 53), (518, 48), (627, 48))

        text(surface, "BUGZ", (518, 10), (235, 248, 255), self.font_20)
        text(surface, "NEURAL SWARM", (519, 34), (93, 191, 197), self.font_10)

        status_color = (67, 220, 170) if active_count else (255, 174, 76)
        status_label = "● LIVE" if active_count else "● RESPAWNING"
        pygame.draw.rect(surface, (19, 34, 43), (516, 57, 112, 31), border_radius=6)
        text(surface, status_label, (523, 66), status_color, self.font_10)
        pause_hovered = self.pause_button.collidepoint(pygame.mouse.get_pos())
        pause_fill = (104, 49, 53) if paused else (28, 57, 70)
        pause_edge = (255, 112, 133) if paused else (70, 220, 205)
        if pause_hovered:
            pause_fill = (132, 59, 65) if paused else (38, 77, 91)
        pygame.draw.rect(surface, pause_fill, self.pause_button, border_radius=5)
        pygame.draw.rect(surface, pause_edge, self.pause_button, 1, border_radius=5)
        pause_label = "PLAY" if paused else "PAUSE"
        pause_text = self.font_8.render(pause_label, True, (245, 248, 255))
        surface.blit(pause_text, pause_text.get_rect(center=self.pause_button.center))

        pygame.draw.rect(surface, (15, 25, 39), (513, 99, 119, 70), border_radius=8)
        pygame.draw.rect(surface, (28, 57, 70), (513, 99, 119, 70), 1, border_radius=8)
        text(surface, "RADIATION", (522, 108), (130, 158, 177), self.font_10)
        text(surface, f"{mutation_rate:.2f}x", (575, 105), (255, 190, 82), self.font_14)
        pygame.draw.rect(surface, (32, 48, 62), self.radiation_slider, border_radius=4)
        fill_width = round(self.radiation_slider.width * mutation_rate / 2)
        if fill_width:
            pygame.draw.rect(
                surface,
                (255, 165, 65),
                (
                    self.radiation_slider.left,
                    self.radiation_slider.top,
                    fill_width,
                    self.radiation_slider.height,
                ),
                border_radius=4,
            )
        knob_x = self.radiation_slider.left + fill_width
        pygame.draw.circle(
            surface,
            (255, 239, 205),
            (knob_x, self.radiation_slider.centery),
            6,
        )
        pygame.draw.circle(
            surface,
            (255, 165, 65),
            (knob_x, self.radiation_slider.centery),
            6,
            1,
        )
        text(surface, "0x", (520, 149), (114, 139, 158), self.font_10)
        text(surface, "2x", (611, 149), (114, 139, 158), self.font_10)

        pygame.draw.rect(surface, (15, 25, 39), (513, 180, 119, 83), border_radius=8)
        pygame.draw.rect(surface, (28, 57, 70), (513, 180, 119, 83), 1, border_radius=8)
        text(surface, "FIELD STATUS", (522, 189), (130, 158, 177), self.font_10)
        text(surface, "ALIVE", (522, 207), (114, 139, 158), self.font_10)
        text(surface, f"{active_count:02d}", (582, 202), (90, 232, 198), self.font_14)
        text(surface, "BEST / RECORD", (522, 232), (114, 139, 158), self.font_10)
        text(
            surface,
            f"{best_live:03d} / {record:03d}",
            (522, 246),
            (235, 248, 255),
            self.font_10,
        )

        pygame.draw.rect(surface, (15, 25, 39), (513, 274, 119, 119), border_radius=8)
        pygame.draw.rect(surface, (28, 57, 70), (513, 274, 119, 119), 1, border_radius=8)
        text(surface, "NEURAL SIGNAL", (522, 283), (130, 158, 177), self.font_10)
        active_network = next(
            (obj.Ann for obj in objects if obj.death == 0),
            None,
        )
        if active_network is None:
            text(surface, "awaiting signal", (522, 316), (94, 117, 137), self.font_10)
        else:
            for index, neuron in enumerate(active_network.neurons[:active_network.hiddenSize][:9]):
                y = 302 + index * 9
                pygame.draw.line(surface, (35, 51, 65), (542, y + 3), (619, y + 3), 3)
                value = max(-1, min(1, neuron.out))
                center_x = 580
                end_x = round(center_x + value * 37)
                color = (72, 222, 194) if value >= 0 else (255, 112, 133)
                pygame.draw.line(surface, color, (center_x, y + 3), (end_x, y + 3), 3)
                pygame.draw.circle(surface, color, (end_x, y + 3), 2)

        pygame.draw.line(surface, (24, 37, 53), (518, 407), (627, 407))
        hovered = self.edit_button.collidepoint(pygame.mouse.get_pos())
        fill = (24, 76, 80) if hovered else (17, 43, 52)
        border = (70, 220, 205) if hovered else (35, 91, 101)
        pygame.draw.rect(surface, fill, self.edit_button, border_radius=6)
        pygame.draw.rect(surface, border, self.edit_button, 1, border_radius=6)
        text(surface, "EDIT NETWORK", (535, 418), (224, 245, 242), self.font_10)
        text(surface, "LMB mutate   //   RMB reset", (519, 449), (115, 145, 161), self.font_9)
        self.draw_neural_activity(surface, objects)
