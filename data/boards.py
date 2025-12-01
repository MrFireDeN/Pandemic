from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data.enums import RoleType, ColorType
    from data.cities import CityGame
    from data.decks import CardGame

class Board:
    def __init__(self, game):
        """
        Board — состояние игровой партии.
        code — это game_id (game_sessions.code).
        """
        self.game = game
        self.code = game.code

        self.turn_order: int = 0
        self.outbreak_indicator: int = 0
        self.infection_indicator: int = 0
        self.research_stations: int = 0
        self.cubes_per_color: list[int] = [24, 24, 24, 24]
        self.vaccines_state: list[int] = [0, 0, 0, 0]

        self.is_game_over: bool = False

    def add_outbreak(self):
        """Увеличивает счётчик вспышек."""
        self.outbreak_indicator += 1

    def add_infection_epidemic(self):
        """Увеличивает индикатор эпидемии (эпидемия карты EPIDEMIC)."""
        self.infection_indicator += 1

    def use_cube(self, color_index: int, count: int = 1):
        """
        color_index — 0=blue, 1=yellow, 2=black, 3=red
        уменьшает количество доступных кубиков.
        """
        self.cubes_per_color[color_index] = max(
            0,
            self.cubes_per_color[color_index] - count
        )

    def return_cube(self, color_index: int, count: int = 1):
        self.cubes_per_color[color_index] += count

    def cure_discovered(self, color: str | ColorEnumDB):
        """Лекарство создано."""
        if isinstance(color, ColorEnumDB):
            color = color.value
            
        if color == ColorEnumDB.red:
            self.vaccines_state[0] = 1
        if color == ColorEnumDB.yellow:
            self.vaccines_state[1] = 1
        if color == ColorEnumDB.blue:
            self.vaccines_state[2] = 1
        if color == ColorEnumDB.black:
            self.vaccines_state[3] = 1

    def cure_upgraded(self, color_index: int):
        """Лекарство уничтожило болезнь."""
        self.vaccines_state[color_index] = 2

    def trigger_game_over(self, is_victory=False):
        pass

    def log_action(self):
        pass

    def serialize(self):
        pass

    def deserialize(self):
        pass
