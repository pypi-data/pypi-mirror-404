"""Graphics rendering using pygame."""

import hashlib
import itertools
import math
import os
import random
import struct
import sys
from collections import deque
from functools import cached_property

from sneks.engine.config.base import Config
from sneks.engine.config.graphics import GraphicsConfig, TailDecorationBehavior
from sneks.engine.core.cell import Cell
from sneks.engine.entity.base import Entity
from sneks.engine.entity.dynamic import DynamicEntity
from sneks.engine.entity.static import StaticEntity
from sneks.engine.manager.cell import CellManager
from sneks.engine.recorder import Recorder

# Set this flag to avoid the pygame community console text
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
from pygame import Surface


class Graphics:
    """Responsible for maintaining the graphics."""

    recorder: Recorder
    ended_head_splashes: deque[list[Cell]]

    def __init__(self) -> None:
        if not Config().graphics.display:
            return

        if Config().graphics.headless:
            os.environ["SDL_VIDEODRIVER"] = "dummy"

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(Config().title)
        self.recorder = Recorder()
        self.ended_head_splashes = deque(maxlen=10)

    def start(self) -> None:
        if not Config().graphics.display:
            return

    def paint(self, entities: list[Entity]) -> None:
        if not Config().graphics.display:
            return

        self._paint_board()
        if Config().graphics.draw_stars:
            self._paint_stars()

        ended_entities = []
        for entity in reversed(entities):
            match entity:
                case StaticEntity():
                    self.paint_static_entity(entity)
                case DynamicEntity():
                    if entity.ended_this_step:
                        ended_entities.append(entity.head)
                    self.paint_dynamic_entity(entity)
                case _:
                    raise RuntimeError

        self.ended_head_splashes.appendleft(ended_entities)
        self.paint_head_splashes()

        # check for exit conditions
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        # switch to the most recently drawn board
        pygame.display.flip()
        self.recorder.record_frame(self.screen)
        self.step_delay()

    def paint_static_entity(self, entity: StaticEntity) -> None:
        """Paint a blob with all cells connecting."""
        surface = Surface(
            (self.cell_size + self.padding, self.cell_size + self.padding)
        )
        surface.fill(entity.color)

        for cell in entity.position_cells:
            rect = self.get_cell_rect_from_surface(
                surface, cell, surface_has_padding=True
            )
            self.screen.blit(surface, rect)

    def paint_dynamic_entity(self, entity: DynamicEntity) -> None:
        """Paint a line using the visible deque."""
        cell_surface = Surface(
            (self.cell_size - self.padding, self.cell_size - self.padding)
        )
        horizontal_fill_surface = Surface(
            (self.padding * 2, self.cell_size - self.padding)
        )
        vertical_fill_surface = Surface(
            (self.cell_size - self.padding, self.padding * 2)
        )
        cell_surface.fill(entity.color)
        horizontal_fill_surface.fill(entity.color)
        vertical_fill_surface.fill(entity.color)

        # Determine which cells to draw
        iterables = []
        if TailDecorationBehavior.POSITION in Config().graphics.tail_decoration:
            iterables.append(entity.position_cells)
        if TailDecorationBehavior.COLLIDING in Config().graphics.tail_decoration:
            iterables.append(entity.head_colliding_cells)
            iterables.append(entity.tail_colliding_cells)
        if TailDecorationBehavior.DECORATIVE in Config().graphics.tail_decoration:
            iterables.append(entity.decorative_cells)

        color = entity.color
        previous: Cell | None = None
        start_gradiant_index = len(entity.position_cells)
        for i, cell in enumerate(itertools.chain(*iterables)):
            if i >= start_gradiant_index:
                color = tuple(int(c * 0.95) for c in color)
                cell_surface.fill(color)
                horizontal_fill_surface.fill(color)
                vertical_fill_surface.fill(color)

            # Blit cell
            rect = self.get_cell_rect_from_surface(surface=cell_surface, cell=cell)
            self.screen.blit(cell_surface, rect)

            # Blit padding
            self.blit_padding(
                cell=cell,
                previous=previous,
                horizontal_fill_surface=horizontal_fill_surface,
                vertical_fill_surface=vertical_fill_surface,
            )

            previous = cell

        # Blit head in distinct color
        if entity.ended:
            color = self.color_invalid
        else:
            color = struct.unpack(
                "BBB", hashlib.md5(struct.pack("BBB", *entity.color)).digest()[-3:]
            )
        cell_surface.fill(color)
        rect = self.get_cell_rect_from_surface(surface=cell_surface, cell=entity.head)
        self.screen.blit(cell_surface, rect)

    def paint_head_splashes(self) -> None:
        cell_surface = Surface(
            (self.cell_size - self.padding, self.cell_size - self.padding)
        )
        cell_surface.fill(self.color_invalid)
        for i, ended in enumerate(self.ended_head_splashes):
            for cell in ended:
                rect = self.get_cell_rect_from_surface(surface=cell_surface, cell=cell)
                self.screen.blit(cell_surface, rect)

                cell_surface.fill(tuple(int((0.85**i) * c) for c in self.color_invalid))

                splash_cells = [
                    CellManager.get_absolute_by_offset(
                        cell=cell, x_offset=x, y_offset=y
                    )
                    for x, y in itertools.product(
                        range(-int(i / 2), int(i / 2)), repeat=2
                    )
                ]
                for c in splash_cells:
                    rect = self.get_cell_rect_from_surface(surface=cell_surface, cell=c)
                    self.screen.blit(cell_surface, rect)

    def blit_padding(
        self,
        cell: Cell,
        previous: Cell | None,
        horizontal_fill_surface: Surface,
        vertical_fill_surface: Surface,
    ) -> None:
        # Blit padding
        if previous is not None:
            # Check if cell loops around the game board
            looped = abs(cell.x - previous.x) + abs(cell.y - previous.y) > 1

            relative = CellManager.get_relative_to(cell, previous)
            dx = min(1, max(relative.x, -1))
            dy = min(1, max(relative.y, -1))
            match (dx, dy):
                case (1, 0):
                    # cell is to the right, so fill left
                    rect = self.get_left_fill_from_surface(
                        surface=horizontal_fill_surface, cell=cell
                    )
                    self.screen.blit(horizontal_fill_surface, rect)
                    if looped:
                        # fill right of previous
                        rect = self.get_right_fill_from_surface(
                            surface=horizontal_fill_surface, cell=previous
                        )
                        self.screen.blit(horizontal_fill_surface, rect)
                case (-1, 0):
                    # cell is to the left, so fill right
                    rect = self.get_right_fill_from_surface(
                        surface=horizontal_fill_surface, cell=cell
                    )
                    self.screen.blit(horizontal_fill_surface, rect)
                    if looped:
                        # fill left of previous
                        rect = self.get_left_fill_from_surface(
                            surface=horizontal_fill_surface, cell=previous
                        )
                        self.screen.blit(horizontal_fill_surface, rect)
                case (0, 1):
                    # cell is up, so fill down
                    rect = self.get_down_fill_from_surface(
                        surface=vertical_fill_surface, cell=cell
                    )
                    self.screen.blit(vertical_fill_surface, rect)
                    if looped:
                        # fill up of previous
                        rect = self.get_up_fill_from_surface(
                            surface=vertical_fill_surface, cell=previous
                        )
                        self.screen.blit(vertical_fill_surface, rect)
                case (0, -1):
                    # cell is down, so fill up
                    rect = self.get_up_fill_from_surface(
                        surface=vertical_fill_surface, cell=cell
                    )
                    self.screen.blit(vertical_fill_surface, rect)
                    if looped:
                        # fill down of previous
                        rect = self.get_down_fill_from_surface(
                            surface=vertical_fill_surface, cell=previous
                        )
                        self.screen.blit(vertical_fill_surface, rect)

    def get_cell_rect_from_surface(
        self, surface: Surface, cell: Cell, surface_has_padding: bool = False
    ) -> pygame.Rect:
        offset = self.cell_size + (0 if surface_has_padding else self.padding)
        return surface.get_rect(
            top=offset
            + (Config().world.rows - cell.y - 1) * (self.cell_size + self.padding),
            left=offset + cell.x * (self.cell_size + self.padding),
        )

    def get_left_fill_from_surface(self, surface: Surface, cell: Cell) -> pygame.Rect:
        return surface.get_rect(
            top=self.cell_size
            + (Config().world.rows - cell.y - 1) * (self.cell_size + self.padding)
            + self.padding,
            left=self.cell_size
            + cell.x * (self.cell_size + self.padding)
            - self.padding,
        )

    def get_right_fill_from_surface(self, surface: Surface, cell: Cell) -> pygame.Rect:
        return surface.get_rect(
            top=self.cell_size
            + (Config().world.rows - cell.y - 1) * (self.cell_size + self.padding)
            + self.padding,
            left=self.cell_size
            + (cell.x + 1) * (self.cell_size + self.padding)
            - self.padding,
        )

    def get_down_fill_from_surface(self, surface: Surface, cell: Cell) -> pygame.Rect:
        return surface.get_rect(
            top=self.cell_size
            + (Config().world.rows - cell.y) * (self.cell_size + self.padding)
            - self.padding,
            left=self.cell_size
            + cell.x * (self.cell_size + self.padding)
            + self.padding,
        )

    def get_up_fill_from_surface(self, surface: Surface, cell: Cell) -> pygame.Rect:
        return surface.get_rect(
            top=self.cell_size
            + (Config().world.rows - cell.y - 1) * (self.cell_size + self.padding)
            - self.padding,
            left=self.cell_size
            + cell.x * (self.cell_size + self.padding)
            + self.padding,
        )

    def _paint_board(self) -> None:
        self.screen.fill(self.color_background)
        # borders
        top = (
            0,
            0,
            self.width,
            self.cell_size - self.padding,
        )
        bottom = (
            0,
            self.height - self.cell_size + self.padding,
            self.width,
            self.height,
        )
        left = (
            0,
            self.cell_size - self.padding,
            self.cell_size - self.padding,
            self.height,
        )
        right = (
            self.width - self.cell_size + self.padding,
            0,
            self.width,
            self.height,
        )
        for rect in (top, bottom, left, right):
            pygame.draw.rect(self.screen, self.color_border, rect)

    def _paint_stars(self) -> None:
        for center in self.stars:
            modifier = math.prod(center) % (256 - max(self.color_background))
            pygame.draw.circle(
                surface=self.screen,
                color=tuple(modifier + c for c in self.color_background),
                center=center,
                radius=1.0,
            )

    def end(self) -> None:
        if not Config().graphics.display:
            return

        self.end_delay()
        self.recorder.animate_game()

    @property
    def rows(self) -> int:
        return Config().world.rows

    @property
    def columns(self) -> int:
        return Config().world.columns

    @property
    def cell_size(self) -> int:
        return Config().graphics.cell_size

    @property
    def padding(self) -> int:
        return Config().graphics.padding

    @property
    def color_border(self) -> tuple[int, int, int]:
        return Config().graphics.colors.border

    @property
    def color_background(self) -> tuple[int, int, int]:
        return Config().graphics.colors.background

    @property
    def color_invalid(self) -> tuple[int, int, int]:
        return Config().graphics.colors.invalid

    @property
    def height(self) -> int:
        return (2 + self.rows) * self.cell_size + self.rows * self.padding

    @property
    def width(self) -> int:
        return (2 + self.columns) * self.cell_size + self.columns * self.padding

    @cached_property
    def stars(self) -> list[tuple[int, int]]:
        return [
            (
                random.randint(
                    self.cell_size + self.padding,
                    self.width - self.cell_size - self.padding,
                ),
                random.randint(
                    self.cell_size + self.padding,
                    self.height - self.cell_size - self.padding,
                ),
            )
            for _ in range(self.rows + self.columns)
        ]

    def step_delay(self):
        if not Config().graphics.headless:
            if Config().graphics.step_keypress_wait:
                self.wait_for_keypress()
            pygame.time.delay(Config().graphics.step_delay)

    def end_delay(self):
        if not Config().graphics.headless:
            if Config().graphics.end_keypress_wait:
                self.wait_for_keypress()
            pygame.time.delay(Config().graphics.end_delay)

    @staticmethod
    def wait_for_keypress():
        while True:
            # allow the key to be held instead of waiting for each step
            if any(pygame.key.get_pressed()):
                break
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                break


def generate_poster():
    """Draw the game board with nothing on it and save the image."""
    Config(
        graphics=GraphicsConfig(
            headless=True,
            record=True,
        ),
    )
    graphics = Graphics()
    graphics.paint([])
