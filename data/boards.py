import json
from typing import TYPE_CHECKING

from eng import db
from models import GameState


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

    def cure_discovered(self, color_index: int):
        """Лекарство создано."""
        self.vaccines_state[color_index] = 1

    def cure_upgraded(self, color_index: int):
        """Лекарство уничтожило болезнь."""
        self.vaccines_state[color_index] = 2

    def load_from_db(self):
        gs = GameState.query.filter_by(game_id=self.code).first()
        
        if gs is None:
            raise RuntimeError(f"GameState for game '{self.code}' not found")

        self.turn_order = gs.turn_order
        self.outbreak_indicator = gs.outbreak_indicator
        self.infection_indicator = gs.infection_indicator
        self.research_stations = gs.research_stations

        self.cubes_per_color = json.loads(gs.cubes_per_color)
        self.vaccines_state = json.loads(gs.vaccines_state)

        return self

    def save_to_db(self):
        gs: GameState | None = GameState.query.filter_by(game_id=self.code).first()
        if gs is None:
            raise RuntimeError(f"GameState for game '{self.code}' not found")

        gs.turn_order = self.turn_order
        gs.outbreak_indicator = self.outbreak_indicator
        gs.infection_indicator = self.infection_indicator
        gs.research_stations = self.research_stations

        gs.cubes_per_color = json.dumps(self.cubes_per_color)
        gs.vaccines_state = json.dumps(self.vaccines_state)

        db.session.commit()
