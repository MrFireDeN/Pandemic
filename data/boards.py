from __future__ import annotations

import json
from typing import TYPE_CHECKING

from data.enums import ColorType

if TYPE_CHECKING:
    from data.cities import CityGame
    from data.decks import CardGame
    from data.players import PlayerGame

class Board:
    def __init__(self, game):
        """
        Board — состояние игровой партии.
        """
        self.game = game
        self.code = game.code

        self.turn_order: int = 0
        
        self.outbreak_indicator: int = 0
        self.infection_indicator: int = 0
        
        self.cubes_per_color = {color: 24 for color in ColorType}
        self.vaccines_state = {color: 0 for color in ColorType}

        self.is_game_over = False

    def add_outbreak(self):
        """Увеличивает счётчик вспышек."""
        self.outbreak_indicator += 1
        if self.outbreak_indicator >= 8:
            self.trigger_game_over()

    def add_infection_epidemic(self):
        """Увеличивает индикатор эпидемии (эпидемия карты EPIDEMIC)."""
        self.infection_indicator += 1

    def use_cube(self, color: ColorType, count: int = 1):
        """
        Использует кубики для болезни определенного цвета.
        
        :param color: Цвет болезни.
        :param count: Количество кубиков для использования.
        """
        if self.cubes_per_color[color] >= count:
            self.cubes_per_color[color] -= count
            print(f"Использовано {count} кубиков цвета {color.name}. Осталось: {self.cubes_per_color[color]}")
        else:
            self.trigger_game_over()

    def return_cube(self, color: ColorType, count: int = 1):
        """
        Возвращает кубики обратно в запасы.
        
        :param color: Цвет болезни.
        :param count: Количество кубиков для возврата.
        """
        self.cubes_per_color[color] += count
        print(f"Возвращено {count} кубиков цвета {color.name}. Осталось: {self.cubes_per_color[color]}")
        
        if self.cubes_per_color[color] >= 24 and self.vaccines_state[color] == 1:
            self.cure_upgraded(color)

    def cure_discovered(self, color: ColorType):
        """
        Открытие лекарства от болезни определенного цвета.
        
        :param color: Цвет болезни.
        """
        self.vaccines_state[color] = 1
        print(f"Лекарство для {color.name} создано!")

    def cure_upgraded(self, color: ColorType):
        """
        Лекарство от болезни определенного цвета уничтожает болезнь.
        
        :param color: Цвет болезни.
        """
        self.vaccines_state[color] = 2
        print(f"Лекарство для {color.name} улучшено и болезнь уничтожена!")

    def trigger_game_over(self, is_victory=False):
        """
        Завершается игра и уведомляется об этом всех участников.
        
        :param is_victory: Если True, игра завершена победой, если False — поражением.
        """
        self.is_game_over = True
    
        result = "Победа" if is_victory else "Поражение"
        print(f"Игра завершена: {result}")
    
        self.game.notify_game_over(is_victory)


    def log_action(self):
        pass

    def serialize(self):
        return json.dumps({
            'code': self.code,
            'turn_order': self.turn_order,
            'outbreak_indicator': self.outbreak_indicator,
            'infection_indicator': self.infection_indicator,
            'cubes_per_color': {color.name: count for color, count in self.cubes_per_color.items()},
            'vaccines_state': {color.name: state for color, state in self.vaccines_state.items()},
            'is_game_over': self.is_game_over,
        })
    
    @staticmethod
    def deserialize(game, data):
        """
        Восстанавливает доску из данных.
        
        :param data: Данные доски (строка JSON или уже распарсенный словарь).
        :param game: Игра, к которой относится доска.
        """
        if isinstance(data, str):
            # Если данные — строка, парсим их
            data = json.loads(data)
    
        board = Board(game)
        board.turn_order = data['turn_order']
        board.outbreak_indicator = data['outbreak_indicator']
        board.infection_indicator = data['infection_indicator']
        board.cubes_per_color = {ColorType[color]: count for color, count in data["cubes_per_color"].items()}
        board.vaccines_state = {ColorType[color]: state for color, state in data["vaccines_state"].items()}
    
        return board
